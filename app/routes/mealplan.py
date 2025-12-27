from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..deps import get_current_user, get_or_set_csrf, validate_csrf
from .. import crud, models
from ._render import templates, ctx
from app.core.activity import log_activity


router = APIRouter(prefix="/mealplan", tags=["mealplan"])


def _start_of_week(d: date) -> date:
    # Monday start
    return d - timedelta(days=d.weekday())


@router.get("", include_in_schema=False)
def mealplan_week(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    week: str | None = None,
):
    csrf = get_or_set_csrf(request)

    today = datetime.utcnow().date()
    start = _start_of_week(date.fromisoformat(week) if week else today)
    end = start + timedelta(days=6)

    meals = crud.list_meals_in_range(db, user.household_id, start, end)
    by_key = {(m.meal_date, m.meal_slot): m for m in meals}

    days = [start + timedelta(days=i) for i in range(7)]
    slots = ["breakfast", "lunch", "dinner"]

    return templates.TemplateResponse(
        "mealplan/week.html",
        ctx(request, csrf=csrf, start=start, end=end, days=days, slots=slots, by_key=by_key),
    )


@router.post("/set", include_in_schema=False)
def mealplan_set(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    meal_date: str = Form(...),
    meal_slot: str = Form(...),
    title: str = Form(...),
    notes: str = Form(""),
    week: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    d = date.fromisoformat(meal_date)
    crud.upsert_meal(
        db,
        household_id=user.household_id,
        meal_date=d,
        meal_slot=meal_slot,
        title=title,
        notes=notes or None,
        created_by_user_id=user.id,
    )
    request.session["flash"] = {"type": "success", "message": "Meal saved."}
    target_week = week or meal_date
    return RedirectResponse(f"/mealplan?week={target_week}", status_code=302)


@router.post("/{entry_id}/delete", include_in_schema=False)
def mealplan_delete(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    week: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    crud.delete_meal(db, user.household_id, entry_id)
    request.session["flash"] = {"type": "success", "message": "Meal removed."}
    return RedirectResponse(f"/mealplan?week={week}" if week else "/mealplan", status_code=302)
