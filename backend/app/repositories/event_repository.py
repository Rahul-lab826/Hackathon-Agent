"""
Event Repository — database operations for Event, AgentOutput, and Generation models.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event, AgentOutput, Generation
from app.types import EventStatus, AgentStatus


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Event CRUD ─────────────────────────────────────────────────────────────

    async def create(
        self,
        user_id: uuid.UUID,
        theme: str,
        domain: str,
        duration_hours: int,
        audience_type: str,
        expected_participants: int,
        location_type: str,
        location_detail: str | None = None,
        special_requirements: str | None = None,
        organization_id: uuid.UUID | None = None,
    ) -> Event:
        event = Event(
            user_id=user_id,
            theme=theme,
            domain=domain,
            duration_hours=duration_hours,
            audience_type=audience_type,
            expected_participants=expected_participants,
            location_type=location_type,
            location_detail=location_detail,
            special_requirements=special_requirements,
            organization_id=organization_id,
            status=EventStatus.DRAFT.value,
        )
        self.db.add(event)
        await self.db.flush()
        
        # Refresh event and load the outputs relationship to prevent lazy-load MissingGreenlet error
        await self.db.refresh(event, ["outputs"])
        return event



    async def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        result = await self.db.execute(
            select(Event)
            .where(Event.id == event_id)
            .options(selectinload(Event.outputs))
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Event], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(Event).where(Event.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(Event)
            .where(Event.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Event.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def update(self, event_id: uuid.UUID, **kwargs) -> Event | None:
        await self.db.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(**kwargs, updated_at=datetime.now(timezone.utc))
        )
        return await self.get_by_id(event_id)

    async def delete(self, event_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(Event).where(Event.id == event_id)
        )
        return result.rowcount > 0

    # ─── Agent Output Management ────────────────────────────────────────────────

    async def get_agent_output(self, event_id: uuid.UUID, agent_name: str) -> AgentOutput | None:
        result = await self.db.execute(
            select(AgentOutput).where(
                AgentOutput.event_id == event_id,
                AgentOutput.agent_name == agent_name
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update_agent_output(
        self,
        event_id: uuid.UUID,
        agent_name: str,
        status: str,
        raw_output: dict | None = None,
        generation_ms: int | None = None,
        error_message: str | None = None,
    ) -> AgentOutput:
        existing = await self.get_agent_output(event_id, agent_name)
        if existing:
            existing.status = status
            if raw_output is not None:
                existing.raw_output = raw_output
            if generation_ms is not None:
                existing.generation_ms = generation_ms
            if error_message is not None:
                existing.error_message = error_message
            existing.updated_at = datetime.now(timezone.utc)
            self.db.add(existing)
            await self.db.flush()
            return existing
        else:
            new_output = AgentOutput(
                event_id=event_id,
                agent_name=agent_name,
                status=status,
                raw_output=raw_output,
                generation_ms=generation_ms,
                error_message=error_message,
            )
            self.db.add(new_output)
            await self.db.flush()
            return new_output

    # ─── Generation Tracking ───────────────────────────────────────────────────

    async def create_generation(self, event_id: uuid.UUID, user_id: uuid.UUID) -> Generation:
        gen = Generation(
            event_id=event_id,
            user_id=user_id,
            status=AgentStatus.PENDING.value,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(gen)
        await self.db.flush()
        await self.db.refresh(gen)
        return gen

    async def update_generation(self, generation_id: uuid.UUID, **kwargs) -> Generation | None:
        await self.db.execute(
            update(Generation)
            .where(Generation.id == generation_id)
            .values(**kwargs)
        )
        result = await self.db.execute(select(Generation).where(Generation.id == generation_id))
        return result.scalar_one_or_none()

    async def get_generation(self, generation_id: uuid.UUID) -> Generation | None:
        result = await self.db.execute(select(Generation).where(Generation.id == generation_id))
        return result.scalar_one_or_none()
