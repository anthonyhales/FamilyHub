from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..deps import require_admin, get_or_set_csrf, validate_csrf
from ..routes._render import templates, ctx
from ..crud import shopping_categories
from ..core.activity import log_activity

router = APIRouter(prefix="/admin/categories", tags=["admin"])


@router.get("", include_in_schema=False)
def categories_page(
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    csrf = get_or_set_csrf(request)
    categories = shopping_categories.list_categories(db, admin.household_id)

    return templates.TemplateResponse(
        "admin/categories.html",
        ctx(request, csrf=csrf, categories=categories),
    )


@router.post("/create", include_in_schema=False)
def create_category(
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
    name: str = Form(...),
    color: str = Form(""),
    icon: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    shopping_categories.create_category(
        db,
        admin.household_id,
        name=name,
        color=color or None,
        icon=icon or None,
    )

    log_activity(
        db,
        request=request,
        action="shopping.category.created",
        entity_type="shopping_category",
        details={"name": name},
    )

    return RedirectResponse("/admin/categories", status_code=302)
