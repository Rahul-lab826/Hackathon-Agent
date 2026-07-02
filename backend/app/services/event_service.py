"""
Event Service — coordinates event creation, retrieval, launch score calculation, and exports.
"""
import uuid
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventResponse, EventSummaryResponse
from app.services.mcp_service import MCPService


class EventService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.event_repo = EventRepository(db)
        self.mcp_service = MCPService()

    async def create_event(self, user_id: uuid.UUID, payload: EventCreate) -> Any:
        """Create a new event brief draft."""
        return await self.event_repo.create(
            user_id=user_id,
            theme=payload.theme,
            domain=payload.domain,
            duration_hours=payload.duration_hours,
            audience_type=payload.audience_type,
            expected_participants=payload.expected_participants,
            location_type=payload.location_type,
            location_detail=payload.location_detail,
            special_requirements=payload.special_requirements,
            organization_id=payload.organization_id,
        )

    async def get_event(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Any:
        """Retrieve single event details. Validates user owns the event."""
        event = await self.event_repo.get_by_id(event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
        if event.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return event

    async def list_events(self, user_id: uuid.UUID, page: int = 1, size: int = 20) -> tuple[list[Any], int]:
        """List events created by user with pagination."""
        skip = (page - 1) * size
        return await self.event_repo.list_by_user(user_id, skip=skip, limit=size)

    async def calculate_readiness_score(self, event_id: uuid.UUID) -> int:
        """
        Dynamically calculate Launch Readiness Score (0-100).
        Assigns weightages to agent completions:
        - Brand: 15%
        - Structure: 20%
        - Content: 20%
        - Marketing: 15%
        - Emails: 15%
        - Execution: 15%
        """
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            return 0

        score = 0
        weights = {
            "brand": 15,
            "structure": 20,
            "content": 20,
            "marketing": 15,
            "email": 15,
            "execution": 15
        }

        for output in event.outputs:
            if output.status == "done" and output.agent_name in weights:
                score += weights[output.agent_name]

        return score

    async def compile_export_package(self, event_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        """Assemble full event GTM outputs into one structured JSON package."""
        event = await self.get_event(event_id, user_id)
        
        outputs_map = {}
        for output in event.outputs:
            if output.status == "done":
                outputs_map[output.agent_name] = output.raw_output

        return {
            "event_id": str(event.id),
            "theme": event.theme,
            "domain": event.domain,
            "duration_hours": event.duration_hours,
            "audience": event.audience_type,
            "expected_participants": event.expected_participants,
            "location": event.location_type,
            "location_detail": event.location_detail,
            "status": event.status,
            "launch_readiness_score": event.launch_score,
            "gtm_package": outputs_map
        }

    async def trigger_mcp_action(self, event_id: uuid.UUID, user_id: uuid.UUID, action_type: str) -> dict[str, Any]:
        """Expose Google Workspace sync tools."""
        event = await self.get_event(event_id, user_id)
        
        # Build maps of outputs
        outputs_map = {o.agent_name: o.raw_output for o in event.outputs if o.status == "done"}

        if action_type == "calendar":
            structure = outputs_map.get("structure")
            if not structure or "timeline" not in structure:
                raise HTTPException(status_code=400, detail="Structure timeline must be generated first.")
            return await self.mcp_service.create_calendar_milestones(event.id, structure["timeline"])

        elif action_type == "docs":
            full_package = await self.compile_export_package(event.id, user_id)
            name = event.name or "Hackathon"
            return await self.mcp_service.export_to_google_docs(event.id, name, full_package)

        elif action_type == "gmail":
            emails = outputs_map.get("email")
            if not emails:
                raise HTTPException(status_code=400, detail="Emails must be generated first.")
            return await self.mcp_service.draft_emails_in_gmail(event.id, emails)

        else:
            raise HTTPException(status_code=400, detail="Invalid MCP action type.")
