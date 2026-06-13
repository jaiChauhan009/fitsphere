"""
Nutrition log CRUD + daily summary + history tests.
All state mutations use the shared in-memory SQLite DB.
"""
import pytest
from datetime import date, timedelta


# ── helpers ───────────────────────────────────────────────────────────────────

def _meal_payload(**overrides):
    base = {
        "food_name": "Test Rice",
        "meal_type": "lunch",
        "quantity_g": 200,
        "calories": 432,
        "protein_g": 10,
        "carbs_g": 90,
        "fat_g": 3.6,
        "fiber_g": 7,
        "log_date": date.today().isoformat(),
    }
    base.update(overrides)
    return base


# ── POST /nutrition/log ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_meal_success(client):
    r = await client.post("/nutrition/log", json=_meal_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["food_name"] == "Test Rice"
    assert body["meal_type"] == "lunch"
    assert body["calories"] == 432
    assert "id" in body
    assert "user_id" in body
    assert "logged_at" in body


@pytest.mark.asyncio
async def test_log_meal_breakfast(client):
    r = await client.post("/nutrition/log", json=_meal_payload(
        food_name="Oatmeal", meal_type="breakfast", calories=300,
        protein_g=12, carbs_g=54, fat_g=6
    ))
    assert r.status_code == 200, r.text
    assert r.json()["meal_type"] == "breakfast"


@pytest.mark.asyncio
async def test_log_meal_with_food_id(client):
    """Log with a valid food_id (from seeded Banana) links correctly."""
    from unittest.mock import patch, AsyncMock
    # First get a real food id
    with patch("routers.food.search_usda", new=AsyncMock(return_value=[])):
        s = await client.get("/food/search", params={"q": "banana"})
    food_id = s.json()[0]["id"]

    r = await client.post("/nutrition/log", json=_meal_payload(
        food_name="Banana", food_id=food_id, meal_type="snack",
        calories=89, protein_g=1.1, carbs_g=23, fat_g=0.3
    ))
    assert r.status_code == 200, r.text
    assert r.json()["food_id"] == food_id


@pytest.mark.asyncio
async def test_log_meal_zero_quantity_rejected(client):
    """quantity_g must be > 0 (Pydantic Field gt=0)."""
    r = await client.post("/nutrition/log", json=_meal_payload(quantity_g=0))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_log_meal_missing_food_name(client):
    payload = _meal_payload()
    del payload["food_name"]
    r = await client.post("/nutrition/log", json=payload)
    assert r.status_code == 422


# ── GET /nutrition/daily/{date} ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_daily_summary_today(client):
    today = date.today().isoformat()
    # Log a meal first to ensure the day is non-empty
    await client.post("/nutrition/log", json=_meal_payload(
        food_name="Daily Summary Food", calories=500, protein_g=20,
        carbs_g=70, fat_g=10, log_date=today
    ))

    r = await client.get(f"/nutrition/daily/{today}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["date"] == today
    assert body["total_calories"] >= 500
    assert "total_protein_g" in body
    assert "calorie_target" in body
    assert "calorie_remaining" in body
    assert "meals" in body
    assert "nutrient_completion" in body
    assert isinstance(body["meals"], dict)


@pytest.mark.asyncio
async def test_daily_summary_empty_day(client):
    """A day with no logs still returns a valid summary (all zeros)."""
    past_date = (date.today() - timedelta(days=99)).isoformat()
    r = await client.get(f"/nutrition/daily/{past_date}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_calories"] == 0
    assert body["total_protein_g"] == 0


@pytest.mark.asyncio
async def test_daily_summary_meals_bucketed(client):
    """Meals are grouped by meal_type in the response."""
    today = date.today().isoformat()
    await client.post("/nutrition/log", json=_meal_payload(
        food_name="Dinner Item", meal_type="dinner", calories=600, log_date=today
    ))
    r = await client.get(f"/nutrition/daily/{today}")
    assert r.status_code == 200
    meals = r.json()["meals"]
    assert "dinner" in meals
    assert len(meals["dinner"]) >= 1


# ── GET /nutrition/history ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nutrition_history_default(client):
    r = await client.get("/nutrition/history")
    assert r.status_code == 200, r.text
    logs = r.json()
    assert isinstance(logs, list)
    # Should have at least the logs we created in other tests
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_nutrition_history_single_day(client):
    """days=1 returns only today's logs."""
    r = await client.get("/nutrition/history", params={"days": 1})
    assert r.status_code == 200
    logs = r.json()
    today = date.today().isoformat()
    for log in logs:
        assert log["log_date"] == today


@pytest.mark.asyncio
async def test_nutrition_history_max_days_exceeded(client):
    """days > 90 is rejected (Query le=90)."""
    r = await client.get("/nutrition/history", params={"days": 91})
    assert r.status_code == 422


# ── DELETE /nutrition/log/{log_id} ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_nutrition_log(client):
    # Create a log, then delete it
    r_create = await client.post("/nutrition/log", json=_meal_payload(
        food_name="To Be Deleted", calories=100
    ))
    log_id = r_create.json()["id"]

    r_delete = await client.delete(f"/nutrition/log/{log_id}")
    assert r_delete.status_code == 200, r_delete.text
    assert r_delete.json()["deleted"] == log_id

    # Verify it's gone from history
    r_history = await client.get("/nutrition/history")
    ids = [l["id"] for l in r_history.json()]
    assert log_id not in ids


@pytest.mark.asyncio
async def test_delete_nonexistent_log(client):
    r = await client.delete("/nutrition/log/nonexistent-log-id")
    assert r.status_code == 404
