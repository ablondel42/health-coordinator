"""
API routes module.

Exports all route routers for inclusion in the main FastAPI application.
"""
from app.api.routes_tasks import router as tasks_router
from app.api.routes_runs import router as runs_router
from app.api.routes_approval import router as approval_router

__all__ = ["tasks_router", "runs_router", "approval_router"]
