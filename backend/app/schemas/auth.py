from typing import Optional

from pydantic import BaseModel, EmailStr, constr


class RegisterRequest(BaseModel):
    name: constr(min_length=2, max_length=100)
    email: EmailStr
    password: constr(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: str
    name: str
    email: EmailStr


class TokenResponse(BaseModel):
    success: bool
    user: Optional[UserProfile] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: constr(min_length=8)
