"""
Approval gate API routes.

Handles user review and approval of tasks before fixes are applied.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models import DBTaskRecord

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Approval"])


@router.get("/approval")
def get_pending_approvals(db: Session = Depends(get_db_session)) -> list[dict]:
    """Get all tasks pending user approval."""
    try:
        records = db.query(DBTaskRecord).filter_by(approvalState="pending_review").all()
        logger.info(f"Retrieved {len(records)} tasks pending approval")
        return [record.raw_payload for record in records]
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to get pending approvals.")


@router.post("/tasks/{taskId}/approve")
def approve_task(taskId: str, db: Session = Depends(get_db_session)) -> dict:
    """Approve a task for the fix phase."""
    try:
        record = db.query(DBTaskRecord).filter_by(id=taskId).first()
        if not record:
            logger.warning(f"Task not found for approval: {taskId}")
            raise HTTPException(status_code=404, detail="Task not found.")

        payload = record.raw_payload
        payload["approvalState"] = "approved"
        record.raw_payload = payload
        record.approvalState = "approved"

        db.commit()
        logger.info(f"Task approved: {taskId}")
        return {"status": "approved", "taskId": taskId}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to approve task {taskId}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to approve task.")


@router.post("/tasks/{taskId}/ignore")
def ignore_task(taskId: str, db: Session = Depends(get_db_session)) -> dict:
    """Mark a task as ignored (will not be fixed)."""
    try:
        record = db.query(DBTaskRecord).filter_by(id=taskId).first()
        if not record:
            logger.warning(f"Task not found for ignore: {taskId}")
            raise HTTPException(status_code=404, detail="Task not found.")

        payload = record.raw_payload
        payload["approvalState"] = "ignored"
        record.raw_payload = payload
        record.approvalState = "ignored"

        db.commit()
        logger.info(f"Task ignored: {taskId}")
        return {"status": "ignored", "taskId": taskId}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ignore task {taskId}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to ignore task.")
