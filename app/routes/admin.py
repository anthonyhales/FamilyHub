from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..deps import require_admin, get_or_set_csrf, validate_csrf
from .. import crud, models
from ._render import templates, ctx
from app.core.activity import log_activity


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", include_in_schema=False)
def users_page(
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    csrf = get_or_set_csrf(request)
    users = crud.list_users(db, admin.household_id)
    return templates.TemplateResponse("admin/users.html", ctx(request, csrf=csrf, users=users))


@router.post("/users/create", include_in_schema=False)
def create_user(
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
    is_admin: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    if crud.get_user_by_email(db, email):
        request.session["flash"] = {"type": "danger", "message": "That email is already in use."}
        return RedirectResponse("/admin/users", status_code=302)

    crud.create_user(
        db,
        household_id=admin.household_id,
        email=email,
        display_name=display_name,
        password=password,
        is_admin=bool(is_admin),
    )
    request.session["flash"] = {"type": "success", "message": "User created."}
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/password", include_in_schema=False)
def reset_password(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
    password: str = Form(...),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    user = crud.get_user(db, user_id)
    if not user or user.household_id != admin.household_id:
        return RedirectResponse("/admin/users", status_code=302)
    crud.set_user_password(db, user, password)
    request.session["flash"] = {"type": "success", "message": "Password updated."}
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/toggle_admin", include_in_schema=False)
def toggle_admin(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    user = crud.get_user(db, user_id)
    if not user or user.household_id != admin.household_id:
        return RedirectResponse("/admin/users", status_code=302)
    if user.id == admin.id:
        request.session["flash"] = {"type": "warning", "message": "You can't remove your own admin access."}
        return RedirectResponse("/admin/users", status_code=302)
    crud.set_user_admin(db, user, not user.is_admin)
    request.session["flash"] = {"type": "success", "message": "Role updated."}
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/toggle_active", include_in_schema=False)
def toggle_active(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    user = crud.get_user(db, user_id)
    if not user or user.household_id != admin.household_id:
        return RedirectResponse("/admin/users", status_code=302)
    if user.id == admin.id:
        request.session["flash"] = {"type": "warning", "message": "You can't disable your own account."}
        return RedirectResponse("/admin/users", status_code=302)
    crud.set_user_active(db, user, not user.is_active)
    request.session["flash"] = {"type": "success", "message": "User status updated."}
    return RedirectResponse("/admin/users", status_code=302)
