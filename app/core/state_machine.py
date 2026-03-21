"""
Task State Machine

Enforces valid state transitions for the task lifecycle:
Audit -> Review -> Fix -> Verify
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Valid execution state transitions
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "not_started": ["ready", "cancelled"],
    "ready": ["in_progress", "skipped", "cancelled"],
    "in_progress": ["done", "failed"],
    "done": [],  # Terminal state
    "failed": ["ready"],  # Allow retry
    "skipped": ["ready"],  # Allow un-skip
    "cancelled": ["not_started"],  # Allow re-open
}


def is_valid_transition(current_state: str, next_state: str) -> bool:
    """
    Check if a state transition is valid.

    Args:
        current_state: The current execution state.
        next_state: The desired next state.

    Returns:
        True if the transition is allowed.
    """
    allowed = VALID_TRANSITIONS.get(current_state, [])
    if next_state in allowed:
        return True
    if current_state == next_state:
        return True  # Self-transition is a no-op

    logger.warning(f"Invalid state transition: {current_state} -> {next_state}")
    return False


def update_task_state(payload: dict, next_state: str) -> dict:
    """
    Update a task's execution state after validating the transition.

    Args:
        payload: The task record payload.
        next_state: The new state to set.

    Returns:
        The updated payload.

    Raises:
        ValueError: If the transition is not allowed.
    """
    current_state = payload.get("executionState", "not_started")

    if not is_valid_transition(current_state, next_state):
        task_id = payload.get("id", "UNKNOWN")
        error_msg = f"Task {task_id}: cannot transition from '{current_state}' to '{next_state}'."
        logger.error(error_msg)
        raise ValueError(error_msg)

    payload["executionState"] = next_state
    return payload
