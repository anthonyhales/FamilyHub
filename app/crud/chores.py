from datetime import date
from sqlalchemy.orm import Session

from app import models


def list_chores(db: Session, household_id: int):
    return (
        db.query(models.Chore)
        .filter(
            models.Chore.household_id == household_id,
            models.Chore.is_active == True,
        )
        .order_by(models.Chore.created_at.asc())
        .all()
    )


def create_chore(
    db: Session,
    household_id: int,
    name: str,
    description: str | None,
    every_n_days: int,
    assigned_to_user_id: int | None,
):
    chore = models.Chore(
        household_id=household_id,
        name=name,
        description=description,
        every_n_days=every_n_days,
        assigned_to_user_id=assigned_to_user_id,
    )
    db.add(chore)
    db.commit()
    return chore


def last_completed_on(db: Session, chore_id: int):
    row = (
        db.query(models.ChoreCompletion.completed_on)
        .filter(models.ChoreCompletion.chore_id == chore_id)
        .order_by(models.ChoreCompletion.completed_on.desc())
        .first()
    )
    return row[0] if row else None
