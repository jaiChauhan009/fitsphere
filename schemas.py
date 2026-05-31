from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from models import GoalType, ActivityLevel, Gender


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    age: int = Field(ge=10, le=100)
    gender: Gender
    height_cm: float = Field(gt=50, lt=300)
    weight_kg: float = Field(gt=10, lt=500)
    target_weight_kg: Optional[float] = None
    goal: GoalType = GoalType.maintain
    activity_level: ActivityLevel = ActivityLevel.lightly_active
    firebase_uid: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    goal: Optional[GoalType] = None
    activity_level: Optional[ActivityLevel] = None


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    age: Optional[int]
    gender: Optional[Gender]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    target_weight_kg: Optional[float]
    goal: Optional[GoalType]
    activity_level: Optional[ActivityLevel]
    daily_calorie_target: Optional[int]
    profile_photo_url: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Food ──────────────────────────────────────────────────────────────────────

class FoodOut(BaseModel):
    id: str
    name: str
    category: Optional[str]
    calories_per_100g: Optional[float]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fiber_g: Optional[float]
    sodium_mg: Optional[float]
    vitamin_c_mg: Optional[float]
    iron_mg: Optional[float]
    calcium_mg: Optional[float]
    best_time_to_eat: Optional[str]
    serving_size_g: Optional[float]
    health_benefits: Optional[str]
    is_vegetarian: Optional[bool]
    is_vegan: Optional[bool]

    class Config:
        from_attributes = True


class FoodSearch(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 20


# ── Nutrition Log ─────────────────────────────────────────────────────────────

class NutritionLogCreate(BaseModel):
    food_id: Optional[str] = None
    food_name: str
    meal_type: str  # breakfast, lunch, dinner, snack
    quantity_g: float = Field(gt=0)
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    micronutrients: Dict[str, Any] = {}
    log_date: Optional[date] = None
    notes: Optional[str] = None


class NutritionLogOut(NutritionLogCreate):
    id: str
    user_id: str
    photo_url: Optional[str]
    logged_at: datetime

    class Config:
        from_attributes = True


class DailySummary(BaseModel):
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    calorie_target: int
    calorie_remaining: float
    meals: Dict[str, List[NutritionLogOut]]
    nutrient_completion: Dict[str, float]  # % of daily target met


# ── Workout ───────────────────────────────────────────────────────────────────

class WorkoutLogCreate(BaseModel):
    workout_plan_id: Optional[str] = None
    exercises_done: List[Dict[str, Any]] = []
    duration_minutes: int
    calories_burned: Optional[float] = None
    notes: Optional[str] = None
    log_date: Optional[date] = None


class WorkoutLogOut(WorkoutLogCreate):
    id: str
    user_id: str
    logged_at: datetime

    class Config:
        from_attributes = True


# ── Body Measurement ──────────────────────────────────────────────────────────

class BodyMeasurementCreate(BaseModel):
    weight_kg: float
    body_fat_percent: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    waist_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    measure_date: Optional[date] = None


class BodyMeasurementOut(BodyMeasurementCreate):
    id: str
    user_id: str
    bmi: Optional[float]
    measured_at: datetime

    class Config:
        from_attributes = True


# ── AI Photo Analysis ─────────────────────────────────────────────────────────

class PhotoAnalysisResult(BaseModel):
    detected_foods: List[Dict[str, Any]]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    confidence: float
    raw_response: str


# ── Progress ──────────────────────────────────────────────────────────────────

class ProgressSummary(BaseModel):
    current_weight_kg: Optional[float]
    target_weight_kg: Optional[float]
    weight_change_kg: Optional[float]
    bmi: Optional[float]
    avg_daily_calories_7d: Optional[float]
    avg_daily_calories_30d: Optional[float]
    workout_count_7d: int
    workout_count_30d: int
    streak_days: int
    top_nutrient_deficiencies: List[str]
    measurements_history: List[BodyMeasurementOut]


# ── AI Recommendation ─────────────────────────────────────────────────────────

class AIRecommendation(BaseModel):
    diet_tips: List[str]
    workout_tips: List[str]
    deficiency_alerts: List[str]
    meal_suggestions: List[str]
    motivational_message: str
