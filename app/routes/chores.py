from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..deps import get_current_user, get_or_set_csrf, validate_csrf
from .. import crud, models
from ._render import templates, ctx

router = APIRouter(prefix="/chores", tags=["chores"])


@router.get("", include_in_schema=False)
def chores_list(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)
    chores = crud.list_chores(db, user.household_id)
    today = datetime.utcnow().date()
    enriched = []
    for ch in chores:
        last_done = crud.last_completed_on(db, ch.id)
        due = True
        if last_done and ch.every_n_days > 0:
            due = (today - last_done).days >= ch.every_n_days
        enriched.append({"chore": ch, "last_done": last_done, "due": due})
    users = crud.list_users(db, user.household_id)
    return templates.TemplateResponse("chores/list.html", ctx(request, csrf=csrf, chores=enriched, users=users))


@router.post("/new", include_in_schema=False)
def chores_create(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    name: str = Form(...),
    description: str = Form(""),
    every_n_days: int = Form(7),
    assigned_to_user_id: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    assigned = int(assigned_to_user_id) if assigned_to_user_id else None
    crud.create_chore(
        db,
        household_id=user.household_id,
        name=name,
        description=description or None,
        every_n_days=every_n_days,
        assigned_to_user_id=assigned,
    )
    request.session["flash"] = {"type": "success", "message": "Chore created."}
    return RedirectResponse("/chores", status_code=302)


@router.post("/{chore_id}/complete", include_in_schema=False)
def chores_complete(
    request: Request,
    chore_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    crud.complete_chore(db, chore_id=chore_id, completed_by_user_id=user.id, completed_on=datetime.utcnow().date())
    request.session["flash"] = {"type": "success", "message": "Marked as done."}
    return RedirectResponse("/chores", status_code=302)


@router.post("/{chore_id}/delete", include_in_schema=False)
def chores_delete(
    request: Request,
    chore_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    crud.delete_chore(db, user.household_id, chore_id)
    request.session["flash"] = {"type": "success", "message": "Chore deleted."}
    return RedirectResponse("/chores", status_code=302)
