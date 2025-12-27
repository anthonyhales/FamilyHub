from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..deps import get_current_user, get_or_set_csrf
from .. import crud, models
from ._render import templates, ctx
from app.core.activity import log_activity


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", include_in_schema=False)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)
    upcoming = crud.list_upcoming_events(db, user.household_id, datetime.utcnow(), limit=10)

    chores = crud.list_chores(db, user.household_id)
    chore_cards = []
    today = datetime.utcnow().date()
    for ch in chores:
        last_done = crud.last_completed_on(db, ch.id)
        due = True
        if last_done and ch.every_n_days > 0:
            due = (today - last_done).days >= ch.every_n_days
        chore_cards.append({"chore": ch, "last_done": last_done, "due": due})

    start = today
    end = today + timedelta(days=6)
    meals = crud.list_meals_in_range(db, user.household_id, start, end)

    return templates.TemplateResponse(
        "dashboard.html",
        ctx(
            request,
            csrf=csrf,
            upcoming=upcoming,
            chore_cards=chore_cards[:8],
            meals=meals,
            meal_range=(start, end),
        ),
    )
