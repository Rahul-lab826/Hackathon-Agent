"""
Generation API Routes — start pipeline & stream SSE updates.

POST /generation/start          → kick off background pipeline
GET  /generation/{gen_id}/stream → SSE stream of agent progress
GET  /generation/{gen_id}       → current generation status
"""
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db, async_session_factory
from app.models.user import User
from app.schemas.event import StartGenerationRequest
from app.repositories.event_repository import EventRepository
from app.agents.pipeline import PipelineOrchestrator

router = APIRouter(prefix="/generation", tags=["Generation"])


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start the 6-agent GTM generation pipeline",
)
async def start_generation(
    payload: StartGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Kicks off the multi-agent pipeline as a background task.
    Returns the generation_id immediately for SSE stream subscription.
    """
    event_repo = EventRepository(db)
    event = await event_repo.get_by_id(payload.event_id)

    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    if event.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if event.status in ("generating", "complete"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event is already in '{event.status}' state. Cannot restart.",
        )

    # Create a generation record
    generation = await event_repo.create_generation(
        event_id=payload.event_id,
        user_id=current_user.id,
    )
    await db.commit()

    generation_id = generation.id
    event_id = payload.event_id
    user_id = current_user.id

    # Run pipeline in background using a fresh DB session
    async def _run_pipeline_bg():
        async with async_session_factory() as bg_db:
            orchestrator = PipelineOrchestrator(bg_db)
            # Consume the entire async generator to run the pipeline to completion
            async for _ in orchestrator.run_stream(event_id, generation_id, user_id):
                pass  # SSE events are persisted; the stream here is for background completion

    background_tasks.add_task(_run_pipeline_bg)

    return {
        "generation_id": str(generation_id),
        "event_id": str(event_id),
        "message": "Pipeline started. Subscribe to the SSE stream for live updates.",
        "stream_url": f"/api/v1/generation/{generation_id}/stream",
    }


@router.get(
    "/{generation_id}/stream",
    summary="Subscribe to live SSE stream of agent pipeline progress",
)
async def stream_generation(
    generation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Server-Sent Events endpoint. Clients connect here to receive live agent progress.
    The pipeline runs in a separate session; this endpoint re-runs the orchestrator
    for the live-streaming experience on first connection.
    
    If the pipeline is already complete, it returns a single 'pipeline_complete' event.
    """
    event_repo = EventRepository(db)
    gen = await event_repo.get_generation(generation_id)

    if gen is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found.")
    if gen.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # If already complete, return just the final event immediately
    if gen.status == "complete":
        event = await event_repo.get_by_id(gen.event_id)

        async def already_done():
            import json
            payload = json.dumps({
                "score": event.launch_score or 0,
                "event_id": str(gen.event_id),
                "status": "complete"
            })
            yield f"event: pipeline_complete\ndata: {payload}\n\n"

        return StreamingResponse(
            already_done(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    # Live stream: orchestrate in a new DB session
    async def _live_stream():
        async with async_session_factory() as stream_db:
            orchestrator = PipelineOrchestrator(stream_db)
            async for sse_chunk in orchestrator.run_stream(gen.event_id, generation_id, gen.user_id):
                if await request.is_disconnected():
                    break
                yield sse_chunk
                await asyncio.sleep(0)  # Yield control to event loop

    return StreamingResponse(
        _live_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/{generation_id}",
    summary="Get generation status",
)
async def get_generation_status(
    generation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    event_repo = EventRepository(db)
    gen = await event_repo.get_generation(generation_id)

    if gen is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found.")
    if gen.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return {
        "generation_id": str(gen.id),
        "event_id": str(gen.event_id),
        "status": gen.status,
        "started_at": gen.started_at.isoformat() if gen.started_at else None,
        "completed_at": gen.completed_at.isoformat() if gen.completed_at else None,
        "error_message": gen.error_message,
    }
