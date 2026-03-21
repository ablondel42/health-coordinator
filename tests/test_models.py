"""
Tests Pydantic schema validation.

Verifies that invalid JSON schemas are rejected.
"""
import pytest
from pydantic import ValidationError

from app.models import SubagentAuditOutput


def test_model_rejects_extra_fields():
    """Verify Pydantic enforces additionalProperties: false."""
    invalid_payload = {
        "domain": "documentation",
        "agentName": "Docs Auditor",
        "score": 100,
        "findings": [],
        "extra_field": "should be rejected"
    }

    with pytest.raises(ValidationError) as exc_info:
        SubagentAuditOutput.model_validate(invalid_payload)

    assert "extra_field" in str(exc_info.value)


def test_model_accepts_valid_payload():
    """Verify valid payloads pass validation."""
    valid_payload = {
        "domain": "documentation",
        "agentName": "Docs Auditor",
        "score": 100,
        "findings": []
    }

    result = SubagentAuditOutput.model_validate(valid_payload)
    assert result.domain == "documentation"
    assert result.score == 100
