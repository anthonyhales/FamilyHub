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


def create_event(
    db: Session,
    household_id: int,
    title: str,
    description: str | None,
    start_at: datetime,
    end_at: datetime | None,
    created_by_user_id: int,
):
    ev = models.CalendarEvent(
        household_id=household_id,
        title=title,
        description=description,
        start_at=start_at,
        end_at=end_at,
        created_by_user_id=created_by_user_id,
    )
    db.add(ev)
    db.commit()
    return ev
