"""
API routes for explicit Task CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import fetch_transactional_database_session
from app.models import DBTaskRecord, TaskRecord

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Detailed REST Endpoints logic as mapped in spec...
@router.post("", response_model=TaskRecord)
def manual_task_creation_endpoint(payload: TaskRecord, db: Session = Depends(fetch_transactional_database_session)):
    """Manually creates a new Task record mapped centrally."""
    existing_record = db.query(DBTaskRecord).filter_by(id=payload.id).first()
    if existing_record:
        raise HTTPException(status_code=400, detail="Task ID perfectly collides. Already mapped bounds.")
        
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
    return db_record.raw_payload

@router.get("", response_model=List[TaskRecord])
def poll_tasks_list_filtered(
    domain: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    db: Session = Depends(fetch_transactional_database_session)
):
    """Provides filtered global polling for the Task database block securely via SQLite mapping."""
    compiled_database_query = db.query(DBTaskRecord)
    if domain:
        compiled_database_query = compiled_database_query.filter_by(domain=domain)
    if state:
        compiled_database_query = compiled_database_query.filter_by(executionState=state)
        
    extracted_database_records = compiled_database_query.all()
    return [mapped_record_dictionary.raw_payload for mapped_record_dictionary in extracted_database_records]

@router.get("/{taskId}", response_model=TaskRecord)
def fetch_task_payload_dynamically_single(taskId: str, db: Session = Depends(fetch_transactional_database_session)):
    """Fetch exact metadata block cleanly exposing raw JSON dictionaries mapping strictly."""
    locked_active_database_record = db.query(DBTaskRecord).filter_by(id=taskId).first()
    if not locked_active_database_record:
        raise HTTPException(status_code=404, detail="Requested Task ID bounds not cleanly mapped globally.")
    return locked_active_database_record.raw_payload

@router.delete("/{taskId}")
def destroy_task_record_securely_globally(taskId: str, db: Session = Depends(fetch_transactional_database_session)):
    """Wipes the database mapping natively ensuring atomic rollbacks prevent leaks cleanly."""
    locked_active_database_record = db.query(DBTaskRecord).filter_by(id=taskId).first()
    if not locked_active_database_record:
        raise HTTPException(status_code=404, detail="Task bounds unmapped.")
    db.delete(locked_active_database_record)
    db.commit()
    return {"status": "destroyed", "taskId": taskId}
