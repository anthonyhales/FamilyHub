from datetime import datetime
from sqlalchemy.orm import Session

from app import models


def list_upcoming_events(
    db: Session,
    household_id: int,
    from_dt: datetime,
    limit: int = 10,
):
    return (
        db.query(models.CalendarEvent)
        .filter(
            models.CalendarEvent.household_id == household_id,
            models.CalendarEvent.start_at >= from_dt,
        )
        .order_by(models.CalendarEvent.start_at.asc())
        .limit(limit)
        .all()
    )
