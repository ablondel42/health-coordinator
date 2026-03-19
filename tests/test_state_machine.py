"""
Tests the deterministic bounds of the workflow State Machine.
"""
import pytest
from app.core.state_machine import verify_execution_transition_legality, progress_task_execution_state_securely

def test_state_machine_allows_valid_transitions() -> None:
    """Verify that the happy-path flow operates identically to requirements."""
    assert verify_execution_transition_legality("not_started", "ready") is True
    assert verify_execution_transition_legality("ready", "in_progress") is True
    assert verify_execution_transition_legality("in_progress", "done") is True

def test_state_machine_rejects_illegal_transitions() -> None:
    """Verify that jumping the timeline is strictly prohibited yielding zero exceptions falling through."""
    assert verify_execution_transition_legality("not_started", "done") is False
    assert verify_execution_transition_legality("in_progress", "not_started") is False

def test_progress_task_execution_state_raises_value_error() -> None:
    """Ensure the dictionary mutation helper securely throws on illegal parameters preventing blind writes."""
    mock_task_definition = {"id": "TASK-100", "executionState": "not_started"}
    
    with pytest.raises(ValueError) as error_payload:
        progress_task_execution_state_securely(mock_task_definition, "done")
        
    assert "cannot transition executionState" in str(error_payload.value)
    
    # Ensure the dictionary is perfectly unaltered!
    assert mock_task_definition["executionState"] == "not_started"
