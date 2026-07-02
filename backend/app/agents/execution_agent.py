"""
Execution Agent — generates the week-by-week operational plan, day-of checklist,
risk mitigation plan, KPI tracker, and post-event report template.
"""
from typing import Any
from app.agents.base_agent import BaseAgent
from app.agents.context_builder import SharedContext
from app.schemas.agent_outputs import ExecutionGTMOutput


class ExecutionAgent(BaseAgent):
    async def execute(self, context: SharedContext) -> dict[str, Any]:
        system_instruction = (
            "You are Execution Agent, a seasoned hackathon operations manager and project planner.\n"
            "Your job is to generate the complete operations and execution playbook for the hackathon.\n"
            "Be actionable, realistic, and thorough — organizers should be able to run the event entirely from your plan.\n"
            "Account for the event size, location type, and audience when planning logistics."
        )

        brand = context.brand_output or {}
        event_name = brand.get("event_name", "the Hackathon")
        structure = context.structure_output or {}
        team_roles = structure.get("team_roles", [])
        role_names = [r.get("role") for r in team_roles[:5]] if team_roles else []

        prompt = (
            f"Generate the complete execution playbook for '{event_name}'.\n\n"
            f"Event Brief:\n{context.serialize_brief()}\n\n"
            f"Core Team Roles: {', '.join(role_names) or 'Event Coordinator, Tech Lead, Marketing Lead'}\n\n"
            f"Generate structured JSON output containing:\n\n"
            f"1. weekly_plan: Tasks organized from 'Week -4' (4 weeks before) through 'Event Day' to 'Week +1' (post-event week). "
            f"   Each week must have 5-7 specific tasks with clear owners and action verbs.\n\n"
            f"2. day_of_checklist: A detailed pre-event day checklist covering all setup, test, and coordination items "
            f"   specific to a {context.location_type} hackathon.\n\n"
            f"3. risk_plan: Exactly 5 realistic risks with concrete mitigation strategies "
            f"   (e.g., low registration, tech failure, sponsor drop-out).\n\n"
            f"4. kpis: 8 specific measurable KPIs to track success "
            f"   (e.g., 'Number of registered teams', 'Sponsor ROI', 'NPS score').\n\n"
            f"5. report_template: A markdown-formatted post-event report template with sections for "
            f"   Executive Summary, Attendance Stats, Highlights, Sponsor Report, and Lessons Learned.\n\n"
            f"Make everything specific to a {context.duration_hours}-hour {context.location_type} hackathon "
            f"with {context.expected_participants} expected participants."
        )

        return await self.gemini.generate_json(
            prompt=prompt,
            response_schema=ExecutionGTMOutput,
            system_instruction=system_instruction
        )
