"""
Pydantic schemas for Gemini Service structured output generation.
Ensures every model call returns strictly validated JSON.
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── 1. Event Planning Schema ──────────────────────────────────────────────────
class EventPlanningSchema(BaseModel):
    event_name: str = Field(description="The creative, brand-aligned name of the event.")
    tagline: str = Field(description="A punchy slogan or tagline under 10 words.")
    description: str = Field(description="A descriptive overview (~150 words) of the event.")
    theme: str = Field(description="Core theme and vibe of the hackathon.")
    goals: list[str] = Field(description="List of 3 primary goals of the event.")
    required_roles: list[str] = Field(description="Key organizer/mentor roles needed.")


# ─── 2. Landing Page Schema ────────────────────────────────────────────────────
class FAQItem(BaseModel):
    question: str
    answer: str


class FeatureItem(BaseModel):
    title: str
    description: str


class LandingPageSchema(BaseModel):
    hero_title: str = Field(description="Attention-grabbing headline for the hero section.")
    hero_subtitle: str = Field(description="Subheadline supporting the hero title.")
    about_copy: str = Field(description="Main description text introducing the event (~150 words).")
    features: list[FeatureItem] = Field(description="Exactly 3 key features/highlights of the event.")
    faq: list[FAQItem] = Field(description="Exactly 5 frequently asked questions with answers.")
    cta_text: str = Field(description="Call to action button label.")


# ─── 3. Marketing Schema ───────────────────────────────────────────────────────
class TwitterPost(BaseModel):
    tweet_num: int
    content: str


class MarketingSchema(BaseModel):
    campaign_name: str = Field(description="Name of the promo campaign.")
    strategy: str = Field(description="Summary of the promotional strategy.")
    twitter_thread: list[TwitterPost] = Field(description="A thread of 3 punchy tweets promoting registration.")
    linkedin_copy: str = Field(description="Professional LinkedIn announcement copy.")
    keywords: list[str] = Field(description="Top 5 target search/hashtag keywords.")


# ─── 4. Email Campaigns Schema ─────────────────────────────────────────────────
class EmailTemplate(BaseModel):
    purpose: str = Field(description="e.g. 'invite', 'reminder', 'sponsor'")
    subject: str
    body: str


class EmailCampaignSchema(BaseModel):
    templates: list[EmailTemplate] = Field(description="List containing invite, outreach, and reminder templates.")


# ─── 5. Sponsorship Schema ─────────────────────────────────────────────────────
class SponsorTier(BaseModel):
    name: str = Field(description="Bronze, Silver, Gold, etc.")
    price: float = Field(description="Price tag in USD.")
    benefits: list[str] = Field(description="Benefits included (e.g. logo, booth, keynote).")


class SponsorshipSchema(BaseModel):
    pitch_hook: str = Field(description="One-sentence hook to convince brands.")
    tiers: list[SponsorTier] = Field(description="List of sponsor tiers.")
    target_sectors: list[str] = Field(description="Industry sectors to pitch.")


# ─── 6. Budget Schema ──────────────────────────────────────────────────────────
class BudgetItem(BaseModel):
    item: str
    category: str = Field(description="venue, food, marketing, software, prizes, admin")
    cost: float


class BudgetSchema(BaseModel):
    expenses: list[BudgetItem] = Field(description="List of estimated expenses.")
    projected_revenues: list[BudgetItem] = Field(description="Sponsorships or ticket revenues.")
    total_cost: float = Field(description="Sum of all expenses.")
    total_revenue: float = Field(description="Sum of all revenues.")
    contingency_reserve: float = Field(description="10% safety reserve buffer.")
    net_margin: float = Field(description="Total revenue minus total cost.")


# ─── 7. Timeline Schema ────────────────────────────────────────────────────────
class TimelineMilestone(BaseModel):
    time: str = Field(description="Time/Date or relative offset (e.g. 'Week -2', '09:00 AM')")
    activity: str
    duration_minutes: int
    details: str


class TimelineSchema(BaseModel):
    pre_event: list[TimelineMilestone] = Field(description="Preparation timeline milestones.")
    event_day: list[TimelineMilestone] = Field(description="Hour-by-hour day of event schedule.")
    post_event: list[TimelineMilestone] = Field(description="Follow-up and closing milestones.")


# ─── 8. Volunteer Plans Schema ─────────────────────────────────────────────────
class VolunteerRole(BaseModel):
    role_title: str
    description: str
    shifts_needed: list[str] = Field(description="List of shifts (e.g. 'Morning: 8am-12pm')")
    coordinator_contact: str = Field(description="Mock email/handler for coordinating this role.")


class VolunteerPlansSchema(BaseModel):
    intro: str = Field(description="Overview of volunteer requirements.")
    roles: list[VolunteerRole] = Field(description="Roles (e.g., Tech Support, Registration Desk, Catering).")
