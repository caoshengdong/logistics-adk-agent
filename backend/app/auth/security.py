"""JWT token creation / verification and password hashing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend.app.config import backend_settings


def hash_password(plain: str) -> str:
    pwd = plain.encode("utf-8")[:72]  # bcrypt has a 72-byte limit
    return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd = plain.encode("utf-8")[:72]  # bcrypt has a 72-byte limit
    return bcrypt.checkpw(pwd, hashed.encode("utf-8"))


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=backend_settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, backend_settings.jwt_secret, algorithm=backend_settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Return payload dict or raise JWTError."""
    return jwt.decode(token, backend_settings.jwt_secret, algorithms=[backend_settings.jwt_algorithm])

