from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, NutritionLog, Food
from schemas import NutritionLogCreate, NutritionLogOut, DailySummary
from utils.firebase import get_current_firebase_uid
from utils.gemini import analyze_food_photo
from datetime import date, datetime
import uuid

router = APIRouter(prefix="/nutrition", tags=["nutrition"])

DAILY_TARGETS = {
    "protein_g": 50, "fiber_g": 25, "vitamin_c_mg": 90,
    "iron_mg": 18, "calcium_mg": 1000, "potassium_mg": 3500,
}


async def _get_user(firebase_uid: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found. Create profile first.")
    return user


@router.post("/log", response_model=NutritionLogOut)
async def log_meal(
    payload: NutritionLogCreate,
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(firebase_uid, db)
    log = NutritionLog(
        id=str(uuid.uuid4()),
        user_id=user.id,
        log_date=payload.log_date or date.today(),
        **payload.model_dump(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.post("/photo-analyze")
async def analyze_photo(
    file: UploadFile = File(...),
    firebase_uid: str = Depends(get_current_firebase_uid),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    image_bytes = await file.read()
    result = await analyze_food_photo(image_bytes)
    return result


@router.get("/daily/{log_date}", response_model=DailySummary)
async def get_daily_summary(
    log_date: date,
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(firebase_uid, db)
    result = await db.execute(
        select(NutritionLog).where(
            NutritionLog.user_id == user.id,
            NutritionLog.log_date == log_date,
        )
    )
    logs = result.scalars().all()

    totals = {
        "calories": sum(l.calories or 0 for l in logs),
        "protein_g": sum(l.protein_g or 0 for l in logs),
        "carbs_g": sum(l.carbs_g or 0 for l in logs),
        "fat_g": sum(l.fat_g or 0 for l in logs),
        "fiber_g": sum(l.fiber_g or 0 for l in logs),
    }

    meals: dict = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    for log in logs:
        meals.setdefault(log.meal_type, []).append(log)

    nutrient_completion = {}
    for nutrient, target in DAILY_TARGETS.items():
        total_micro = sum(
            (l.micronutrients or {}).get(nutrient, 0) for l in logs
        )
        direct = totals.get(nutrient, 0) + total_micro
        nutrient_completion[nutrient] = round(min(100, (direct / target) * 100), 1)

    return DailySummary(
        date=log_date,
        total_calories=totals["calories"],
        total_protein_g=totals["protein_g"],
        total_carbs_g=totals["carbs_g"],
        total_fat_g=totals["fat_g"],
        total_fiber_g=totals["fiber_g"],
        calorie_target=user.daily_calorie_target or 2000,
        calorie_remaining=max(0, (user.daily_calorie_target or 2000) - totals["calories"]),
        meals=meals,
        nutrient_completion=nutrient_completion,
    )


@router.get("/history", response_model=list[NutritionLogOut])
async def get_history(
    days: int = Query(7, le=90),
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    user = await _get_user(firebase_uid, db)
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(NutritionLog)
        .where(NutritionLog.user_id == user.id, NutritionLog.log_date >= since)
        .order_by(NutritionLog.logged_at.desc())
    )
    return result.scalars().all()


@router.delete("/log/{log_id}")
async def delete_log(
    log_id: str,
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(firebase_uid, db)
    result = await db.execute(
        select(NutritionLog).where(NutritionLog.id == log_id, NutritionLog.user_id == user.id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(404, "Log not found")
    await db.delete(log)
    await db.commit()
    return {"deleted": log_id}
