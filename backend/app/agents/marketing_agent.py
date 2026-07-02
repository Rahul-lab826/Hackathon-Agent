"""
Marketing Agent — generates LinkedIn posts, WhatsApp announcements, Instagram captions, and Twitter/X threads.
"""
from typing import Any
from app.agents.base_agent import BaseAgent
from app.agents.context_builder import SharedContext
from app.schemas.agent_outputs import MarketingGTMOutput


class MarketingAgent(BaseAgent):
    async def execute(self, context: SharedContext) -> dict[str, Any]:
        system_instruction = (
            "You are Marketing Agent, an elite growth marketer and social media strategist.\n"
            "Your job is to generate buzz for the hackathon by writing engaging posts across platforms.\n"
            "Tailor the tone specifically to each channel: professional for LinkedIn, short for WhatsApp, trendy for Instagram, and hook-centric for Twitter."
        )

        brand = context.brand_output or {}
        event_name = brand.get("event_name", "the Hackathon")
        content = context.content_output or {}

        prompt = (
            f"Write the complete social media launch campaign for '{event_name}'.\n"
            f"Event Brief:\n{context.serialize_brief()}\n\n"
            f"Brand Guide Details:\n"
            f"Tagline: {brand.get('tagline')}\n"
            f"Tone: {brand.get('tone_adjectives')}\n\n"
            f"Landing Page Hook Details:\n"
            f"Headline: {content.get('hero_headline')}\n"
            f"Sponsor Hook: {content.get('sponsor_pitch_oneliner')}\n\n"
            f"Generate structured JSON output containing:\n"
            f"1. linkedin_announcement: Professional announcement post (150-200 words, 5 hashtags).\n"
            f"2. linkedin_countdown: Countdown post with urgency/hype (1 week before).\n"
            f"3. whatsapp_announcement: Emojis-rich brief post under 100 words.\n"
            f"4. whatsapp_reminder: Short reminder post (2 days before).\n"
            f"5. instagram_caption: Hype caption with 10 hashtags.\n"
            f"6. twitter_thread: Exactly 3 punchy tweets in a thread (each under 280 characters).\n"
            f"7. hashtags: Recommended campaign hashtags."
        )

        return await self.gemini.generate_json(
            prompt=prompt,
            response_schema=MarketingGTMOutput,
            system_instruction=system_instruction
        )
