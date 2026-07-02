"""
Content Agent — generates landing page copy, FAQs, registration CTA variants, and sponsor pitch.
"""
from typing import Any
from app.agents.base_agent import BaseAgent
from app.agents.context_builder import SharedContext
from app.schemas.agent_outputs import ContentGTMOutput


class ContentAgent(BaseAgent):
    async def execute(self, context: SharedContext) -> dict[str, Any]:
        system_instruction = (
            "You are Content Agent, an elite conversion copywriter specializing in landing pages and marketing assets.\n"
            "Your job is to generate compelling copy that makes builders register and sponsors fund the hackathon.\n"
            "Align all messaging with the provided event name, brand tone, and colors."
        )

        brand = context.brand_output or {}
        event_name = brand.get("event_name", "the Hackathon")

        prompt = (
            f"Generate high-converting landing page copywriting for '{event_name}'.\n"
            f"Event Brief:\n{context.serialize_brief()}\n\n"
            f"Brand Guide Details:\n"
            f"Tagline: {brand.get('tagline')}\n"
            f"Tone: {brand.get('tone_adjectives')}\n\n"
            f"Generate structured JSON output containing:\n"
            f"1. hero_headline: High-impact main header.\n"
            f"2. hero_subheadline: Hook sentence that elaborates on the headline.\n"
            f"3. about_copy: Engaging about paragraph (approx 150 words) describing the mission and focus.\n"
            f"4. faq: Exactly 8 FAQs with clear answers addressing common builder questions (prizes, coding rules, team size).\n"
            f"5. cta_variants: Exactly 3 CTA button copy options.\n"
            f"6. sponsor_pitch_oneliner: One-sentence value proposition for potential sponsors."
        )

        return await self.gemini.generate_json(
            prompt=prompt,
            response_schema=ContentGTMOutput,
            system_instruction=system_instruction
        )
