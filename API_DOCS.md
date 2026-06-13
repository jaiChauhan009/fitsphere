# FitSphere API — Frontend Reference

**Base URL:** `https://fitsphere-ofl4.onrender.com` (prod) · `http://localhost:8000` (local)  
**All endpoints are prefixed with nothing extra** — paths below are complete.  
**Auth:** All protected endpoints require a Firebase ID token in the `Authorization` header.

```
Authorization: Bearer <firebase_id_token>
```

---

## Global Error Format

Every error response uses this shape:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Code | When it happens |
|-----------|----------------|
| `400` | Bad request (e.g. duplicate email) |
| `401` | Missing or expired Firebase token |
| `403` | No auth credentials provided at all |
| `404` | Resource not found |
| `422` | Validation error — wrong field type, value out of range, missing required field |
| `500` | Server/AI error |

For `422`, the response has a more detailed shape:
```json
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "Input should be greater than or equal to 10",
      "type": "greater_than_equal"
    }
  ]
}
```

---

## Health Check

### `GET /health`
No auth required.

**Response `200`**
```json
{
  "status": "ok",
  "api": "ok",
  "database": "ok",
  "latency_ms": 12.4,
  "version": "1.0.0"
}
```

**Response `503`** — DB unreachable
```json
{
  "status": "degraded",
  "api": "ok",
  "database": "error: <message>",
  "latency_ms": 1200.0,
  "version": "1.0.0"
}
```

---

## Users

### `POST /users/`
Create a new user profile. Call this once after Firebase sign-up.  
**No auth required** — but send `firebase_uid` in the body to link the account.

**Request Body**
```json
{
  "email": "jai@example.com",          // required, valid email
  "name": "Jai Chauhan",               // required, string
  "age": 25,                           // required, 10–100
  "gender": "male",                    // required: "male" | "female" | "other"
  "height_cm": 175.0,                  // required, 50–300
  "weight_kg": 72.0,                   // required, 10–500
  "target_weight_kg": 68.0,            // optional
  "goal": "weight_loss",               // optional, default "maintain"
  "activity_level": "moderately_active", // optional, default "lightly_active"
  "firebase_uid": "abc123uid"          // optional but highly recommended
}
```

**goal values:** `"weight_loss"` | `"muscle_gain"` | `"maintain"` | `"endurance"` | `"flexibility"`

**activity_level values:** `"sedentary"` | `"lightly_active"` | `"moderately_active"` | `"very_active"` | `"extra_active"`

**Response `200`**
```json
{
  "id": "uuid-string",
  "email": "jai@example.com",
  "name": "Jai Chauhan",
  "age": 25,
  "gender": "male",
  "height_cm": 175.0,
  "weight_kg": 72.0,
  "target_weight_kg": 68.0,
  "goal": "weight_loss",
  "activity_level": "moderately_active",
  "daily_calorie_target": 1980,        // auto-calculated from profile
  "profile_photo_url": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors**
| Code | Detail |
|------|--------|
| `400` | `"Email already registered"` |
| `422` | age < 10 or > 100, height_cm out of range, invalid enum value |

---

### `GET /users/me`
Get the current user's profile.  
**Auth required.**

**Response `200`** — same shape as `POST /users/` response above.

**Errors**
| Code | Detail |
|------|--------|
| `401` | Missing/expired token |
| `404` | `"User not found"` — profile not yet created |

---

### `PATCH /users/me`
Update profile fields. Only send what changed — all fields optional.  
**Auth required.**

**Request Body** (all optional)
```json
{
  "name": "New Name",
  "age": 26,
  "height_cm": 176.0,
  "weight_kg": 70.0,
  "target_weight_kg": 65.0,
  "goal": "muscle_gain",
  "activity_level": "very_active"
}
```

> Updating `weight_kg`, `height_cm`, `goal`, or `activity_level` automatically recalculates `daily_calorie_target`.

**Response `200`** — full updated user object (same shape as `POST /users/`).

**Errors**
| Code | Detail |
|------|--------|
| `401` | Missing/expired token |
| `404` | `"User not found"` |

---

## Food

### `GET /food/search`
Search food by name or category. Checks local DB first, falls back to USDA API.  
No auth required.

**Query Params**
| Param | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `q` | string | yes | — | Min 1 character |
| `category` | string | no | — | Filter by category |
| `limit` | int | no | 20 | Max 50 |

**Response `200`** — array of food objects
```json
[
  {
    "id": "uuid-string",
    "name": "Chicken Breast",
    "category": "protein",
    "calories_per_100g": 165.0,
    "protein_g": 31.0,
    "carbs_g": 0.0,
    "fat_g": 3.6,
    "fiber_g": 0.0,
    "sodium_mg": 74.0,
    "vitamin_c_mg": 0.0,
    "iron_mg": 0.9,
    "calcium_mg": 11.0,
    "best_time_to_eat": null,          // "morning" | "afternoon" | "evening" | "any" | null
    "serving_size_g": 100.0,
    "health_benefits": null,
    "is_vegetarian": false,
    "is_vegan": false
  }
]
```

**Errors**
| Code | Detail |
|------|--------|
| `422` | `q` is empty string |

---

### `GET /food/{food_id}`
Get a specific food item by its ID.  
No auth required.

**Response `200`** — single food object (same shape as search result above).

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"Food not found"` |

