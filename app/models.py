"""
Pydantic models and SQLAlchemy ORM.

Enforces strict schema validation with `extra='forbid'`.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, String, JSON

from app.database import Base


class StrictBaseModel(BaseModel):
    """Base model that rejects unknown fields."""
    model_config = ConfigDict(extra='forbid')


class EvidenceItem(StrictBaseModel):
    """Evidence for a finding."""
    type: Literal["file", "command", "test", "config", "log"]
    path: str
    line: Optional[int] = None
    snippet: str


class Finding(StrictBaseModel):
    """An audit finding (issue)."""
    title: str
    description: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    priority: Literal["P0", "P1", "P2", "P3"]
    evidence: List[EvidenceItem]
    affectedFiles: List[str]
    suggestedFix: str
    autoFixable: bool


class SubagentAuditOutput(StrictBaseModel):
    """Output from an audit subagent."""
    domain: str
    agentName: str
    score: int = Field(ge=0, le=100)
    findings: List[Finding]


class FixItem(StrictBaseModel):
    """A fix applied by a subagent."""
    taskId: str
    findingId: Optional[str] = None
    status: Literal["applied", "partial", "failed", "skipped"]
    changedFiles: List[str]
    testsRun: List[str]
    patchSummary: str


class SubagentFixOutput(StrictBaseModel):
    """Output from a fix subagent."""
    domain: str
    agentName: str
    fixes: List[FixItem]


class TaskRecord(StrictBaseModel):
    """A task record."""
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


class DBTaskRecord(Base):
    """SQLAlchemy model for task storage."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    sourceType = Column(String, nullable=False)
    domain = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    approvalState = Column(String, nullable=False)
    executionState = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    raw_payload = Column(JSON, nullable=False)
