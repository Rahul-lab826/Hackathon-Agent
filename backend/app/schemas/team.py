"""Pydantic v2 schemas for Teams."""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.team import TeamMemberRole


class TeamCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=500)
    is_private: bool = False


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None
    is_private: bool | None = None


class TeamResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    avatar_url: str | None = None
    is_active: bool
    is_private: bool
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: TeamMemberRole
    created_at: datetime
    user_email: str | None = None
    user_name: str | None = None
    user_avatar: str | None = None

    model_config = {"from_attributes": True}


class AddTeamMemberRequest(BaseModel):
    user_id: uuid.UUID
    role: TeamMemberRole = TeamMemberRole.MEMBER


class UpdateTeamMemberRoleRequest(BaseModel):
    role: TeamMemberRole


class PaginatedTeams(BaseModel):
    items: list[TeamResponse]
    total: int
    page: int
    size: int
    pages: int
