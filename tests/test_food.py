"""
Food search, get-by-id, category listing tests.
External APIs (USDA, OpenFoodFacts) are patched so tests are offline.
"""
import pytest
from unittest.mock import patch, AsyncMock


# ── GET /food/search ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_food_search_local_hit(client):
    """Search for 'chicken' — seeded as Chicken Breast — returns local result."""
    with patch("routers.food.search_usda", new=AsyncMock(return_value=[])):
        r = await client.get("/food/search", params={"q": "chicken"})
    assert r.status_code == 200, r.text
    foods = r.json()
    assert len(foods) >= 1
    names = [f["name"] for f in foods]
    assert any("Chicken" in n for n in names)


@pytest.mark.asyncio
async def test_food_search_by_category(client):
    """Filtering by category=fruit returns banana but not chicken."""
    with patch("routers.food.search_usda", new=AsyncMock(return_value=[])):
        r = await client.get("/food/search", params={"q": "banana", "category": "fruit"})
    assert r.status_code == 200, r.text
    foods = r.json()
    for f in foods:
        assert f["category"] == "fruit"


@pytest.mark.asyncio
async def test_food_search_empty_query(client):
    """Empty query string must fail (min_length=1)."""
    r = await client.get("/food/search", params={"q": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_food_search_usda_fallback(client):
    """When local DB < 5 results, USDA is called for extra items."""
    fake_usda = [
        {
            "fdcId": 9999991,
            "description": "USDA Test Food",
            "foodCategory": "other",
            "foodNutrients": [
                {"nutrientId": 1008, "value": 200},  # calories
                {"nutrientId": 1003, "value": 10},   # protein
                {"nutrientId": 1005, "value": 30},   # carbs
                {"nutrientId": 1004, "value": 5},    # fat
                {"nutrientId": 1079, "value": 2},    # fiber
                {"nutrientId": 2000, "value": 5},    # sugar
                {"nutrientId": 1093, "value": 100},  # sodium
                {"nutrientId": 1092, "value": 200},  # potassium
                {"nutrientId": 1087, "value": 50},   # calcium
                {"nutrientId": 1089, "value": 2},    # iron
                {"nutrientId": 1162, "value": 10},   # vitamin C
            ],
        }
    ]
    with patch("routers.food.search_usda", new=AsyncMock(return_value=fake_usda)):
        r = await client.get("/food/search", params={"q": "usda_unique_xyz"})
    assert r.status_code == 200, r.text
    names = [f["name"] for f in r.json()]
    assert "USDA Test Food" in names


# ── GET /food/{food_id} ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_food_by_id(client):
    """Get a specific food item by ID (use ID from a search first)."""
    with patch("routers.food.search_usda", new=AsyncMock(return_value=[])):
        search_r = await client.get("/food/search", params={"q": "spinach"})
    food_id = search_r.json()[0]["id"]

    r = await client.get(f"/food/{food_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == food_id
    assert "calories_per_100g" in body
    assert body["calories_per_100g"] is not None


@pytest.mark.asyncio
async def test_get_food_not_found(client):
    r = await client.get("/food/nonexistent-food-id")
    assert r.status_code == 404


# ── GET /food/category/{category} ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_by_category_protein(client):
    r = await client.get("/food/category/protein")
    assert r.status_code == 200, r.text
    foods = r.json()
    assert len(foods) >= 1
    for f in foods:
        assert f["category"] == "protein"


@pytest.mark.asyncio
async def test_list_by_category_vegetable(client):
    r = await client.get("/food/category/vegetable")
    assert r.status_code == 200
    foods = r.json()
    for f in foods:
        assert f["category"] == "vegetable"


@pytest.mark.asyncio
async def test_list_by_category_empty(client):
    """Non-existent category returns empty list, not an error."""
    r = await client.get("/food/category/nonexistent_category")
    assert r.status_code == 200
    assert r.json() == []


# ── GET /food/barcode/{barcode} ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_barcode_lookup_success(client):
    mock_data = {
        "name": "Test Snack Bar",
        "category": "snack",
        "calories_per_100g": 450,
        "protein_g": 10,
        "carbs_g": 60,
        "fat_g": 18,
        "fiber_g": 3,
        "sugar_g": 30,
        "sodium_mg": 150,
        "calcium_mg": 80,
        "iron_mg": 2,
        "vitamin_c_mg": 0,
        "is_vegetarian": True,
        "is_vegan": False,
    }
    with patch("routers.food.get_by_barcode", new=AsyncMock(return_value=mock_data)):
        r = await client.get("/food/barcode/1234567890")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Test Snack Bar"
    assert body["calories_per_100g"] == 450


@pytest.mark.asyncio
async def test_barcode_not_found(client):
    with patch("routers.food.get_by_barcode", new=AsyncMock(return_value=None)):
        r = await client.get("/food/barcode/0000000000")
    assert r.status_code == 404
