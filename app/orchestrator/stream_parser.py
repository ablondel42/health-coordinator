"""
Stream Parser Module

Buffers and parses JSON streams from subprocess stdout.
Prevents errors from fragmented output chunks.
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class JSONStreamBuffer:
    """Accumulates and parses JSON stream chunks."""

    def __init__(self):
        self._buffer = ""

    def append(self, chunk: str) -> None:
        """Add a chunk to the buffer."""
        self._buffer += chunk

    def parse(self) -> Optional[dict]:
        """
        Try to parse the buffer as JSON.

        Returns:
            The parsed JSON object, or None if incomplete.
        """
        data = self._buffer.strip()
        if not data:
            return None

        try:
            result = json.loads(data)
            self._buffer = ""
            return result
        except json.JSONDecodeError:
            return None  # Incomplete, wait for more data
