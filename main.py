from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import engine, Base, AsyncSessionLocal
from config import settings
from routers import users, food, nutrition, workouts, progress, ai, knowledge
from sqlalchemy import text, select
import time


async def _seed_static_data():
    """Populate exercises, workout plans, and knowledge articles if the DB is empty."""
    from models import Exercise, WorkoutPlan, KnowledgeArticle
    import uuid

    def uid():
        return str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        # Skip if already seeded
        result = await db.execute(select(Exercise).limit(1))
        if result.scalar_one_or_none():
            return

        print("[seed] Seeding static data...")

        db.add_all([
            Exercise(id=uid(), name="Push-up", category="strength", muscle_groups=["chest","triceps","shoulders"],
                     difficulty="beginner", equipment="none", instructions="Start in plank. Lower chest to floor, push back up.",
                     sets=3, reps="10-15", rest_seconds=60, calories_per_minute=7.0, is_offline=True),
            Exercise(id=uid(), name="Squat", category="strength", muscle_groups=["quads","glutes","hamstrings"],
                     difficulty="beginner", equipment="none", instructions="Feet shoulder-width. Lower hips below knees, drive back up.",
                     sets=3, reps="12-15", rest_seconds=60, calories_per_minute=8.0, is_offline=True),
            Exercise(id=uid(), name="Running", category="cardio", muscle_groups=["legs","core"],
                     difficulty="beginner", equipment="none", instructions="Steady pace. Land mid-foot, arms relaxed.",
                     sets=1, reps="20 min", rest_seconds=0, calories_per_minute=10.0, is_offline=True),
            Exercise(id=uid(), name="Plank", category="strength", muscle_groups=["core","shoulders"],
                     difficulty="beginner", equipment="none", instructions="Hold straight-body on forearms. Don't let hips sag.",
                     sets=3, reps="30-60 sec", rest_seconds=45, calories_per_minute=5.0, is_offline=True),
            Exercise(id=uid(), name="Pull-up", category="strength", muscle_groups=["back","biceps"],
                     difficulty="intermediate", equipment="none", instructions="Hang from bar. Pull chin above, lower with control.",
                     sets=3, reps="6-10", rest_seconds=90, calories_per_minute=9.0, is_offline=True),
            Exercise(id=uid(), name="Lunges", category="strength", muscle_groups=["quads","glutes"],
                     difficulty="beginner", equipment="none", instructions="Step forward, lower back knee toward floor. Alternate legs.",
                     sets=3, reps="10 each", rest_seconds=60, calories_per_minute=7.5, is_offline=True),
            Exercise(id=uid(), name="Burpee", category="hiit", muscle_groups=["full body"],
                     difficulty="intermediate", equipment="none", instructions="Squat, kick feet back, push-up, jump up overhead.",
                     sets=4, reps="10", rest_seconds=30, calories_per_minute=12.0, is_offline=True),
            Exercise(id=uid(), name="Mountain Climber", category="hiit", muscle_groups=["core","shoulders"],
                     difficulty="beginner", equipment="none", instructions="From plank, alternate driving knees to chest rapidly.",
                     sets=3, reps="20 each", rest_seconds=30, calories_per_minute=9.0, is_offline=True),
            Exercise(id=uid(), name="Dumbbell Row", category="strength", muscle_groups=["back","biceps"],
                     difficulty="beginner", equipment="dumbbells", instructions="Hinge forward, row dumbbell to hip, control descent.",
                     sets=3, reps="10-12", rest_seconds=60, calories_per_minute=6.0, is_offline=True),
            Exercise(id=uid(), name="Deadlift", category="strength", muscle_groups=["back","glutes","hamstrings"],
                     difficulty="intermediate", equipment="barbell", instructions="Hip hinge neutral spine. Drive hips forward to stand.",
                     sets=4, reps="5-8", rest_seconds=120, calories_per_minute=8.5, is_offline=True),
            Exercise(id=uid(), name="Bicycle Crunch", category="strength", muscle_groups=["core"],
                     difficulty="beginner", equipment="none", instructions="Alternate elbow to opposite knee, extend other leg.",
                     sets=3, reps="20 total", rest_seconds=45, calories_per_minute=6.0, is_offline=True),
            Exercise(id=uid(), name="Jump Rope", category="cardio", muscle_groups=["legs","cardio"],
                     difficulty="beginner", equipment="none", instructions="Light feet, consistent rhythm. Jump just enough to clear rope.",
                     sets=5, reps="1 min", rest_seconds=30, calories_per_minute=11.0, is_offline=True),
            Exercise(id=uid(), name="Shoulder Press", category="strength", muscle_groups=["shoulders","triceps"],
                     difficulty="beginner", equipment="dumbbells", instructions="Press from shoulder height overhead. Lock out at top.",
                     sets=3, reps="10-12", rest_seconds=60, calories_per_minute=6.5, is_offline=True),
            Exercise(id=uid(), name="Yoga Sun Salutation", category="yoga", muscle_groups=["full body"],
                     difficulty="beginner", equipment="none", instructions="Flow: mountain → forward fold → plank → cobra → downdog.",
                     sets=1, reps="5 rounds", rest_seconds=0, calories_per_minute=4.0, is_offline=True),
        ])

        db.add_all([
            WorkoutPlan(id=uid(), name="Beginner Full Body", goal="maintain", difficulty="beginner",
                        duration_weeks=4, days_per_week=3, exercises=[],
                        description="Perfect for starters. Full-body movements 3 days/week with rest days between.", is_offline=True),
            WorkoutPlan(id=uid(), name="Weight Loss Cardio Blast", goal="weight_loss", difficulty="beginner",
                        duration_weeks=6, days_per_week=5, exercises=[],
                        description="Cardio + HIIT intervals to maximise calorie burn. Combines running, burpees, and jump rope.", is_offline=True),
            WorkoutPlan(id=uid(), name="Muscle Builder", goal="muscle_gain", difficulty="intermediate",
                        duration_weeks=8, days_per_week=4, exercises=[],
                        description="Progressive overload strength training split targeting all major muscle groups.", is_offline=True),
            WorkoutPlan(id=uid(), name="Endurance Base", goal="endurance", difficulty="intermediate",
                        duration_weeks=12, days_per_week=5, exercises=[],
                        description="Running and functional training to build aerobic capacity and stamina.", is_offline=True),
            WorkoutPlan(id=uid(), name="Flexibility & Mobility", goal="flexibility", difficulty="beginner",
                        duration_weeks=4, days_per_week=6, exercises=[],
                        description="Daily yoga and stretching to improve range of motion and enhance recovery.", is_offline=True),
        ])

        db.add_all([
            KnowledgeArticle(id=uid(), title="Why Protein Is the King of Macros", category="nutrition",
                             summary="Why protein is essential for muscle growth, satiety, and metabolism.",
                             content="Protein is made of amino acids — the building blocks of muscle. Consume 1.6–2.2g per kg of bodyweight daily. Best sources: chicken, eggs, Greek yogurt, lentils, tofu.",
                             tags=["protein","muscle"], read_time_minutes=4, is_offline=True),
            KnowledgeArticle(id=uid(), title="Best Pre-Workout Foods", category="nutrition",
                             summary="What to eat 1-2 hours before exercise for maximum energy.",
                             content="Aim for moderate carbs + protein, low fat 1-2 hours before training. Examples: oats + banana, rice + chicken. Hydrate 500ml beforehand.",
                             tags=["pre-workout","nutrition"], read_time_minutes=3, is_offline=True),
            KnowledgeArticle(id=uid(), title="Progressive Overload: #1 Rule for Strength", category="workout",
                             summary="Why you must progressively increase stress to keep gaining strength.",
                             content="Increase weight 2-5% each week, or add 1-2 reps per set. Without progressive overload, your body adapts and stops growing. Track every session.",
                             tags=["strength","training"], read_time_minutes=5, is_offline=True),
            KnowledgeArticle(id=uid(), title="Sleep: The Most Underrated Recovery Tool", category="recovery",
                             summary="Why 7-9 hours of sleep is as important as your training.",
                             content="Growth hormone releases during deep sleep — this is when muscles repair. Cortisol spikes with poor sleep, increasing fat storage. Consistent sleep/wake times and a dark cool room below 18°C are key.",
                             tags=["sleep","recovery"], read_time_minutes=4, is_offline=True),
            KnowledgeArticle(id=uid(), title="Micronutrients Every Athlete Needs", category="nutrition",
                             summary="Iron, Magnesium, Vitamin D — what they do and how to get enough.",
                             content="Iron carries oxygen to muscles (spinach, lentils). Magnesium aids sleep and muscle contraction (nuts, seeds). Vitamin D supports bone and testosterone (sunlight, fatty fish). Zinc boosts immunity (pumpkin seeds).",
                             tags=["micronutrients","vitamins"], read_time_minutes=6, is_offline=True),
            KnowledgeArticle(id=uid(), title="HIIT vs Steady State Cardio", category="workout",
                             summary="Which burns more fat? The science behind both approaches.",
                             content="HIIT burns more per minute and creates afterburn (EPOC). Steady state builds aerobic base and is easier to recover from. Optimal: 2 HIIT + 2 steady state per week.",
                             tags=["hiit","cardio","fat loss"], read_time_minutes=4, is_offline=True),
            KnowledgeArticle(id=uid(), title="Mindful Eating: Stop Eating on Autopilot", category="mental_health",
                             summary="Practical steps to build awareness around food and stop overeating.",
                             content="Eat slowly — it takes 20 minutes for satiety signals to reach the brain. Remove distractions, use smaller plates, check hunger 1-10 before eating. Mindful eaters consume ~300 fewer calories daily without dieting.",
                             tags=["mindfulness","eating"], read_time_minutes=5, is_offline=True),
            KnowledgeArticle(id=uid(), title="Creatine: The Complete Beginner Guide", category="supplements",
                             summary="The most researched supplement in fitness — everything you need to know.",
                             content="Creatine monohydrate increases ATP for short high-intensity bursts. Dose: 3-5g daily (no loading needed). Expect 1-2kg water weight gain in muscle cells. Safe for healthy kidneys. Stay hydrated.",
                             tags=["creatine","supplements"], read_time_minutes=5, is_offline=True),
            KnowledgeArticle(id=uid(), title="Calculate Your Daily Calorie Needs", category="nutrition",
                             summary="BMR and TDEE explained — how to set the right calorie target.",
                             content="BMR × activity factor = TDEE. Lose weight: eat 300-500 below TDEE. Gain muscle: eat 200-300 above. FitSphere calculates this via Mifflin-St Jeor. Adjust by 100 kcal if no results after 2-3 weeks.",
                             tags=["calories","tdee","nutrition"], read_time_minutes=5, is_offline=True),
            KnowledgeArticle(id=uid(), title="Active Recovery on Rest Days", category="recovery",
                             summary="Light activity on rest days speeds recovery and reduces soreness.",
                             content="Light walks, swimming, or yoga increase blood flow, speeding nutrient delivery to sore muscles. Keep heart rate below 120 BPM. 20-40 minutes is enough to accelerate recovery without adding fatigue.",
                             tags=["recovery","rest"], read_time_minutes=3, is_offline=True),
        ])

        await db.commit()
        print("[seed] Static data seeded successfully.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _seed_static_data()
    except Exception as e:
        print(f"[startup] DB init warning: {e}")
    yield
    await engine.dispose()


app = FastAPI(
    title="FitSphere API",
    version="1.0.0",
    description="Complete fitness ecosystem — nutrition, workouts, AI recommendations",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(food.router)
app.include_router(nutrition.router)
app.include_router(workouts.router)
app.include_router(progress.router)
app.include_router(ai.router)
app.include_router(knowledge.router)


@app.get("/")
def root():
    return {"app": "FitSphere API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    """Health check used by Render. Verifies API + DB connectivity."""
    start = time.monotonic()
    db_ok = False
    db_error = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    latency_ms = round((time.monotonic() - start) * 1000, 1)
    payload = {
        "status": "ok" if db_ok else "degraded",
        "api": "ok",
        "database": "ok" if db_ok else f"error: {db_error}",
        "latency_ms": latency_ms,
        "version": "1.0.0",
    }
    status_code = 200 if db_ok else 503
    return JSONResponse(content=payload, status_code=status_code)
