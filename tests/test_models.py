"""
Tests to ensure Pydantic boundaries refuse invalid JSON schemas.
"""
import pytest
from pydantic import ValidationError
from app.models import SubagentAuditOutput

def test_subagent_output_rejects_hallucinated_properties() -> None:
    """
    Prove that Pydantic enforces additionalProperties: false.
    If an LLM hallucinates extra fields, it should crash the ingestion step.
    """
    corrupt_llm_payload = {
        "domain": "documentation",
        "agentName": "Docs Auditor",
        "score": 100,
        "findings": [],
        "hallucinated_extra_field": "LLM garbage"
    }
    
    with pytest.raises(ValidationError) as validation_exception_info:
        SubagentAuditOutput.model_validate(corrupt_llm_payload)
        
    assert "hallucinated_extra_field" in str(validation_exception_info.value), "Strict model incorrectly allowed extra fields."

def test_subagent_output_accepts_perfect_schema() -> None:
    """
    Verify standard pass case for validation bounds.
    """
    valid_llm_payload = {
        "domain": "documentation",
        "agentName": "Docs Auditor",
        "score": 100,
        "findings": []
    }
    validated_schema_model = SubagentAuditOutput.model_validate(valid_llm_payload)
    assert validated_schema_model.domain == "documentation"
