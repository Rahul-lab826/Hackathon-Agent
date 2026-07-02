"""
Brand Agent — generates the event name, tagline, adjectives, primary/secondary hex colors, and target persona.
"""
from typing import Any
from app.agents.base_agent import BaseAgent
from app.agents.context_builder import SharedContext
from app.schemas.agent_outputs import BrandGTMOutput


class BrandAgent(BaseAgent):
    async def execute(self, context: SharedContext) -> dict[str, Any]:
        system_instruction = (
            "You are Brand Agent, an elite brand designer specializing in tech events and hackathons.\n"
            "Your job is to create a fully fleshed out brand identity for a new hackathon based on its intake brief.\n"
            "Be highly creative, memorable, and thematic. Avoid generic names."
        )

        few_shot = await self.get_few_shot_examples(
            f"theme: {context.theme} domain: {context.domain} audience: {context.audience_type}"
        )

        prompt = (
            f"Create a brand identity launch package for the following hackathon:\n"
            f"{context.serialize_brief()}\n\n"
            f"Here is some context from similar previous hackathons:\n"
            f"{few_shot}\n\n"
            f"Generate structured JSON output containing:\n"
            f"1. event_name: A highly memorable, catchy, thematic event name.\n"
            f"2. tagline: A punchy slogan under 10 words.\n"
            f"3. tone_adjectives: Exactly 3 adjectives outlining the brand voice.\n"
            f"4. color_primary: Hex code for primary color (e.g. vibrant indigo/cyan).\n"
            f"5. color_secondary: Hex code for secondary color (e.g. electric pink/orange).\n"
            f"6. color_names: List of names for primary and secondary colors.\n"
            f"7. persona_text: Profile description paragraph of the target participant (max 150 words)."
        )

        return await self.gemini.generate_json(
            prompt=prompt,
            response_schema=BrandGTMOutput,
            system_instruction=system_instruction
        )
