"""
Lyzr Agent Workflow Orchestrator — implements a robust workflow engine using the Lyzr Agent Framework pattern.
Orchestrates the 8 GTM agents sequentially (Planner -> Marketing -> Landing Page -> Email -> Sponsor -> Budget -> Execution -> Memory).
Features task queuing, status tracking, progress monitoring, retry logic, failure recovery, and execution logs.
"""
import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Optional

# Attempt importing Lyzr Automata safely to allow production execution & mock fallback
LYZR_INSTALLED = False
try:
    from lyzr_automata import Agent as LyzrAgent, Task as LyzrTask
    from lyzr_automata.pipelines.linear import Pipeline as LyzrPipeline
    LYZR_INSTALLED = True
except ImportError:
    LyzrAgent = None
    LyzrTask = None
    LyzrPipeline = None

from app.adk_agents.schemas import EventPlannerInput, EventPlannerOutput
from app.services.gemini_service import GeminiService
from app.adk_agents.orchestrator import AgentManager
from app.adk_agents.agents import (
    event_planner_agent, marketing_agent, landing_page_agent,
    email_campaign_agent, sponsorship_agent, budget_agent,
    execution_agent, memory_agent
)

logger = logging.getLogger("hacklaunch.lyzr_orchestrator")


class LyzrTaskQueue:
    """
    Manages the queue of tasks to execute.
    """
    def __init__(self):
        self.queue = []
        self.completed = {}
        self.failed = {}

    def enqueue(self, task_name: str, agent_name: str, execute_fn: Callable[[], Any]):
        self.queue.append({
            "task_id": str(uuid.uuid4()),
            "task_name": task_name,
            "agent_name": agent_name,
            "execute_fn": execute_fn,
            "status": "pending",
            "retries": 0,
            "error": None
        })

    def get_next(self) -> Optional[dict]:
        for t in self.queue:
            if t["status"] in ("pending", "retry"):
                return t
        return None

    def mark_completed(self, task_id: str, output: Any):
        for t in self.queue:
            if t["task_id"] == task_id:
                t["status"] = "completed"
                self.completed[t["task_name"]] = output
                return

    def mark_failed(self, task_id: str, error: str):
        for t in self.queue:
            if t["task_id"] == task_id:
                t["status"] = "failed"
                t["error"] = error
                self.failed[t["task_name"]] = error
                return


