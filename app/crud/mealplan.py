from datetime import date
from sqlalchemy.orm import Session

from app import models


def upsert_meal(
    db: Session,
    household_id: int,
    meal_date: date,
    meal_slot: str,
    title: str,
    notes: str | None,
    created_by_user_id: int,
):
    meal = (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.household_id == household_id,
            models.MealPlanEntry.meal_date == meal_date,
            models.MealPlanEntry.meal_slot == meal_slot,
        )
        .first()
    )

    if meal:
        meal.title = title
        meal.notes = notes
    else:
        meal = models.MealPlanEntry(
            household_id=household_id,
            meal_date=meal_date,
            meal_slot=meal_slot,
            title=title,
            notes=notes,
            created_by_user_id=created_by_user_id,
        )
        db.add(meal)

def list_meals_in_range(
    db: Session,
    household_id: int,
    start: date,
    end: date,
):
    return (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.household_id == household_id,
            models.MealPlanEntry.meal_date >= start,
            models.MealPlanEntry.meal_date <= end,
        )
        .order_by(
            models.MealPlanEntry.meal_date.asc(),
            models.MealPlanEntry.meal_slot.asc(),
        )
        .all()
    )

 db.commit()
return meal