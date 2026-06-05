import uuid
from typing import Optional

import bcrypt
from postgrest import APIError

from app.models.user import User
from app.core.supabase_client import supabase
from app.core.security import create_access_token


USER_STORE_BY_EMAIL: dict[str, User] = {}
USER_STORE_BY_ID: dict[str, User] = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_user_by_email(email: str) -> Optional[User]:
    return USER_STORE_BY_EMAIL.get(email.lower())


def get_user_by_id(user_id: str) -> Optional[User]:
    return USER_STORE_BY_ID.get(user_id)


def create_user(name: str, email: str, password: str) -> User:
    """In-memory user creation (kept for compatibility / tests)."""
    normalized_email = email.lower()
    if normalized_email in USER_STORE_BY_EMAIL:
        raise ValueError("Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=normalized_email,
        hashed_password=hash_password(password),
    )

    USER_STORE_BY_EMAIL[normalized_email] = user
    USER_STORE_BY_ID[user.id] = user
    return user


def authenticate_user(email: str, password: str) -> Optional[User]:
    user = get_user_by_email(email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def register_user(name: str, email: str, password: str) -> dict:
    """Register a user into Supabase, return result dict with token.

    Returns:
      {"success": True, "user": {...}, "access_token": "..."}
      or
      {"success": False, "error": "..."}
    """
    normalized_email = email.lower()

    try:
        existing = (
            supabase.table("users").select("*").eq("email", normalized_email).execute()
        )
    except APIError as exc:
        return {"success": False, "error": f"Supabase error: {exc}"}

    if existing.data:
        return {"success": False, "error": "Email already registered"}

    password_hash = hash_password(password)

    try:
        inserted = (
            supabase.table("users")
            .insert({"name": name, "email": normalized_email, "password_hash": password_hash})
            .execute()
        )
    except APIError as exc:
        return {"success": False, "error": f"Supabase insert error: {exc}"}

    if not inserted.data:
        return {"success": False, "error": "Failed to create user"}

    user = inserted.data[0]

    token = create_access_token({"sub": user.get("id"), "email": user.get("email")})

    return {
        "success": True,
        "user": {"id": user.get("id"), "name": user.get("name"), "email": user.get("email")},
        "access_token": token,
    }
