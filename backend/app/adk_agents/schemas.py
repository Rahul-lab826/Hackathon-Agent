"""
Pydantic V2 schemas for Google ADK Agent inputs and outputs.
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── 1. Event Planner Agent Schemas ──────────────────────────────────────────────
class EventPlannerInput(BaseModel):
    theme: str = Field(description="The theme or topic of the hackathon")
    domain: str = Field(description="The domain or sector (e.g., AI, Web3, FinTech)")
    duration_hours: int = Field(description="Duration of the event in hours")
    audience_type: str = Field(description="Target audience (e.g., students, professionals)")
    expected_participants: int = Field(description="Expected number of participants")
    location_type: str = Field(description="Location type: online, in-person, or hybrid")


class EventPlannerOutput(BaseModel):
    event_name: str = Field(description="Creative name of the hackathon")
    tagline: str = Field(description="Punchy tagline under 10 words")
    description: str = Field(description="High-level description of the event")
    audience_persona: str = Field(description="Paragraph profiling the target audience")
    team_roles: list[str] = Field(description="List of core team roles needed to run the event")


# ─── 2. Marketing Agent Schemas ──────────────────────────────────────────────────
class MarketingInput(BaseModel):
    event_name: str
    tagline: str
    description: str
    audience_persona: str


class MarketingOutput(BaseModel):
    campaign_name: str = Field(description="Name of the marketing campaign")
    marketing_strategy: str = Field(description="Overall marketing strategy summary")
    twitter_copy: list[str] = Field(description="List of 3 promotion tweets")
    linkedin_copy: str = Field(description="Professional LinkedIn announcement copy")


# ─── 3. Landing Page Agent Schemas ───────────────────────────────────────────────
class LandingPageInput(BaseModel):
    event_name: str
    tagline: str
    description: str


class LandingPageOutput(BaseModel):
    hero_headline: str = Field(description="Main hero section headline")
    hero_subheadline: str = Field(description="Main hero section subheadline")
    about_section: str = Field(description="Detailed about section copy")
    faqs: list[dict[str, str]] = Field(description="List of FAQs containing 'question' and 'answer'")
    cta_text: str = Field(description="Primary call-to-action text")


# ─── 5. Sponsorship Agent Schemas ────────────────────────────────────────────────
class SponsorshipInput(BaseModel):
    event_name: str
    tagline: str
    description: str


class SponsorTier(BaseModel):
    name: str
    price: float
    benefits: list[str]


class SponsorshipOutput(BaseModel):
    pitch_oneliner: str = Field(description="One-liner hook to pitch sponsors")
    tiers: list[SponsorTier] = Field(description="List of sponsor tiers (Bronze, Silver, Gold)")
    target_sectors: list[str] = Field(description="Sectors to target (e.g., Tech, Venture Capital)")


# ─── 6. Budget Agent Schemas ─────────────────────────────────────────────────────
class BudgetInput(BaseModel):
    expected_participants: int
    location_type: str
    sponsorship_tiers: list[dict[str, Any]] = Field(description="List of sponsorship tiers with prices")


class BudgetItem(BaseModel):
    category: str
    amount: float
    description: str


class BudgetOutput(BaseModel):
    cost_items: list[BudgetItem] = Field(description="Estimated expenses categories")
    revenue_items: list[BudgetItem] = Field(description="Estimated sponsorship and ticket revenues")
    total_cost: float = Field(description="Sum of all cost items")
    total_revenue: float = Field(description="Sum of all revenue items")
    net_margin: float = Field(description="Revenue minus cost")


# ─── 4. Email Campaign Agent Schemas ─────────────────────────────────────────────
class EmailCampaignInput(BaseModel):
    event_name: str
    tagline: str
    description: str
    sponsorship_tiers: list[dict[str, Any]] = Field(description="Sponsor tier structures")


class EmailTemplate(BaseModel):
    subject: str
    body: str


class EmailCampaignOutput(BaseModel):
    participant_invite: EmailTemplate = Field(description="Email copy for inviting participants")
    sponsor_outreach: EmailTemplate = Field(description="Email copy for sponsorship outreach")
    countdown_reminder: EmailTemplate = Field(description="Email copy reminding registered users")


# ─── 7. Execution Agent Schemas ──────────────────────────────────────────────────
class ExecutionInput(BaseModel):
    event_name: str
    team_roles: list[str]
    total_cost: float


class WeeklyMilestone(BaseModel):
    week: str
    tasks: list[str]


class RiskMitigation(BaseModel):
    risk: str
    mitigation: str


class ExecutionOutput(BaseModel):
    weekly_checklists: list[WeeklyMilestone] = Field(description="Ops checklist from Week -4 to Week +1")
    day_of_checklist: list[str] = Field(description="Day-of timeline milestones")
    risks: list[RiskMitigation] = Field(description="Potential risks and mitigation plans")
    kpis: list[str] = Field(description="Success KPIs")


# ─── 8. Memory Agent Schemas ─────────────────────────────────────────────────────
class MemoryInput(BaseModel):
    query: str
    action: str = Field(description="Must be 'search' or 'save'")
    data_to_save: Optional[dict[str, Any]] = Field(default=None, description="Compiled GTM package dict if saving")


class MemoryOutput(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list, description="Similar events from Qdrant search")
    status: str = Field(description="Status of operation: 'success', 'not_found', or 'saved'")
