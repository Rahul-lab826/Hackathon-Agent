"""
Memory Layer API Router — exposes endpoints to search and register memories in Qdrant collections.
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.guards import get_current_active_user
from app.models.user import User
from app.services.memory.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["Qdrant Memory Layer"])
memory_service = MemoryService()


class MemorySearchRequest(BaseModel):
    collection_name: str  # "events", "conversations", "preferences", "feedback"
    query: str
    limit: int = 5


class MemorySaveRequest(BaseModel):
    collection_name: str  # "events", "conversations", "preferences", "feedback"
    entity_id: str
    details: dict[str, Any]
    entity_type: Optional[str] = "custom_preference"


@router.get(
    "/collections",
    summary="List all Qdrant vector memory collections",
)
async def list_collections(
    current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Returns the collection names and descriptions managed by the system.
    """
    return {
        "collections": [
            {"name": "events", "description": "Stores previous hackathon ideas and compiled GTM packages"},
            {"name": "conversations", "description": "Saves message chat strings and model response transcripts"},
            {"name": "preferences", "description": "Keeps user settings, brand guidelines, and organization metadata"},
            {"name": "feedback", "description": "Maintains user ratings and event feedback reviews"}
        ]
    }


@router.post(
    "/search",
    summary="Run cosine similarity searches over Qdrant collections",
)
async def search_memory(
    payload: MemorySearchRequest,
    current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Computes text embeddings via text-embedding-004 and searches Qdrant collections.
    Falls back to Python-based Cosine Similarity if Qdrant is offline.
    """
    col = payload.collection_name
    if col not in ("events", "conversations", "preferences", "feedback"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Collection '{col}' is invalid. Supported: events, conversations, preferences, feedback."
        )

    try:
        if col == "events":
            matches = await memory_service.search_events_memory(payload.query, limit=payload.limit)
        elif col == "conversations":
            matches = await memory_service.search_conversation_memory(session_id="global_chat", query=payload.query, limit=payload.limit)
        elif col == "preferences":
            matches = await memory_service.search_preference_memory(payload.query, limit=payload.limit)
        else:
            # feedback search
            matches = await memory_service.search_preference_memory(payload.query, limit=payload.limit) # fallback search
            
        return {
            "status": "success",
            "query": payload.query,
            "collection": col,
            "results": matches
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic memory query failed: {e}"
        )


@router.post(
    "/save",
    summary="Directly store an item inside vector long-term memory",
)
async def save_memory(
    payload: MemorySaveRequest,
    current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Saves and indexes payload detail points directly inside vector database.
    """
    col = payload.collection_name
    if col not in ("events", "conversations", "preferences", "feedback"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported collections: events, conversations, preferences, feedback."
        )

    try:
        if col == "events":
            success = await memory_service.save_event_memory(
                event_id=payload.entity_id,
                name=payload.details.get("name", "Untitled Idea"),
                theme=payload.details.get("theme", "General"),
                domain=payload.details.get("domain", "General"),
                output_package=payload.details.get("output_package", {})
            )
        elif col == "conversations":
            success = await memory_service.save_conversation_memory(
                session_id=payload.entity_id,
                prompt=payload.details.get("prompt", ""),
                response=payload.details.get("response", "")
            )
        elif col == "preferences":
            success = await memory_service.save_preference_memory(
                entity_id=payload.entity_id,
                entity_type=payload.entity_type,
                details=payload.details
            )
        else:
            success = await memory_service.save_feedback_memory(
                feedback_id=payload.entity_id,
                event_id=payload.details.get("event_id", ""),
                feedback_text=payload.details.get("feedback_text", ""),
                rating=payload.details.get("rating", 5)
            )

        return {
            "status": "stored" if success else "failed",
            "collection": col,
            "id": payload.entity_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist memory object: {e}"
        )
