"""
API endpoints managing User Validation Gates before executing unsafe fix patches.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import fetch_transactional_database_session
from app.models import DBTaskRecord

router = APIRouter(prefix="", tags=["Approval"])

@router.get("/approval")
def pull_tasks_blocked_by_user_guard_states(db: Session = Depends(fetch_transactional_database_session)):
    """Queries any Task structurally requiring Human-in-the-Loop review gates definitively prior processing loop injections natively."""
    blocked_database_records_tracked = db.query(DBTaskRecord).filter_by(approvalState="pending_review").all()
    return [db_mapped_record.raw_payload for db_mapped_record in blocked_database_records_tracked]

@router.post("/tasks/{taskId}/approve")
def unblock_task_approval_gate_safely(taskId: str, db: Session = Depends(fetch_transactional_database_session)):
    """Move State Machine correctly strictly mapping parameters into `approved` to safely execute patches properly seamlessly tracking bounds dynamically."""
    mapped_database_record_target = db.query(DBTaskRecord).filter_by(id=taskId).first()
    if not mapped_database_record_target:
        raise HTTPException(status_code=404, detail="Unmapped Task schema context bounds failure loop.")
        
    extracted_database_dictionary = mapped_database_record_target.raw_payload
    extracted_database_dictionary["approvalState"] = "approved"
    
    mapped_database_record_target.raw_payload = extracted_database_dictionary
    mapped_database_record_target.approvalState = "approved"
    
    db.commit()
    return {"status": "approved", "taskId": taskId}

@router.post("/tasks/{taskId}/ignore")
def suppress_task_from_workspace_actively_permanent(taskId: str, db: Session = Depends(fetch_transactional_database_session)):
    """Mark strictly purely natively as `ignored` blocking fix application pipeline natively tracking schemas permanently reliably."""
    mapped_database_record_target = db.query(DBTaskRecord).filter_by(id=taskId).first()
    if not mapped_database_record_target:
        raise HTTPException(status_code=404, detail="Unmapped context bounds.")
        
    extracted_database_dictionary = mapped_database_record_target.raw_payload
    extracted_database_dictionary["approvalState"] = "ignored"
    
    mapped_database_record_target.raw_payload = extracted_database_dictionary
    mapped_database_record_target.approvalState = "ignored"
    
    db.commit()
    return {"status": "ignored", "taskId": taskId}
