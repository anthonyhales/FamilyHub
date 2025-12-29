from sqlalchemy.orm import Session
from app import models


def list_chores(db: Session, household_id: int):
    return (
        db.query(models.Chore)
        .filter(models.Chore.household_id == household_id)
        .order_by(models.Chore.due_date.asc().nulls_last())
        .all()
    )
