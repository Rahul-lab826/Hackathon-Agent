"""Pydantic v2 schemas for Organizations."""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from app.models.organization import OrgMemberRole, OrgPlan


# ─── Organization ──────────────────────────────────────────────────────────────
class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=1000)
    website: str | None = None
    industry: str | None = None
    location: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    logo_url: str | None = None
    website: str | None = None
    industry: str | None = None
    size: str | None = None
    location: str | None = None


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    industry: str | None = None
    size: str | None = None
    location: str | None = None
    plan: OrgPlan
    is_active: bool
    max_members: int
    max_events: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Organization Member ───────────────────────────────────────────────────────
class OrgMemberResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgMemberRole
    accepted_at: datetime | None = None
    created_at: datetime
    # Nested user info
    user_email: str | None = None
    user_name: str | None = None
    user_avatar: str | None = None

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: OrgMemberRole = OrgMemberRole.MEMBER


class UpdateMemberRoleRequest(BaseModel):
    role: OrgMemberRole


class PaginatedOrganizations(BaseModel):
    items: list[OrganizationResponse]
    total: int
    page: int
    size: int
    pages: int
