"""
Gemini Service — interfaces with Google Gemini API models using the Google GenAI SDK.
Features client-side rate limiting, exponential backoff retries, token usage tracking,
and streaming & structured JSON generation validated by Pydantic models.
"""
import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Optional, Type
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings

logger = logging.getLogger("hacklaunch.gemini_service")


# ─── Client-Side Rate Limiter ────────────────────────────────────────────────
class AsyncRateLimiter:
    """
    Limits the number of requests sent to Gemini to stay within tier limits (e.g. 15 RPM).
    """
    def __init__(self, max_requests: int = 15, per_seconds: float = 60.0):
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.requests = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            # Clean old request timestamps outside the time window
            self.requests = [r for r in self.requests if now - r < self.per_seconds]
            if len(self.requests) >= self.max_requests:
                sleep_time = self.per_seconds - (now - self.requests[0])
                if sleep_time > 0:
                    logger.info(f"[RateLimiter] Limit reached. Sleeping for {sleep_time:.2f} seconds...")
                    await asyncio.sleep(sleep_time)
                # Refresh now
                now = time.monotonic()
                self.requests = [r for r in self.requests if now - r < self.per_seconds]
            self.requests.append(time.monotonic())


# ─── Token Usage Tracker ──────────────────────────────────────────────────────
class TokenTracker:
    """
    Tracks aggregate prompts and candidates token usage across all Gemini model calls.
    """
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_candidate_tokens = 0
        self.lock = asyncio.Lock()

    async def track(self, prompt_tokens: int, candidate_tokens: int):
        async with self.lock:
            self.total_prompt_tokens += prompt_tokens
            self.total_candidate_tokens += candidate_tokens
            logger.info(
                f"[TokenTracker] Usage in this call: prompt={prompt_tokens}, candidate={candidate_tokens}. "
                f"Aggregate: prompt={self.total_prompt_tokens}, candidate={self.total_candidate_tokens}."
            )

    async def get_metrics(self) -> dict[str, int]:
        async with self.lock:
            return {
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_candidate_tokens": self.total_candidate_tokens,
                "total_tokens": self.total_prompt_tokens + self.total_candidate_tokens
            }


# Global instances for rate limiting and token tracking
rate_limiter = AsyncRateLimiter(max_requests=15, per_seconds=60.0)
token_tracker = TokenTracker()


