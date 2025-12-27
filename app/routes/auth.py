from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db
from ..core.security import totp_generate_secret, totp_provisioning_uri, totp_verify
from ..deps import get_or_set_csrf, validate_csrf, get_current_user
from .. import crud, models
from ._render import templates, ctx

router = APIRouter(tags=["auth"])


def _set_csrf_cookie_if_needed(request: Request, resp):
    """
    If get_or_set_csrf() generated a new token, it's stored on request.state.set_csrf.
    We must write it to a cookie on the response (GET pages), otherwise POST will 400.
    """
    token = getattr(request.state, "set_csrf", None)
    if token:
        resp.set_cookie(
            settings.csrf_cookie,
            token,
            httponly=False,
            samesite="lax",
            secure=False,  # rely on TLS at reverse proxy
        )
    return resp


@router.get("/login", include_in_schema=False)
def login_page(request: Request):
    csrf = get_or_set_csrf(request)
    resp = templates.TemplateResponse("auth/login.html", ctx(request, csrf=csrf))
    return _set_csrf_cookie_if_needed(request, resp)


@router.post("/login", include_in_schema=False)
def login_post(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    user = crud.authenticate_user(db, email, password)
    if not user:
        request.session["flash"] = {"type": "danger", "message": "Invalid email or password."}
        return RedirectResponse("/login", status_code=302)

    # If TOTP enabled, require MFA step
    if user.totp_enabled and user.totp_secret:
        request.session["pending_user_id"] = user.id
        return RedirectResponse("/mfa", status_code=302)

    sess = crud.create_session(db, user, settings.session_ttl_minutes)
    resp = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie(
        settings.session_cookie,
        sess.token,
        httponly=True,
        samesite="lax",
        secure=False,  # rely on TLS at reverse proxy
        max_age=settings.session_ttl_minutes * 60,
    )

    # Keep this (harmless) in case a CSRF cookie is ever generated during this request.
    if getattr(request.state, "set_csrf", None):
        resp.set_cookie(
            settings.csrf_cookie,
            request.state.set_csrf,
            httponly=False,
            samesite="lax",
            secure=False,
        )
    return resp


@router.get("/mfa", include_in_schema=False)
def mfa_page(request: Request):
    csrf = get_or_set_csrf(request)
    if not request.session.get("pending_user_id"):
        return RedirectResponse("/login", status_code=302)
    resp = templates.TemplateResponse("auth/mfa.html", ctx(request, csrf=csrf))
    return _set_csrf_cookie_if_needed(request, resp)


@router.post("/mfa", include_in_schema=False)
def mfa_post(
    request: Request,
    db: Session = Depends(get_db),
    code: str = Form(...),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    user = crud.get_user(db, int(user_id))
    if not user or not user.totp_enabled or not user.totp_secret:
        request.session.pop("pending_user_id", None)
        return RedirectResponse("/login", status_code=302)

    if not totp_verify(code, user.totp_secret):
        request.session["flash"] = {"type": "danger", "message": "Invalid code. Try again."}
        return RedirectResponse("/mfa", status_code=302)

    request.session.pop("pending_user_id", None)
    sess = crud.create_session(db, user, settings.session_ttl_minutes)
    resp = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie(
        settings.session_cookie,
        sess.token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.session_ttl_minutes * 60,
    )
    if getattr(request.state, "set_csrf", None):
        resp.set_cookie(settings.csrf_cookie, request.state.set_csrf, httponly=False, samesite="lax", secure=False)
    return resp


@router.post("/logout", include_in_schema=False)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    token = request.cookies.get(settings.session_cookie)
    if token:
        crud.delete_session(db, token)
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(settings.session_cookie)
    return resp


@router.get("/account", include_in_schema=False)
def account_page(
    request: Request,
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)
    resp = templates.TemplateResponse("auth/account.html", ctx(request, csrf=csrf, totp_uri=None))
    return _set_csrf_cookie_if_needed(request, resp)


@router.post("/account/totp/start", include_in_schema=False)
def totp_start(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    secret = totp_generate_secret()
    request.session["totp_secret_pending"] = secret
    return RedirectResponse("/account/totp/verify", status_code=302)


@router.get("/account/totp/verify", include_in_schema=False)
def totp_verify_page(
    request: Request,
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)
    secret = request.session.get("totp_secret_pending")
    totp_uri = totp_provisioning_uri(user.email, secret, issuer=settings.app_name) if secret else None
    resp = templates.TemplateResponse("auth/totp_verify.html", ctx(request, csrf=csrf, totp_uri=totp_uri))
    return _set_csrf_cookie_if_needed(request, resp)


@router.post("/account/totp/verify", include_in_schema=False)
def totp_verify_post(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    code: str = Form(...),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    secret = request.session.get("totp_secret_pending")
    if not secret:
        return RedirectResponse("/account", status_code=302)

    if not totp_verify(code, secret):
        request.session["flash"] = {"type": "danger", "message": "That code didn't match. Please try again."}
        return RedirectResponse("/account/totp/verify", status_code=302)

    crud.enable_totp(db, user, secret)
    request.session.pop("totp_secret_pending", None)
    request.session["flash"] = {"type": "success", "message": "Two-factor authentication enabled."}
    return RedirectResponse("/account", status_code=302)


@router.post("/account/totp/disable", include_in_schema=False)
def totp_disable(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)
    crud.disable_totp(db, user)
    request.session["flash"] = {"type": "success", "message": "Two-factor authentication disabled."}
    return RedirectResponse("/account", status_code=302)
