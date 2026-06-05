from datetime import datetime, timedelta

import jwt
from jwt import PyJWTError

from app.core.config import settings


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.algorithm)


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise ValueError("Invalid access token")
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            raise ValueError("Invalid token payload")
        return {"sub": user_id, "email": email}
    except PyJWTError as exc:
        raise ValueError("Invalid token") from exc


def verify_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            raise ValueError("Invalid token payload")
        return {"sub": user_id, "email": email}
    except PyJWTError as exc:
        raise ValueError("Invalid token") from exc


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.algorithm])
        return payload
    except PyJWTError:
        return None
