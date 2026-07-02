"""
Prompt Manager — stores and compiles custom prompt templates for the 8 key launch package components.
Enforces structured outputs by requesting strict compliance with schemas.
"""
from typing import Any


class PromptManager:
    # ─── System Instructions ──────────────────────────────────────────────────
    SYSTEM_INSTRUCTION = (
        "You are an expert event planning and Hackathon GTM consultant.\n"
        "Your task is to generate high-quality, professional, and detailed launch documents.\n"
        "You must return the outputs strictly structured as JSON matching the requested schema.\n"
        "Do not include any conversational preamble, notes, or markdown formatting outside the JSON."
    )

    # ─── Prompt Templates ──────────────────────────────────────────────────────
    TEMPLATES = {
        "event_planning": (
            "Generate event planning details for a hackathon based on these inputs:\n"
            "- Theme: {theme}\n"
            "- Domain: {domain}\n"
            "- Expected Participants: {expected_participants}\n"
            "- Duration: {duration_hours} hours\n"
            "- Audience Type: {audience_type}\n"
            "- Location: {location_type}\n\n"
            "Produce an aligned name, tagline, description, theme, goals, and required team roles."
        ),
        "landing_pages": (
            "Create high-converting landing page copy for the following hackathon:\n"
            "- Event Name: {event_name}\n"
            "- Tagline: {tagline}\n"
            "- Description: {description}\n\n"
            "Generate hero section headlines, about page body copy, 3 highlight features, 5 detailed FAQs, "
            "and a compelling CTA button label."
        ),
        "marketing": (
            "Design a digital marketing promo campaign for:\n"
            "- Event Name: {event_name}\n"
            "- Tagline: {tagline}\n"
            "- Description: {description}\n"
            "- Target Audience: {audience_persona}\n\n"
            "Provide a campaign name, summary strategy, a Twitter thread of 3 promotional tweets, "
            "a professional LinkedIn announcement post, and 5 hashtags/keywords."
        ),
        "email_campaigns": (
            "Draft a comprehensive email outreach sequence for:\n"
            "- Event Name: {event_name}\n"
            "- Description: {description}\n"
            "- Sponsorship Perks Summary: {sponsor_perks}\n\n"
            "Write exactly 3 distinct email templates: \n"
            "1. An inviting pitch for participants.\n"
            "2. A sponsorship proposal pitch.\n"
            "3. A countdown reminder email to register."
        ),
        "sponsorship": (
            "Develop a corporate sponsorship package for:\n"
            "- Event Name: {event_name}\n"
            "- Tagline: {tagline}\n"
            "- Description: {description}\n\n"
            "Provide a strong sponsor pitch hook, exactly 3 tiers (Bronze, Silver, Gold) with USD pricing "
            "and developer-centric benefits, and a list of target sectors to approach."
        ),
        "budget": (
            "Formulate a complete budget plan for:\n"
            "- Event Name: {event_name}\n"
            "- Location: {location_type}\n"
            "- Expected Participants: {expected_participants}\n"
            "- Sponsor Tiers & Prices: {sponsor_tiers}\n\n"
            "Estimate costs (venue, swag, prizes, platforms), project sponsorship revenues, "
            "calculate total costs/revenues, include a 10% contingency buffer, and compute the net margin."
        ),
        "timeline": (
            "Create a master timeline schedule for:\n"
            "- Event Name: {event_name}\n"
            "- Duration: {duration_hours} hours\n\n"
            "Generate milestone check-ins for: \n"
            "1. Pre-event phase (weeks before).\n"
            "2. Event day (hour-by-hour agenda).\n"
            "3. Post-event phase (closing and follow-ups)."
        ),
        "volunteer_plans": (
            "Plan volunteer operations for:\n"
            "- Event Name: {event_name}\n"
            "- Team Roles List: {team_roles}\n\n"
            "Create volunteer roles, shift timetables, coordinator contact addresses, and training notes."
        )
    }

    @classmethod
    def render(cls, template_key: str, **kwargs: Any) -> str:
        """Renders the selected prompt template with provided variables."""
        template = cls.TEMPLATES.get(template_key)
        if not template:
            raise KeyError(f"Prompt template for key '{template_key}' not found.")
        return template.format(**kwargs)