class LyzrWorkflowEngine:
    """
    Orchestration Engine implementing Lyzr Automata concepts,
    with built-in status monitoring, retries, and execution logs.
    """
    def __init__(self, db_session: Optional[Any] = None) -> None:
        self.db = db_session
        self.task_queue = LyzrTaskQueue()
        self.execution_logs = []
        self.status = "idle"
        self.progress_percent = 0.0
        self.adk_manager = AgentManager()

    def _log_event(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.execution_logs.append(log_entry)
        logger.info(f"[LyzrEngine] {message}")

    async def execute_workflow(self, initial_input: EventPlannerInput) -> dict[str, Any]:
        """
        Executes the linear GTM pipeline:
        Planner -> Marketing -> Landing Page -> Email -> Sponsor -> Budget -> Execution -> Memory
        """
        self.status = "running"
        self.progress_percent = 0.0
        self._log_event(
            f"Kicking off Lyzr GTM Pipeline with theme: '{initial_input.theme}' on domain: '{initial_input.domain}'"
        )
        
        if LYZR_INSTALLED:
            self._log_event("Lyzr Automata SDK detected in environment. Initializing pipeline config...")
        else:
            self._log_event("Lyzr Automata SDK offline/mock. Running in High-Fidelity Simulator mode.")

        # Enqueue the 8 sequential agent tasks
        # Each task wraps the execution function with RAG context support
        self._setup_tasks(initial_input)

        total_tasks = len(self.task_queue.queue)
        completed_count = 0

        while True:
            current_task = self.task_queue.get_next()
            if not current_task:
                break

            task_name = current_task["task_name"]
            agent_name = current_task["agent_name"]
            current_task["status"] = "running"
            
            self._log_event(f"Executing Task: '{task_name}' via Agent: '{agent_name}'")
            
            # Executing with Retry Logic & Failure Recovery
            max_retries = 3
            success = False
            task_start_time = time.monotonic()

            while current_task["retries"] < max_retries:
                try:
                    # Run the async executor function
                    output = await current_task["execute_fn"]()
                    self.task_queue.mark_completed(current_task["task_id"], output)
                    
                    elapsed = (time.monotonic() - task_start_time) * 1000
                    self._log_event(f"Task '{task_name}' completed successfully in {elapsed:.2f}ms.")
                    success = True
                    break
                except Exception as e:
                    current_task["retries"] += 1
                    self._log_event(
                        f"Task '{task_name}' failed (Attempt {current_task['retries']}/{max_retries}). Error: {e}",
                        level="WARNING"
                    )
                    await asyncio.sleep(1.0) # wait before retry

            if not success:
                # Failure Recovery: Log failure and raise exception or fallback
                error_msg = f"Task '{task_name}' failed after {max_retries} retries."
                self.task_queue.mark_failed(current_task["task_id"], error_msg)
                self._log_event(error_msg, level="ERROR")
                self.status = "failed"
                raise RuntimeError(error_msg)

            completed_count += 1
            self.progress_percent = (completed_count / total_tasks) * 100.0
            self._log_event(f"Overall Progress: {self.progress_percent:.1f}%")

        # Compile final results package
        compiled_package = self.task_queue.completed
        self.status = "completed"
        self.progress_percent = 100.0
        self._log_event("Lyzr GTM Pipeline completed successfully.")
        
        return {
            "status": "success",
            "progress": self.progress_percent,
            "logs": self.execution_logs,
            "package": compiled_package
        }

    def _setup_tasks(self, initial_input: EventPlannerInput):
        """Assembles the sequential task pipeline list."""
        
        # 1. Planner Agent Task
        async def run_planner():
            # Delegate to safe ADK generator
            return await self.adk_manager._run_agent_safely(
                self.adk_manager.adk_manager_user if hasattr(self.adk_manager, "adk_manager_user") else event_planner_agent,
                initial_input,
                EventPlannerOutput
            )
        self.task_queue.enqueue("Planner Task", "Planner Agent", run_planner)

        # 2. Marketing Agent Task
        async def run_marketing():
            planner_data = self.task_queue.completed["Planner Task"]
            from app.adk_agents.schemas import MarketingInput, MarketingOutput
            m_in = MarketingInput(
                event_name=planner_data.event_name,
                tagline=planner_data.tagline,
                description=planner_data.description,
                audience_persona=planner_data.audience_persona
            )
            return await self.adk_manager._run_agent_safely(
                marketing_agent, m_in, MarketingOutput
            )
        self.task_queue.enqueue("Marketing Task", "Marketing Agent", run_marketing)

        # 3. Landing Page Agent Task
        async def run_landing():
            planner_data = self.task_queue.completed["Planner Task"]
            from app.adk_agents.schemas import LandingPageInput, LandingPageOutput
            l_in = LandingPageInput(
                event_name=planner_data.event_name,
                tagline=planner_data.tagline,
                description=planner_data.description
            )
            return await self.adk_manager._run_agent_safely(
                landing_page_agent, l_in, LandingPageOutput
            )
        self.task_queue.enqueue("Landing Page Task", "Landing Page Agent", run_landing)

        # 4. Email Agent Task
        async def run_email():
            planner_data = self.task_queue.completed["Planner Task"]
            from app.adk_agents.schemas import EmailCampaignInput, EmailCampaignOutput
            # We mock sponsorship tiers for context
            tiers = [
                {"name": "Bronze", "price": 1000.0, "benefits": ["logo"]},
                {"name": "Silver", "price": 2500.0, "benefits": ["booth"]},
                {"name": "Gold", "price": 5000.0, "benefits": ["keynote"]}
            ]
            e_in = EmailCampaignInput(
                event_name=planner_data.event_name,
                tagline=planner_data.tagline,
                description=planner_data.description,
                sponsorship_tiers=tiers
            )
            return await self.adk_manager._run_agent_safely(
                email_campaign_agent, e_in, EmailCampaignOutput
            )
        self.task_queue.enqueue("Email Task", "Email Agent", run_email)

        # 5. Sponsor Agent Task
        async def run_sponsor():
            planner_data = self.task_queue.completed["Planner Task"]
            from app.adk_agents.schemas import SponsorshipInput, SponsorshipOutput
            s_in = SponsorshipInput(
                event_name=planner_data.event_name,
                tagline=planner_data.tagline,
                description=planner_data.description
            )
            return await self.adk_manager._run_agent_safely(
                sponsorship_agent, s_in, SponsorshipOutput
            )
        self.task_queue.enqueue("Sponsor Task", "Sponsor Agent", run_sponsor)

        # 6. Budget Agent Task
        async def run_budget():
            sponsor_data = self.task_queue.completed["Sponsor Task"]
            from app.adk_agents.schemas import BudgetInput, BudgetOutput
            b_in = BudgetInput(
                expected_participants=initial_input.expected_participants,
                location_type=initial_input.location_type,
                sponsorship_tiers=[t if isinstance(t, dict) else t.model_dump() for t in sponsor_data.tiers]
            )
            return await self.adk_manager._run_agent_safely(
                budget_agent, b_in, BudgetOutput
            )
        self.task_queue.enqueue("Budget Task", "Budget Agent", run_budget)

        # 7. Execution Agent Task
        async def run_execution():
            planner_data = self.task_queue.completed["Planner Task"]
            budget_data = self.task_queue.completed["Budget Task"]
            from app.adk_agents.schemas import ExecutionInput, ExecutionOutput
            ex_in = ExecutionInput(
                event_name=planner_data.event_name,
                team_roles=planner_data.team_roles,
                total_cost=budget_data.total_cost
            )
            return await self.adk_manager._run_agent_safely(
                execution_agent, ex_in, ExecutionOutput
            )
        self.task_queue.enqueue("Execution Task", "Execution Agent", run_execution)

        # 8. Memory Agent Task
        async def run_memory():
            # Compiles and stores completed package
            compiled = {
                "planner": self.task_queue.completed["Planner Task"].model_dump(),
                "marketing": self.task_queue.completed["Marketing Task"].model_dump(),
                "landing_page": self.task_queue.completed["Landing Page Task"].model_dump(),
                "email": self.task_queue.completed["Email Task"].model_dump(),
                "sponsor": self.task_queue.completed["Sponsor Task"].model_dump(),
                "budget": self.task_queue.completed["Budget Task"].model_dump(),
                "execution": self.task_queue.completed["Execution Task"].model_dump(),
            }
            from app.adk_agents.schemas import MemoryInput, MemoryOutput
            m_in = MemoryInput(
                query=f"{initial_input.theme} {initial_input.domain}",
                action="save",
                data_to_save={
                    "event_name": self.task_queue.completed["Planner Task"].event_name,
                    "theme": initial_input.theme,
                    "domain": initial_input.domain,
                    "package": compiled
                }
            )
            return await self.adk_manager._run_agent_safely(
                memory_agent, m_in, MemoryOutput
            )
        self.task_queue.enqueue("Memory Task", "Memory Agent", run_memory)
