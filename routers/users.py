from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserOut
from utils.firebase import get_current_firebase_uid
from utils.calories import calculate_daily_calories, calculate_bmi
import uuid

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    daily_calories = calculate_daily_calories(
        payload.weight_kg, payload.height_cm, payload.age,
        payload.gender, payload.activity_level, payload.goal
    )

    user = User(
        id=str(uuid.uuid4()),
        **payload.model_dump(),
        daily_calorie_target=daily_calories,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
async def get_me(
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    if any([payload.weight_kg, payload.height_cm, payload.goal, payload.activity_level]):
        user.daily_calorie_target = calculate_daily_calories(
            user.weight_kg, user.height_cm, user.age,
            user.gender, user.activity_level, user.goal
        )

    await db.commit()
    await db.refresh(user)
    return user
