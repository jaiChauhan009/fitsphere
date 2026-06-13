"""
Run this once to populate exercises, workout plans, and knowledge articles.
Usage:
  cd /home/jai/Pictures/code/fitsphere-backend
  DATABASE_URL=postgresql+asyncpg://... python3 seed_data.py
  OR (if .env is set up):
  python3 seed_data.py
"""
import asyncio
import os
import sys
import uuid

# Allow running without full .env by accepting DATABASE_URL from environment
if "DATABASE_URL" not in os.environ:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

if "DATABASE_URL" not in os.environ:
    print("ERROR: DATABASE_URL not set. Run:")
    print("  DATABASE_URL='postgresql+asyncpg://...' python3 seed_data.py")
    sys.exit(1)

# Minimal env for config to load
for k in ["SUPABASE_URL","SUPABASE_PUBLISHABLE_KEY","SUPABASE_SERVICE_ROLE_KEY",
          "FIREBASE_PROJECT_ID","FIREBASE_SERVICE_ACCOUNT_JSON",
          "GEMINI_API_KEY","OPENAI_API_KEY","USDA_API_KEY"]:
    os.environ.setdefault(k, "")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text
from models import Base, Exercise, WorkoutPlan, KnowledgeArticle


def uid():
    return str(uuid.uuid4())


EXERCISES = [
    Exercise(id=uid(), name="Push-up", category="strength", muscle_groups=["chest","triceps","shoulders"],
             difficulty="beginner", equipment="none", instructions="Start in plank position. Lower chest to floor, push back up.",
             sets=3, reps="10-15", rest_seconds=60, calories_per_minute=7.0, is_offline=True),
    Exercise(id=uid(), name="Squat", category="strength", muscle_groups=["quads","glutes","hamstrings"],
             difficulty="beginner", equipment="none", instructions="Stand feet shoulder-width. Lower hips below knees, drive back up.",
             sets=3, reps="12-15", rest_seconds=60, calories_per_minute=8.0, is_offline=True),
    Exercise(id=uid(), name="Running", category="cardio", muscle_groups=["legs","core","cardio"],
             difficulty="beginner", equipment="none", instructions="Maintain steady pace. Land mid-foot, arms relaxed.",
             sets=1, reps="20 minutes", rest_seconds=0, calories_per_minute=10.0, is_offline=True),
    Exercise(id=uid(), name="Plank", category="strength", muscle_groups=["core","shoulders"],
             difficulty="beginner", equipment="none", instructions="Hold straight-body position on forearms. Don't let hips sag.",
             sets=3, reps="30-60 seconds", rest_seconds=45, calories_per_minute=5.0, is_offline=True),
    Exercise(id=uid(), name="Pull-up", category="strength", muscle_groups=["back","biceps"],
             difficulty="intermediate", equipment="none", instructions="Hang from bar. Pull chin above bar, lower with control.",
             sets=3, reps="6-10", rest_seconds=90, calories_per_minute=9.0, is_offline=True),
    Exercise(id=uid(), name="Lunges", category="strength", muscle_groups=["quads","glutes"],
             difficulty="beginner", equipment="none", instructions="Step forward, lower back knee toward floor. Alternate legs.",
             sets=3, reps="10 each leg", rest_seconds=60, calories_per_minute=7.5, is_offline=True),
    Exercise(id=uid(), name="Burpee", category="hiit", muscle_groups=["full body"],
             difficulty="intermediate", equipment="none", instructions="Squat, kick feet back, push-up, jump up with arms overhead.",
             sets=4, reps="10", rest_seconds=30, calories_per_minute=12.0, is_offline=True),
    Exercise(id=uid(), name="Mountain Climber", category="hiit", muscle_groups=["core","shoulders"],
             difficulty="beginner", equipment="none", instructions="From plank position, alternate driving knees to chest rapidly.",
             sets=3, reps="20 each leg", rest_seconds=30, calories_per_minute=9.0, is_offline=True),
    Exercise(id=uid(), name="Dumbbell Row", category="strength", muscle_groups=["back","biceps"],
             difficulty="beginner", equipment="dumbbells", instructions="Hinge forward, row dumbbell to hip, control the descent.",
             sets=3, reps="10-12", rest_seconds=60, calories_per_minute=6.0, is_offline=True),
    Exercise(id=uid(), name="Deadlift", category="strength", muscle_groups=["back","glutes","hamstrings"],
             difficulty="intermediate", equipment="barbell", instructions="Hip hinge with neutral spine. Drive hips forward to stand.",
             sets=4, reps="5-8", rest_seconds=120, calories_per_minute=8.5, is_offline=True),
    Exercise(id=uid(), name="Bicycle Crunch", category="strength", muscle_groups=["core"],
             difficulty="beginner", equipment="none", instructions="Alternate elbow to opposite knee while extending the other leg.",
             sets=3, reps="20 total", rest_seconds=45, calories_per_minute=6.0, is_offline=True),
    Exercise(id=uid(), name="Jump Rope", category="cardio", muscle_groups=["legs","cardio"],
             difficulty="beginner", equipment="none", instructions="Maintain light feet and consistent rhythm. Jump just enough to clear rope.",
             sets=5, reps="1 minute", rest_seconds=30, calories_per_minute=11.0, is_offline=True),
    Exercise(id=uid(), name="Shoulder Press", category="strength", muscle_groups=["shoulders","triceps"],
             difficulty="beginner", equipment="dumbbells", instructions="Press dumbbells overhead from shoulder height. Lock out at top.",
             sets=3, reps="10-12", rest_seconds=60, calories_per_minute=6.5, is_offline=True),
    Exercise(id=uid(), name="Yoga Sun Salutation", category="yoga", muscle_groups=["full body"],
             difficulty="beginner", equipment="none", instructions="Flow through mountain, forward fold, plank, cobra, downdog, and back.",
             sets=1, reps="5 rounds", rest_seconds=0, calories_per_minute=4.0, is_offline=True),
]

