from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, NutritionLog, WorkoutLog
from schemas import AIRecommendation
from utils.firebase import get_current_firebase_uid
from utils.gemini import get_ai_recommendations
from datetime import date, timedelta

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/recommendations", response_model=AIRecommendation)
async def get_recommendations(
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    d7 = date.today() - timedelta(days=7)

    # 7-day nutrition averages
    n_logs = await db.execute(
        select(NutritionLog).where(NutritionLog.user_id == user.id, NutritionLog.log_date >= d7)
    )
    n_list = n_logs.scalars().all()
    avg_cal = sum(l.calories or 0 for l in n_list) / max(len(n_list), 1)
    avg_protein = sum(l.protein_g or 0 for l in n_list) / max(len(n_list), 1)
    avg_carbs = sum(l.carbs_g or 0 for l in n_list) / max(len(n_list), 1)
    avg_fat = sum(l.fat_g or 0 for l in n_list) / max(len(n_list), 1)

    deficiencies = []
    for nutrient, target in [("protein_g", 50), ("fiber_g", 25)]:
        avg = sum(getattr(l, nutrient, 0) or 0 for l in n_list) / max(len(n_list), 1)
        if avg < target * 0.7:
            deficiencies.append(nutrient)

    # 7-day workout summary
    w_logs = await db.execute(
        select(WorkoutLog).where(WorkoutLog.user_id == user.id, WorkoutLog.log_date >= d7)
    )
    w_list = w_logs.scalars().all()
    avg_duration = sum(l.duration_minutes or 0 for l in w_list) / max(len(w_list), 1)

    result_data = await get_ai_recommendations(
        user_data={
            "age": user.age, "gender": user.gender,
            "height_cm": user.height_cm, "weight_kg": user.weight_kg,
            "goal": user.goal, "activity_level": user.activity_level,
            "daily_calorie_target": user.daily_calorie_target,
        },
        nutrition_7d={
            "avg_calories": round(avg_cal), "avg_protein_g": round(avg_protein),
            "avg_carbs_g": round(avg_carbs), "avg_fat_g": round(avg_fat),
            "deficiencies": deficiencies,
        },
        workout_7d={"count": len(w_list), "avg_duration_min": round(avg_duration)},
    )

    return AIRecommendation(**result_data)


@router.post("/diet-plan-generate")
async def generate_diet_plan(
    firebase_uid: str = Depends(get_current_firebase_uid),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized 7-day diet plan using Gemini."""
    from utils.gemini import _configure
    import google.generativeai as genai
    _configure()

    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Create a 7-day personalized diet plan for:
    - Goal: {user.goal}, Calories/day: {user.daily_calorie_target}
    - Age: {user.age}, Gender: {user.gender}, Weight: {user.weight_kg}kg

    Return JSON:
    {{
      "plan_name": "...",
      "days": [
        {{
          "day": 1,
          "breakfast": [{{"food": "...", "quantity_g": 150, "calories": 300}}],
          "lunch": [...],
          "dinner": [...],
          "snacks": [...],
          "total_calories": 2000
        }}
      ]
    }}
    Only return valid JSON.
    """
    import json, re
    response = model.generate_content(prompt)
    text = response.text.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group())
    raise HTTPException(500, "AI failed to generate plan")
