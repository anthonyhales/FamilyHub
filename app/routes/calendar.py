from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..deps import get_current_user, get_or_set_csrf, validate_csrf
from .. import crud, models
from ._render import templates, ctx
from app.core.activity import log_activity


router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", include_in_schema=False)
def calendar_list(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)
    events = crud.list_upcoming_events(db, user.household_id, datetime.utcnow(), limit=100)
    return templates.TemplateResponse("calendar/list.html", ctx(request, csrf=csrf, events=events))


@router.get("/new", include_in_schema=False)
def calendar_new(
    request: Request,
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)
    return templates.TemplateResponse("calendar/new.html", ctx(request, csrf=csrf))


@router.post("/new", include_in_schema=False)
def calendar_create(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    title: str = Form(...),
    description: str = Form(""),
    start_at: str = Form(...),
    end_at: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    # from <input type=datetime-local> (no timezone). interpret as local server time
    start_dt = datetime.fromisoformat(start_at)
    end_dt = datetime.fromisoformat(end_at) if end_at else None

    crud.create_event(
        db,
        household_id=user.household_id,
        title=title,
        description=description or None,
        start_at=start_dt,
        end_at=end_dt,
        created_by_user_id=user.id,
    )
    request.session["flash"] = {"type": "success", "message": "Event added."}
    return RedirectResponse("/calendar", status_code=302)


@router.post("/{event_id}/delete", include_in_schema=False)
def calendar_delete(
    request: Request,
    event_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    crud.delete_event(db, user.household_id, event_id)
    request.session["flash"] = {"type": "success", "message": "Event deleted."}
    return RedirectResponse("/calendar", status_code=302)
