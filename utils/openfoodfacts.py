import httpx

BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "FitSphere/1.0 (jai@getkosh.com)"}


async def get_by_barcode(barcode: str) -> dict | None:
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        r = await client.get(f"{BASE}/api/v2/product/{barcode}.json")
        data = r.json()
        if data.get("status") != 1:
            return None
        return _normalize(data["product"])


async def search_off(query: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        r = await client.get(
            f"{BASE}/api/v2/search",
            params={"search_terms": query, "page_size": limit, "fields": _FIELDS},
        )
        data = r.json()
        return [_normalize(p) for p in data.get("products", []) if p.get("product_name")]


_FIELDS = "product_name,brands,categories_tags,nutriscore_grade,nova_group,labels_tags,nutriments,ingredients_text_en"


def _normalize(p: dict) -> dict:
    n = p.get("nutriments", {})
    labels = p.get("labels_tags", [])
    return {
        "name": p.get("product_name") or p.get("generic_name", "Unknown"),
        "brand": p.get("brands", ""),
        "category": (p.get("categories_tags") or ["other"])[0].replace("en:", ""),
        "calories_per_100g": n.get("energy-kcal_100g") or n.get("energy-kcal", 0),
        "protein_g": n.get("proteins_100g", 0),
        "carbs_g": n.get("carbohydrates_100g", 0),
        "fat_g": n.get("fat_100g", 0),
        "fiber_g": n.get("fiber_100g", 0),
        "sugar_g": n.get("sugars_100g", 0),
        "sodium_mg": (n.get("sodium_100g", 0) or 0) * 1000,
        "calcium_mg": n.get("calcium_100g", 0),
        "iron_mg": n.get("iron_100g", 0),
        "vitamin_c_mg": n.get("vitamin-c_100g", 0),
        "vitamin_a_ug": n.get("vitamin-a_100g", 0),
        "nutriscore": p.get("nutriscore_grade", ""),
        "nova_group": p.get("nova_group"),
        "is_vegetarian": "en:vegetarian" in labels,
        "is_vegan": "en:vegan" in labels,
        "ingredients_text": p.get("ingredients_text_en", ""),
        "source": "openfoodfacts",
    }
