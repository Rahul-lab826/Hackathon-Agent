"""
Qdrant Client Service — connects to the Qdrant server and initializes collections.
Handles upserting vector points and handles offline fallbacks gracefully.
"""
import logging
from typing import Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from app.config import settings

logger = logging.getLogger("hacklaunch.memory.qdrant")


class QdrantClientService:
    def __init__(self) -> None:
        self.client = None
        self.enabled = False
        
        # Collection mappings
        self.collections = {
            "events": "hacklaunch_events",
            "conversations": "hacklaunch_conversations",
            "preferences": "hacklaunch_preferences",
            "feedback": "hacklaunch_feedback"
        }

        # Initialize Qdrant client connection
        try:
            qdrant_url = getattr(settings, "QDRANT_URL", "http://localhost:6333")
            qdrant_api_key = getattr(settings, "QDRANT_API_KEY", None)

            if qdrant_url:
                self.client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=3.0
                )
                self.enabled = True
                self._ensure_all_collections()
        except Exception as e:
            logger.warning(
                f"[QdrantClientService] Could not connect to Qdrant server: {e}. "
                f"Running in Mock Memory mode."
            )
            self.client = None
            self.enabled = False

    def _ensure_all_collections(self) -> None:
        """Create collections in Qdrant if they do not exist."""
        if not self.enabled or not self.client:
            return
        try:
            existing = [c.name for c in self.client.get_collections().collections]
            for key, name in self.collections.items():
                if name not in existing:
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=768,  # Gemini text-embedding-004 vector length
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"[QdrantClientService] Created collection '{name}' successfully.")
        except Exception as e:
            logger.error(f"[QdrantClientService] Failed to initialize collections: {e}")
            self.enabled = False

    def upsert_point(self, collection_key: str, point_id: str, vector: list[float], payload: dict[str, Any]) -> bool:
        """Upserts a single PointStruct to the requested Qdrant collection."""
        if not self.enabled or not self.client:
            return False

        collection_name = self.collections.get(collection_key)
        if not collection_name:
            logger.error(f"[QdrantClientService] Invalid collection key: '{collection_key}'")
            return False

        try:
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"[QdrantClientService] Upsert failed for collection '{collection_name}': {e}")
            return False

    def get_collection_name(self, key: str) -> Optional[str]:
        return self.collections.get(key)
