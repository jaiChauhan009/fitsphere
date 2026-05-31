from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, WorkoutLog, WorkoutPlan, Exercise
from schemas import WorkoutLogCreate, WorkoutLogOut
from utils.firebase import get_current_firebase_uid
from datetime import date, timedelta
import uuid

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/plans")
async def list_workout_plans(
    goal: str = Query(None),
    difficulty: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(WorkoutPlan)
    if goal:
        query = query.where(WorkoutPlan.goal == goal)
    if difficulty:
        query = query.where(WorkoutPlan.difficulty == difficulty)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/exercises")
async def list_exercises(
    category: str = Query(None),
    muscle_group: str = Query(None),
    difficulty: str = Query(None),
    equipment: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Exercise)
    if category:
        query = query.where(Exercise.category == category)
    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)
    if equipment:
        query = query.where(Exercise.equipment == equipment)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/log", response_model=WorkoutLogOut)
async def log_workout(
    payload: WorkoutLogCreate,
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()

    log = WorkoutLog(
        id=str(uuid.uuid4()),
        user_id=user.id,
        log_date=payload.log_date or date.today(),
        **payload.model_dump(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/history", response_model=list[WorkoutLogOut])
async def workout_history(
    days: int = Query(30, le=365),
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    since = date.today() - timedelta(days=days)

    logs = await db.execute(
        select(WorkoutLog)
        .where(WorkoutLog.user_id == user.id, WorkoutLog.log_date >= since)
        .order_by(WorkoutLog.logged_at.desc())
    )
    return logs.scalars().all()
