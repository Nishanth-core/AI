from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    TokenResponse,
    UserProfile,
)
from app.services.auth_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    result = register_user(payload.name, payload.email, payload.password)
    if not result.get("success"):
        # treat existing email as conflict
        if "Email" in (result.get("error") or ""):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result.get("error"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    return result


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest):
    try:
        token_payload = verify_refresh_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        {"sub": token_payload["sub"], "email": token_payload["email"]}
    )
    refresh_token = create_refresh_token(
        {"sub": token_payload["sub"], "email": token_payload["email"]}
    )
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserProfile)
def me(current_user=Depends(get_current_user)):
    return current_user
