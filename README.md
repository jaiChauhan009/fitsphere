# FitSphere Backend

Complete fitness ecosystem REST API — nutrition tracking, workout logging, AI-powered food analysis, and personalized recommendations.

Built with **FastAPI** + **SQLAlchemy (async)** + **PostgreSQL (Supabase)** + **Firebase Auth** + **Google Gemini AI**.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Production Deployment](#production-deployment)
- [Calorie Calculation Logic](#calorie-calculation-logic)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL via Supabase (`asyncpg` driver) |
| Auth | Firebase Admin SDK (JWT verification) |
| AI | Google Gemini 1.5 Flash |
| Food Data | USDA FoodData Central API + Open Food Facts |
| Server | Gunicorn + Uvicorn workers |
| Config | Pydantic Settings + `.env` |

---

## Project Structure

```
fitsphere-backend/
├── main.py                 # FastAPI app, CORS, router registration
├── config.py               # Pydantic settings (reads .env)
├── database.py             # Async engine, session factory, Base
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic request/response schemas
│
├── routers/
│   ├── users.py            # User profile CRUD
│   ├── food.py             # Food search, barcode scan, category listing
│   ├── nutrition.py        # Meal logging, photo analysis, daily summary
│   ├── workouts.py         # Exercise library, workout plans, workout logs
│   ├── progress.py         # Body measurements, progress summary
│   ├── ai.py               # AI recommendations, diet plan generation
│   └── knowledge.py        # Health articles
│
├── utils/
│   ├── calories.py         # BMR/TDEE/BMI calculations (Mifflin-St Jeor)
│   ├── firebase.py         # Firebase token verification dependency
│   ├── gemini.py           # Gemini AI — food photo analysis + recommendations
│   ├── usda.py             # USDA FoodData Central API client
│   └── openfoodfacts.py    # Open Food Facts barcode API client
│
├── .env.example            # All required environment variables
├── requirements.txt        # Python dependencies
├── Procfile                # Heroku/Railway deployment command
└── gunicorn.conf.py        # Gunicorn worker configuration
```

---

## Database Models

### `User`
Stores the fitness profile. Calorie target is auto-calculated on create/update.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID string | Primary key |
| `firebase_uid` | string | Links to Firebase Auth |
| `email` | string | Unique |
| `age`, `gender` | int, enum | `male / female / other` |
| `height_cm`, `weight_kg` | float | Used for BMR calculation |
| `goal` | enum | `weight_loss / muscle_gain / maintain / endurance / flexibility` |
| `activity_level` | enum | `sedentary` → `extra_active` |
| `daily_calorie_target` | int | Auto-calculated via Mifflin-St Jeor |

### `Food`
Nutritional database. Populated from USDA API and barcode scans.

| Field | Notes |
|---|---|
| `usda_fdc_id` | USDA or `off_<barcode>` for Open Food Facts |
| `calories_per_100g` | Base unit for all macro calculations |
| `protein_g`, `carbs_g`, `fat_g`, `fiber_g` | Per 100g |
| `sodium_mg`, `calcium_mg`, `iron_mg`, `vitamin_c_mg`, ... | Micronutrients |
| `best_time_to_eat` | `morning / afternoon / evening / any` |
| `is_vegetarian`, `is_vegan` | Dietary flags |

### `NutritionLog`
One entry per food item per meal.

| Field | Notes |
|---|---|
| `meal_type` | `breakfast / lunch / dinner / snack` |
| `quantity_g` | User-entered portion |
| `log_date` | Indexed for daily queries |
| `micronutrients` | JSON dict for extra vitamins/minerals |

### `Exercise`
Offline-available exercise library.

| Field | Notes |
|---|---|
| `category` | `strength / cardio / flexibility / yoga / hiit` |
| `muscle_groups` | JSON array |
| `difficulty` | `beginner / intermediate / advanced` |
| `equipment` | `none / dumbbells / barbell / machine / resistance_band` |
| `calories_per_minute` | Used for burn estimation |

### `WorkoutPlan`
Curated plans linked to fitness goals.

### `WorkoutLog`
User workout session record with exercises done and calories burned.

### `BodyMeasurement`
Weight, body fat %, BMI, and body circumference history.

### `DietPlan`
AI-generated or template 7-day meal plans stored as JSON.

### `KnowledgeArticle`
Health and fitness articles categorized by `nutrition / workout / recovery / mental_health`.

---

## API Endpoints

### Users — `/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/users/` | No | Create user profile, auto-calculates daily calorie target |
| GET | `/users/me` | Yes | Get current user profile |
| PATCH | `/users/me` | Yes | Update profile, recalculates calories if body metrics change |

### Food — `/food`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/food/search?q=&category=&limit=` | No | Search local DB first, falls back to USDA API and auto-imports results |
| GET | `/food/{food_id}` | No | Get food by ID |
| GET | `/food/barcode/{barcode}` | No | Scan product barcode via Open Food Facts |
| GET | `/food/category/{category}` | No | List all foods in a category |

### Nutrition — `/nutrition`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/nutrition/log` | Yes | Log a meal entry |
| POST | `/nutrition/photo-analyze` | Yes | Upload food photo → Gemini AI returns macros |
| GET | `/nutrition/daily/{YYYY-MM-DD}` | Yes | Daily summary with per-meal breakdown and nutrient completion % |
| GET | `/nutrition/history?days=7` | Yes | Nutrition log history (up to 90 days) |
| DELETE | `/nutrition/log/{log_id}` | Yes | Delete a meal log entry |

**Daily Summary response includes:**
- Total calories, protein, carbs, fat, fiber
- Calories remaining vs target
- Meals grouped by type (`breakfast`, `lunch`, `dinner`, `snack`)
- Nutrient completion % for protein, fiber, vitamin C, iron, calcium, potassium

### Workouts — `/workouts`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/workouts/plans?goal=&difficulty=` | No | List workout plans |
| GET | `/workouts/exercises?category=&muscle_group=&difficulty=&equipment=` | No | Browse exercise library |
| POST | `/workouts/log` | Yes | Log a workout session |
| GET | `/workouts/history?days=30` | Yes | Workout history (up to 365 days) |

### Progress — `/progress`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/progress/measurement` | Yes | Log body measurement (weight, body fat %, waist, etc.), auto-calculates BMI |
| GET | `/progress/measurements` | Yes | Last 90 body measurements |
| GET | `/progress/summary` | Yes | Full progress dashboard |

**Progress Summary includes:**
- Current weight, target weight, total weight change
- BMI
- Average daily calories (7-day and 30-day)
- Workout count (7-day and 30-day)
- Consecutive logging streak (days)
- Top nutrient deficiencies (based on 7-day averages)

### AI — `/ai`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/ai/recommendations` | Yes | Personalized diet + workout tips from Gemini based on 7-day history |
| POST | `/ai/diet-plan-generate` | Yes | Generate a full 7-day personalized meal plan (JSON) |

**AI Recommendation response:**
```json
{
  "diet_tips": ["..."],
  "workout_tips": ["..."],
  "deficiency_alerts": ["..."],
  "meal_suggestions": ["..."],
  "motivational_message": "..."
}
```

### Knowledge — `/knowledge`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/knowledge/articles?category=&q=&limit=` | No | List/search health articles |
| GET | `/knowledge/articles/{article_id}` | No | Get article by ID |
| GET | `/knowledge/categories` | No | List available categories |

### Health Check

| Method | Path | Description |
|---|---|---|
| GET | `/` | App name and version |
| GET | `/health` | `{"status": "ok"}` |

---

## Authentication

All protected endpoints require a **Firebase ID token** in the `Authorization` header:

```
Authorization: Bearer <firebase_id_token>
```

The token is verified via `firebase-admin` SDK. The user's `firebase_uid` is extracted and used to look up the database user record.

**Getting a token (Flutter/Dart example):**
```dart
final token = await FirebaseAuth.instance.currentUser!.getIdToken();
```

If `FIREBASE_SERVICE_ACCOUNT_JSON` is not set, Firebase verification is skipped (useful for local testing without Firebase).

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# Firebase Auth
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_SERVICE_ACCOUNT_JSON=path/to/serviceAccountKey.json

# AI
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key  # optional

# USDA Food Database (free at fdc.nal.usda.gov)
USDA_API_KEY=your_usda_api_key

# App
SECRET_KEY=change_this_in_production
APP_ENV=development
CORS_ORIGINS=http://localhost:3000,http://10.0.2.2:8000
```

---

## Local Setup

**Requirements:** Python 3.11+

```bash
# 1. Clone and enter the directory
git clone https://github.com/jaiChauhan009/fitsphere.git
cd fitsphere

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Run development server
uvicorn main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs` (Swagger UI).

---

## Production Deployment

The app is configured for **Gunicorn + Uvicorn workers**.

**Start production server:**
```bash
gunicorn main:app -c gunicorn.conf.py
```

**Gunicorn config (`gunicorn.conf.py`):**
- Workers: `(CPU cores × 2) + 1`
- Worker class: `uvicorn.workers.UvicornWorker`
- Bind: `0.0.0.0:8000`
- Timeout: 120s
- Max requests per worker: 1000 (with jitter to prevent thundering herd)

**Railway / Heroku:** The `Procfile` is already set up:
```
web: gunicorn main:app -c gunicorn.conf.py
```

**Database tables** are created automatically on startup via SQLAlchemy's `create_all`. For production schema changes, use Alembic migrations (configured in `migrations/`).

---

## Calorie Calculation Logic

Daily calorie target is calculated using the **Mifflin-St Jeor equation**:

```
BMR (male)   = 10×weight + 6.25×height − 5×age + 5
BMR (female) = 10×weight + 6.25×height − 5×age − 161

TDEE = BMR × activity_multiplier

Activity multipliers:
  sedentary         → 1.2
  lightly_active    → 1.375
  moderately_active → 1.55
  very_active       → 1.725
  extra_active      → 1.9

Goal adjustments applied to TDEE:
  weight_loss  → −500 kcal
  muscle_gain  → +300 kcal
  endurance    → +200 kcal
  maintain     →   ±0 kcal

Minimum floor: 1200 kcal/day
```

BMI is calculated as: `weight_kg / (height_m)²`



for testing 
