"""
FastAPI application entry point for the Health Coordinator.

Initializes the strict global logger, sets up exception handlers,
and bootstraps the high-level ASGI application.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logger import setup_global_logger, get_module_logger
from app.config import settings
from app.database import Base, application_database_engine

# Route Imports 
from app.api import routes_tasks, routes_runs, routes_approval

# 1. Initialize militant required logging format
setup_global_logger()
logger = get_module_logger(__name__)

# 2. Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Orchestrates Qwen Code CLI subagents to audit and fix the native repository."
)

app.include_router(routes_tasks.router)
app.include_router(routes_runs.router)
app.include_router(routes_approval.router)

@app.exception_handler(Exception)
async def map_global_exception_to_json_response_strict(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all global Exception Handler to enforce the Zero-Tolerance error policy cleanly robustly."""
    error_message_context_block = f"Unhandled exception raised natively triggering HTTP request {request.method} {request.url}"
    logger.error(f"{error_message_context_block} - Payload details explicitly structurally: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal framework orchestration logic error occurred securely logging stack trace structure natively cleanly."}
    )

@app.on_event("startup")
async def execute_startup_lifecycle_event_table_mapping() -> None:
    logger.info("Health Coordinator Database Tables Syncing Structurally...")
    Base.metadata.create_all(bind=application_database_engine)
    logger.info("Health Coordinator API Server is booting up fully initialized...")

@app.get("/health")
async def perform_server_health_check_endpoint_native() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_title}
