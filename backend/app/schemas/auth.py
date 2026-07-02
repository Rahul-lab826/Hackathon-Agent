"""
Pydantic v2 schemas for authentication request/response payloads.
These are the DTOs at the API boundary — never expose ORM models directly.
"""
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ─── Registration ──────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """Payload for POST /auth/register"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        errors = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


# ─── Login ─────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    """Payload for POST /auth/login"""
    email: EmailStr
    password: str = Field(min_length=1)


# ─── Token Responses ───────────────────────────────────────────────────────────
class TokenPair(BaseModel):
    """Returned after successful login or token refresh."""
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int             # Access token TTL in seconds
    user_id: uuid.UUID


class AccessTokenResponse(BaseModel):
    """Returned after refreshing an access token."""
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


# ─── Token Refresh ─────────────────────────────────────────────────────────────
class RefreshTokenRequest(BaseModel):
    """Payload for POST /auth/refresh"""
    refresh_token: str = Field(min_length=1)


# ─── Logout ────────────────────────────────────────────────────────────────────
class LogoutRequest(BaseModel):
    """Payload for POST /auth/logout — revokes the given refresh token."""
    refresh_token: str = Field(min_length=1)


# ─── Google OAuth ──────────────────────────────────────────────────────────────
class GoogleAuthURL(BaseModel):
    """Returned by GET /auth/google — the URL to redirect the user to."""
    auth_url: str


class GoogleCallbackRequest(BaseModel):
    """Internal schema for processing Google OAuth callback."""
    code: str
    state: str | None = None


class GoogleUserInfo(BaseModel):
    """Data extracted from Google's userinfo endpoint."""
    google_id: str = Field(alias="sub")
    email: str
    email_verified: bool
    name: str | None = None
    picture: str | None = None

    model_config = {"populate_by_name": True}


# ─── Message Responses ─────────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
    success: bool = True
