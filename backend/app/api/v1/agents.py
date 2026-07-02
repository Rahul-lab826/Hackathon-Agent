"""
Agents API Routes — retrieve individual agent outputs for a specific event.

GET /agents/{event_id}/brand
GET /agents/{event_id}/structure
GET /agents/{event_id}/{agent_name}
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.repositories.event_repository import EventRepository

VALID_AGENTS = {"brand", "structure", "content", "marketing", "email", "execution"}

router = APIRouter(prefix="/agents", tags=["Agent Outputs"])


@router.get(
    "/{event_id}/{agent_name}",
    summary="Retrieve a specific agent's output for an event",
)
async def get_agent_output(
    event_id: uuid.UUID,
    agent_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if agent_name not in VALID_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent name. Must be one of: {', '.join(VALID_AGENTS)}",
        )

    repo = EventRepository(db)

    # Verify event ownership
    event = await repo.get_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    if event.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    output = await repo.get_agent_output(event_id, agent_name)
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' has not run yet for this event.",
        )

    return {
        "event_id": str(event_id),
        "agent_name": output.agent_name,
        "status": output.status,
        "raw_output": output.raw_output,
        "generation_ms": output.generation_ms,
        "error_message": output.error_message,
        "created_at": output.created_at.isoformat(),
        "updated_at": output.updated_at.isoformat(),
    }


@router.get(
    "/{event_id}",
    summary="List all agent outputs for an event",
)
async def list_agent_outputs(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)

    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    if event.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return {
        "event_id": str(event_id),
        "agents": [
            {
                "agent_name": o.agent_name,
                "status": o.status,
                "generation_ms": o.generation_ms,
                "has_output": o.raw_output is not None,
                "error": o.error_message,
            }
            for o in event.outputs
        ],
    }
