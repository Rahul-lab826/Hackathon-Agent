"""
Search Service — implements semantic vector queries using Qdrant client.
Includes a fully functional in-memory Cosine Similarity fallback database
so that semantic search works locally without running a Qdrant server.
"""
import math
import logging
from typing import Any, Optional
from app.services.memory.qdrant_client_service import QdrantClientService

logger = logging.getLogger("hacklaunch.memory.search")


def calculate_cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes the Cosine Similarity metric between two numeric vector lists."""
    if len(v1) != len(v2):
        return 0.0
    dot_prod = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_prod / (norm_a * norm_b)


class SearchService:
    def __init__(self, qdrant_service: QdrantClientService) -> None:
        self.qdrant = qdrant_service
        
        # Local in-memory mock database cache
        self._mock_db: dict[str, list[dict[str, Any]]] = {
            "events": [],
            "conversations": [],
            "preferences": [],
            "feedback": []
        }

    def register_in_mock_db(self, collection_key: str, point_id: str, vector: list[float], payload: dict[str, Any]):
        """Caches a point locally to enable local in-memory cosine similarity search."""
        if collection_key in self._mock_db:
            # Check and replace if same ID
            self._mock_db[collection_key] = [
                item for item in self._mock_db[collection_key] if item["id"] != point_id
            ]
            self._mock_db[collection_key].append({
                "id": point_id,
                "vector": vector,
                "payload": payload
            })

    async def search_similar(
        self,
        collection_key: str,
        query_vector: list[float],
        limit: int = 3
    ) -> list[dict[str, Any]]:
        """
        Searches the vector database for items matching the query vector.
        Uses Qdrant semantic search if active, falling back to local Python cosine similarity.
        """
        # 1. Attempt Qdrant search
        if self.qdrant.enabled and self.qdrant.client:
            collection_name = self.qdrant.get_collection_name(collection_key)
            if collection_name:
                try:
                    # Run search in thread executor to prevent blocking
                    import asyncio
                    hits = await asyncio.to_thread(
                        self.qdrant.client.search,
                        collection_name=collection_name,
                        query_vector=query_vector,
                        limit=limit
                    )
                    return [hit.payload for hit in hits if hit.payload]
                except Exception as e:
                    logger.warning(f"[SearchService] Qdrant search failed: {e}. Falling back to in-memory.")

        # 2. Fallback in-memory search using cosine similarity
        logger.info(f"[SearchService] Performing in-memory Cosine Similarity search on '{collection_key}'...")
        candidates = self._mock_db.get(collection_key, [])
        if not candidates:
            return []

        # Calculate similarities and sort
        scored = []
        for item in candidates:
            similarity = calculate_cosine_similarity(query_vector, item["vector"])
            scored.append((similarity, item["payload"]))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [payload for score, payload in scored[:limit]]
        logger.info(f"[SearchService] Found {len(results)} matches in-memory.")
        return results
