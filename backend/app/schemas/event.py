"""
Pydantic v2 schemas for Event, Generation, and Agent Outputs.
"""
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.types import EventStatus, AgentName, AgentStatus


class EventCreate(BaseModel):
    theme: str = Field(min_length=3, max_length=255)
    domain: str = Field(min_length=2, max_length=100)
    duration_hours: int = Field(default=36, ge=12, le=72)
    audience_type: str = Field(default="college_students")
    expected_participants: int = Field(default=100, ge=10)
    location_type: str = Field(default="offline")
    location_detail: str | None = None
    special_requirements: str | None = None
    organization_id: uuid.UUID | None = None


class EventUpdate(BaseModel):
    name: str | None = None
    tagline: str | None = None
    theme: str | None = None
    domain: str | None = None
    duration_hours: int | None = None
    audience_type: str | None = None
    expected_participants: int | None = None
    location_type: str | None = None
    location_detail: str | None = None
    special_requirements: str | None = None
    status: str | None = None
    launch_score: int | None = None


class AgentOutputResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    agent_name: str
    status: str
    raw_output: dict | None = None
    generation_ms: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerationResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    theme: str
    domain: str
    duration_hours: int
    audience_type: str
    expected_participants: int
    location_type: str
    location_detail: str | None = None
    special_requirements: str | None = None
    name: str | None = None
    tagline: str | None = None
    status: str
    generation_id: uuid.UUID | None = None
    launch_score: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventDetailResponse(EventResponse):
    outputs: list[AgentOutputResponse] = []



class EventSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str | None = None
    theme: str
    domain: str
    duration_hours: int
    location_type: str
    status: str
    launch_score: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class StartGenerationRequest(BaseModel):
    event_id: uuid.UUID
