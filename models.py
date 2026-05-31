from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey,
    Text, JSON, Enum as SAEnum, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid


def gen_uuid():
    return str(uuid.uuid4())


class GoalType(str, enum.Enum):
    weight_loss = "weight_loss"
    muscle_gain = "muscle_gain"
    maintain = "maintain"
    endurance = "endurance"
    flexibility = "flexibility"


class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extra_active = "extra_active"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(SAEnum(Gender))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    target_weight_kg = Column(Float)
    goal = Column(SAEnum(GoalType), default=GoalType.maintain)
    activity_level = Column(SAEnum(ActivityLevel), default=ActivityLevel.lightly_active)
    daily_calorie_target = Column(Integer)
    profile_photo_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    nutrition_logs = relationship("NutritionLog", back_populates="user", cascade="all, delete")
    workout_logs = relationship("WorkoutLog", back_populates="user", cascade="all, delete")
    body_measurements = relationship("BodyMeasurement", back_populates="user", cascade="all, delete")
    diet_plans = relationship("DietPlan", back_populates="user", cascade="all, delete")


class Food(Base):
    __tablename__ = "foods"

    id = Column(String, primary_key=True, default=gen_uuid)
    usda_fdc_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, index=True)
    category = Column(String, index=True)  # vegetable, fruit, spice, grain, protein, dairy
    calories_per_100g = Column(Float)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    fiber_g = Column(Float)
    sugar_g = Column(Float)
    sodium_mg = Column(Float)
    potassium_mg = Column(Float)
    calcium_mg = Column(Float)
    iron_mg = Column(Float)
    vitamin_c_mg = Column(Float)
    vitamin_a_ug = Column(Float)
    vitamin_d_ug = Column(Float)
    vitamin_b12_ug = Column(Float)
    magnesium_mg = Column(Float)
    zinc_mg = Column(Float)
    extra_nutrients = Column(JSON, default={})
    best_time_to_eat = Column(String)  # morning, afternoon, evening, any
    serving_size_g = Column(Float, default=100.0)
    serving_unit = Column(String, default="g")
    image_url = Column(String)
    health_benefits = Column(Text)
    is_vegetarian = Column(Boolean, default=True)
    is_vegan = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    food_id = Column(String, ForeignKey("foods.id"), nullable=True)
    food_name = Column(String)  # fallback if food not in DB
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    quantity_g = Column(Float)
    calories = Column(Float)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    fiber_g = Column(Float)
    micronutrients = Column(JSON, default={})
    photo_url = Column(String)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    log_date = Column(Date, index=True)
    notes = Column(Text)

    user = relationship("User", back_populates="nutrition_logs")
    food = relationship("Food")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, index=True)
    category = Column(String, index=True)  # strength, cardio, flexibility, yoga, hiit
    muscle_groups = Column(JSON, default=[])
    difficulty = Column(String)  # beginner, intermediate, advanced
    equipment = Column(String)  # none, dumbbells, barbell, machine, resistance_band
    instructions = Column(Text)
    sets = Column(Integer)
    reps = Column(String)  # "8-12" or "30 seconds"
    rest_seconds = Column(Integer)
    calories_per_minute = Column(Float)
    video_url = Column(String)
    image_url = Column(String)
    is_offline = Column(Boolean, default=True)


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String)
    goal = Column(SAEnum(GoalType))
    difficulty = Column(String)
    duration_weeks = Column(Integer)
    days_per_week = Column(Integer)
    description = Column(Text)
    exercises = Column(JSON, default=[])  # list of {exercise_id, sets, reps, rest}
    is_offline = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    workout_plan_id = Column(String, ForeignKey("workout_plans.id"), nullable=True)
    exercises_done = Column(JSON, default=[])
    duration_minutes = Column(Integer)
    calories_burned = Column(Float)
    notes = Column(Text)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    log_date = Column(Date, index=True)

    user = relationship("User", back_populates="workout_logs")


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # null = template plan
    name = Column(String)
    goal = Column(SAEnum(GoalType))
    total_calories = Column(Integer)
    meals = Column(JSON, default={})  # {breakfast: [...], lunch: [...], dinner: [...], snacks: [...]}
    duration_days = Column(Integer, default=7)
    is_offline = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="diet_plans")


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    weight_kg = Column(Float)
    body_fat_percent = Column(Float)
    muscle_mass_kg = Column(Float)
    bmi = Column(Float)
    waist_cm = Column(Float)
    chest_cm = Column(Float)
    hips_cm = Column(Float)
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
    measure_date = Column(Date, index=True)

    user = relationship("User", back_populates="body_measurements")


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, index=True)
    category = Column(String, index=True)  # nutrition, workout, recovery, mental_health
    content = Column(Text)
    summary = Column(Text)
    tags = Column(JSON, default=[])
    image_url = Column(String)
    read_time_minutes = Column(Integer)
    is_offline = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
