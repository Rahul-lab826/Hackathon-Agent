"""
Events API Routes — CRUD for hackathon event briefs.
"""
import math
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.event import (
    EventCreate, EventResponse, EventDetailResponse, EventSummaryResponse, EventUpdate
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new hackathon event brief",
)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EventResponse:
    service = EventService(db)
    event = await service.create_event(current_user.id, payload)
    return EventResponse.model_validate(event)


@router.get(
    "/",
    summary="List all my hackathon events",
)
async def list_events(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    service = EventService(db)
    events, total = await service.list_events(current_user.id, page=page, size=size)
    return {
        "items": [EventSummaryResponse.model_validate(e) for e in events],
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total > 0 else 0,
    }


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    summary="Get a specific event by ID",
)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EventDetailResponse:
    service = EventService(db)
    event = await service.get_event(event_id, current_user.id)
    return EventDetailResponse.model_validate(event)


@router.patch(
    "/{event_id}",
    response_model=EventDetailResponse,
    summary="Update event metadata",
)
async def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EventDetailResponse:
    service = EventService(db)
    # Verify ownership first
    await service.get_event(event_id, current_user.id)
    from app.repositories.event_repository import EventRepository
    repo = EventRepository(db)
    event = await repo.update(event_id, **payload.model_dump(exclude_none=True))
    return EventDetailResponse.model_validate(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a hackathon event",
)
async def delete_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    service = EventService(db)
    await service.get_event(event_id, current_user.id)
    from app.repositories.event_repository import EventRepository
    repo = EventRepository(db)
    await repo.delete(event_id)
