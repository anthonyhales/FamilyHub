from __future__ import annotations

from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models


def list_chores(db: Session, household_id: int):
    """Return chores for household.

    Older DBs / models may not have certain optional columns (e.g. due_date).
    We keep this defensive so the dashboard never crashes.
    """
    q = db.query(models.Chore).filter(models.Chore.household_id == household_id)

    # Only order by due_date if the model actually has that attribute.
    if hasattr(models.Chore, "due_date"):
        q = q.order_by(models.Chore.due_date.asc().nulls_last())
    else:
        q = q.order_by(models.Chore.id.asc())

    return q.all()


def last_completed_on(db: Session, chore_id: int) -> date | None:
    """Return the most recent completion date for a chore, or None."""
    # Use SQLAlchemy select to stay compatible with SQLite.
    stmt = select(func.max(models.ChoreCompletion.completed_on)).where(
        models.ChoreCompletion.chore_id == chore_id
    )
    return db.scalar(stmt)
