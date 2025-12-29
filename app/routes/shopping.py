from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.deps import get_current_user, get_or_set_csrf, validate_csrf
from app.core.activity import log_activity
from app import crud, models
from ._render import templates, ctx

router = APIRouter(tags=["shopping"])


# -------------------------
# Helpers
# -------------------------

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


# -------------------------
# Shopping home
# -------------------------

@router.get("/shopping", include_in_schema=False)
def shopping_home(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)

    shops = crud.list_shops(db, user.household_id)
    lists = crud.list_lists(db, user.household_id, include_archived=False)

    list_rows = []
    for lst in lists:
        list_rows.append(
            {
                "id": lst.id,
                "name": lst.name,
                "shop_id": lst.shop_id,
                "shop_name": lst.shop.name if lst.shop else "",
                "created_at": lst.created_at,
                "open_count": crud.count_open_items(db, lst.id),
            }
        )

    resp = templates.TemplateResponse(
        "shopping/index.html",
        ctx(request, csrf=csrf, shops=shops, lists=list_rows),
    )
    return _set_csrf_cookie_if_needed(request, resp)


# -------------------------
# Shops
# -------------------------

@router.post("/shopping/shop/create", include_in_schema=False)
def shopping_create_shop(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    name: str = Form(...),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    shop = crud.create_shop(db, user.household_id, name=name)

    log_activity(
        db,
        request=request,
        action="shopping.shop.created",
        entity_type="shopping_shop",
        entity_id=shop.id,
        details={"name": shop.name},
    )

    request.session["flash"] = {"type": "success", "message": "Shop added"}
    return RedirectResponse("/shopping", status_code=302)


# -------------------------
# Lists
# -------------------------

@router.post("/shopping/list/create", include_in_schema=False)
def shopping_create_list(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    shop_id: int = Form(...),
    name: str = Form(...),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    lst = crud.create_list(
        db,
        household_id=user.household_id,
        shop_id=shop_id,
        name=name,
    )

    log_activity(
        db,
        request=request,
        action="shopping.list.created",
        entity_type="shopping_list",
        entity_id=lst.id,
        details={"name": lst.name, "shop_id": lst.shop_id},
    )

    return RedirectResponse(f"/shopping/{lst.id}", status_code=302)


@router.get("/shopping/{list_id}", include_in_schema=False)
def shopping_list_page(
    request: Request,
    list_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    csrf = get_or_set_csrf(request)

    lst = crud.get_list(db, list_id)
    if not lst or lst.household_id != user.household_id:
        return RedirectResponse("/shopping", status_code=302)

    items = crud.list_items(db, list_id)
    categories = crud.list_categories(db, user.household_id)

    by_cat = {}
    for item in items:
        label = item.category.name if item.category else "Uncategorised"
        by_cat.setdefault(label, []).append(item)

    resp = templates.TemplateResponse(
        "shopping/list.html",
        ctx(
            request,
            csrf=csrf,
            lst=lst,
            items=items,
            categories=categories,
            by_cat=by_cat,
        ),
    )
    return _set_csrf_cookie_if_needed(request, resp)


# -------------------------
# Items
# -------------------------

@router.post("/shopping/{list_id}/item/add", include_in_schema=False)
def shopping_add_item(
    request: Request,
    list_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    name: str = Form(...),
    quantity: int = Form(1),
    category_id: str = Form(""),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    lst = crud.get_list(db, list_id)
    if not lst or lst.household_id != user.household_id:
        return RedirectResponse("/shopping", status_code=302)

    cat_id = int(category_id) if category_id.strip() else None

    item = crud.add_item(
        db,
        list_id=list_id,
        name=name,
        quantity=quantity,
        category_id=cat_id,
    )

    log_activity(
        db,
        request=request,
        action="shopping.item.added",
        entity_type="shopping_item",
        entity_id=item.id,
        details={"name": item.name, "qty": item.quantity},
    )

    return RedirectResponse(f"/shopping/{list_id}", status_code=302)


@router.post("/shopping/item/{item_id}/toggle", include_in_schema=False)
def shopping_toggle_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    item = crud.get_item(db, item_id)
    if not item:
        return RedirectResponse("/shopping", status_code=302)

    lst = crud.get_list(db, item.list_id)
    if not lst or lst.household_id != user.household_id:
        return RedirectResponse("/shopping", status_code=302)

    crud.toggle_item(db, item)

    log_activity(
        db,
        request=request,
        action="shopping.item.toggled",
        entity_type="shopping_item",
        entity_id=item.id,
        details={"checked": bool(item.is_checked)},
    )

    return RedirectResponse(f"/shopping/{item.list_id}", status_code=302)


@router.post("/shopping/item/{item_id}/delete", include_in_schema=False)
def shopping_delete_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    item = crud.get_item(db, item_id)
    if not item:
        return RedirectResponse("/shopping", status_code=302)

    lst = crud.get_list(db, item.list_id)
    if not lst or lst.household_id != user.household_id:
        return RedirectResponse("/shopping", status_code=302)

    list_id = item.list_id
    crud.delete_item(db, item)

    log_activity(
        db,
        request=request,
        action="shopping.item.deleted",
        entity_type="shopping_item",
        entity_id=item_id,
        details={"list_id": list_id},
    )

    return RedirectResponse(f"/shopping/{list_id}", status_code=302)


# -------------------------
# Archive list
# -------------------------

@router.post("/shopping/{list_id}/archive", include_in_schema=False)
def shopping_archive_list(
    request: Request,
    list_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    csrf: str = Form(...),
):
    validate_csrf(request, csrf)

    lst = crud.get_list(db, list_id)
    if not lst or lst.household_id != user.household_id:
        return RedirectResponse("/shopping", status_code=302)

    crud.archive_list(db, lst, archived=True)

    log_activity(
        db,
        request=request,
        action="shopping.list.archived",
        entity_type="shopping_list",
        entity_id=lst.id,
        details={"name": lst.name},
    )

    return RedirectResponse("/shopping", status_code=302)
