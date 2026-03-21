"""
Tests the task state machine.

Verifies valid and invalid state transitions.
"""
import pytest

from app.core.state_machine import is_valid_transition, update_task_state


def test_valid_transitions():
    """Verify allowed transitions return True."""
    assert is_valid_transition("not_started", "ready") is True
    assert is_valid_transition("ready", "in_progress") is True
    assert is_valid_transition("in_progress", "done") is True


def test_invalid_transitions():
    """Verify disallowed transitions return False."""
    assert is_valid_transition("not_started", "done") is False
    assert is_valid_transition("in_progress", "not_started") is False


def test_update_state_raises_on_invalid_transition():
    """Verify update_task_state raises ValueError for illegal transitions."""
    task = {"id": "TASK-100", "executionState": "not_started"}

    with pytest.raises(ValueError) as exc_info:
        update_task_state(task, "done")

    assert "cannot transition" in str(exc_info.value).lower()
    assert task["executionState"] == "not_started"  # Unchanged
