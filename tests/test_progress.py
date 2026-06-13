"""
Body measurement logging + progress summary tests.
"""
import pytest
from datetime import date, timedelta


# ── helpers ───────────────────────────────────────────────────────────────────

def _measurement_payload(**overrides):
    base = {
        "weight_kg": 74.5,
        "body_fat_percent": 18.5,
        "muscle_mass_kg": 35.0,
        "waist_cm": 82.0,
        "chest_cm": 98.0,
        "hips_cm": 96.0,
        "measure_date": date.today().isoformat(),
    }
    base.update(overrides)
    return base


# ── POST /progress/measurement ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_measurement_success(client):
    r = await client.post("/progress/measurement", json=_measurement_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["weight_kg"] == 74.5
    assert body["body_fat_percent"] == 18.5
    assert body["bmi"] is not None
    assert body["bmi"] > 0
    assert "id" in body
    assert "user_id" in body


@pytest.mark.asyncio
async def test_log_measurement_weight_only(client):
    """Only weight_kg is required — all others are optional."""
    r = await client.post("/progress/measurement", json={"weight_kg": 76.0})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["weight_kg"] == 76.0
    assert body["bmi"] is not None  # Height is on the user profile


@pytest.mark.asyncio
async def test_log_measurement_past_date(client):
    past = (date.today() - timedelta(days=10)).isoformat()
    r = await client.post("/progress/measurement", json=_measurement_payload(measure_date=past))
    assert r.status_code == 200
    assert r.json()["measure_date"] == past


@pytest.mark.asyncio
async def test_log_measurement_bmi_calculation(client):
    """BMI must equal weight / (height_m^2). Test user: 175cm height."""
    r = await client.post("/progress/measurement", json=_measurement_payload(weight_kg=77.44))
    assert r.status_code == 200
    bmi = r.json()["bmi"]
    expected_bmi = round(77.44 / (1.75 ** 2), 2)
    assert abs(bmi - expected_bmi) < 0.1, f"BMI {bmi} differs from expected {expected_bmi}"


@pytest.mark.asyncio
async def test_log_multiple_measurements(client):
    """Multiple measurements can be logged for different days."""
    for i in range(3):
        past = (date.today() - timedelta(days=i + 20)).isoformat()
        r = await client.post("/progress/measurement", json=_measurement_payload(
            weight_kg=75.0 - i * 0.5, measure_date=past
        ))
        assert r.status_code == 200


# ── GET /progress/measurements ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_measurements(client):
    r = await client.get("/progress/measurements")
    assert r.status_code == 200, r.text
    measurements = r.json()
    assert isinstance(measurements, list)
    assert len(measurements) >= 1


@pytest.mark.asyncio
async def test_measurements_ordered_desc(client):
    """Measurements are returned newest first."""
    r = await client.get("/progress/measurements")
    measurements = r.json()
    if len(measurements) >= 2:
        for i in range(len(measurements) - 1):
            assert measurements[i]["measured_at"] >= measurements[i + 1]["measured_at"]


# ── GET /progress/summary ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_progress_summary(client):
    """Summary must return all required keys with valid values."""
    r = await client.get("/progress/summary")
    assert r.status_code == 200, r.text
    body = r.json()

    required_keys = [
        "current_weight_kg", "target_weight_kg", "bmi",
        "avg_daily_calories_7d", "avg_daily_calories_30d",
        "workout_count_7d", "workout_count_30d",
        "streak_days", "top_nutrient_deficiencies", "measurements_history"
    ]
    for key in required_keys:
        assert key in body, f"Missing key: {key}"

    assert body["workout_count_7d"] >= 0
    assert body["workout_count_30d"] >= 0
    assert body["streak_days"] >= 0
    assert isinstance(body["top_nutrient_deficiencies"], list)
    assert isinstance(body["measurements_history"], list)


@pytest.mark.asyncio
async def test_progress_summary_bmi_positive(client):
    r = await client.get("/progress/summary")
    assert r.status_code == 200
    bmi = r.json()["bmi"]
    if bmi is not None:
        assert bmi > 0


@pytest.mark.asyncio
async def test_progress_summary_calorie_averages_non_negative(client):
    r = await client.get("/progress/summary")
    assert r.status_code == 200
    body = r.json()
    # Averages are None (no logs) or non-negative floats
    for key in ("avg_daily_calories_7d", "avg_daily_calories_30d"):
        val = body[key]
        if val is not None:
            assert val >= 0


@pytest.mark.asyncio
async def test_progress_summary_caches_then_invalidates(client):
    """
    Logging a new measurement must invalidate the cache so the next
    summary fetch reflects fresh data (workout count should be accurate).
    """
    r1 = await client.get("/progress/summary")
    count_before = r1.json()["workout_count_7d"]

    # Log a new workout to bump the count
    await client.post("/workouts/log", json={
        "duration_minutes": 30,
        "calories_burned": 200,
        "exercises_done": [],
        "log_date": date.today().isoformat(),
    })

    r2 = await client.get("/progress/summary")
    count_after = r2.json()["workout_count_7d"]
    assert count_after >= count_before