class GeminiService:
    def __init__(self) -> None:
        # Default models (Gemini 2.5 Pro for high-tier logic, Gemini 2.5 Flash for faster/structured runs)
        self.pro_model = "gemini-2.5-pro"
        self.flash_model = "gemini-2.5-flash"
        
        # Fallback models if 2.5 models are not fully deployed/authorized in the current API tier
        self.default_pro_fallback = "gemini-1.5-pro"
        self.default_flash_fallback = "gemini-2.0-flash"

        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("[GeminiService] Initialized Google GenAI SDK client successfully.")
        else:
            self.client = None
            logger.warning("[GeminiService] GEMINI_API_KEY is not configured. Running in Mock/Fallback mode.")
        
        # Lazy import memory layer to avoid circular dependencies
        try:
            from app.services.memory.memory_service import MemoryService
            from app.services.memory.retrieval_service import RetrievalService
            self.memory = MemoryService()
            self.retrieval = RetrievalService(self.memory)
            logger.info("[GeminiService] Memory and Retrieval services loaded successfully.")
        except Exception as e:
            logger.warning(f"[GeminiService] Failed to initialize memory services: {e}")
            self.memory = None
            self.retrieval = None

    def _select_model(self, use_pro: bool = False) -> str:
        """Returns the appropriate model name based on parameters."""
        if use_pro:
            return self.pro_model
        return self.flash_model

    # ─── Retry Mechanism Decorator ─────────────────────────────────────────────
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=2, max=10),
        retry=retry_if_exception_type((APIError, Exception)),
        reraise=True
    )
    async def _call_gemini_with_retry(
        self,
        model_name: str,
        contents: str,
        config: types.GenerateContentConfig
    ) -> Any:
        """Executes the API call using the GenAI SDK client with a retry mechanism."""
        # Wait for rate limit approval
        await rate_limiter.acquire()
        
        # Attempt generation using the primary model choice
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=contents,
                config=config
            )
            return response
        except APIError as e:
            # If model is unavailable (e.g. 404), attempt a fallback model choice
            if e.code == 404 or "not found" in str(e).lower():
                fallback_name = (
                    self.default_pro_fallback if "pro" in model_name else self.default_flash_fallback
                )
                logger.warning(f"[GeminiService] Model '{model_name}' not found. Retrying with fallback: '{fallback_name}'...")
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=fallback_name,
                    contents=contents,
                    config=config
                )
                return response
            raise e

    # ─── Structured JSON Generation ───────────────────────────────────────────
    async def generate_json(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        system_instruction: Optional[str] = None,
        use_pro: bool = False,
        rag_query: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Generates structured JSON strictly validated against the specified Pydantic schema class.
        Automatically retrieves context from memory if rag_query is provided.
        """
        # Fetch relevant context from memory layer (RAG)
        if rag_query and self.retrieval:
            retrieved_context = await self.retrieval.retrieve_context(rag_query, session_id=session_id)
            if system_instruction:
                system_instruction = f"{system_instruction}\n\n{retrieved_context}"
            else:
                system_instruction = retrieved_context

        model_name = self._select_model(use_pro)

        if not self.client:
            # Fallback mock generator
            logger.info(f"[GeminiService] [MOCK] Generating mock JSON for schema '{response_schema.__name__}'")
            return self._mock_schema_data(response_schema)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction,
            temperature=0.2, # Lower temperature for strict JSON adherence
        )

        try:
            response = await self._call_gemini_with_retry(model_name, prompt, config)
            
            # Track token usage if available
            if response.usage_metadata:
                await token_tracker.track(
                    prompt_tokens=response.usage_metadata.prompt_token_count or 0,
                    candidate_tokens=response.usage_metadata.candidates_token_count or 0
                )

            # Parse and validate response
            raw_text = response.text
            parsed = json.loads(raw_text)
            
            # Simple validation check
            response_schema.model_validate(parsed)
            return parsed

        except Exception as err:
            logger.error(f"[GeminiService] Structured JSON completion failed: {err}. Returning schema fallback.")
            return self._mock_schema_data(response_schema)

    # ─── Streaming Responses ───────────────────────────────────────────────────
    async def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        use_pro: bool = False,
        rag_query: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams text response chunks from Gemini.
        """
        # Fetch relevant context from memory layer (RAG)
        if rag_query and self.retrieval:
            retrieved_context = await self.retrieval.retrieve_context(rag_query, session_id=session_id)
            if system_instruction:
                system_instruction = f"{system_instruction}\n\n{retrieved_context}"
            else:
                system_instruction = retrieved_context

        model_name = self._select_model(use_pro)

        if not self.client:
            # Stream mock text response
            mock_text = (
                f"[MOCK STREAM] This is a mock streamed response for the query. "
                f"Gemini API key is not configured in settings."
            )
            for word in mock_text.split(" "):
                yield word + " "
                await asyncio.sleep(0.08)
            return

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )

        await rate_limiter.acquire()

        try:
            # Use to_thread to get the stream iterator, then iterate asynchronously
            stream_iterator = await asyncio.to_thread(
                self.client.models.generate_content_stream,
                model=model_name,
                contents=prompt,
                config=config
            )
            for chunk in stream_iterator:
                if chunk.text:
                    yield chunk.text
                await asyncio.sleep(0.01) # brief pause to prevent task starvation
        except Exception as err:
            logger.error(f"[GeminiService] Streaming generation failed: {err}")
            yield f"\n[Streaming Error: {err}]"

    # ─── Token Usage Metrics Endpoint helper ──────────────────────────────────
    @classmethod
    async def get_metrics(cls) -> dict[str, int]:
        """Returns the global token usage statistics."""
        return await token_tracker.get_metrics()

    # ─── Mock Schema Generator Fallbacks ──────────────────────────────────────
    def _mock_schema_data(self, schema_cls: Type[BaseModel]) -> dict[str, Any]:
        """Produces a dictionary matching the schema fields with fallback values."""
        from app.schemas.gemini_schemas import (
            EventPlanningSchema, LandingPageSchema, MarketingSchema,
            EmailCampaignSchema, SponsorshipSchema, BudgetSchema,
            TimelineSchema, VolunteerPlansSchema
        )
        
        # 1. EventPlanningSchema
        if schema_cls == EventPlanningSchema:
            return {
                "event_name": "TechForge Hackathon",
                "tagline": "Forge the future of open technology.",
                "description": "A high-intensity hackathon where innovators build systems and collaborate on open solutions.",
                "theme": "Developer tools, AI enhancements, and open-source packages.",
                "goals": ["Foster developer collaboration", "Build open source tools", "Encourage creative problem solving"],
                "required_roles": ["Lead Organizer", "Mentor Coordinator", "Sponsorship Manager"]
            }

        # 2. LandingPageSchema
        elif schema_cls == LandingPageSchema:
            return {
                "hero_title": "Build the Future of Open Tech",
                "hero_subtitle": "48 hours of collaborative hacking, learning, and prize-winning.",
                "about_copy": "TechForge is where ideas turn into working prototypes. Join builders around the globe.",
                "features": [
                    {"title": "Expert Mentorship", "description": "Get guidance from senior engineers and designers."},
                    {"title": "Grand Prizes", "description": "Win cash prizes, tech hardware, and developer credits."},
                    {"title": "Community Networking", "description": "Form long-lasting connections with professional developers."}
                ],
                "faq": [
                    {"question": "Who can participate?", "answer": "Developers, designers, and students of all experience levels."},
                    {"question": "Is there a registration fee?", "answer": "No, this event is 100% free of charge."}
                ],
                "cta_text": "Join TechForge Today"
            }

        # 3. MarketingSchema
        elif schema_cls == MarketingSchema:
            return {
                "campaign_name": "TechForge Registration Hype Campaign",
                "strategy": "Engage developers through community Slack/Discord channels, Twitter spaces, and LinkedIn posts.",
                "twitter_thread": [
                    {"tweet_num": 1, "content": "Ready to hack? Join us at TechForge Hackathon! Registration is open. Link in bio!"},
                    {"tweet_num": 2, "content": "Meet our mentors from top companies. Level up your coding skills. #TechForge"},
                    {"tweet_num": 3, "content": "Over $5,000 in cash prizes. What are you waiting for? Apply now!"}
                ],
                "linkedin_copy": "Excited to launch TechForge! 48 hours of pure creation, coding, and builder community. Apply today.",
                "keywords": ["hackathon", "developers", "coding", "opensource", "techforge"]
            }

        # 4. EmailCampaignSchema
        elif schema_cls == EmailCampaignSchema:
            return {
                "templates": [
                    {
                        "purpose": "invite",
                        "subject": "You're Invited: TechForge Hackathon!",
                        "body": "Hi Builder,\n\nJoin us at TechForge, a 48-hour virtual hackathon starting soon. Build cool things, win cash prizes, and connect with engineers.\n\nApply here: https://techforge.hacklaunch.ai"
                    },
                    {
                        "purpose": "sponsor",
                        "subject": "Partner Opportunity: Sponsor TechForge",
                        "body": "Dear Partner,\n\nWe would love to invite your company to sponsor TechForge and gain visibility among hundreds of developers."
                    }
                ]
            }

        # 5. SponsorshipSchema
        elif schema_cls == SponsorshipSchema:
            return {
                "pitch_hook": "Connect with top developer talent and showcase your API at TechForge.",
                "tiers": [
                    {"name": "Bronze", "price": 1500.0, "benefits": ["Logo on website", "Shared Slack channel shout-out"]},
                    {"name": "Silver", "price": 3000.0, "benefits": ["Keynote logo", "Virtual booth", "Resume book access"]},
                    {"name": "Gold", "price": 6000.0, "benefits": ["Dedicated track prize", "Workshop host slot", "Opening ceremony pitch"]}
                ],
                "target_sectors": ["Cloud Services", "AI & Analytics Providers", "Venture Funds"]
            }

        # 6. BudgetSchema
        elif schema_cls == BudgetSchema:
            return {
                "expenses": [
                    {"item": "Virtual Platform (Gather.town/Discord)", "category": "software", "cost": 500.0},
                    {"item": "Prizes (Cash & Devices)", "category": "prizes", "cost": 3000.0},
                    {"item": "Marketing & Social Ads", "category": "marketing", "cost": 800.0}
                ],
                "projected_revenues": [
                    {"item": "Sponsorship Tier Sales", "category": "admin", "cost": 7500.0}
                ],
                "total_cost": 4300.0,
                "total_revenue": 7500.0,
                "contingency_reserve": 430.0,
                "net_margin": 3200.0
            }

        # 7. TimelineSchema
        elif schema_cls == TimelineSchema:
            return {
                "pre_event": [
                    {"time": "Week -4", "activity": "Open Registrations", "duration_minutes": 0, "details": "Launch the landing page and start marketing campaigns."},
                    {"time": "Week -1", "activity": "Finalize Mentors & Schedules", "duration_minutes": 120, "details": "Run a prep sync with all mentors and organizers."}
                ],
                "event_day": [
                    {"time": "09:00 AM", "activity": "Opening Ceremony", "duration_minutes": 45, "details": "Introduce sponsors, rules, and track details."},
                    {"time": "10:00 AM", "activity": "Hacking Kickoff", "duration_minutes": 2880, "details": "Teams begin building, mentoring channels open."}
                ],
                "post_event": [
                    {"time": "Day +1", "activity": "Award Winners Announcement", "duration_minutes": 60, "details": "Broadcast the top winners and closing notes."}
                ]
            }

        # 8. VolunteerPlansSchema
        elif schema_cls == VolunteerPlansSchema:
            return {
                "intro": "Volunteer guide to coordinate operations and support teams during TechForge.",
                "roles": [
                    {
                        "role_title": "Discord / Slack Moderator",
                        "description": "Monitor text channels, help developers find teams, and enforce the Code of Conduct.",
                        "shifts_needed": ["Shift A: 8am-4pm", "Shift B: 4pm-12am"],
                        "coordinator_contact": "mod-leads@hacklaunch.ai"
                    },
                    {
                        "role_title": "Catering Coordinator (Local Hub)",
                        "description": "Manage snacks, meal deliveries, and trash disposal at the physical coworking space.",
                        "shifts_needed": ["Shift A: 11am-2pm", "Shift B: 5pm-8pm"],
                        "coordinator_contact": "hubs-leads@hacklaunch.ai"
                    }
                ]
            }

        return {}
