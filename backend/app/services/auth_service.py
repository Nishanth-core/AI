from typing import Optional

import bcrypt
from postgrest import APIError
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.email import send_password_reset_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.core.supabase_client import supabase
from app.core.otp import generate_otp


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def fetch_user_by_email(email: str) -> Optional[dict]:
    normalized_email = email.lower()
    try:
        result = supabase.table("users").select("*").eq("email", normalized_email).execute()
    except APIError:
        return None

    if not result.data:
        return None
    return result.data[0]


def fetch_user_by_id(user_id: str) -> Optional[dict]:
    try:
        result = supabase.table("users").select("*").eq("id", user_id).single().execute()
    except APIError:
        return None

    return result.data


def login_user(email: str, password: str) -> Optional[dict]:
    user = fetch_user_by_email(email)
    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    role = user.get("role", "user")
    access_token = create_access_token({"sub": user["id"], "email": user["email"], "role": role})
    refresh_token = create_refresh_token({"sub": user["id"], "email": user["email"], "role": role})
    refresh_expires = (datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)).isoformat()

    try:
        supabase.table("refresh_tokens").insert({
            "user_id": user["id"],
            "token": refresh_token,
            "expires_at": refresh_expires,
        }).execute()
    except APIError:
        return None

    return {
        "success": True,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def register_user(name: str, email: str, password: str) -> dict:
    """Register a user into Supabase, return result dict with token."""
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
    role = user.get("role", "user")
    token = create_access_token({"sub": user.get("id"), "email": user.get("email"), "role": role})

    return {
        "success": True,
        "user": {"id": user.get("id"), "name": user.get("name"), "email": user.get("email")},
        "access_token": token,
    }


def refresh_access_token(refresh_token: str) -> Optional[dict]:
    try:
        payload = verify_refresh_token(refresh_token)
    except ValueError:
        return None

    user_id = payload["sub"]
    email = payload["email"]

    try:
        token_record = (
            supabase.table("refresh_tokens")
            .select("*")
            .eq("token", refresh_token)
            .eq("revoked", False)
            .limit(1)
            .execute()
        )
    except APIError:
        return None

    if not token_record.data:
        return None

    record = token_record.data[0]
    expires_at = record.get("expires_at")
    if isinstance(expires_at, str):
        if expires_at.endswith("Z"):
            expires_at = expires_at.replace("Z", "+00:00")
        expires_dt = datetime.fromisoformat(expires_at)
    else:
        expires_dt = datetime.fromisoformat(str(expires_at))

    # Ensure both datetimes are naive for comparison
    now = datetime.utcnow()
    if expires_dt.tzinfo is not None:
        expires_dt = expires_dt.replace(tzinfo=None)

    if now > expires_dt:
        return None

    try:
        supabase.table("refresh_tokens").update({"revoked": True}).eq("id", record.get("id")).execute()
    except APIError:
        return None

    new_access_token = create_access_token({"sub": user_id, "email": email})
    new_refresh_token = create_refresh_token({"sub": user_id, "email": email})
    new_refresh_expires = (datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)).isoformat()

    try:
        supabase.table("refresh_tokens").insert({
            "user_id": user_id,
            "token": new_refresh_token,
            "expires_at": new_refresh_expires,
        }).execute()
    except APIError:
        return None

    return {
        "success": True,
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


def forgot_password(email: str) -> bool:
    """Generate and store an OTP for email if user exists. Prints OTP for development."""
    normalized_email = email.lower()
    try:
        user = supabase.table("users").select("*").eq("email", normalized_email).execute()
    except APIError:
        return False

    if not user.data:
        return False

    otp = generate_otp()
    expiry = (datetime.utcnow() + timedelta(minutes=10)).isoformat()

    try:
        supabase.table("password_reset_otps").insert({
            "email": normalized_email,
            "otp": otp,
            "expires_at": expiry,
            "verified": False,
        }).execute()
    except APIError:
        return False

    try:
        if settings.smtp_host:
            send_password_reset_email(normalized_email, otp)
        elif settings.environment == "development":
            print(f"OTP for {normalized_email}: {otp}")
    except Exception:
        # keep the API response opaque; email failures should not reveal account state
        pass

    return True


def verify_otp(email: str, otp: str) -> bool:
    normalized_email = email.lower()
    try:
        result = (
            supabase.table("password_reset_otps").select("*").eq("email", normalized_email).eq("otp", otp).order("created_at", desc=True).limit(1).execute()
        )
    except APIError:
        return False

    if not result.data:
        return False

    record = result.data[0]
    expires_at = record.get("expires_at")
    if isinstance(expires_at, str):
        # handle Z suffix
        if expires_at.endswith("Z"):
            expires_at = expires_at.replace("Z", "+00:00")
        expires_dt = datetime.fromisoformat(expires_at)
    else:
        expires_dt = datetime.fromisoformat(str(expires_at))

    if datetime.utcnow() > expires_dt:
        return False

    # mark as verified
    try:
        supabase.table("password_reset_otps").update({"verified": True}).eq("id", record.get("id")).execute()
    except APIError:
        return False

    return True


def reset_password(email: str, otp: str, new_password: str) -> bool:
    normalized_email = email.lower()
    try:
        result = (
            supabase.table("password_reset_otps").select("*")
            .eq("email", normalized_email)
            .eq("otp", otp)
            .eq("verified", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except APIError:
        return False

    if not result.data:
        return False

    record = result.data[0]
    expires_at = record.get("expires_at")
    if isinstance(expires_at, str):
        if expires_at.endswith("Z"):
            expires_at = expires_at.replace("Z", "+00:00")
        expires_dt = datetime.fromisoformat(expires_at)
    else:
        expires_dt = datetime.fromisoformat(str(expires_at))

    if datetime.utcnow() > expires_dt:
        return False

    # update the user's password
    password_hash = hash_password(new_password)
    try:
        supabase.table("users").update({"password_hash": password_hash}).eq("email", normalized_email).execute()
    except APIError:
        return False

    return True
