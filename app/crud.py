from __future__ import annotations

from datetime import date, datetime, timedelta
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session

from . import models
from .core.security import hash_password, verify_password, new_token, expires_in, now_utc


# --- Households & users ----------------------------------------------------

def get_household_by_name(db: Session, name: str) -> models.Household | None:
    return db.scalar(select(models.Household).where(models.Household.name == name))


def create_household(db: Session, name: str) -> models.Household:
    hh = models.Household(name=name)
    db.add(hh)
    db.commit()
    db.refresh(hh)
    return hh


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.scalar(select(models.User).where(models.User.email == email.lower().strip()))


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.get(models.User, user_id)


def list_users(db: Session, household_id: int) -> list[models.User]:
    return list(db.scalars(select(models.User).where(models.User.household_id == household_id).order_by(models.User.display_name)))


def create_user(
    db: Session,
    *,
    household_id: int,
    email: str,
    display_name: str,
    password: str,
    is_admin: bool = False,
) -> models.User:
    user = models.User(
        household_id=household_id,
        email=email.lower().strip(),
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_user_password(db: Session, user: models.User, password: str) -> None:
    user.password_hash = hash_password(password)
    db.add(user)
    db.commit()


def set_user_active(db: Session, user: models.User, is_active: bool) -> None:
    user.is_active = is_active
    db.add(user)
    db.commit()


def set_user_admin(db: Session, user: models.User, is_admin: bool) -> None:
    user.is_admin = is_admin
    db.add(user)
    db.commit()


def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# --- Sessions --------------------------------------------------------------

def create_session(db: Session, user: models.User, ttl_minutes: int) -> models.Session:
    sess = models.Session(
        user_id=user.id,
        token=new_token(32),
        created_at=now_utc(),
        last_seen_at=now_utc(),
        expires_at=expires_in(ttl_minutes),
    )
    user.last_login_at = now_utc()
    db.add(sess)
    db.add(user)
    db.commit()
    db.refresh(sess)
    return sess


def get_session_by_token(db: Session, token: str) -> models.Session | None:
    sess = db.scalar(select(models.Session).where(models.Session.token == token))
    if not sess:
        return None
    if sess.expires_at < now_utc():
        # cleanup expired
        db.delete(sess)
        db.commit()
        return None
    sess.last_seen_at = now_utc()
    db.add(sess)
    db.commit()
    return sess


def delete_session(db: Session, token: str) -> None:
    db.execute(delete(models.Session).where(models.Session.token == token))
    db.commit()


def prune_sessions(db: Session) -> int:
    res = db.execute(delete(models.Session).where(models.Session.expires_at < now_utc()))
    db.commit()
    return res.rowcount or 0


# --- TOTP ------------------------------------------------------------------

def enable_totp(db: Session, user: models.User, secret: str) -> None:
    user.totp_secret = secret
    user.totp_enabled = True
    db.add(user)
    db.commit()


def disable_totp(db: Session, user: models.User) -> None:
    user.totp_secret = None
    user.totp_enabled = False
    db.add(user)
    db.commit()


# --- Calendar --------------------------------------------------------------

def list_upcoming_events(db: Session, household_id: int, start_from: datetime, limit: int = 50):
    return list(
        db.scalars(
            select(models.CalendarEvent)
            .where(models.CalendarEvent.household_id == household_id)
            .where(models.CalendarEvent.start_at >= start_from)
            .order_by(models.CalendarEvent.start_at)
            .limit(limit)
        )
    )


def create_event(
    db: Session,
    *,
    household_id: int,
    title: str,
    description: str | None,
    start_at: datetime,
    end_at: datetime | None,
    created_by_user_id: int,
) -> models.CalendarEvent:
    ev = models.CalendarEvent(
        household_id=household_id,
        title=title.strip(),
        description=(description.strip() if description else None),
        start_at=start_at,
        end_at=end_at,
        created_by_user_id=created_by_user_id,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def delete_event(db: Session, household_id: int, event_id: int) -> None:
    db.execute(delete(models.CalendarEvent).where(models.CalendarEvent.household_id == household_id, models.CalendarEvent.id == event_id))
    db.commit()


# --- Chores ----------------------------------------------------------------

def list_chores(db: Session, household_id: int):
    return list(
        db.scalars(
            select(models.Chore)
            .where(models.Chore.household_id == household_id)
            .where(models.Chore.is_active == True)  # noqa: E712
            .order_by(models.Chore.name)
        )
    )


def create_chore(
    db: Session,
    *,
    household_id: int,
    name: str,
    description: str | None,
    every_n_days: int,
    assigned_to_user_id: int | None,
) -> models.Chore:
    ch = models.Chore(
        household_id=household_id,
        name=name.strip(),
        description=(description.strip() if description else None),
        every_n_days=max(0, int(every_n_days)),
        assigned_to_user_id=assigned_to_user_id,
        is_active=True,
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def complete_chore(db: Session, *, chore_id: int, completed_by_user_id: int, completed_on: date):
    cc = models.ChoreCompletion(chore_id=chore_id, completed_by_user_id=completed_by_user_id, completed_on=completed_on)
    db.add(cc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # likely unique constraint - ignore
        return
    return cc


def last_completed_on(db: Session, chore_id: int) -> date | None:
    return db.scalar(select(func.max(models.ChoreCompletion.completed_on)).where(models.ChoreCompletion.chore_id == chore_id))


def delete_chore(db: Session, household_id: int, chore_id: int) -> None:
    db.execute(delete(models.Chore).where(models.Chore.household_id == household_id, models.Chore.id == chore_id))
    db.commit()


# --- Meal plan -------------------------------------------------------------

def list_meals_in_range(db: Session, household_id: int, start: date, end: date):
    return list(
        db.scalars(
            select(models.MealPlanEntry)
            .where(models.MealPlanEntry.household_id == household_id)
            .where(models.MealPlanEntry.meal_date >= start, models.MealPlanEntry.meal_date <= end)
            .order_by(models.MealPlanEntry.meal_date, models.MealPlanEntry.meal_slot)
        )
    )


def upsert_meal(
    db: Session,
    *,
    household_id: int,
    meal_date: date,
    meal_slot: str,
    title: str,
    notes: str | None,
    created_by_user_id: int,
) -> models.MealPlanEntry:
    meal_slot = meal_slot.lower().strip()
    existing = db.scalar(
        select(models.MealPlanEntry).where(
            models.MealPlanEntry.household_id == household_id,
            models.MealPlanEntry.meal_date == meal_date,
            models.MealPlanEntry.meal_slot == meal_slot,
        )
    )
    if existing:
        existing.title = title.strip()
        existing.notes = (notes.strip() if notes else None)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    ent = models.MealPlanEntry(
        household_id=household_id,
        meal_date=meal_date,
        meal_slot=meal_slot,
        title=title.strip(),
        notes=(notes.strip() if notes else None),
        created_by_user_id=created_by_user_id,
    )
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


def delete_meal(db: Session, household_id: int, entry_id: int) -> None:
    db.execute(delete(models.MealPlanEntry).where(models.MealPlanEntry.household_id == household_id, models.MealPlanEntry.id == entry_id))
    db.commit()
