import httpx
from config import settings

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"


async def search_usda(query: str, limit: int = 10) -> list[dict]:
    if not settings.USDA_API_KEY:
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{USDA_BASE}/foods/search",
            params={"query": query, "pageSize": limit, "api_key": settings.USDA_API_KEY},
        )
        r.raise_for_status()
        data = r.json()
        return data.get("foods", [])


async def get_usda_food(fdc_id: str) -> dict | None:
    if not settings.USDA_API_KEY:
        return None
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{USDA_BASE}/food/{fdc_id}", params={"api_key": settings.USDA_API_KEY})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


def extract_nutrient(food_data: dict, nutrient_id: int, default: float = 0.0) -> float:
    nutrients = food_data.get("foodNutrients", [])
    for n in nutrients:
        nid = n.get("nutrientId") or n.get("nutrient", {}).get("id")
        if nid == nutrient_id:
            return float(n.get("value") or n.get("amount") or default)
    return default


# USDA nutrient IDs
NUTRIENT_MAP = {
    "calories": 1008,
    "protein_g": 1003,
    "fat_g": 1004,
    "carbs_g": 1005,
    "fiber_g": 1079,
    "sugar_g": 2000,
    "sodium_mg": 1093,
    "potassium_mg": 1092,
    "calcium_mg": 1087,
    "iron_mg": 1089,
    "vitamin_c_mg": 1162,
    "vitamin_a_ug": 1104,
    "vitamin_d_ug": 1114,
    "vitamin_b12_ug": 1178,
    "magnesium_mg": 1090,
    "zinc_mg": 1095,
}
