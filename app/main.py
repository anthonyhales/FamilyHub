from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from .core.config import settings
from .core.db import engine, SessionLocal
from .core.security import hash_password
from . import models, crud
from .routes import auth, dashboard, calendar, chores, mealplan, admin


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)


    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="fh_app_session",  # separate from our auth cookie
        same_site="lax",
        https_only=False,  # allow LAN use; rely on reverse proxy for TLS
    )

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(calendar.router)
    app.include_router(chores.router)
    app.include_router(mealplan.router)
    app.include_router(admin.router)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/dashboard", status_code=302)

    @app.on_event("startup")
    def _startup():
        models.Base.metadata.create_all(bind=engine)
        _ensure_bootstrap_admin()

    return app


def _ensure_bootstrap_admin():
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    db: Session = SessionLocal()
    try:
        # Ensure a default household exists
        hh = crud.get_household_by_name(db, "Family")
        if not hh:
            hh = crud.create_household(db, "Family")

        user = crud.get_user_by_email(db, settings.bootstrap_admin_email)
        if not user:
            crud.create_user(
                db,
                household_id=hh.id,
                email=settings.bootstrap_admin_email,
                display_name="Admin",
                password=settings.bootstrap_admin_password,
                is_admin=True,
            )
        else:
            # ensure admin + household
            user.household_id = hh.id
            user.is_admin = True
            user.password_hash = hash_password(settings.bootstrap_admin_password)
            user.is_active = True
            db.add(user)
            db.commit()
    finally:
        db.close()


app = create_app()
