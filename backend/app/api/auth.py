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
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    login_user,
    register_user,
    forgot_password,
    verify_otp,
    reset_password,
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
    result = login_user(payload.email, payload.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


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


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return {"user": current_user}


@router.post("/forgot-password")
def forgot_password_api(payload: ForgotPasswordRequest):
    # best-effort: do not reveal whether account exists
    forgot_password(payload.email)
    return {"message": "OTP sent if account exists"}


@router.post("/verify-otp")
def verify_otp_api(payload: VerifyOTPRequest):
    valid = verify_otp(payload.email, payload.otp)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    return {"message": "OTP verified"}


@router.patch("/reset-password")
def reset_password_api(payload: ResetPasswordRequest):
    success = reset_password(payload.email, payload.otp, payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid request")
    return {"message": "Password updated"}
