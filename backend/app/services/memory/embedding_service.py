"""
Embedding Service — generates 768-dimensional text embeddings using the
modern Google GenAI SDK with the models/text-embedding-004 model.
Includes client-side fallback generation if API credentials are not set.
"""
import logging
from typing import Optional
from google import genai
from app.config import settings

logger = logging.getLogger("hacklaunch.memory.embedding")


class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = "text-embedding-004"
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("[EmbeddingService] Initialized Google GenAI SDK Client successfully.")
        else:
            self.client = None
            logger.warning("[EmbeddingService] GEMINI_API_KEY is not configured. Running in Mock/Fallback embedding mode.")

    async def get_embedding(self, text: str) -> list[float]:
        """
        Retrieves the 768-dimensional vector embedding for the given input text.
        """
        if not text.strip():
            return [0.0] * 768

        if not self.client:
            # Resilient fallback mock: generate a repeatable mock vector from string hashes
            return self._mock_embedding_vector(text)

        try:
            # run embed_content in executor for async safety
            import asyncio
            response = await asyncio.to_thread(
                self.client.models.embed_content,
                model=self.model_name,
                contents=text
            )
            
            if response and response.embeddings:
                return response.embeddings[0].values
            raise ValueError("No embeddings returned in response.")

        except Exception as e:
            logger.error(f"[EmbeddingService] Failed to retrieve embedding for text from API: {e}. Falling back to mock.")
            return self._mock_embedding_vector(text)

    def _mock_embedding_vector(self, text: str) -> list[float]:
        """Generates a stable, mock 768-dimensional float list from the text string."""
        import hashlib
        # compute multiple hashes to fill 768 slots
        vector = []
        for i in range(12): # 12 * 64 bytes (512 bits / 8 = 64 floats from sha512)
            hasher = hashlib.sha512(f"{text}_{i}".encode("utf-8"))
            digest = hasher.digest()
            for b in digest:
                vector.append(float(b) / 255.0 - 0.5) # normalise between -0.5 and 0.5
        # trim or pad to exactly 768
        vector = vector[:768]
        while len(vector) < 768:
            vector.append(0.0)
        return vector
