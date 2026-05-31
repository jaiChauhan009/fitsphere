import google.generativeai as genai
import base64
from io import BytesIO
from PIL import Image
from config import settings

_configured = False


def _configure():
    global _configured
    if not _configured and settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True


async def analyze_food_photo(image_bytes: bytes) -> dict:
    _configure()
    model = genai.GenerativeModel("gemini-1.5-flash")

    img = Image.open(BytesIO(image_bytes))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    prompt = """
    Analyze this food image and provide detailed nutritional information.

    Return a JSON response with this exact structure:
    {
      "detected_foods": [
        {
          "name": "food name",
          "estimated_quantity_g": 150,
          "calories": 200,
          "protein_g": 10,
          "carbs_g": 25,
          "fat_g": 8,
          "fiber_g": 3,
          "confidence": 0.9
        }
      ],
      "total_calories": 200,
      "total_protein_g": 10,
      "total_carbs_g": 25,
      "total_fat_g": 8,
      "overall_confidence": 0.9,
      "meal_type_suggestion": "lunch",
      "health_notes": "brief note about this meal"
    }

    Be accurate. If multiple foods are visible, list each separately.
    Estimate portion sizes visually. Only return valid JSON, no extra text.
    """

    response = model.generate_content(
        [{"mime_type": "image/jpeg", "data": img_b64}, prompt]
    )

    import json
    import re
    text = response.text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError(f"Gemini returned unexpected format: {text[:200]}")


async def get_ai_recommendations(user_data: dict, nutrition_7d: dict, workout_7d: dict) -> dict:
    _configure()
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    You are a professional fitness and nutrition coach. Analyze this user's data and give personalized recommendations.

    User Profile:
    - Age: {user_data.get('age')}, Gender: {user_data.get('gender')}
    - Height: {user_data.get('height_cm')}cm, Current Weight: {user_data.get('weight_kg')}kg
    - Goal: {user_data.get('goal')}, Activity Level: {user_data.get('activity_level')}
    - Daily Calorie Target: {user_data.get('daily_calorie_target')} kcal

    Last 7 Days Nutrition Average:
    - Calories: {nutrition_7d.get('avg_calories')}/day
    - Protein: {nutrition_7d.get('avg_protein_g')}g, Carbs: {nutrition_7d.get('avg_carbs_g')}g, Fat: {nutrition_7d.get('avg_fat_g')}g
    - Missing nutrients: {nutrition_7d.get('deficiencies', [])}

    Last 7 Days Workouts: {workout_7d.get('count')} sessions, avg duration {workout_7d.get('avg_duration_min')} minutes

    Return JSON:
    {{
      "diet_tips": ["tip1", "tip2", "tip3"],
      "workout_tips": ["tip1", "tip2"],
      "deficiency_alerts": ["alert1"],
      "meal_suggestions": ["suggestion1", "suggestion2"],
      "motivational_message": "one encouraging sentence"
    }}
    Only return valid JSON.
    """

    import json
    import re
    response = model.generate_content(prompt)
    text = response.text.strip()
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return {
        "diet_tips": [], "workout_tips": [], "deficiency_alerts": [],
        "meal_suggestions": [], "motivational_message": "Keep going!"
    }
