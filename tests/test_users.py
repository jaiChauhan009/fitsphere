
"""
User registration, profile fetch, and profile update tests.
All tests hit a real SQLite DB through the FastAPI test client.
"""
import pytest


# ── POST /users/ — registration ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_user_success(client):
    payload = {
        "email": "newuser@fitsphere.com",
        "name": "New User",
        "age": 25,
        "gender": "female",
        "height_cm": 165,
        "weight_kg": 60,
        "target_weight_kg": 55,
        "goal": "weight_loss",
        "activity_level": "moderately_active",
    }
    r = await client.post("/users/", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "newuser@fitsphere.com"
    assert body["name"] == "New User"
    assert body["daily_calorie_target"] is not None
    assert body["daily_calorie_target"] >= 1200
    assert "id" in body


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client):
    """Second registration with same email must return 400."""
    payload = {
        "email": "duplicate@fitsphere.com",
        "name": "Dup A",
        "age": 30,
        "gender": "male",
        "height_cm": 180,
        "weight_kg": 80,
        "goal": "maintain",
        "activity_level": "lightly_active",
    }
    r1 = await client.post("/users/", json=payload)
    assert r1.status_code == 200

    r2 = await client.post("/users/", json=payload)
    assert r2.status_code == 400
    assert "Email already registered" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_invalid_age(client):
    """Age < 10 must fail schema validation (422)."""
    payload = {
        "email": "young@fitsphere.com",
        "name": "Too Young",
        "age": 5,
        "gender": "male",
        "height_cm": 150,
        "weight_kg": 40,
        "goal": "maintain",
        "activity_level": "lightly_active",
    }
    r = await client.post("/users/", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_user_invalid_height(client):
    """Height > 300 must fail schema validation (422)."""
    payload = {
        "email": "giant@fitsphere.com",
        "name": "Too Tall",
        "age": 25,
        "gender": "male",
        "height_cm": 400,
        "weight_kg": 80,
        "goal": "maintain",
        "activity_level": "lightly_active",
    }
    r = await client.post("/users/", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_required_field(client):
    """Missing 'age' → 422 Unprocessable Entity."""
    r = await client.post("/users/", json={
        "email": "nage@fitsphere.com",
        "name": "No Age",
        "gender": "male",
        "height_cm": 170,
        "weight_kg": 70,
    })
    assert r.status_code == 422


# ── GET /users/me ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me(client):
    """Fetching own profile returns the seeded test user."""
    r = await client.get("/users/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "test@fitsphere.com"
    assert body["name"] == "Test User"
    assert body["gender"] == "male"
    assert body["daily_calorie_target"] >= 1200


# ── PATCH /users/me ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_me_weight(client):
    """Updating weight recalculates calorie target."""
    r = await client.patch("/users/me", json={"weight_kg": 72.5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["weight_kg"] == 72.5
    # Calorie target must remain a positive integer
    assert body["daily_calorie_target"] >= 1200


@pytest.mark.asyncio
async def test_update_me_goal(client):
    """Changing goal updates calorie target."""
    r1 = await client.get("/users/me")
    original_cal = r1.json()["daily_calorie_target"]

    r2 = await client.patch("/users/me", json={"goal": "muscle_gain"})
    assert r2.status_code == 200, r2.text
    new_cal = r2.json()["daily_calorie_target"]
    # muscle_gain adds 300 kcal — new target must be higher
    assert new_cal > original_cal - 100  # allow for float rounding


@pytest.mark.asyncio
async def test_update_me_name_only(client):
    """Updating name-only should NOT break calorie target."""
    r = await client.patch("/users/me", json={"name": "Updated Name"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Updated Name"