---

### `GET /food/barcode/{barcode}`
Look up a product by barcode (Open Food Facts). Saves to local DB automatically.  
No auth required.

**Example:** `GET /food/barcode/8901491502057`

**Response `200`** — food object (same shape as search result).

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"Product not found"` |

---

### `GET /food/category/{category}`
List all foods in a category.  
No auth required.

**Query Params**
| Param | Type | Required | Default | Max |
|-------|------|----------|---------|-----|
| `limit` | int | no | 50 | 200 |

**Common categories:** `protein` · `grain` · `vegetable` · `fruit` · `dairy` · `spice` · `other`

**Response `200`** — array of food objects (same shape as search result). Returns `[]` if category not found.

---

## Nutrition

All endpoints require **Auth**.

### `POST /nutrition/log`
Log a meal.

**Request Body**
```json
{
  "food_name": "Brown Rice",            // required, string
  "meal_type": "lunch",                 // required: "breakfast" | "lunch" | "dinner" | "snack"
  "quantity_g": 200.0,                  // required, must be > 0
  "calories": 432.0,                    // required, float
  "protein_g": 10.0,                    // optional, default 0
  "carbs_g": 90.0,                      // optional, default 0
  "fat_g": 3.6,                         // optional, default 0
  "fiber_g": 7.0,                       // optional, default 0
  "food_id": "uuid-string",             // optional — link to food in DB
  "micronutrients": {                   // optional, extra nutrients
    "vitamin_c_mg": 5.0,
    "iron_mg": 1.2,
    "calcium_mg": 30.0,
    "potassium_mg": 150.0
  },
  "log_date": "2024-01-15",             // optional, defaults to today (YYYY-MM-DD)
  "notes": "post-workout meal"          // optional
}
```

**Response `200`**
```json
{
  "id": "uuid-string",
  "user_id": "uuid-string",
  "food_id": "uuid-string or null",
  "food_name": "Brown Rice",
  "meal_type": "lunch",
  "quantity_g": 200.0,
  "calories": 432.0,
  "protein_g": 10.0,
  "carbs_g": 90.0,
  "fat_g": 3.6,
  "fiber_g": 7.0,
  "micronutrients": {},
  "photo_url": null,
  "log_date": "2024-01-15",
  "notes": null,
  "logged_at": "2024-01-15T12:30:00Z"
}
```

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found. Create profile first."` |
| `422` | `quantity_g` is 0 or negative, missing `food_name`, invalid `meal_type` |

---

### `POST /nutrition/photo-analyze`
Analyze a food photo using AI (Gemini). Returns detected foods and nutrition estimates.  
**Auth required.**

**Request:** `multipart/form-data`
| Field | Type | Notes |
|-------|------|-------|
| `file` | image file | Any image format (jpg, png, webp) |

**Response `200`**
```json
{
  "detected_foods": [
    {
      "name": "Rice",
      "quantity_g": 200,
      "calories": 260,
      "protein_g": 5,
      "carbs_g": 57,
      "fat_g": 0.4
    },
    {
      "name": "Grilled Chicken",
      "quantity_g": 150,
      "calories": 248,
      "protein_g": 46,
      "carbs_g": 0,
      "fat_g": 5.4
    }
  ],
  "total_calories": 508.0,
  "total_protein_g": 51.0,
  "total_carbs_g": 57.0,
  "total_fat_g": 5.8,
  "confidence": 0.85,
  "raw_response": "AI response text..."
}
```

