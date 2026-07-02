"""
Structure Agent — generates timeline phases, hour-by-hour schedules, roles needed, venue/platform checklists, criteria, and prize configurations.
"""
from typing import Any
from app.agents.base_agent import BaseAgent
from app.agents.context_builder import SharedContext
from app.schemas.agent_outputs import StructureGTMOutput


class StructureAgent(BaseAgent):
    async def execute(self, context: SharedContext) -> dict[str, Any]:
        system_instruction = (
            "You are Structure Agent, an expert in hackathon operational logistics and structural planning.\n"
            "Your job is to generate a comprehensive schedule, timeline, and logistics plan for the hackathon.\n"
            "Ensure the timetable fits the duration constraints exactly (e.g. 24hr, 36hr, or 48hr)."
        )

        brand = context.brand_output or {}
        event_name = brand.get("event_name", "the Hackathon")

        few_shot = await self.get_few_shot_examples(
            f"event name: {event_name} duration: {context.duration_hours} hours logistics: {context.location_type}"
        )

        prompt = (
            f"Generate the operational schedule and structure for the hackathon '{event_name}'.\n"
            f"Event Brief:\n{context.serialize_brief()}\n\n"
            f"Brand Guide Details:\n"
            f"Tagline: {brand.get('tagline')}\n"
            f"Tone adjectives: {brand.get('tone_adjectives')}\n\n"
            f"Here is some context from similar previous hackathons:\n"
            f"{few_shot}\n\n"
            f"Generate structured JSON output containing:\n"
            f"1. timeline: Dictionary of milestones divided into 'pre_event', 'event_day', and 'post_event'.\n"
            f"2. schedule: Hour-by-hour list of items fitting the {context.duration_hours}-hour period. Categorize each activity type as 'session', 'break', 'activity', or 'ceremony'.\n"
            f"3. team_roles: Core roles needed (e.g., Coordinator, Mentor Lead) with their responsibilities.\n"
            f"4. venue_checklist: List of spaces/tools (e.g., Discord servers, catering, main stage).\n"
            f"5. judging_criteria: Exactly 5 criteria parameters with percentage weights totaling 100 (e.g., Innovation, Impact, Technical complexity).\n"
            f"6. prize_structure: Grand prize, category prizes, and details."
        )

        return await self.gemini.generate_json(
            prompt=prompt,
            response_schema=StructureGTMOutput,
            system_instruction=system_instruction
        )
