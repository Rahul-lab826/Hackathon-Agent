"""
ADK Agents package initializer. Exposes the AgentManager orchestrator.
"""
from app.adk_agents.orchestrator import AgentManager
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

__all__ = [
    "AgentManager",
    "EventPlannerInput",
    "EventPlannerOutput",
    "MarketingInput",
    "MarketingOutput",
    "LandingPageInput",
    "LandingPageOutput",
    "SponsorshipInput",
    "SponsorshipOutput",
    "BudgetInput",
    "BudgetOutput",
    "EmailCampaignInput",
    "EmailCampaignOutput",
    "ExecutionInput",
    "ExecutionOutput",
    "MemoryInput",
    "MemoryOutput"
]
