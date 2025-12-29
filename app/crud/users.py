from sqlalchemy.orm import Session
from app import models
from app.core.security import hash_password, verify_password


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def list_users(db: Session, household_id: int):
    return (
        db.query(models.User)
        .filter(models.User.household_id == household_id)
        .order_by(models.User.display_name)
        .all()
    )


def create_user(
    db: Session,
    household_id: int,
    email: str,
    display_name: str,
    password: str,
    is_admin: bool = False,
):
    user = models.User(
        household_id=household_id,
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def set_user_password(db: Session, user: models.User, password: str):
    user.password_hash = hash_password(password)
    db.add(user)
    db.commit()


def set_user_admin(db: Session, user: models.User, is_admin: bool):
    user.is_admin = is_admin
    db.add(user)
    db.commit()


def set_user_active(db: Session, user: models.User, is_active: bool):
    user.is_active = is_active
    db.add(user)
    db.commit()
