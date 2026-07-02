"""
Base Agent — abstract parent class for all GTM pipeline agents.
Built on top of GeminiService and QdrantService.
Provides core workflow: memory retrieval (few-shot), prompt compiling, and structured JSON generation.
"""
from typing import Any, Type
from pydantic import BaseModel

from app.services.gemini_service import GeminiService
from app.services.qdrant_service import QdrantService
from app.agents.context_builder import SharedContext


class BaseAgent:
    def __init__(self, gemini_service: GeminiService, qdrant_service: QdrantService) -> None:
        self.gemini = gemini_service
        self.qdrant = qdrant_service

    async def execute(self, context: SharedContext) -> dict[str, Any]:
        """
        Execute the agent pipeline:
        1. Query similar events from Qdrant vector memory for few-shot examples
        2. Construct system instruction + compile prompt template
        3. Call Gemini API structured JSON model
        """
        raise NotImplementedError("Agents must implement the execute method.")

    async def get_few_shot_examples(self, query_text: str) -> str:
        """Fetch similar historical event data to serve as few-shot context."""
        examples = await self.qdrant.search_similar_events(query_text, limit=2)
        if not examples:
            return "No historical examples found in memory. Generate from first principles."

        shot_texts = []
        for idx, ex in enumerate(examples):
            shot_texts.append(
                f"### Example {idx + 1}:\n"
                f"Theme: {ex.get('theme')}\n"
                f"Domain: {ex.get('domain')}\n"
                f"Audience: {ex.get('audience_type')}\n"
                f"Generated output structure: {ex.get('gtm_package', {})}\n"
            )
        return "\n\n".join(shot_texts)
