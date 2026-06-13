"""
Workout plans, exercises, workout log CRUD, and history tests.
"""
import pytest
from datetime import date, timedelta


# ── helpers ───────────────────────────────────────────────────────────────────

def _workout_payload(**overrides):
    base = {
        "duration_minutes": 45,
        "calories_burned": 320,
        "exercises_done": [
            {"name": "Push-up", "sets": 3, "reps": 12},
            {"name": "Squat", "sets": 4, "reps": 10},
        ],
        "notes": "Felt great",
        "log_date": date.today().isoformat(),
    }
    base.update(overrides)
    return base


# ── GET /workouts/plans ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_workout_plans(client):
    r = await client.get("/workouts/plans")
    assert r.status_code == 200, r.text
    plans = r.json()
    assert isinstance(plans, list)
    assert len(plans) >= 1
    plan = plans[0]
    assert "name" in plan
    assert "goal" in plan
    assert "difficulty" in plan


@pytest.mark.asyncio
async def test_list_workout_plans_filter_goal(client):
    r = await client.get("/workouts/plans", params={"goal": "maintain"})
    assert r.status_code == 200, r.text
    plans = r.json()
    for p in plans:
        assert p["goal"] == "maintain"


@pytest.mark.asyncio
async def test_list_workout_plans_filter_difficulty(client):
    r = await client.get("/workouts/plans", params={"difficulty": "beginner"})
    assert r.status_code == 200
    plans = r.json()
    for p in plans:
        assert p["difficulty"] == "beginner"


@pytest.mark.asyncio
async def test_list_workout_plans_no_match(client):
    """Non-existent goal returns empty list."""
    r = await client.get("/workouts/plans", params={"goal": "teleportation"})
    assert r.status_code == 200
    assert r.json() == []


# ── GET /workouts/exercises ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_exercises(client):
    r = await client.get("/workouts/exercises")
    assert r.status_code == 200, r.text
    exercises = r.json()
    assert isinstance(exercises, list)
    assert len(exercises) >= 3
    for ex in exercises:
        assert "name" in ex
        assert "category" in ex


@pytest.mark.asyncio
async def test_list_exercises_by_category(client):
    r = await client.get("/workouts/exercises", params={"category": "strength"})
    assert r.status_code == 200
    for ex in r.json():
        assert ex["category"] == "strength"


@pytest.mark.asyncio
async def test_list_exercises_by_difficulty(client):
    r = await client.get("/workouts/exercises", params={"difficulty": "beginner"})
    assert r.status_code == 200
    for ex in r.json():
        assert ex["difficulty"] == "beginner"


@pytest.mark.asyncio
async def test_list_exercises_by_equipment(client):
    r = await client.get("/workouts/exercises", params={"equipment": "none"})
    assert r.status_code == 200
    for ex in r.json():
        assert ex["equipment"] == "none"


# ── POST /workouts/log ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_workout_success(client):
    r = await client.post("/workouts/log", json=_workout_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["duration_minutes"] == 45
    assert body["calories_burned"] == 320
    assert len(body["exercises_done"]) == 2
    assert "id" in body
    assert "user_id" in body
    assert "logged_at" in body


@pytest.mark.asyncio
async def test_log_workout_no_calories(client):
    """calories_burned is optional — should succeed without it."""
    payload = _workout_payload()
    del payload["calories_burned"]
    r = await client.post("/workouts/log", json=payload)
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_log_workout_missing_duration(client):
    payload = _workout_payload()
    del payload["duration_minutes"]
    r = await client.post("/workouts/log", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_log_workout_with_plan_id(client):
    """Log a workout referencing an existing workout plan."""
    plans = (await client.get("/workouts/plans")).json()
    plan_id = plans[0]["id"]

    r = await client.post("/workouts/log", json=_workout_payload(workout_plan_id=plan_id))
    assert r.status_code == 200, r.text
    assert r.json()["workout_plan_id"] == plan_id


@pytest.mark.asyncio
async def test_log_workout_past_date(client):
    """Log a workout for a past date."""
    past = (date.today() - timedelta(days=5)).isoformat()
    r = await client.post("/workouts/log", json=_workout_payload(log_date=past))
    assert r.status_code == 200, r.text
    assert r.json()["log_date"] == past


# ── GET /workouts/history ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workout_history_default(client):
    r = await client.get("/workouts/history")
    assert r.status_code == 200, r.text
    logs = r.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1  # At least what previous tests logged


@pytest.mark.asyncio
async def test_workout_history_custom_days(client):
    r = await client.get("/workouts/history", params={"days": 7})
    assert r.status_code == 200
    logs = r.json()
    cutoff = date.today() - timedelta(days=7)
    for log in logs:
        log_date = date.fromisoformat(log["log_date"])
        assert log_date >= cutoff


@pytest.mark.asyncio
async def test_workout_history_max_days_exceeded(client):
    """days > 365 is rejected (Query le=365)."""
    r = await client.get("/workouts/history", params={"days": 400})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_workout_history_is_ordered_desc(client):
    """History is returned in descending chronological order."""
    r = await client.get("/workouts/history")
    logs = r.json()
    if len(logs) >= 2:
        for i in range(len(logs) - 1):
            assert logs[i]["logged_at"] >= logs[i + 1]["logged_at"]