**Errors**
| Code | Detail |
|------|--------|
| `400` | `"File must be an image"` |
| `500` | AI service error |

---

### `GET /nutrition/daily/{log_date}`
Get complete nutrition summary for a specific day.  
**Auth required.**

**Path Param:** `log_date` in `YYYY-MM-DD` format. Example: `/nutrition/daily/2024-01-15`

**Response `200`**
```json
{
  "date": "2024-01-15",
  "total_calories": 1850.0,
  "total_protein_g": 95.0,
  "total_carbs_g": 220.0,
  "total_fat_g": 55.0,
  "total_fiber_g": 28.0,
  "calorie_target": 2000,              // from user profile
  "calorie_remaining": 150.0,          // always >= 0
  "meals": {
    "breakfast": [
      { /* NutritionLog object — same as POST /nutrition/log response */ }
    ],
    "lunch": [ /* ... */ ],
    "dinner": [ /* ... */ ],
    "snack": [ /* ... */ ]
  },
  "nutrient_completion": {
    "protein_g": 87.5,                 // % of daily target met (0–100)
    "fiber_g": 100.0,
    "vitamin_c_mg": 45.0,
    "iron_mg": 60.0,
    "calcium_mg": 30.0,
    "potassium_mg": 20.0
  }
}
```

> Returns all zeros for days with no logs — never errors on empty days.

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found. Create profile first."` |
| `422` | Invalid date format |

---

### `GET /nutrition/history`
Get nutrition logs for the past N days.  
**Auth required.**

**Query Params**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `days` | int | 7 | 90 |

**Response `200`** — array of log objects ordered newest first (same shape as `POST /nutrition/log` response).

**Errors**
| Code | Detail |
|------|--------|
| `422` | `days` > 90 |

---

### `DELETE /nutrition/log/{log_id}`
Delete a specific nutrition log entry.  
**Auth required.**

