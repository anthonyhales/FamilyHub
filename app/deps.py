from __future__ import annotations

from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session

from .core.config import settings
from .core.db import get_db
from . import crud, models
from .core.security import new_token


def get_current_session_token(request: Request) -> str | None:
    return request.cookies.get(settings.session_cookie)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> models.User:
    token = get_current_session_token(request)
    if not token:
        raise HTTPException(status_code=401)
    sess = crud.get_session_by_token(db, token)
    if not sess:
        raise HTTPException(status_code=401)
    user = crud.get_user(db, sess.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401)
    request.state.session = sess
    request.state.user = user
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if not user.is_admin:
        raise HTTPException(status_code=403)
    return user


def get_or_set_csrf(request: Request) -> str:
    csrf = request.cookies.get(settings.csrf_cookie)
    if not csrf:
        csrf = new_token(16)
        request.state.set_csrf = csrf
    return csrf


def validate_csrf(request: Request, form_csrf: str | None) -> None:
    cookie_csrf = request.cookies.get(settings.csrf_cookie)
    if not cookie_csrf or not form_csrf or cookie_csrf != form_csrf:
        raise HTTPException(status_code=400, detail="Bad CSRF token")
