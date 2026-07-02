"""
Pydantic v2 schemas for User profiles.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from app.models.user import AuthProvider, UserPlan


# ─── Base ──────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    username: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")


# ─── Read / Response ───────────────────────────────────────────────────────────
class UserProfile(BaseModel):
    """Full user profile — returned from GET /users/me and GET /users/{id}."""
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    phone: str | None = None
    location: str | None = None
    website: str | None = None
    plan: UserPlan
    auth_provider: AuthProvider
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Minimal public user info — safe to expose to other users."""
    id: uuid.UUID
    full_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    """Compact user info for list views (e.g., org members)."""
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None
    plan: UserPlan

    model_config = {"from_attributes": True}


# ─── Update ────────────────────────────────────────────────────────────────────
class UpdateProfileRequest(BaseModel):
    """Payload for PATCH /users/me — all fields optional."""
    full_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    bio: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=1000)


class ChangePasswordRequest(BaseModel):
    """Payload for POST /users/me/change-password."""
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str

    def validate_passwords_match(self) -> None:
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")


# ─── Pagination ────────────────────────────────────────────────────────────────
class PaginatedUsers(BaseModel):
    items: list[UserSummary]
    total: int
    page: int
    size: int
    pages: int
