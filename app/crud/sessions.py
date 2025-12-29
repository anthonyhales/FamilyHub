from datetime import datetime
from sqlalchemy.orm import Session

from app import models
from app.core.security import new_token, expires_in, now_utc


def create_session(db: Session, user: models.User, ttl_minutes: int):
    token = new_token()
    sess = models.Session(
        user_id=user.id,
        token=token,
        expires_at=expires_in(ttl_minutes),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def get_session_by_token(db: Session, token: str):
    if not token:
        return None

    sess = (
        db.query(models.Session)
        .filter(models.Session.token == token)
        .first()
    )

    if not sess:
        return None

    # Expired
    if sess.expires_at < now_utc():
        db.delete(sess)
        db.commit()
        return None

    return sess


def delete_session(db: Session, token: str):
    sess = (
        db.query(models.Session)
        .filter(models.Session.token == token)
        .first()
    )
    if sess:
        db.delete(sess)
        db.commit()