**Response `200`**
```json
{
  "deleted": "uuid-of-deleted-log"
}
```

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"Log not found"` — doesn't exist or belongs to another user |

---

## Workouts

### `GET /workouts/plans`
List available workout plans. No auth required.

**Query Params** (all optional)
| Param | Values |
|-------|--------|
| `goal` | `weight_loss` · `muscle_gain` · `maintain` · `endurance` · `flexibility` |
| `difficulty` | `beginner` · `intermediate` · `advanced` |

**Response `200`**
```json
[
  {
    "id": "uuid-string",
    "name": "Beginner Full Body",
    "goal": "maintain",
    "difficulty": "beginner",
    "duration_weeks": 4,
    "days_per_week": 3,
    "description": "Simple full-body routine",
    "exercises": [
      {
        "exercise_id": "uuid-string",
        "sets": 3,
        "reps": "10-12",
        "rest": 60
      }
    ],
    "is_offline": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

Returns `[]` if no plans match the filters.

---

### `GET /workouts/exercises`
List exercises. No auth required.

**Query Params** (all optional)
| Param | Example values |
|-------|---------------|
| `category` | `strength` · `cardio` · `flexibility` · `yoga` · `hiit` |
| `difficulty` | `beginner` · `intermediate` · `advanced` |
| `equipment` | `none` · `dumbbells` · `barbell` · `machine` · `resistance_band` |

**Response `200`**
```json
[
  {
    "id": "uuid-string",
    "name": "Push-up",
    "category": "strength",
    "muscle_groups": ["chest", "triceps", "shoulders"],
    "difficulty": "beginner",
    "equipment": "none",
    "instructions": "Start in plank position...",
    "sets": 3,
    "reps": "10-15",
    "rest_seconds": 60,
    "calories_per_minute": 7.0,
    "video_url": null,
    "image_url": null,
    "is_offline": true
  }
]
```

---

### `POST /workouts/log`
Log a completed workout.  
**Auth required.**

**Request Body**
```json
{
  "duration_minutes": 45,              // required, integer
  "exercises_done": [                  // optional, default []
    {
      "name": "Push-up",
      "sets": 3,
      "reps": 12,
      "weight_kg": null
    },
    {
      "name": "Running",
      "duration_minutes": 20
    }
  ],
  "workout_plan_id": "uuid-string",    // optional — link to a plan
  "calories_burned": 320.0,            // optional
  "notes": "Tough session",            // optional
  "log_date": "2024-01-15"             // optional, defaults to today
}
```

**Response `200`**
```json
{
  "id": "uuid-string",
  "user_id": "uuid-string",
  "workout_plan_id": null,
  "exercises_done": [ /* array of exercise objects as sent */ ],
  "duration_minutes": 45,
  "calories_burned": 320.0,
  "notes": "Tough session",
  "log_date": "2024-01-15",
  "logged_at": "2024-01-15T18:45:00Z"
}
```

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found"` |
| `422` | Missing `duration_minutes` |

---

### `GET /workouts/history`
Get workout history for the past N days.  
**Auth required.**

**Query Params**
| Param | Default | Max |
|-------|---------|-----|
| `days` | 30 | 365 |

**Response `200`** — array of workout log objects ordered newest first (same shape as `POST /workouts/log` response).

**Errors**
| Code | Detail |
|------|--------|
| `422` | `days` > 365 |

---

## Progress

All endpoints require **Auth**.

### `POST /progress/measurement`
Log a body measurement. Also updates `weight_kg` on the user profile.

**Request Body**
```json
{
  "weight_kg": 72.5,                   // required
  "body_fat_percent": 18.5,            // optional
  "muscle_mass_kg": 35.0,              // optional
  "waist_cm": 82.0,                    // optional
  "chest_cm": 98.0,                    // optional
  "hips_cm": 96.0,                     // optional
  "measure_date": "2024-01-15"         // optional, defaults to today
}
```

**Response `200`**
```json
{
  "id": "uuid-string",
  "user_id": "uuid-string",
  "weight_kg": 72.5,
  "body_fat_percent": 18.5,
  "muscle_mass_kg": 35.0,
  "waist_cm": 82.0,
  "chest_cm": 98.0,
  "hips_cm": 96.0,
  "bmi": 23.67,                        // auto-calculated from weight + user's height
  "measure_date": "2024-01-15",
  "measured_at": "2024-01-15T08:00:00Z"
}
```

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found"` |
| `422` | Missing `weight_kg` |

---

### `GET /progress/measurements`
Get measurement history (last 90 entries, newest first).  
**Auth required.**

**Response `200`** — array of measurement objects (same shape as `POST /progress/measurement` response).

---

### `GET /progress/summary`
Get a full progress dashboard summary. Cached for 2 minutes.  
**Auth required.**

**Response `200`**
```json
{
  "current_weight_kg": 72.5,           // from most recent measurement
  "target_weight_kg": 68.0,
  "weight_change_kg": -2.5,            // negative = lost weight, positive = gained
  "bmi": 23.67,
  "avg_daily_calories_7d": 1850.5,     // null if no logs
  "avg_daily_calories_30d": 1920.0,    // null if no logs
  "workout_count_7d": 4,
  "workout_count_30d": 14,
  "streak_days": 5,                    // consecutive days with nutrition logs
  "top_nutrient_deficiencies": [       // nutrients averaging < 70% of daily target
    "protein",
    "fiber"
  ],
  "measurements_history": [            // last 30 measurements, newest first
    {
      "id": "uuid",
      "user_id": "uuid",
      "weight_kg": 72.5,
      "body_fat_percent": 18.5,
      "muscle_mass_kg": 35.0,
      "waist_cm": 82.0,
      "chest_cm": 98.0,
      "hips_cm": 96.0,
      "bmi": 23.67,
      "measure_date": "2024-01-15",
      "measured_at": "2024-01-15T08:00:00Z"
    }
  ]
}
```

**Notes for frontend:**
- `weight_change_kg` is `null` if only one measurement exists
- `avg_daily_calories_7d` / `avg_daily_calories_30d` are `null` if no nutrition logs exist
- `top_nutrient_deficiencies` is an empty `[]` when diet is good
- `streak_days` counts today only if today has at least one nutrition log

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found"` |

---

## Knowledge

No auth required for any knowledge endpoints.

### `GET /knowledge/articles`
List articles with optional filters.

**Query Params** (all optional)
| Param | Notes |
|-------|-------|
| `category` | `nutrition` · `workout` · `recovery` · `mental_health` · `supplements` |
| `q` | Full-text search on title and summary |
| `limit` | Default 20, max 100 |

**Response `200`**
```json
[
  {
    "id": "uuid-string",
    "title": "Why Protein Matters",
    "category": "nutrition",
    "content": "Full article content...",
    "summary": "Short summary shown in cards",
    "tags": ["protein", "muscle", "diet"],
    "image_url": null,
    "read_time_minutes": 5,
    "is_offline": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**Errors**
| Code | Detail |
|------|--------|
| `422` | `limit` > 100 |

---

### `GET /knowledge/articles/{article_id}`
Get a single article.

**Response `200`** — single article object (same shape as list above).

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"Article not found"` |

---

### `GET /knowledge/categories`
Get all article categories.

**Response `200`**
```json
[
  { "id": "nutrition",     "label": "Nutrition",     "icon": "🥗" },
  { "id": "workout",       "label": "Workout",       "icon": "💪" },
  { "id": "recovery",      "label": "Recovery",      "icon": "😴" },
  { "id": "mental_health", "label": "Mental Health", "icon": "🧠" },
  { "id": "supplements",   "label": "Supplements",   "icon": "💊" }
]
```

---

## AI

All endpoints require **Auth**.

### `GET /ai/recommendations`
Get personalized diet and workout recommendations based on last 7 days of logs.

**Response `200`**
```json
{
  "diet_tips": [
    "Increase protein intake — you're averaging only 45g/day vs a 50g target.",
    "Add more leafy greens for iron."
  ],
  "workout_tips": [
    "You've been consistent! Try adding 1 more session this week.",
    "Consider adding HIIT for better fat burn."
  ],
  "deficiency_alerts": [
    "Low fiber intake detected — aim for 25g/day.",
    "Iron levels below target — consider spinach or lentils."
  ],
  "meal_suggestions": [
    "Grilled chicken with quinoa for lunch",
    "Greek yogurt with berries as a snack"
  ],
  "motivational_message": "Great job logging your meals! Keep up the streak!"
}
```

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found"` |
| `500` | Gemini API error |

---

### `POST /ai/diet-plan-generate`
Generate a personalized 7-day meal plan using Gemini AI.  
**Auth required.** No request body needed.

**Response `200`**
```json
{
  "plan_name": "Weight Loss Plan for Jai",
  "days": [
    {
      "day": 1,
      "breakfast": [
        { "food": "Oats with banana", "quantity_g": 200, "calories": 350 }
      ],
      "lunch": [
        { "food": "Grilled chicken salad", "quantity_g": 300, "calories": 420 }
      ],
      "dinner": [
        { "food": "Dal with brown rice", "quantity_g": 350, "calories": 480 }
      ],
      "snacks": [
        { "food": "Almonds", "quantity_g": 30, "calories": 174 }
      ],
      "total_calories": 1424
    }
    // ... 6 more days
  ]
}
```

**Errors**
| Code | Detail |
|------|--------|
| `404` | `"User not found"` |
| `500` | `"AI failed to generate plan"` |

---

## Enum Reference

| Enum | Values |
|------|--------|
| `gender` | `male` · `female` · `other` |
| `goal` | `weight_loss` · `muscle_gain` · `maintain` · `endurance` · `flexibility` |
| `activity_level` | `sedentary` · `lightly_active` · `moderately_active` · `very_active` · `extra_active` |
| `meal_type` | `breakfast` · `lunch` · `dinner` · `snack` |
| `exercise_category` | `strength` · `cardio` · `flexibility` · `yoga` · `hiit` |
| `exercise_difficulty` | `beginner` · `intermediate` · `advanced` |
| `equipment` | `none` · `dumbbells` · `barbell` · `machine` · `resistance_band` |
| `food_category` | `protein` · `grain` · `vegetable` · `fruit` · `dairy` · `spice` · `other` |
| `article_category` | `nutrition` · `workout` · `recovery` · `mental_health` · `supplements` |

---

## Typical App Flow

```
1. Firebase sign-up/login
   ↓
2. POST /users/  { email, name, age, gender, height_cm, weight_kg, firebase_uid, ... }
   ↓
3. GET /users/me  (on every app open — check if profile exists)
   ↓
4. Home screen: GET /progress/summary
               GET /nutrition/daily/2024-01-15
   ↓
5. Log food:  GET /food/search?q=rice
             POST /nutrition/log  { food_name, meal_type, calories, ... }
   ↓
6. Log workout: GET /workouts/plans
               GET /workouts/exercises
               POST /workouts/log  { duration_minutes, exercises_done, ... }
   ↓
7. Track body: POST /progress/measurement  { weight_kg }
              GET /progress/measurements
   ↓
8. AI nudge:  GET /ai/recommendations
              POST /ai/diet-plan-generate
```
