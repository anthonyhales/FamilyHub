from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.deps import require_admin, get_or_set_csrf, validate_csrf
from app.core.activity import log_activity
from app.routes._render import templates, ctx
from app.crud.shopping_categories import list_categories, create_category

router = APIRouter(prefix="/admin/categories", tags=["admin"])


def _set_csrf_cookie_if_needed(request: Request, resp):
    token = getattr(request.state, "set_csrf", None)
    if token:
        resp.set_cookie(
            settings.csrf_cookie,
            token,
            httponly=False,
            samesite="lax",
            secure=False,
        )
    return resp


@router.get("", include_in_schema=False)
def categories_page(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    csrf = get_or_set_csrf(request)
    categories = list_categories(db, admin.household_id)
    resp = templates.TemplateResponse(
        "admin/categories.html",
        ctx(request, csrf=csrf, categories=categories),
    )
    return _set_csrf_cookie_if_needed(request, resp)


@router.post("/create", include_in_schema=False)
def categories_create(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
    name: str = Form(...),
    color: str = Form(""),
    icon: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    cat_id = create_category(
        db,
        admin.household_id,
        name=name.strip(),
        color=(color or None),
        icon=(icon or None),
    )

    log_activity(
        db,
        request=request,
        action="shopping.category.created",
        entity_type="shopping_category",
        entity_id=cat_id,
        details={"name": name.strip()},
    )

    request.session["flash"] = {"type": "success", "message": "Category added."}
    return RedirectResponse("/admin/categories", status_code=302)
