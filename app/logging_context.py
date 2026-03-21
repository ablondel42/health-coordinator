"""
Logging context for structured, request-scoped logging.

Provides async-safe context propagation for correlation IDs, request IDs,
user IDs, and other contextual information.
"""
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Generator, Optional

# Context variable for storing log context
_log_context: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})


class ContextFilter(logging.Filter):
    """
    Logging filter that injects context variables into log records.
    
    Automatically adds correlation_id, request_id, user_id, and custom
    fields to every log record within the current context.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        context = _log_context.get()
        
        # Add context fields to the record
        for key, value in context.items():
            setattr(record, key, value)
        
        return True


def get_context() -> Dict[str, Any]:
    """Get the current logging context."""
    return _log_context.get().copy()


def set_context(**kwargs: Any) -> None:
    """
    Set or update fields in the logging context.
    
    Args:
        **kwargs: Key-value pairs to add to the context.
    """
    current = _log_context.get().copy()
    current.update(kwargs)
    _log_context.set(current)


def clear_context() -> None:
    """Clear all fields from the logging context."""
    _log_context.set({})


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return _log_context.get().get("correlation_id")


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the logging context."""
    set_context(correlation_id=correlation_id)


@contextmanager
def log_context(**kwargs: Any) -> Generator[None, None, None]:
    """
    Context manager for scoped logging context.
    
    Usage:
        with log_context(request_id="abc-123", user_id="user-456"):
            logger.info("Processing request")
    
    Args:
        **kwargs: Key-value pairs to add to the context for this scope.
    
    Yields:
        None
    """
    # Save current context
    previous_context = _log_context.get().copy()
    
    # Merge with new context
    new_context = previous_context.copy()
    new_context.update(kwargs)
    
    # Set new context
    token = _log_context.set(new_context)
    
    try:
        yield
    finally:
        # Restore previous context
        _log_context.reset(token)


def setup_context_filter() -> None:
    """
    Add the context filter to the root logger.
    
    Call this once at application startup after setup_global_logger().
    """
    root_logger = logging.getLogger()
    
    # Check if filter already exists
    for handler in root_logger.handlers:
        if not any(isinstance(f, ContextFilter) for f in handler.filters):
            handler.addFilter(ContextFilter())
