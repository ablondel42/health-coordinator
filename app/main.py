"""
FastAPI application entry point.

Initializes logging, exception handlers, and routes.
Includes middleware-level error handling for complete observability.
"""
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.logger import setup_global_logger, get_logger
from app.logging_context import setup_context_filter, log_context
from app.config import settings
from app.database import Base, engine

from app.api import tasks_router, runs_router, approval_router

setup_global_logger()
setup_context_filter()
logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    
    Includes explicit error handling to ensure failures are logged.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # XSS protection (legacy but still useful)
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions policy (disable unnecessary features)
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            
            # Cache control for API responses
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            
            return response
            
        except Exception as e:
            # Log middleware errors explicitly - they won't hit global handler
            logger.error(f"SecurityHeadersMiddleware failed: {e}", exc_info=e)
            raise  # Re-raise to be handled by RequestLoggerMiddleware


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Add request ID and logging to all requests.
    
    Wraps request processing in try/except to ensure all errors are logged,
    including those that occur in other middleware or route handlers.
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = None

        try:
            start_time = time.time()
            
            with log_context(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                client_host=request.client.host if request.client else "unknown"
            ):
                try:
                    response = await call_next(request)
                except Exception as route_error:
                    # Exception from route handlers or downstream middleware
                    logger.error(
                        f"Request failed: {request.method} {request.url.path}",
                        exc_info=route_error,
                        extra={
                            "request_id": request_id,
                            "status_code": 500,
                        }
                    )
                    raise

                elapsed_ms = int((time.time() - start_time) * 1000)

                # Log successful requests
                logger.info(
                    f"Request completed: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "elapsed_ms": elapsed_ms,
                    }
                )
                
                response.headers["X-Request-ID"] = request_id
                return response
                
        except Exception as e:
            # Catch-all for any exception not handled above
            elapsed_ms = int((time.time() - start_time) * 1000) if start_time else 0
            
            logger.error(
                f"Request middleware failed: {request.method} {request.url.path}",
                exc_info=e,
                extra={
                    "request_id": request_id,
                    "elapsed_ms": elapsed_ms,
                }
            )
            raise  # Let FastAPI handle the response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for application startup and shutdown.
    
    Replaces deprecated @app.on_event("startup") pattern.
    """
    # Startup
    logger.info("Application startup: creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown: cleaning up resources...")
    # Add any cleanup logic here (e.g., close DB connections)
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Orchestrates Qwen Code CLI subagents to audit repositories.",
    lifespan=lifespan,
)

# Add middleware in reverse order of execution:
# 1. RequestLoggerMiddleware (outermost - sees all requests/responses)
# 2. SecurityHeadersMiddleware (innermost - closest to routes)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(tasks_router)
app.include_router(runs_router)
app.include_router(approval_router)


@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for route-level errors.
    
    Note: Middleware exceptions are handled within their own dispatch methods.
    This handler catches exceptions from route handlers only.
    """
    # Extract request_id from headers if available
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    logger.error(
        f"Unhandled exception in route handler: {request.method} {request.url}",
        exc_info=exc,
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred.",
            "request_id": request_id if request_id != "unknown" else None,
        }
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "app": settings.app_title}
