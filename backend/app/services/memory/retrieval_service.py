"""
Retrieval Service — implements the Retrieval-Augmented Generation (RAG) context compiler.
Fetches relevant historical memories, preferences, and conversations to inject before model prompts.
"""
import logging
from typing import Optional
from app.services.memory.memory_service import MemoryService

logger = logging.getLogger("hacklaunch.memory.retrieval")


class RetrievalService:
    def __init__(self, memory_service: MemoryService) -> None:
        self.memory = memory_service
        logger.info("[RetrievalService] Initialized RAG compiler successfully.")

    async def retrieve_context(self, query: str, session_id: Optional[str] = None) -> str:
        """
        Queries vector collections for past events, user preferences, and conversation memory,
        and returns a compiled markdown string representing the retrieved knowledge context.
        """
        logger.info(f"[RetrievalService] Retrieving memory context for query: '{query}'...")
        
        # 1. Search past similar events
        past_events = await self.memory.search_events_memory(query, limit=2)
        
        # 2. Search brand preferences
        preferences = await self.memory.search_preference_memory(query, limit=1)
        
        # 3. Search conversation history (if session is available)
        conversations = []
        if session_id:
            conversations = await self.memory.search_conversation_memory(session_id, query, limit=2)

        # Assemble markdown context
        context_parts = ["### Retrieved Context & Historical Memories"]

        if past_events:
            context_parts.append("\nSimilar Past Events:")
            for idx, event in enumerate(past_events):
                pkg = event.get("output_package", {})
                planner = pkg.get("planner", {})
                context_parts.append(
                    f" {idx+1}. Name: {event.get('name')} | Theme: {event.get('theme')} | Domain: {event.get('domain')}\n"
                    f"    Tagline: {planner.get('tagline', '')}\n"
                    f"    Description: {planner.get('description', '')}"
                )
        else:
            context_parts.append("\nNo relevant past events found in memory.")

        if preferences:
            context_parts.append("\nUser Preferences & Brand Memories:")
            for pref in preferences:
                context_parts.append(
                    f" - Type: {pref.get('entity_type')} | Details: {str(pref.get('details'))}"
                )

        if conversations:
            context_parts.append("\nRelevant Conversation Thread History:")
            for conv in conversations:
                context_parts.append(
                    f" - User: {conv.get('prompt')}\n"
                    f" - Agent: {conv.get('response')}"
                )

        context_str = "\n".join(context_parts)
        logger.info(f"[RetrievalService] RAG context built successfully ({len(context_str)} characters).")
        return context_str
