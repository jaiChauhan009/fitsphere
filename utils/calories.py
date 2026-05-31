from models import GoalType, ActivityLevel


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


ACTIVITY_MULTIPLIERS = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.lightly_active: 1.375,
    ActivityLevel.moderately_active: 1.55,
    ActivityLevel.very_active: 1.725,
    ActivityLevel.extra_active: 1.9,
}

GOAL_ADJUSTMENTS = {
    GoalType.weight_loss: -500,
    GoalType.muscle_gain: +300,
    GoalType.maintain: 0,
    GoalType.endurance: +200,
    GoalType.flexibility: 0,
}


def calculate_daily_calories(weight_kg, height_cm, age, gender, activity_level, goal) -> int:
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    return max(1200, int(tdee + adjustment))


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    h_m = height_cm / 100
    return round(weight_kg / (h_m * h_m), 2)
