"""
Shared fixtures for FitSphere tests.

* Uses an in-memory SQLite database (aiosqlite) — no real Postgres needed.
* Overrides get_db and get_current_firebase_uid so every test is self-contained.
* A test user is pre-created in the DB with firebase_uid = "test-uid-001".
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT_JSON", "")
os.environ.setdefault("FIREBASE_PROJECT_ID", "")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("USDA_API_KEY", "")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

import main as app_module
from database import Base, get_db
from utils.firebase import get_current_firebase_uid
from models import User, Food, WorkoutPlan, Exercise, KnowledgeArticle
from utils.calories import calculate_daily_calories
import uuid

# ── in-memory engine shared across a whole test session ───────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

TEST_UID = "test-uid-001"
TEST_USER_EMAIL = "test@fitsphere.com"


# ── schema setup ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── seed fixtures ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_static_data(create_tables):
    """Insert food items, exercises, workout plans, knowledge articles once."""
    async with _TestSession() as db:
        # Foods
        db.add_all([
            Food(id=str(uuid.uuid4()), name="Chicken Breast", category="protein",
                 calories_per_100g=165, protein_g=31, carbs_g=0, fat_g=3.6,
                 fiber_g=0, sugar_g=0, sodium_mg=74, is_vegetarian=False, is_vegan=False),
            Food(id=str(uuid.uuid4()), name="Brown Rice", category="grain",
                 calories_per_100g=216, protein_g=5, carbs_g=45, fat_g=1.8,
                 fiber_g=3.5, sugar_g=0, sodium_mg=10, is_vegetarian=True, is_vegan=True),
            Food(id=str(uuid.uuid4()), name="Spinach", category="vegetable",
                 calories_per_100g=23, protein_g=2.9, carbs_g=3.6, fat_g=0.4,
                 fiber_g=2.2, sugar_g=0.4, sodium_mg=79, is_vegetarian=True, is_vegan=True),
            Food(id=str(uuid.uuid4()), name="Banana", category="fruit",
                 calories_per_100g=89, protein_g=1.1, carbs_g=23, fat_g=0.3,
                 fiber_g=2.6, sugar_g=12, sodium_mg=1, is_vegetarian=True, is_vegan=True),
            Food(id=str(uuid.uuid4()), name="Almonds", category="protein",
                 calories_per_100g=579, protein_g=21, carbs_g=22, fat_g=49,
                 fiber_g=12.5, sugar_g=4.4, sodium_mg=1, is_vegetarian=True, is_vegan=True),
        ])

        # Exercises
        db.add_all([
            Exercise(id=str(uuid.uuid4()), name="Push-up", category="strength",
                     muscle_groups=["chest", "triceps"], difficulty="beginner",
                     equipment="none", calories_per_minute=7.0),
            Exercise(id=str(uuid.uuid4()), name="Running", category="cardio",
                     muscle_groups=["legs", "core"], difficulty="beginner",
                     equipment="none", calories_per_minute=10.0),
            Exercise(id=str(uuid.uuid4()), name="Squat", category="strength",
                     muscle_groups=["quads", "glutes"], difficulty="beginner",
                     equipment="none", calories_per_minute=8.0),
        ])

        # Workout plan
        db.add_all([
            WorkoutPlan(id=str(uuid.uuid4()), name="Beginner Full Body",
                        goal="maintain", difficulty="beginner",
                        duration_weeks=4, days_per_week=3,
                        description="Simple full-body routine", exercises=[]),
        ])

        # Knowledge articles
        db.add_all([
            KnowledgeArticle(id=str(uuid.uuid4()), title="Eat More Protein",
                             category="nutrition", content="Protein builds muscle.",
                             summary="Why protein matters", tags=["protein", "muscle"],
                             read_time_minutes=3),
            KnowledgeArticle(id=str(uuid.uuid4()), title="Sleep for Recovery",
                             category="recovery", content="Sleep 8 hours.",
                             summary="Sleep tips", tags=["sleep"],
                             read_time_minutes=2),
        ])

        await db.commit()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_test_user(seed_static_data):
    """Create the canonical test user linked to TEST_UID."""
    async with _TestSession() as db:
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.firebase_uid == TEST_UID))
        if existing.scalar_one_or_none():
            return

        cal = calculate_daily_calories(75, 175, 28, "male", "lightly_active", "maintain")
        user = User(
            id=str(uuid.uuid4()),
            firebase_uid=TEST_UID,
            email=TEST_USER_EMAIL,
            name="Test User",
            age=28,
            gender="male",
            height_cm=175,
            weight_kg=75,
            target_weight_kg=70,
            goal="maintain",
            activity_level="lightly_active",
            daily_calorie_target=cal,
        )
        db.add(user)
        await db.commit()


# ── per-test DB override ───────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with DB and Firebase auth overridden."""

    async def override_get_db():
        yield db

    async def override_auth():
        return TEST_UID

    app = app_module.app
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_firebase_uid] = override_auth

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
