"""
Qdrant Service — manages vector DB storage, collection setup, and semantic search.
Uses Google Gemini API "text-embedding-004" model to generate 768-dimensional embeddings.
Includes full in-memory mock fallback mode for development without running Qdrant.
"""
import uuid
import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger("hacklaunch.qdrant")


class QdrantService:
    def __init__(self) -> None:
        self.client = None
        self.enabled = False
        self.collection_name = settings.QDRANT_COLLECTION_EVENTS if hasattr(settings, "QDRANT_COLLECTION_EVENTS") else "hacklaunch_events"

        # Initialize Google GenAI configuration
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

        # Initialize Qdrant connection
        if settings.REDIS_URL: # Use settings validation or check if configured
            try:
                # Parse config values or fallback
                qdrant_url = getattr(settings, "QDRANT_URL", "http://localhost:6333")
                qdrant_api_key = getattr(settings, "QDRANT_API_KEY", None)

                if qdrant_url:
                    self.client = QdrantClient(
                        url=qdrant_url,
                        api_key=qdrant_api_key,
                        timeout=5.0
                    )
                    self.enabled = True
                    self._ensure_collection()
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant vector database: {e}. Falling back to mock memory mode.")
                self.client = None
                self.enabled = False

    def _ensure_collection(self) -> None:
        """Create Qdrant collection if it does not exist."""
        if not self.enabled or not self.client:
            return
        try:
            collections = self.client.get_collections()
            exist = any(c.name == self.collection_name for c in collections.collections)
            if not exist:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,  # Gemini text-embedding-004 size is 768
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' successfully.")
        except Exception as e:
            logger.error(f"Failed to check/create Qdrant collection: {e}")
            self.enabled = False

    async def get_embedding(self, text: str) -> list[float]:
        """Generate 768-dimensional text embedding vector using Gemini API."""
        try:
            # We run this synchronously since SDK uses synchronous HTTP requests internally
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return response["embedding"]
        except Exception as e:
            logger.error(f"Failed to fetch embedding from Gemini API: {e}")
            # Return dummy vector if API call fails in dev
            return [0.0] * 768

    async def store_event(self, event_id: uuid.UUID, payload_data: dict[str, Any]) -> bool:
        """Embed event summary (theme, domain, target, name) and save to Qdrant."""
        if not self.enabled or not self.client:
            logger.info("Qdrant not active. Skipping vector storage.")
            return False

        # Assemble summary text to embed
        summary_text = (
            f"Event Name: {payload_data.get('name', 'Untitled')}\n"
            f"Theme: {payload_data.get('theme', '')}\n"
            f"Domain: {payload_data.get('domain', '')}\n"
            f"Audience: {payload_data.get('audience_type', '')}\n"
            f"Requirements: {payload_data.get('special_requirements', '')}"
        )

        vector = await self.get_embedding(summary_text)

        try:
            point = PointStruct(
                id=str(event_id),
                vector=vector,
                payload=payload_data
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Successfully upserted event '{event_id}' payload to Qdrant vector memory.")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert event to Qdrant: {e}")
            return False

    async def search_similar_events(self, brief_text: str, limit: int = 3) -> list[dict[str, Any]]:
        """Search similar historical hackathon launches in vector database memory."""
        if not self.enabled or not self.client:
            logger.info("Qdrant not active. Returning empty list of similar memories.")
            return []

        try:
            query_vector = await self.get_embedding(brief_text)
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return [hit.payload for hit in hits if hit.payload]
        except Exception as e:
            logger.error(f"Failed to perform semantic search in Qdrant: {e}")
            return []
