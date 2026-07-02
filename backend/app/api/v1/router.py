"""API v1 Router — aggregates all sub-routers into a single APIRouter."""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.organizations import router as orgs_router
from app.api.v1.teams import router as teams_router
from app.api.v1.events import router as events_router
from app.api.v1.generation import router as generation_router
from app.api.v1.agents import router as agents_router
from app.api.v1.export import router as export_router
from app.api.v1.gemini import router as gemini_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.memory import router as memory_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(orgs_router)
api_router.include_router(teams_router)
api_router.include_router(events_router)
api_router.include_router(generation_router)
api_router.include_router(agents_router)
api_router.include_router(export_router)
api_router.include_router(gemini_router)
api_router.include_router(workflows_router)
api_router.include_router(memory_router)
