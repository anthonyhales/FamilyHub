from sqlalchemy.orm import Session
from app import models


def list_chores(db: Session, household_id: int):
    """
    Dashboard-safe chore listing.

    This does not assume optional fields (like due_date) exist on the Chore model.
    If you later add a due_date column via migration, this will automatically
    start ordering by it.
    """
    query = (
        db.query(models.Chore)
        .filter(models.Chore.household_id == household_id)
    )

    if hasattr(models.Chore, "due_date"):
        query = query.order_by(models.Chore.due_date.asc())
    else:
        query = query.order_by(models.Chore.id.asc())

    return query.all()
