"""
Email Agent — generates 5 ready-to-send email templates:
Participant Invite, Sponsor Outreach, Registration Confirmation, Countdown Reminder, Post-Event Thank You.
"""
from typing import Any
from app.agents.base_agent import BaseAgent
from app.agents.context_builder import SharedContext
from app.schemas.agent_outputs import EmailGTMOutput


class EmailAgent(BaseAgent):
    async def execute(self, context: SharedContext) -> dict[str, Any]:
        system_instruction = (
            "You are Email Agent, an expert email copywriter specializing in event marketing and B2B outreach.\n"
            "Your job is to write 5 high-converting, polished, ready-to-send email templates for the hackathon.\n"
            "Each email must have a compelling subject line and a full professional body copy.\n"
            "Match the brand tone and event identity throughout all emails."
        )

        brand = context.brand_output or {}
        event_name = brand.get("event_name", "the Hackathon")
        structure = context.structure_output or {}
        prizes = structure.get("prize_structure", [])
        prize_text = "; ".join([f"{p.get('position')}: {p.get('prize')}" for p in prizes[:3]]) or "Amazing prizes"

        prompt = (
            f"Write 5 complete email templates for the hackathon '{event_name}'.\n\n"
            f"Event Brief:\n{context.serialize_brief()}\n\n"
            f"Brand Identity:\n"
            f"Tagline: {brand.get('tagline')}\n"
            f"Tone: {brand.get('tone_adjectives')}\n"
            f"Prizes: {prize_text}\n\n"
            f"Generate structured JSON with 5 emails, each having subject and body:\n\n"
            f"1. invite_subject + invite_body: Participant invitation announcing the hackathon, prizes, how to register.\n"
            f"2. sponsor_subject + sponsor_body: Outreach to potential corporate sponsors pitching partnership value.\n"
            f"3. confirmation_subject + confirmation_body: Registration confirmation email sent after sign-up.\n"
            f"4. reminder_subject + reminder_body: Countdown reminder (2 days before the event begins).\n"
            f"5. thankyou_subject + thankyou_body: Post-event gratitude email to all participants.\n\n"
            f"Each body must be at least 200 words. Use a professional, warm, and energetic tone."
        )

        return await self.gemini.generate_json(
            prompt=prompt,
            response_schema=EmailGTMOutput,
            system_instruction=system_instruction
        )
