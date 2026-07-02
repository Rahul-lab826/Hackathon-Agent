"""
Pipeline Orchestrator — coordinates sequential A2A execution of all 6 GTM agents.

Flow:
  Brand → Structure → Content → Marketing → Email → Execution

Each agent's output is stored in SharedContext and fed forward to the next agent.
Emits Server-Sent Events (SSE) at each agent boundary for real-time progress streaming.

SSE Event Format:
  event: agent_start     data: {"agent": "brand",    "timestamp": "..."}
  event: agent_done      data: {"agent": "brand",    "output": {...}, "duration_ms": 1234}
  event: agent_error     data: {"agent": "brand",    "error": "..."}
  event: pipeline_complete data: {"score": 95, "event_id": "..."}
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.brand_agent import BrandAgent
from app.agents.content_agent import ContentAgent
from app.agents.email_agent import EmailAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.structure_agent import StructureAgent
from app.agents.context_builder import SharedContext
from app.repositories.event_repository import EventRepository
from app.services.gemini_service import GeminiService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger("hacklaunch.pipeline")


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


class PipelineOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.event_repo = EventRepository(db)
        self.gemini = GeminiService()
        self.qdrant = QdrantService()
        self._agents = [
            ("brand",     BrandAgent(self.gemini, self.qdrant)),
            ("structure", StructureAgent(self.gemini, self.qdrant)),
            ("content",   ContentAgent(self.gemini, self.qdrant)),
            ("marketing", MarketingAgent(self.gemini, self.qdrant)),
            ("email",     EmailAgent(self.gemini, self.qdrant)),
            ("execution", ExecutionAgent(self.gemini, self.qdrant)),
        ]

    async def run_stream(
        self, event_id: uuid.UUID, generation_id: uuid.UUID, user_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """
        Execute all 6 agents in sequence, yielding SSE strings at each step.
        On each agent completion, results are persisted to the database.
        """
        # Fetch event details
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            yield _sse_event("pipeline_error", {"error": "Event not found."})
            return

        # Mark generation as running
        await self.event_repo.update_generation(
            generation_id, status="running", started_at=datetime.now(timezone.utc)
        )
        await self.event_repo.update(event_id, status="generating")
        await self.db.commit()

        # Build initial SharedContext from event brief
        context = SharedContext(
            theme=event.theme,
            domain=event.domain,
            duration_hours=event.duration_hours,
            audience_type=event.audience_type,
            expected_participants=event.expected_participants,
            location_type=event.location_type,
            location_detail=event.location_detail,
            special_requirements=event.special_requirements,
        )

        # Give the frontend a brief moment to connect to the SSE stream
        await asyncio.sleep(0.3)

        error_occurred = False

        for agent_name, agent in self._agents:
            # Emit agent_start
            yield _sse_event("agent_start", {
                "agent": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Mark DB status as running
            await self.event_repo.create_or_update_agent_output(
                event_id=event_id,
                agent_name=agent_name,
                status="running"
            )
            await self.db.commit()

            start_time = time.monotonic()

            try:
                output = await agent.execute(context)
                duration_ms = int((time.monotonic() - start_time) * 1000)

                # Propagate output forward into the shared context (A2A)
                setattr(context, f"{agent_name}_output", output)

                # Persist agent output
                await self.event_repo.create_or_update_agent_output(
                    event_id=event_id,
                    agent_name=agent_name,
                    status="done",
                    raw_output=output,
                    generation_ms=duration_ms,
                )
                await self.db.commit()

                yield _sse_event("agent_done", {
                    "agent": agent_name,
                    "output": output,
                    "duration_ms": duration_ms
                })

                logger.info(f"[Pipeline] {agent_name} Agent completed in {duration_ms}ms.")

            except Exception as e:
                duration_ms = int((time.monotonic() - start_time) * 1000)
                error_msg = str(e)
                logger.error(f"[Pipeline] {agent_name} Agent FAILED: {error_msg}")

                await self.event_repo.create_or_update_agent_output(
                    event_id=event_id,
                    agent_name=agent_name,
                    status="error",
                    error_message=error_msg,
                    generation_ms=duration_ms,
                )
                await self.db.commit()

                yield _sse_event("agent_error", {
                    "agent": agent_name,
                    "error": error_msg
                })
                error_occurred = True
                # Continue pipeline despite individual agent failure for resilience

            # Small breathing room between agents
            await asyncio.sleep(0.1)

        # Calculate launch readiness score
        from app.services.event_service import EventService
        service = EventService(self.db)
        score = await service.calculate_readiness_score(event_id)

        # Update event name from brand output and mark complete
        brand_out = context.brand_output or {}
        final_status = "error" if error_occurred else "complete"
        
        await self.event_repo.update(
            event_id,
            status=final_status,
            name=brand_out.get("event_name"),
            tagline=brand_out.get("tagline"),
            launch_score=score,
            generation_id=generation_id,
        )
        await self.event_repo.update_generation(
            generation_id,
            status="complete" if not error_occurred else "error",
            completed_at=datetime.now(timezone.utc),
        )
        await self.db.commit()

        # Store event embedding in Qdrant for future few-shot memory
        await self.qdrant.store_event(
            event_id=event_id,
            payload_data={
                "id": str(event_id),
                "name": brand_out.get("event_name"),
                "theme": event.theme,
                "domain": event.domain,
                "audience_type": event.audience_type,
                "expected_participants": event.expected_participants,
                "location_type": event.location_type,
                "special_requirements": event.special_requirements,
                "tagline": brand_out.get("tagline"),
                "gtm_package": {
                    "brand": context.brand_output,
                    "structure": context.structure_output,
                }
            }
        )

        yield _sse_event("pipeline_complete", {
            "score": score,
            "event_id": str(event_id),
            "status": final_status
        })

        logger.info(f"[Pipeline] Full pipeline completed for event '{event_id}'. Score: {score}%. Status: {final_status}.")
