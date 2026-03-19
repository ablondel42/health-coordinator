"""
Pydantic schemas enforcing strict 1:1 mapping with the canonical JSON schemas.

All models dictate `extra = 'forbid'` to align with json schema `additionalProperties: false`.
SQLAlchemy ORM models map strictly to these definitions.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictBaseModel(BaseModel):
    """Base Pydantic model enforcing that no unknown fields are accepted."""
    model_config = ConfigDict(extra='forbid')

# -- Pydantic Models --

class EvidenceItem(StrictBaseModel):
    type: Literal["file", "command", "test", "config", "log"]
    path: str
    line: Optional[int] = None
    snippet: str

class Finding(StrictBaseModel):
    title: str
    description: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    priority: Literal["P0", "P1", "P2", "P3"]
    evidence: List[EvidenceItem]
    affectedFiles: List[str]
    suggestedFix: str
    autoFixable: bool

class SubagentAuditOutput(StrictBaseModel):
    domain: str
    agentName: str
    score: int = Field(ge=0, le=100)
    findings: List[Finding]

class FixItem(StrictBaseModel):
    taskId: str
    findingId: Optional[str] = None
    status: Literal["applied", "partial", "failed", "skipped"]
    changedFiles: List[str]
    testsRun: List[str]
    patchSummary: str

class SubagentFixOutput(StrictBaseModel):
    domain: str
    agentName: str
    fixes: List[FixItem]

class TaskRecord(StrictBaseModel):
    id: str = Field(pattern=r"^TASK-[0-9]{4,}$")
    sourceType: Literal["finding", "manual"]
    findingId: Optional[str] = None
    manualReason: Optional[str] = None
    domain: str
    title: str = Field(max_length=160)
    description: str = Field(max_length=2000)
    priority: Literal["P0", "P1", "P2", "P3"]
    severity: Optional[Literal["critical", "high", "medium", "low", "info"]] = None
    approvalState: Literal["pending_review", "approved", "rejected", "ignored", "edited"]
    executionState: Literal["not_started", "ready", "in_progress", "done", "failed", "skipped", "cancelled"]
    verificationState: Literal["not_applicable", "pending", "passed", "failed", "partial", "unverifiable"]
    owner: str
    scopeNote: Optional[str] = None
    tags: List[str]

# -- SQLAlchemy ORM Models --

from sqlalchemy import Column, String, JSON
from app.database import Base

class DBTaskRecord(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True) # E.g. TASK-1234
    sourceType = Column(String, nullable=False)
    domain = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    approvalState = Column(String, nullable=False)
    executionState = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    
    # Store complex nested JSON blob safely
    raw_payload = Column(JSON, nullable=False)
