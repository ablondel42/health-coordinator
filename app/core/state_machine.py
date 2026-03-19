"""
Core State Machine

Enforces strict lifecycles for Tasks to ensure the Audit -> Review -> Fix -> Verify 
pipeline is perfectly respected.
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Valid state transitions
_VALID_EXECUTION_TRANSITIONS: Dict[str, List[str]] = {
    # (Current_State) -> List of allowed Target_States
    "not_started": ["ready", "cancelled"],
    "ready": ["in_progress", "skipped", "cancelled"],
    "in_progress": ["done", "failed"],
    "done": [], # Terminal
    "failed": ["ready"], # Retry
    "skipped": ["ready"], # Un-skip
    "cancelled": ["not_started"] # Re-open
}

def verify_execution_transition_legality(current_state_string: str, next_state_string: str) -> bool:
    """
    Determines if an execution state change is structurally valid.
    
    Args:
        current_state_string (str): Current executionState.
        next_state_string (str): Desired executionState.
        
    Returns:
        bool: True if allowed strictly.
    """
    safely_allowed_transitions = _VALID_EXECUTION_TRANSITIONS.get(current_state_string, [])
    if next_state_string in safely_allowed_transitions:
        return True
    
    # Self-transitions are safely ignored
    if current_state_string == next_state_string:
        return True
        
    logger.warning(f"Illegal execution state transition attempted: {current_state_string} -> {next_state_string}")
    return False

def progress_task_execution_state_securely(task_dictionary_payload: dict, next_state_string: str) -> dict:
    """
    Mutates a task payload executionState after verifying it securely against the State Machine logic.
    
    Args:
        task_dictionary_payload (dict): The raw task record payload.
        next_state_string (str): The strictly demanded new state.
        
    Returns:
        dict: The locally updated payload.
        
    Raises:
        ValueError: If the State Machine rejects the state transition.
    """
    current_payload_state = task_dictionary_payload.get("executionState", "not_started")
    
    if not verify_execution_transition_legality(current_payload_state, next_state_string):
        formatted_error_message = f"Task {task_dictionary_payload.get('id', 'UNKNOWN')} cannot transition executionState from '{current_payload_state}' to '{next_state_string}'."
        logger.error(formatted_error_message)
        raise ValueError(formatted_error_message)
        
    task_dictionary_payload["executionState"] = next_state_string
    return task_dictionary_payload
