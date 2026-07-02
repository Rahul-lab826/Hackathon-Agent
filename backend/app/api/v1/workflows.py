"""
Workflow API Routes — exposes endpoints to run and track Lyzr workflows.
"""
import uuid
import asyncio
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from app.core.guards import get_current_active_user
from app.models.user import User
from app.services.lyzr_orchestrator import LyzrWorkflowEngine
from app.adk_agents.schemas import EventPlannerInput

router = APIRouter(prefix="/workflows", tags=["Workflows Orchestration"])

# Global dictionary to track active/completed workflow engine states in memory
WORKFLOW_JOBS: dict[str, LyzrWorkflowEngine] = {}
WORKFLOW_RESULTS: dict[str, dict[str, Any]] = {}


class StartLyzrWorkflowRequest(BaseModel):
    theme: str
    domain: str
    duration_hours: int
    audience_type: str
    expected_participants: int
    location_type: str


@router.post(
    "/lyzr/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger GTM Launch Package generation using Lyzr Agent Framework",
)
async def run_lyzr_workflow(
    payload: StartLyzrWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Spawns the Lyzr sequential workflow as a background execution.
    Returns a workflow_id to monitor status and fetch logs.
    """
    workflow_id = str(uuid.uuid4())
    engine = LyzrWorkflowEngine()
    WORKFLOW_JOBS[workflow_id] = engine

    # Convert request to ADK EventPlannerInput schema for consistency
    initial_input = EventPlannerInput(
        theme=payload.theme,
        domain=payload.domain,
        duration_hours=payload.duration_hours,
        audience_type=payload.audience_type,
        expected_participants=payload.expected_participants,
        location_type=payload.location_type
    )

    # Define background execution task
    async def _execute_job():
        try:
            res = await engine.execute_workflow(initial_input)
            WORKFLOW_RESULTS[workflow_id] = res
        except Exception as err:
            WORKFLOW_RESULTS[workflow_id] = {
                "status": "error",
                "message": f"Execution failed: {err}",
                "logs": engine.execution_logs,
                "package": {}
            }

    background_tasks.add_task(_execute_job)

    return {
        "status": "accepted",
        "workflow_id": workflow_id,
        "message": "Lyzr workflow pipeline started in the background.",
        "status_url": f"/api/v1/workflows/lyzr/{workflow_id}"
    }


@router.get(
    "/lyzr/{workflow_id}",
    summary="Retrieve status, progress, logs, and outputs of a Lyzr workflow",
)
async def get_lyzr_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Checks the status of the Lyzr workflow. Returns intermediate progress percent and execution logs.
    """
    engine = WORKFLOW_JOBS.get(workflow_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow job with id '{workflow_id}' not found."
        )

    # Return completed details if done
    result = WORKFLOW_RESULTS.get(workflow_id)
    
    # Structure the status response
    response_data = {
        "workflow_id": workflow_id,
        "status": engine.status if not result else result.get("status"),
        "progress": engine.progress_percent if not result else result.get("progress", 100.0),
        "logs": engine.execution_logs,
        "results": {}
    }

    if result:
        # If the result model dumps exist, serialize them safely
        pkg = result.get("package", {})
        serialized_package = {}
        for key, val in pkg.items():
            if hasattr(val, "model_dump"):
                serialized_package[key] = val.model_dump()
            else:
                serialized_package[key] = val
        response_data["results"] = serialized_package
        if "message" in result:
            response_data["error_message"] = result["message"]

    return response_data
