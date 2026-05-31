from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from database import get_db
from models import Food
from schemas import FoodOut
from utils.usda import search_usda, NUTRIENT_MAP
from utils.openfoodfacts import get_by_barcode, search_off
import uuid

router = APIRouter(prefix="/food", tags=["food"])


@router.get("/search", response_model=list[FoodOut])
async def search_food(
    q: str = Query(..., min_length=1),
    category: str = Query(None),
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    # Search local DB first
    query = select(Food).where(
        or_(
            func.lower(Food.name).contains(q.lower()),
            func.lower(Food.category).contains(q.lower()),
        )
    )
    if category:
        query = query.where(Food.category == category)
    query = query.limit(limit)

    result = await db.execute(query)
    local_foods = result.scalars().all()

    if len(local_foods) >= 5:
        return local_foods

    # Fall back to USDA API
    usda_results = await search_usda(q, limit=limit - len(local_foods))
    imported = []
    for item in usda_results:
        fdc_id = str(item.get("fdcId", ""))
        exists = await db.execute(select(Food).where(Food.usda_fdc_id == fdc_id))
        if exists.scalar_one_or_none():
            continue

        nutrients = item.get("foodNutrients", [])
        def get_n(nid):
            for n in nutrients:
                if n.get("nutrientId") == nid:
                    return float(n.get("value", 0) or 0)
            return 0.0

        food = Food(
            id=str(uuid.uuid4()),
            usda_fdc_id=fdc_id,
            name=item.get("description", q),
            category=item.get("foodCategory", "other"),
            calories_per_100g=get_n(NUTRIENT_MAP["calories"]),
            protein_g=get_n(NUTRIENT_MAP["protein_g"]),
            carbs_g=get_n(NUTRIENT_MAP["carbs_g"]),
            fat_g=get_n(NUTRIENT_MAP["fat_g"]),
            fiber_g=get_n(NUTRIENT_MAP["fiber_g"]),
            sugar_g=get_n(NUTRIENT_MAP["sugar_g"]),
            sodium_mg=get_n(NUTRIENT_MAP["sodium_mg"]),
            potassium_mg=get_n(NUTRIENT_MAP["potassium_mg"]),
            calcium_mg=get_n(NUTRIENT_MAP["calcium_mg"]),
            iron_mg=get_n(NUTRIENT_MAP["iron_mg"]),
            vitamin_c_mg=get_n(NUTRIENT_MAP["vitamin_c_mg"]),
        )
        db.add(food)
        imported.append(food)

    if imported:
        await db.commit()

    return list(local_foods) + imported


@router.get("/{food_id}", response_model=FoodOut)
async def get_food(food_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Food).where(Food.id == food_id))
    food = result.scalar_one_or_none()
    if not food:
        raise HTTPException(404, "Food not found")
    return food


@router.get("/barcode/{barcode}")
async def lookup_barcode(barcode: str, db: AsyncSession = Depends(get_db)):
    """Scan product barcode → full nutrition data (Open Food Facts)."""
    # Check local DB first
    result = await db.execute(select(Food).where(Food.usda_fdc_id == f"off_{barcode}"))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    data = await get_by_barcode(barcode)
    if not data:
        raise HTTPException(404, "Product not found")

    food = Food(
        id=str(uuid.uuid4()),
        usda_fdc_id=f"off_{barcode}",
        name=data["name"],
        category=data.get("category", "other"),
        calories_per_100g=data.get("calories_per_100g", 0),
        protein_g=data.get("protein_g", 0),
        carbs_g=data.get("carbs_g", 0),
        fat_g=data.get("fat_g", 0),
        fiber_g=data.get("fiber_g", 0),
        sugar_g=data.get("sugar_g", 0),
        sodium_mg=data.get("sodium_mg", 0),
        calcium_mg=data.get("calcium_mg", 0),
        iron_mg=data.get("iron_mg", 0),
        vitamin_c_mg=data.get("vitamin_c_mg", 0),
        is_vegetarian=data.get("is_vegetarian", True),
        is_vegan=data.get("is_vegan", False),
    )
    db.add(food)
    await db.commit()
    await db.refresh(food)
    return food


@router.get("/category/{category}", response_model=list[FoodOut])
async def list_by_category(
    category: str,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Food).where(Food.category == category).limit(limit)
    )
    return result.scalars().all()
