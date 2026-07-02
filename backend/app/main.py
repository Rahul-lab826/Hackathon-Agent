"""
FastAPI Application Entry Point — assembles all middleware, routes, and lifecycle events.
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.v1.router import api_router
from app.config import settings
from app.database import engine
from app.middleware.logging_middleware import RequestLoggingMiddleware

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("hacklaunch")


# ─── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("🚀 HackLaunch AI backend starting up...")
    logger.info("📦 Environment: %s", settings.APP_ENV)
    yield
    logger.info("🛑 HackLaunch AI backend shutting down...")
    await engine.dispose()


# ─── App Factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="HackLaunch AI — Multi-Agent Hackathon GTM Platform",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — outermost applied last) ──────────────────
    # 1. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    # 2. Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Exception Handlers ────────────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return structured validation errors instead of FastAPI's default."""
        errors = [
            {
                "field": " → ".join(str(loc) for loc in e["loc"][1:]),
                "message": e["msg"],
                "type": e["type"],
            }
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed.", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler — masks internal errors in production."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        if settings.is_production:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An internal server error occurred."},
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    # ── Health Check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check() -> dict:
        status_info = {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "checks": {
                "database": "unknown",
                "redis": "unknown",
                "qdrant": "unknown"
            }
        }
        # Check DB
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            status_info["checks"]["database"] = "connected"
        except Exception as e:
            status_info["checks"]["database"] = f"offline: {e}"
            status_info["status"] = "degraded"
            
        # Check Redis
        try:
            from app.services.cache_service import CacheService
            cache = CacheService()
            if cache.redis_client:
                await cache.redis_client.ping()
                status_info["checks"]["redis"] = "connected"
            else:
                status_info["checks"]["redis"] = "running_in_fallback_memory_mode"
        except Exception as e:
            status_info["checks"]["redis"] = f"offline: {e}"
            status_info["status"] = "degraded"

        # Check Qdrant
        try:
            from app.services.memory.qdrant_client_service import QdrantClientService
            qdrant = QdrantClientService()
            status_info["checks"]["qdrant"] = "connected_or_mock_active"
        except Exception as e:
            status_info["checks"]["qdrant"] = f"offline: {e}"

        return status_info

    return app


app = create_app()
