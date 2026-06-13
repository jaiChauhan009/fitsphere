"""
End-to-end user flows that chain multiple API calls together.
These test realistic sequences a mobile app would execute.
"""
import pytest
from datetime import date


# ── Flow 1: New user onboarding → log meals → check daily summary ─────────────

@pytest.mark.asyncio
async def test_flow_onboarding_to_summary(client):
    """
    Full onboarding flow:
    1. Register new user (no auth needed for /users/)
    2. Log breakfast, lunch, dinner via /nutrition/log
    3. Verify /nutrition/daily/<today> totals match what was logged
    """
    today = date.today().isoformat()

    meals = [
        {"food_name": "E2E Oats",      "meal_type": "breakfast", "calories": 350,
         "protein_g": 15, "carbs_g": 55, "fat_g": 8, "fiber_g": 5, "quantity_g": 200},
        {"food_name": "E2E Salad",     "meal_type": "lunch",     "calories": 450,
         "protein_g": 25, "carbs_g": 40, "fat_g": 15, "fiber_g": 8, "quantity_g": 300},
        {"food_name": "E2E Grilled Chicken", "meal_type": "dinner", "calories": 600,
         "protein_g": 50, "carbs_g": 20, "fat_g": 20, "fiber_g": 2, "quantity_g": 350},
    ]
    total_cal = sum(m["calories"] for m in meals)
    total_protein = sum(m["protein_g"] for m in meals)

    for meal in meals:
        r = await client.post("/nutrition/log", json={**meal, "log_date": today})
        assert r.status_code == 200, f"Failed to log {meal['food_name']}: {r.text}"

    # Fetch daily summary
    r = await client.get(f"/nutrition/daily/{today}")
    assert r.status_code == 200, r.text
    body = r.json()

    # Totals must include at least what we just logged
    assert body["total_calories"] >= total_cal
    assert body["total_protein_g"] >= total_protein
    assert body["calorie_remaining"] >= 0


# ── Flow 2: Workout logging → progress summary ────────────────────────────────

@pytest.mark.asyncio
async def test_flow_workout_then_progress(client):
    """
    1. Log 3 workouts (today + 2 past days)
    2. GET /progress/summary → workout_count_7d must include them
    """
    today = date.today()
    for i in range(3):
        log_date = (today - __import__("datetime").timedelta(days=i)).isoformat()
        r = await client.post("/workouts/log", json={
            "duration_minutes": 30 + i * 10,
            "calories_burned": 200 + i * 50,
            "exercises_done": [{"name": "Burpee", "reps": 20}],
            "log_date": log_date,
        })
        assert r.status_code == 200, f"Day -{i}: {r.text}"

    r = await client.get("/progress/summary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workout_count_7d"] >= 3


# ── Flow 3: Body measurement → BMI reflected in progress ─────────────────────

@pytest.mark.asyncio
async def test_flow_measurement_updates_weight(client):
    """
    1. Get current weight from /users/me
    2. Log a new measurement with different weight
    3. /progress/summary should reflect the new weight
    """
    me_r = await client.get("/users/me")
    assert me_r.status_code == 200

    new_weight = 73.0
    r = await client.post("/progress/measurement", json={
        "weight_kg": new_weight,
        "measure_date": date.today().isoformat(),
    })
    assert r.status_code == 200, r.text

    summary_r = await client.get("/progress/summary")
    assert summary_r.status_code == 200
    body = summary_r.json()
    # current_weight_kg reflects the most recent measurement
    assert abs(body["current_weight_kg"] - new_weight) < 0.01


# ── Flow 4: Food search → log by food_id ─────────────────────────────────────

@pytest.mark.asyncio
async def test_flow_search_food_then_log(client):
    """
    1. Search for a food item
    2. Log a meal using the returned food_id
    3. Verify it appears in history
    """
    from unittest.mock import patch, AsyncMock

    with patch("routers.food.search_usda", new=AsyncMock(return_value=[])):
        search_r = await client.get("/food/search", params={"q": "rice"})
    assert search_r.status_code == 200
    foods = search_r.json()
    assert len(foods) >= 1
    food = foods[0]

    log_r = await client.post("/nutrition/log", json={
        "food_id": food["id"],
        "food_name": food["name"],
        "meal_type": "dinner",
        "quantity_g": 150,
        "calories": (food.get("calories_per_100g") or 200) * 1.5,
        "protein_g": (food.get("protein_g") or 5) * 1.5,
        "carbs_g": (food.get("carbs_g") or 30) * 1.5,
        "fat_g": (food.get("fat_g") or 2) * 1.5,
        "fiber_g": (food.get("fiber_g") or 2) * 1.5,
        "log_date": date.today().isoformat(),
    })
    assert log_r.status_code == 200, log_r.text
    logged_id = log_r.json()["id"]

    history_r = await client.get("/nutrition/history", params={"days": 1})
    assert history_r.status_code == 200
    ids = [l["id"] for l in history_r.json()]
    assert logged_id in ids


# ── Flow 5: Full delete cycle ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_flow_log_and_delete_meal(client):
    """
    Log a meal → verify it exists → delete it → verify it's gone.
    """
    today = date.today().isoformat()
    create_r = await client.post("/nutrition/log", json={
        "food_name": "Temporary Snack",
        "meal_type": "snack",
        "quantity_g": 50,
        "calories": 120,
        "protein_g": 3,
        "carbs_g": 20,
        "fat_g": 4,
        "log_date": today,
    })
    assert create_r.status_code == 200
    log_id = create_r.json()["id"]

    # Verify it's in the daily summary
    summary = (await client.get(f"/nutrition/daily/{today}")).json()
    snacks = summary["meals"].get("snack", [])
    snack_ids = [s["id"] for s in snacks]
    assert log_id in snack_ids

    # Delete
    del_r = await client.delete(f"/nutrition/log/{log_id}")
    assert del_r.status_code == 200

    # Verify it's gone from history
    history = (await client.get("/nutrition/history", params={"days": 1})).json()
    assert log_id not in [l["id"] for l in history]
