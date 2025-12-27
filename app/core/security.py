import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def expires_in(minutes: int) -> datetime:
    return now_utc() + timedelta(minutes=minutes)


def totp_generate_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(email: str, secret: str, issuer: str = "FamilyHub") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def totp_verify(code: str, secret: str) -> bool:
    # Allow small clock drift (1 step)
    return pyotp.TOTP(secret).verify(code.replace(" ", ""), valid_window=1)
