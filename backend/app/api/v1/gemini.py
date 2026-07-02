"""
Gemini API Routes — exposes endpoints to run structured generation, 
track token metrics, and stream real-time completions.
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.guards import get_current_active_user
from app.models.user import User
from app.services.gemini_service import GeminiService
from app.services.prompt_manager import PromptManager
from app.schemas.gemini_schemas import (
    EventPlanningSchema, LandingPageSchema, MarketingSchema,
    EmailCampaignSchema, SponsorshipSchema, BudgetSchema,
    TimelineSchema, VolunteerPlansSchema
)

router = APIRouter(prefix="/gemini", tags=["Gemini AI"])
gemini_service = GeminiService()


class GeminiGenerateRequest(BaseModel):
    template_key: str
    parameters: dict[str, Any]
    use_pro: bool = False
    rag_query: Optional[str] = None
    session_id: Optional[str] = None


class GeminiStreamRequest(BaseModel):
    prompt: str
    use_pro: bool = False
    rag_query: Optional[str] = None
    session_id: Optional[str] = None


@router.post(
    "/generate",
    summary="Generate strictly structured GTM package component outputs matching Pydantic schemas",
)
async def generate_structured_gtm(
    payload: GeminiGenerateRequest,
    current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Renders the specified template and requests Gemini to respond matching the schema.
    Supported template_keys: event_planning, landing_pages, marketing, email_campaigns,
    sponsorship, budget, timeline, volunteer_plans.
    """
    # 1. Resolve prompt template
    try:
        prompt = PromptManager.render(payload.template_key, **payload.parameters)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template key '{payload.template_key}' is invalid or unsupported."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to render prompt: {e}"
        )

    # 2. Map template key to response schema
    schema_map = {
        "event_planning": EventPlanningSchema,
        "landing_pages": LandingPageSchema,
        "marketing": MarketingSchema,
        "email_campaigns": EmailCampaignSchema,
        "sponsorship": SponsorshipSchema,
        "budget": BudgetSchema,
        "timeline": TimelineSchema,
        "volunteer_plans": VolunteerPlansSchema,
    }
    schema_cls = schema_map.get(payload.template_key)
    if not schema_cls:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No validation schema mapped for template key '{payload.template_key}'"
        )

    # 3. Call GeminiService
    res = await gemini_service.generate_json(
        prompt=prompt,
        response_schema=schema_cls,
        system_instruction=PromptManager.SYSTEM_INSTRUCTION,
        use_pro=payload.use_pro,
        rag_query=payload.rag_query,
        session_id=payload.session_id
    )
    return res


@router.post(
    "/stream",
    summary="Asynchronously stream text responses from Gemini",
)
async def stream_gemini_completions(
    payload: GeminiStreamRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Standard completion endpoint returning an SSE stream of text fragments.
    """
    async def event_generator():
        async for chunk in gemini_service.generate_stream(
            prompt=payload.prompt,
            system_instruction=PromptManager.SYSTEM_INSTRUCTION,
            use_pro=payload.use_pro,
            rag_query=payload.rag_query,
            session_id=payload.session_id
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@router.get(
    "/metrics",
    summary="Get global token usage statistics and tracking",
)
async def get_token_metrics(
    current_user: User = Depends(get_current_active_user)
) -> dict[str, int]:
    """Returns total tokens consumed by all backend services during the runtime."""
    metrics = await GeminiService.get_metrics()
    return metrics
