from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, BodyMeasurement, NutritionLog, WorkoutLog
from schemas import BodyMeasurementCreate, BodyMeasurementOut, ProgressSummary
from utils.firebase import get_current_firebase_uid
from utils.calories import calculate_bmi
from datetime import date, timedelta
import uuid

router = APIRouter(prefix="/progress", tags=["progress"])

NUTRIENT_TARGETS = {
    "protein_g": 50, "fiber_g": 25, "vitamin_c_mg": 90,
    "iron_mg": 18, "calcium_mg": 1000,
}


@router.post("/measurement", response_model=BodyMeasurementOut)
async def log_measurement(
    payload: BodyMeasurementCreate,
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    bmi = calculate_bmi(payload.weight_kg, user.height_cm) if user.height_cm else None

    measurement = BodyMeasurement(
        id=str(uuid.uuid4()),
        user_id=user.id,
        bmi=bmi,
        measure_date=payload.measure_date or date.today(),
        **payload.model_dump(exclude={"measure_date"}),
    )
    db.add(measurement)

    user.weight_kg = payload.weight_kg
    await db.commit()
    await db.refresh(measurement)
    return measurement


@router.get("/measurements", response_model=list[BodyMeasurementOut])
async def get_measurements(
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    m = await db.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.user_id == user.id)
        .order_by(BodyMeasurement.measured_at.desc())
        .limit(90)
    )
    return m.scalars().all()


@router.get("/summary", response_model=ProgressSummary)
async def get_progress_summary(
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    today = date.today()
    d7 = today - timedelta(days=7)
    d30 = today - timedelta(days=30)

    # Nutrition averages
    n7 = await db.execute(
        select(func.avg(NutritionLog.calories))
        .where(NutritionLog.user_id == user.id, NutritionLog.log_date >= d7)
    )
    n30 = await db.execute(
        select(func.avg(NutritionLog.calories))
        .where(NutritionLog.user_id == user.id, NutritionLog.log_date >= d30)
    )

    # Workout counts
    w7 = await db.execute(
        select(func.count(WorkoutLog.id))
        .where(WorkoutLog.user_id == user.id, WorkoutLog.log_date >= d7)
    )
    w30 = await db.execute(
        select(func.count(WorkoutLog.id))
        .where(WorkoutLog.user_id == user.id, WorkoutLog.log_date >= d30)
    )

    # Recent measurements
    measurements_r = await db.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.user_id == user.id)
        .order_by(BodyMeasurement.measured_at.desc())
        .limit(30)
    )
    measurements = measurements_r.scalars().all()

    first_weight = measurements[-1].weight_kg if measurements else user.weight_kg
    current_weight = measurements[0].weight_kg if measurements else user.weight_kg

    # Streak: consecutive logged days
    streak = 0
    check_date = today
    while True:
        day_log = await db.execute(
            select(NutritionLog).where(
                NutritionLog.user_id == user.id,
                NutritionLog.log_date == check_date,
            ).limit(1)
        )
        if not day_log.scalar_one_or_none():
            break
        streak += 1
        check_date -= timedelta(days=1)

    # Nutrient deficiencies (7d average)
    logs_7d = await db.execute(
        select(NutritionLog).where(NutritionLog.user_id == user.id, NutritionLog.log_date >= d7)
    )
    logs_7d_list = logs_7d.scalars().all()
    deficiencies = []
    for nutrient, target in NUTRIENT_TARGETS.items():
        avg = sum(getattr(l, nutrient, 0) or 0 for l in logs_7d_list) / max(7, 1)
        if avg < target * 0.7:
            deficiencies.append(nutrient.replace("_", " ").replace("g", "").strip())

    return ProgressSummary(
        current_weight_kg=current_weight,
        target_weight_kg=user.target_weight_kg,
        weight_change_kg=round(current_weight - first_weight, 2) if first_weight else None,
        bmi=calculate_bmi(current_weight, user.height_cm) if user.height_cm and current_weight else None,
        avg_daily_calories_7d=n7.scalar(),
        avg_daily_calories_30d=n30.scalar(),
        workout_count_7d=w7.scalar() or 0,
        workout_count_30d=w30.scalar() or 0,
        streak_days=streak,
        top_nutrient_deficiencies=deficiencies,
        measurements_history=measurements,
    )
