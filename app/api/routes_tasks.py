"""
Task CRUD API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db_session
from app.models import DBTaskRecord, TaskRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskRecord)
def create_task(payload: TaskRecord, db: Session = Depends(get_db_session)) -> dict:
    """Create a new task."""
    try:
        existing = db.query(DBTaskRecord).filter_by(id=payload.id).first()
        if existing:
            logger.warning(f"Task creation failed - ID already exists: {payload.id}")
            raise HTTPException(status_code=400, detail="Task ID already exists.")

        db_record = DBTaskRecord(
            id=payload.id,
            sourceType=payload.sourceType,
            domain=payload.domain,
            title=payload.title,
            priority=payload.priority,
            approvalState=payload.approvalState,
            executionState=payload.executionState,
            owner=payload.owner,
            raw_payload=payload.model_dump()
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        logger.info(f"Task created: {payload.id}, domain={payload.domain}, priority={payload.priority}")
        return db_record.raw_payload
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create task {payload.id}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to create task.")


@router.get("", response_model=List[TaskRecord])
def list_tasks(
    domain: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
) -> List[dict]:
    """List tasks with optional domain and state filters."""
    try:
        query = db.query(DBTaskRecord)
        filters = []
        if domain:
            query = query.filter_by(domain=domain)
            filters.append(f"domain={domain}")
        if state:
            query = query.filter_by(executionState=state)
            filters.append(f"state={state}")

        records = query.all()
        logger.info(f"Listed {len(records)} tasks with filters: {filters}")
        return [record.raw_payload for record in records]
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to list tasks.")


@router.get("/{taskId}", response_model=TaskRecord)
def get_task(taskId: str, db: Session = Depends(get_db_session)) -> dict:
    """Get a single task by ID."""
    try:
        record = db.query(DBTaskRecord).filter_by(id=taskId).first()
        if not record:
            logger.warning(f"Task not found: {taskId}")
            raise HTTPException(status_code=404, detail="Task not found.")
        
        logger.info(f"Retrieved task: {taskId}")
        return record.raw_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {taskId}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to get task.")


@router.delete("/{taskId}")
def delete_task(taskId: str, db: Session = Depends(get_db_session)) -> dict:
    """Delete a task."""
    try:
        record = db.query(DBTaskRecord).filter_by(id=taskId).first()
        if not record:
            logger.warning(f"Task not found for deletion: {taskId}")
            raise HTTPException(status_code=404, detail="Task not found.")

        db.delete(record)
        db.commit()
        logger.info(f"Task deleted: {taskId}")
        return {"status": "deleted", "taskId": taskId}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete task {taskId}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail="Failed to delete task.")
