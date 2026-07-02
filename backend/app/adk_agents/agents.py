"""
Google ADK Agent definitions for HackLaunch AI.
Defines all 8 agents (Event Planner, Marketing, Landing Page, Email Campaign, Sponsorship, Budget, Execution, Memory).
"""
import logging
from typing import Any, Optional
from google import adk
from app.config import settings
from app.services.qdrant_service import QdrantService
from app.adk_agents.schemas import (
    EventPlannerInput, EventPlannerOutput,
    MarketingInput, MarketingOutput,
    LandingPageInput, LandingPageOutput,
    SponsorshipInput, SponsorshipOutput,
    BudgetInput, BudgetOutput,
    EmailCampaignInput, EmailCampaignOutput,
    ExecutionInput, ExecutionOutput,
    MemoryInput, MemoryOutput
)

logger = logging.getLogger("hacklaunch.adk_agents")

# ─── Qdrant Memory Service Helper ──────────────────────────────────────────────
qdrant = QdrantService()

def search_historical_events(query: str) -> list[dict[str, Any]]:
    """
    Search vector memory (Qdrant) for similar historical hackathons
    to provide few-shot examples and relevant context.
    """
    try:
        import asyncio
        # Run async search in sync tool function wrapper
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, run in thread/executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                res = pool.submit(
                    lambda: asyncio.run(qdrant.search_similar_events(query, limit=2))
                ).result()
            return res
        else:
            return asyncio.run(qdrant.search_similar_events(query, limit=2))
    except Exception as e:
        logger.warning(f"Memory Agent search failed: {e}. Falling back to empty history.")
        return []

def store_event_in_memory(event_id: str, data: dict[str, Any]) -> str:
    """
    Store the final compiled GTM launch package into vector memory (Qdrant)
    so it can be retrieved by future event generation queries.
    """
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(
                    lambda: asyncio.run(qdrant.store_event(event_id, data))
                ).result()
        else:
            asyncio.run(qdrant.store_event(event_id, data))
        return "success"
    except Exception as e:
        logger.error(f"Memory Agent store failed: {e}")
        return "error"


from app.services.mcp import ALL_MCP_TOOLS

# ─── ADK Agents Definitions ───────────────────────────────────────────────────

# 1. Event Planner Agent
event_planner_agent = adk.Agent(
    name="event_planner_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Event Planner Agent.\n"
        "Your task is to take event parameters (theme, domain, expected participants, duration, location) "
        "and generate the core identity of the hackathon.\n"
        "This includes: a creative event name, a tagline under 10 words, a clear event description, "
        "a target audience persona, and a list of required team roles (e.g. Mentor, Coordinator)."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=EventPlannerInput,
    output_schema=EventPlannerOutput
)

# 2. Marketing Agent
marketing_agent = adk.Agent(
    name="marketing_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Marketing Agent.\n"
        "Your task is to take the core event details (name, tagline, description, target persona) "
        "and design the social media campaign.\n"
        "Generate a creative marketing campaign name, summary strategy, Twitter copy (exactly 3 promotional tweets), "
        "and a LinkedIn professional announcement."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=MarketingInput,
    output_schema=MarketingOutput
)

# 3. Landing Page Agent
landing_page_agent = adk.Agent(
    name="landing_page_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Landing Page Agent.\n"
        "Your task is to generate website content for the hackathon registration landing page.\n"
        "Generate a high-converting hero headline, subheadline, about copy (~150 words), "
        "exactly 5 FAQs, and the primary call-to-action button text."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=LandingPageInput,
    output_schema=LandingPageOutput
)

# 4. Sponsorship Agent
sponsorship_agent = adk.Agent(
    name="sponsorship_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Sponsorship Agent.\n"
        "Your task is to craft the sponsorship strategy for the hackathon.\n"
        "Generate a pitch hook, Gold/Silver/Bronze tiers with pricing and benefits, and target industry sectors."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=SponsorshipInput,
    output_schema=SponsorshipOutput
)

# 5. Budget Agent
budget_agent = adk.Agent(
    name="budget_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Budget Agent.\n"
        "Your task is to generate cost categories (venue, prizes, food, marketing, platform fees) "
        "based on expected participant numbers and location. Calculate expected sponsorship revenues "
        "based on tier structures and compute the final net margin."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=BudgetInput,
    output_schema=BudgetOutput
)

# 6. Email Campaign Agent
email_campaign_agent = adk.Agent(
    name="email_campaign_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Email Campaign Agent.\n"
        "Your task is to write high-converting email templates for the hackathon.\n"
        "Write 3 templates: a participant invitation, sponsor outreach, and a countdown reminder."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=EmailCampaignInput,
    output_schema=EmailCampaignOutput
)

# 7. Execution Agent
execution_agent = adk.Agent(
    name="execution_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Execution Agent.\n"
        "Your task is to plan operations. Generate weekly milestones (Week -4 to Week +1), "
        "day-of schedule checklist, 3 operational risks with mitigations, and performance KPIs."
    ),
    tools=ALL_MCP_TOOLS,
    input_schema=ExecutionInput,
    output_schema=ExecutionOutput
)

# 8. Memory Agent
memory_agent = adk.Agent(
    name="memory_agent",
    model=settings.GEMINI_MODEL,
    instruction=(
        "You are the Memory Agent.\n"
        "Your task is to interact with vector memory. Use the 'search_historical_events' tool to find context, "
        "and 'store_event_in_memory' to index completed launch packages."
    ),
    tools=[search_historical_events, store_event_in_memory] + ALL_MCP_TOOLS,
    input_schema=MemoryInput,
    output_schema=MemoryOutput
)