WORKOUT_PLANS = [
    WorkoutPlan(id=uid(), name="Beginner Full Body", goal="maintain", difficulty="beginner",
                duration_weeks=4, days_per_week=3, exercises=[],
                description="Perfect for those starting out. Full-body movements 3 days a week with rest days in between. Builds habit and base fitness.", is_offline=True),
    WorkoutPlan(id=uid(), name="Weight Loss Cardio Blast", goal="weight_loss", difficulty="beginner",
                duration_weeks=6, days_per_week=5, exercises=[],
                description="Cardio-focused sessions with HIIT intervals to maximise calorie burn. Combines running, burpees, and jump rope.", is_offline=True),
    WorkoutPlan(id=uid(), name="Muscle Builder", goal="muscle_gain", difficulty="intermediate",
                duration_weeks=8, days_per_week=4, exercises=[],
                description="Progressive overload strength training split targeting all major muscle groups. Rest 90-120s between sets.", is_offline=True),
    WorkoutPlan(id=uid(), name="Endurance Base", goal="endurance", difficulty="intermediate",
                duration_weeks=12, days_per_week=5, exercises=[],
                description="Running and functional training to build aerobic capacity and stamina. Distance increases 10% each week.", is_offline=True),
    WorkoutPlan(id=uid(), name="Flexibility & Mobility", goal="flexibility", difficulty="beginner",
                duration_weeks=4, days_per_week=6, exercises=[],
                description="Daily yoga and stretching routine to improve range of motion, reduce injury risk, and enhance recovery.", is_offline=True),
]

