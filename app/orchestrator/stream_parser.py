"""
Stream Parser Module

Responsibility: Safely buffers byte-chunks from standard output (stdout)
pipes and recombines them into validated JSON payloads.
Prevents JSONDecodeError crashes from fragmented output blocks over subprocesses.
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class JSONStreamBuffer:
    """
    Stateful buffer for accumulating and parsing JSON streams cleanly.
    """
    def __init__(self):
        self._text_buffer = ""

    def append_chunk(self, chunk_string: str) -> None:
        """Adds a newly read string chunk to the internal buffer pipeline."""
        self._text_buffer += chunk_string

    def attempt_parse(self) -> Optional[dict]:
        """
        Attempts to parse the buffer. 
        If parsing succeeds, the buffer is cleared.
        If it fails due to being incomplete, it returns None and waits for more chunks.
        """
        stripped_string_buffer = self._text_buffer.strip()
        if not stripped_string_buffer:
            return None
            
        try:
            successfully_parsed_data = json.loads(stripped_string_buffer)
            # Extracted successfully, clear the pipeline buffer for the next sequential object
            self._text_buffer = ""
            return successfully_parsed_data
        except json.JSONDecodeError:
            # It's likely fragmented and incomplete; return None and catch more buffer chunks
            return None
