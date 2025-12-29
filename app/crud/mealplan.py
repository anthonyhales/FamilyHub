from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session

from app import models


def list_meals_in_range(db: Session, household_id: int, start: date, end: date):
    """List meal plan entries between start and end (inclusive)."""
    return (
        db.query(models.MealPlanEntry)
        .filter(
            models.MealPlanEntry.household_id == household_id,
            models.MealPlanEntry.meal_date >= start,
            models.MealPlanEntry.meal_date <= end,
        )
        .order_by(models.MealPlanEntry.meal_date.asc(), models.MealPlanEntry.meal_slot.asc())
        .all()
    )