ARTICLES = [
    KnowledgeArticle(id=uid(), title="Why Protein Is the King of Macros",
                     category="nutrition", summary="Learn why protein is essential for muscle growth, satiety, and metabolism.",
                     content="Protein is made of amino acids — the building blocks of muscle tissue. Consuming 1.6–2.2g per kg of bodyweight daily supports muscle growth and repair, keeps you fuller longer, and has the highest thermic effect of any macro (burns ~30% of its calories just being digested). Best sources: chicken breast, eggs, Greek yogurt, lentils, tofu.",
                     tags=["protein","muscle","diet"], read_time_minutes=4, is_offline=True),
    KnowledgeArticle(id=uid(), title="The Best Foods to Eat Before a Workout",
                     category="nutrition", summary="What to eat 1-2 hours before exercise for maximum energy and endurance.",
                     content="Pre-workout nutrition sets the stage for your session. Aim for a meal 1-2 hours before training with moderate carbs and protein, low fat. Examples: oats + banana, rice + chicken, toast + peanut butter. Avoid high-fat or high-fiber meals that slow digestion. Hydrate with at least 500ml water beforehand.",
                     tags=["pre-workout","nutrition","energy"], read_time_minutes=3, is_offline=True),
    KnowledgeArticle(id=uid(), title="Progressive Overload: The #1 Rule for Strength Gains",
                     category="workout", summary="Why you must progressively increase stress to keep gaining strength.",
                     content="Progressive overload means consistently increasing the demand on your body — more weight, more reps, less rest, better form. Without it, your body adapts and stops growing. Track your lifts. Aim for 2-5% weight increase each week, or add 1-2 reps per set. This principle applies equally to cardio: increase distance or pace gradually.",
                     tags=["strength","progressive overload","training"], read_time_minutes=5, is_offline=True),
    KnowledgeArticle(id=uid(), title="Sleep: The Most Underrated Recovery Tool",
                     category="recovery", summary="Why 7-9 hours of quality sleep is as important as your training plan.",
                     content="Growth hormone is released during deep sleep — this is when muscles actually repair and grow. Chronic sleep deprivation elevates cortisol (the stress hormone), increases fat storage, impairs decision-making, and kills motivation. Tips: consistent sleep/wake times, dark room below 18°C, no screens 30 min before bed, avoid caffeine after 2pm.",
                     tags=["sleep","recovery","hormones"], read_time_minutes=4, is_offline=True),
    KnowledgeArticle(id=uid(), title="Micronutrients Every Athlete Needs",
                     category="nutrition", summary="Iron, Magnesium, Vitamin D — what they do and how to get enough.",
                     content="Deficiencies in micronutrients silently sabotage performance. Iron: carries oxygen to muscles (low iron = fatigue — found in red meat, spinach, lentils). Magnesium: muscle contraction and sleep quality (nuts, seeds, leafy greens). Vitamin D: bone density and testosterone (sunlight, fatty fish, supplements). Zinc: immune function and recovery (pumpkin seeds, oysters).",
                     tags=["micronutrients","vitamins","minerals"], read_time_minutes=6, is_offline=True),
    KnowledgeArticle(id=uid(), title="HIIT vs Steady State Cardio: Which Burns More Fat?",
                     category="workout", summary="The science behind both approaches — when to use each.",
                     content="HIIT (High Intensity Interval Training) burns more calories per minute and creates an 'afterburn' effect (EPOC) that continues burning calories for hours post-workout. Steady state cardio is easier to recover from and builds aerobic base. Best approach: 2 HIIT sessions + 2 steady state sessions per week. Don't do HIIT on consecutive days.",
                     tags=["hiit","cardio","fat loss"], read_time_minutes=4, is_offline=True),
    KnowledgeArticle(id=uid(), title="Mindful Eating: Stop Eating on Autopilot",
                     category="mental_health", summary="Practical steps to build awareness around food and stop overeating.",
                     content="Mindful eating means paying full attention to the experience of eating. Eat slowly (20 minutes for your brain to register fullness), remove distractions, use smaller plates, check in on hunger levels 1-10 before and during meals. Studies show mindful eaters consume 300 fewer calories per day without dieting. Keep a food journal for just 3 days — awareness alone changes behavior.",
                     tags=["mindfulness","eating","psychology"], read_time_minutes=5, is_offline=True),
    KnowledgeArticle(id=uid(), title="Creatine: The Complete Beginner's Guide",
                     category="supplements", summary="Everything you need to know about the most researched supplement in fitness.",
                     content="Creatine monohydrate is the most scientifically supported supplement. It increases ATP (energy) available for short bursts of high-intensity effort, improving strength, power, and muscle volume. Dose: 3-5g daily (no loading phase needed). Take it consistently — timing doesn't matter much. Safe for kidneys in healthy individuals. Stay hydrated. Expect 1-2kg initial weight gain from water retention in muscle cells.",
                     tags=["creatine","supplements","strength"], read_time_minutes=5, is_offline=True),
    KnowledgeArticle(id=uid(), title="How to Calculate Your Daily Calorie Needs",
                     category="nutrition", summary="BMR, TDEE explained — and how to set the right calorie target.",
                     content="BMR (Basal Metabolic Rate) is calories your body needs at rest. TDEE (Total Daily Energy Expenditure) multiplies BMR by activity factor. To lose weight: eat 300-500 below TDEE. To gain muscle: eat 200-300 above TDEE. FitSphere calculates this for you using the Mifflin-St Jeor equation. Weigh yourself weekly (same time, same conditions) and adjust by 100 calories if not seeing results after 2-3 weeks.",
                     tags=["calories","tdee","bmr","nutrition"], read_time_minutes=5, is_offline=True),
    KnowledgeArticle(id=uid(), title="Active Recovery: What to Do on Rest Days",
                     category="recovery", summary="Light activity on rest days speeds recovery and reduces soreness.",
                     content="Complete rest is rarely optimal. Active recovery (light walks, swimming, yoga, foam rolling) increases blood flow to sore muscles, speeding nutrient delivery and waste removal. Aim for 20-40 minutes of easy movement on rest days. Heart rate should stay below 120 BPM. This also maintains the habit of daily movement without stressing the body.",
                     tags=["recovery","rest days","active recovery"], read_time_minutes=3, is_offline=True),
]


async def seed():
    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as db:
        # Check if already seeded
        result = await db.execute(select(Exercise).limit(1))
        if result.scalar_one_or_none():
            print("✓ Exercises already seeded — skipping.")
        else:
            db.add_all(EXERCISES)
            print(f"+ Adding {len(EXERCISES)} exercises...")

        result = await db.execute(select(WorkoutPlan).limit(1))
        if result.scalar_one_or_none():
            print("✓ Workout plans already seeded — skipping.")
        else:
            db.add_all(WORKOUT_PLANS)
            print(f"+ Adding {len(WORKOUT_PLANS)} workout plans...")

        result = await db.execute(select(KnowledgeArticle).limit(1))
        if result.scalar_one_or_none():
            print("✓ Articles already seeded — skipping.")
        else:
            db.add_all(ARTICLES)
            print(f"+ Adding {len(ARTICLES)} knowledge articles...")

        await db.commit()
        print("✓ Seed complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
