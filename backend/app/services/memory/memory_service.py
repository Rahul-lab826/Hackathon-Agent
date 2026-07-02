"""
Memory Service — unified manager providing access to the Qdrant client,
embeddings generator, and semantic search collections.
Stores and queries Event Ideas, Generated Outputs, Conversations, Preferences, and Feedback.
"""
import uuid
import logging
from typing import Any, Optional
from app.services.memory.embedding_service import EmbeddingService
from app.services.memory.qdrant_client_service import QdrantClientService
from app.services.memory.search_service import SearchService

logger = logging.getLogger("hacklaunch.memory.service")


class MemoryService:
    def __init__(self) -> None:
        self.embedding = EmbeddingService()
        self.qdrant = QdrantClientService()
        self.search = SearchService(self.qdrant)
        logger.info("[MemoryService] Initialized unified Memory Layer successfully.")

    # ─── Event Memory ──────────────────────────────────────────────────────────
    async def save_event_memory(self, event_id: str, name: str, theme: str, domain: str, output_package: dict[str, Any]) -> bool:
        """
        Embeds and stores the event idea and its generated outputs in vector memory.
        """
        text_to_embed = (
            f"Event Name: {name}\n"
            f"Theme: {theme}\n"
            f"Domain: {domain}\n"
            f"Outputs: {list(output_package.keys())}"
        )
        vector = await self.embedding.get_embedding(text_to_embed)
        payload = {
            "event_id": event_id,
            "name": name,
            "theme": theme,
            "domain": domain,
            "output_package": output_package
        }
        
        # Save locally in mock db cache and to Qdrant
        self.search.register_in_mock_db("events", event_id, vector, payload)
        return self.qdrant.upsert_point("events", event_id, vector, payload)

    async def search_events_memory(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Searches similar previous events and event ideas."""
        vector = await self.embedding.get_embedding(query)
        return await self.search.search_similar("events", vector, limit=limit)

    # ─── Conversation Memory & Prompt History ──────────────────────────────────
    async def save_conversation_memory(self, session_id: str, prompt: str, response: str) -> bool:
        """
        Saves user prompts and model responses for prompt history & conversation context.
        """
        point_id = str(uuid.uuid4())
        text_to_embed = f"User Prompt: {prompt}\nAgent Response: {response}"
        vector = await self.embedding.get_embedding(text_to_embed)
        payload = {
            "session_id": session_id,
            "prompt": prompt,
            "response": response
        }
        self.search.register_in_mock_db("conversations", point_id, vector, payload)
        return self.qdrant.upsert_point("conversations", point_id, vector, payload)

    async def search_conversation_memory(self, session_id: str, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Searches conversation history for matching context."""
        vector = await self.embedding.get_embedding(query)
        results = await self.search.search_similar("conversations", vector, limit=10)
        # Filter results belonging to this session_id
        filtered = [item for item in results if item.get("session_id") == session_id]
        return filtered[:limit]

    # ─── User Preferences & Brand Memory & Org Details ────────────────────────
    async def save_preference_memory(self, entity_id: str, entity_type: str, details: dict[str, Any]) -> bool:
        """
        Saves user preferences, brand memory guidelines, or organization details.
        """
        text_to_embed = f"Entity Type: {entity_type}\nDetails: {str(details)}"
        vector = await self.embedding.get_embedding(text_to_embed)
        payload = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "details": details
        }
        self.search.register_in_mock_db("preferences", entity_id, vector, payload)
        return self.qdrant.upsert_point("preferences", entity_id, vector, payload)

    async def search_preference_memory(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Searches preference and brand memories."""
        vector = await self.embedding.get_embedding(query)
        return await self.search.search_similar("preferences", vector, limit=limit)

    # ─── User Feedback ─────────────────────────────────────────────────────────
    async def save_feedback_memory(self, feedback_id: str, event_id: str, feedback_text: str, rating: int) -> bool:
        """
        Embeds and saves user feedback ratings.
        """
        text_to_embed = f"Feedback rating: {rating}/5. Comment: {feedback_text}"
        vector = await self.embedding.get_embedding(text_to_embed)
        payload = {
            "feedback_id": feedback_id,
            "event_id": event_id,
            "feedback_text": feedback_text,
            "rating": rating
        }
        self.search.register_in_mock_db("feedback", feedback_id, vector, payload)
        return self.qdrant.upsert_point("feedback", feedback_id, vector, payload)

    async def search_feedback_memory(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Searches user feedback history."""
        vector = await self.embedding.get_embedding(query)
        return await self.search.search_similar("feedback", vector, limit=limit)
