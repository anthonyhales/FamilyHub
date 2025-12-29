from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models


# ---- Shops ----

def list_shops(db: Session, household_id: int):
    return (
        db.query(models.ShoppingShop)
        .filter(models.ShoppingShop.household_id == household_id)
        .order_by(models.ShoppingShop.name.asc())
        .all()
    )


def create_shop(db: Session, household_id: int, name: str) -> models.ShoppingShop:
    shop = models.ShoppingShop(household_id=household_id, name=name.strip())
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


# ---- Lists ----

def list_lists(db: Session, household_id: int, include_archived: bool = False):
    q = (
        db.query(models.ShoppingList)
        .filter(models.ShoppingList.household_id == household_id)
    )
    if not include_archived:
        q = q.filter(models.ShoppingList.is_archived == False)  # noqa: E712
    return q.order_by(models.ShoppingList.created_at.desc()).all()


def get_list(db: Session, list_id: int) -> models.ShoppingList | None:
    return db.query(models.ShoppingList).filter(models.ShoppingList.id == list_id).first()


def create_list(
    db: Session,
    household_id: int,
    shop_id: int,
    name: str,
) -> models.ShoppingList:
    lst = models.ShoppingList(
        household_id=household_id,
        shop_id=shop_id,
        name=name.strip(),
        is_archived=False,
        created_at=datetime.utcnow(),
    )
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return lst


def archive_list(db: Session, lst: models.ShoppingList, archived: bool = True) -> None:
    lst.is_archived = bool(archived)
    db.add(lst)
    db.commit()


# ---- Items ----

def list_items(db: Session, list_id: int):
    return (
        db.query(models.ShoppingItem)
        .filter(models.ShoppingItem.list_id == list_id)
        .order_by(models.ShoppingItem.is_checked.asc(), models.ShoppingItem.created_at.desc())
        .all()
    )


def add_item(
    db: Session,
    list_id: int,
    name: str,
    quantity: int = 1,
    category_id: int | None = None,
) -> models.ShoppingItem:
    qty = int(quantity) if quantity and int(quantity) > 0 else 1
    item = models.ShoppingItem(
        list_id=list_id,
        name=name.strip(),
        quantity=qty,
        category_id=category_id,
        is_checked=False,
        created_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def toggle_item(db: Session, item: models.ShoppingItem) -> None:
    item.is_checked = not bool(item.is_checked)
    db.add(item)
    db.commit()


def delete_item(db: Session, item: models.ShoppingItem) -> None:
    db.delete(item)
    db.commit()


def get_item(db: Session, item_id: int) -> models.ShoppingItem | None:
    return db.query(models.ShoppingItem).filter(models.ShoppingItem.id == item_id).first()


def count_open_items(db: Session, list_id: int) -> int:
    return (
        db.query(func.count(models.ShoppingItem.id))
        .filter(models.ShoppingItem.list_id == list_id, models.ShoppingItem.is_checked == False)  # noqa: E712
        .scalar()
        or 0
    )
