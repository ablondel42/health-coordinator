"""
Swarm execution control API routes.
"""
from fastapi import APIRouter
import uuid

router = APIRouter(prefix="/runs", tags=["Swarm Controls"])


@router.post("")
async def start_audit_swarm() -> dict:
    """Start a new audit swarm execution."""
    run_id = str(uuid.uuid4())
    return {"message": "Audit swarm started.", "runId": run_id}


@router.get("/active")
def get_active_swarm_status() -> dict:
    """Get status of active subagent executions."""
    return {"activeSubagents": 0, "status": "idle"}
