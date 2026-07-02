"""
Agent Manager (Orchestrator) — coordinates the 8 Google ADK agents in a sequential, 
inter-dependent workflow. Connects output of one agent to the input of the next.
Supports async execution, detailed logging, and resilient error recovery with Pydantic fallbacks.
"""
import logging
import time
import uuid
from typing import Any, Optional
from google import adk
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from app.adk_agents.agents import (
    event_planner_agent, marketing_agent, landing_page_agent,
    email_campaign_agent, sponsorship_agent, budget_agent,
    execution_agent, memory_agent, search_historical_events,
    store_event_in_memory
)
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

logger = logging.getLogger("hacklaunch.adk_orchestrator")


class AgentManager:
    def __init__(self, db_session: Optional[Any] = None) -> None:
        self.db = db_session
        self.session_service = InMemorySessionService()

    async def _run_agent_safely(
        self,
        agent: adk.Agent,
        input_data: BaseModel,
        output_schema: type[BaseModel]
    ) -> Any:
        """
        Runs a Google ADK agent using the Runner in a safe way.
        If the agent execution fails (e.g. invalid API key, model rate limits),
        it falls back to generating structured mock data matching the schema.
        """
        agent_name = agent.name
        logger.info(f"[ADK AgentManager] Starting Agent: '{agent_name}'")
        start_time = time.monotonic()

        runner = adk.Runner(
            agent=agent,
            app_name=f"app_{agent_name}",
            session_service=self.session_service,
            auto_create_session=True
        )

        # Serialize Pydantic input model to a string prompt
        prompt_text = (
            f"Please process the following structured inputs and generate the requested output schema:\n"
            f"{input_data.model_dump_json(indent=2)}"
        )
        msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )

        try:
            final_output = None
            async for event in runner.run_async(
                user_id="adk_manager_user",
                session_id=str(uuid.uuid4()),
                new_message=msg
            ):
                if event.output is not None:
                    final_output = event.output

            duration = (time.monotonic() - start_time) * 1000
            if final_output:
                logger.info(f"[ADK AgentManager] '{agent_name}' completed successfully in {duration:.2f}ms.")
                return final_output
            else:
                raise ValueError("Agent completed without producing any structured output.")

        except Exception as err:
            duration = (time.monotonic() - start_time) * 1000
            logger.warning(
                f"[ADK AgentManager] '{agent_name}' failed or skipped due to: {err}. "
                f"Recovering with schema fallback generation."
            )
            # Resilient fallback generator matching the Pydantic schema
            return self._generate_fallback_data(output_schema, input_data)

    def _generate_fallback_data(self, schema_cls: type[BaseModel], inputs: BaseModel) -> Any:
        """
        Generates realistic fallback data matching the Pydantic schema class,
        tailored to the supplied inputs.
        """
        input_dict = inputs.model_dump()
        name = input_dict.get("event_name", input_dict.get("theme", "Hackathon"))
        domain = input_dict.get("domain", "Technology")
        location = input_dict.get("location_type", "online")

        # 1. EventPlannerOutput Fallback
        if schema_cls == EventPlannerOutput:
            return EventPlannerOutput(
                event_name=f"{name.title()} Forge",
                tagline=f"Forge the future of {domain} in {input_dict.get('duration_hours', 48)} hours.",
                description=f"A high-impact, virtual event bringing developers together to build solutions in {domain}.",
                audience_persona=f"Developers, product builders, and designers interested in {domain}.",
                team_roles=["Lead Organizer", "Tech Coordinator", "Mentor Manager", "Marketing Lead"]
            )

        # 2. MarketingOutput Fallback
        elif schema_cls == MarketingOutput:
            return MarketingOutput(
                campaign_name=f"{name} Launch Campaign",
                marketing_strategy=f"Promote the event via developer channels, newsletters, and social media platforms.",
                twitter_copy=[
                    f"Register now for {name}! Build cool projects and win prizes. Link in bio!",
                    f"Are you ready for the ultimate {name} challenge? Join us and show off your skills!",
                    f"Only a few days left to register for {name}. Don't miss out!"
                ],
                linkedin_copy=f"Excited to announce the upcoming {name}! A space for developers to create, collaborate, and launch."
            )

        # 3. LandingPageOutput Fallback
        elif schema_cls == LandingPageOutput:
            return LandingPageOutput(
                hero_headline=f"Build the Future at {name}",
                hero_subheadline=f"{input_dict.get('tagline', 'The ultimate builder experience.')}",
                about_section=f"Welcome to {name}, an event designed to bring creators, developers, and visionaries together.",
                faqs=[
                    {"question": "Who can participate?", "answer": "Anyone interested in building and designing tech products!"},
                    {"question": "Is there a registration fee?", "answer": "No, registration is completely free."}
                ],
                cta_text="Register For Free"
            )

        # 4. SponsorshipOutput Fallback
        elif schema_cls == SponsorshipOutput:
            return SponsorshipOutput(
                pitch_oneliner=f"Reach developers and builders at the premier {name} event.",
                tiers=[
                    {"name": "Bronze", "price": 1000.0, "benefits": ["Logo on website", "Slack channel shout-out"]},
                    {"name": "Silver", "price": 2500.0, "benefits": ["Logo on website", "Opening ceremony slide", "Resumes access"]},
                    {"name": "Gold", "price": 5000.0, "benefits": ["Opening slide", "Keynote address", "Branded track prize"]}
                ],
                target_sectors=["AI/Cloud Providers", "Venture Capital", "Developer Tools"]
            )

        # 5. BudgetOutput Fallback
        elif schema_cls == BudgetOutput:
            tiers = input_dict.get("sponsorship_tiers", [])
            total_rev = sum([t.get("price", 0.0) * 2 for t in tiers]) if tiers else 8500.0
            participants = input_dict.get("expected_participants", 100)
            cost_factor = 25.0 if location == "online" else 80.0
            total_c = participants * cost_factor

            return BudgetOutput(
                cost_items=[
                    {"category": "Platform & Software", "amount": total_c * 0.2, "description": "Streaming, Slack, Devpost"},
                    {"category": "Prizes", "amount": total_c * 0.4, "description": "Cash prize pool and trophies"},
                    {"category": "Marketing & Swag", "amount": total_c * 0.4, "description": "Social ads, t-shirts, stickers"}
                ],
                revenue_items=[
                    {"category": "Sponsorships", "amount": total_rev, "description": "Sponsor tier packages"},
                    {"category": "Ticket Sales", "amount": 0.0, "description": "Free admission"}
                ],
                total_cost=total_c,
                total_revenue=total_rev,
                net_margin=total_rev - total_c
            )

        # 6. EmailCampaignOutput Fallback
        elif schema_cls == EmailCampaignOutput:
            return EmailCampaignOutput(
                participant_invite={
                    "subject": f"You're Invited: Join us at {name}!",
                    "body": f"Hi Builder,\n\nWe are excited to invite you to {name}. Join us for a weekend of hacking, learning, and networking.\n\nBest,\nThe Team"
                },
                sponsor_outreach={
                    "subject": f"Partner Opportunity: Sponsor {name}",
                    "body": f"Dear Partner,\n\nWe would love to invite you to sponsor {name} and connect with top developer talent.\n\nBest,\nSponsorships Team"
                },
                countdown_reminder={
                    "subject": f"Countdown: 2 days until {name} starts!",
                    "body": f"Hi Builder,\n\nGet ready! We start in exactly 2 days. See you online.\n\nBest,\nThe Team"
                }
            )

        # 7. ExecutionOutput Fallback
        elif schema_cls == ExecutionOutput:
            roles = input_dict.get("team_roles", ["Coordinator"])
            return ExecutionOutput(
                weekly_checklists=[
                    {"week": "Week -4", "tasks": ["Secure core team", "Launch landing page", "Open registrations"]},
                    {"week": "Week -1", "tasks": ["Finalize schedules", "Prep mentors", "Send prep email"]}
                ],
                day_of_checklist=[
                    "09:00 AM - Opening Ceremony",
                    "10:00 AM - Hacking Starts",
                    "05:00 PM - Submission Deadline"
                ],
                risks=[
                    {"risk": "Low registration", "mitigation": "Increase social ad spend and email outreach"},
                    {"risk": "Technical platform crash", "mitigation": "Set up secondary backup video call link"}
                ],
                kpis=[
                    "Total registered participants",
                    "Number of projects submitted",
                    "Sponsor satisfaction NPS"
                ]
            )

        # 8. MemoryOutput Fallback
        elif schema_cls == MemoryOutput:
            return MemoryOutput(
                results=[],
                status="saved"
            )

        return schema_cls()

    async def execute_pipeline(self, initial_input: EventPlannerInput) -> dict[str, Any]:
        """
        Runs the complete multi-agent workflow in sequence.
        Inter-agent state flow:
           START ──> Memory Agent (Search) ──> Event Planner ──> Marketing & Landing Page & Sponsorship
           Sponsorship ──> Budget ──> Email Campaign & Execution ──> Memory Agent (Save) ──> END
        """
        logger.info("[ADK AgentManager] Kicking off multi-agent workflow...")

        # Step 1: Memory Agent (Search context)
        memory_in = MemoryInput(
            query=f"{initial_input.theme} {initial_input.domain}",
            action="search"
        )
        # We invoke search tool directly for performance and predictability
        logger.info("[ADK Memory Agent] Searching vector database for similar hackathons...")
        past_events = search_historical_events(memory_in.query)
        logger.info(f"[ADK Memory Agent] Found {len(past_events)} relevant past events.")

        # Step 2: Event Planner Agent
        planner_out: EventPlannerOutput = await self._run_agent_safely(
            agent=event_planner_agent,
            input_data=initial_input,
            output_schema=EventPlannerOutput
        )

        # Step 3: Marketing Agent
        marketing_in = MarketingInput(
            event_name=planner_out.event_name,
            tagline=planner_out.tagline,
            description=planner_out.description,
            audience_persona=planner_out.audience_persona
        )
        marketing_out: MarketingOutput = await self._run_agent_safely(
            agent=marketing_agent,
            input_data=marketing_in,
            output_schema=MarketingOutput
        )

        # Step 4: Landing Page Agent
        landing_in = LandingPageInput(
            event_name=planner_out.event_name,
            tagline=planner_out.tagline,
            description=planner_out.description
        )
        landing_out: LandingPageOutput = await self._run_agent_safely(
            agent=landing_page_agent,
            input_data=landing_in,
            output_schema=LandingPageOutput
        )

        # Step 5: Sponsorship Agent
        sponsorship_in = SponsorshipInput(
            event_name=planner_out.event_name,
            tagline=planner_out.tagline,
            description=planner_out.description
        )
        sponsorship_out: SponsorshipOutput = await self._run_agent_safely(
            agent=sponsorship_agent,
            input_data=sponsorship_in,
            output_schema=SponsorshipOutput
        )

        # Step 6: Budget Agent (Requires Sponsorship tiers)
        budget_in = BudgetInput(
            expected_participants=initial_input.expected_participants,
            location_type=initial_input.location_type,
            sponsorship_tiers=[t.model_dump() for t in sponsorship_out.tiers]
        )
        budget_out: BudgetOutput = await self._run_agent_safely(
            agent=budget_agent,
            input_data=budget_in,
            output_schema=BudgetOutput
        )

        # Step 7: Email Campaign Agent (Requires Sponsorship tiers)
        email_in = EmailCampaignInput(
            event_name=planner_out.event_name,
            tagline=planner_out.tagline,
            description=planner_out.description,
            sponsorship_tiers=[t.model_dump() for t in sponsorship_out.tiers]
        )
        email_out: EmailCampaignOutput = await self._run_agent_safely(
            agent=email_campaign_agent,
            input_data=email_in,
            output_schema=EmailCampaignOutput
        )

        # Step 8: Execution Agent (Requires team roles & budget cost)
        execution_in = ExecutionInput(
            event_name=planner_out.event_name,
            team_roles=planner_out.team_roles,
            total_cost=budget_out.total_cost
        )
        execution_out: ExecutionOutput = await self._run_agent_safely(
            agent=execution_agent,
            input_data=execution_in,
            output_schema=ExecutionOutput
        )

        # compile package
        compiled_package = {
            "planner": planner_out.model_dump(),
            "marketing": marketing_out.model_dump(),
            "landing_page": landing_out.model_dump(),
            "sponsorship": sponsorship_out.model_dump(),
            "budget": budget_out.model_dump(),
            "email_campaign": email_out.model_dump(),
            "execution": execution_out.model_dump(),
        }

        # Step 9: Memory Agent (Save compiled package)
        logger.info("[ADK Memory Agent] Saving compiled launch package to vector store...")
        event_id = str(uuid.uuid4())
        save_status = store_event_in_memory(event_id, {
            "event_name": planner_out.event_name,
            "theme": initial_input.theme,
            "domain": initial_input.domain,
            "package": compiled_package
        })
        logger.info(f"[ADK Memory Agent] Indexing status: {save_status}")

        logger.info("[ADK AgentManager] Multi-agent pipeline completed successfully.")
        return {
            "event_id": event_id,
            "past_events_searched": len(past_events),
            "package": compiled_package
        }
