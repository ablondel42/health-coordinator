"""
FastAPI application entry point for the Health Coordinator.

Initializes the strict global logger, sets up exception handlers,
and bootstraps the high-level ASGI application.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.logger import setup_global_logger, get_module_logger
from app.config import settings

# 1. Initialize militant required logging format
setup_global_logger()
logger = get_module_logger(__name__)

# 2. Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Orchestrates Qwen Code CLI subagents to audit and fix the native repository."
)

@app.exception_handler(Exception)
async def map_global_exception_to_json_response(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all global Exception Handler to enforce the Zero-Tolerance error policy.
    
    Prevents silent crashes from taking down the API layer, guaranteeing that the 
    raw exception payload is stringified and bubbled to the trace logger.
    
    Args:
        request (Request): Starlette Request underlying object.
        exc (Exception): The unhandled exception raised arbitrarily.
        
    Returns:
        JSONResponse: Clean 500 error mapped down for HTTP clients.
    """
    error_message_context = f"Unhandled exception raised during HTTP request {request.method} {request.url}"
    logger.error(f"{error_message_context} - Payload details: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal orchestration error occurred. Check backend logs for stack trace."}
    )

@app.on_event("startup")
async def execute_startup_lifecycle_event() -> None:
    """
    Executes immediately when Uvicorn boots the server.
    """
    logger.info("Health Coordinator API Server is booting up...")

@app.get("/health")
async def perform_server_health_check() -> dict[str, str]:
    """
    Provides a baseline indicator for the CLI/proxy that the web application is alive.
    
    Returns:
        dict[str, str]: Basic ok status message.
    """
    return {"status": "ok", "app": settings.app_title}
