"""
Tests the JSON stream buffer.

Verifies chunked JSON parsing resilience.
"""
from app.orchestrator.stream_parser import JSONStreamBuffer


def test_buffer_assembles_fragmented_json():
    """Verify the buffer handles chunked output correctly."""
    buffer = JSONStreamBuffer()

    # Feed chunks that split JSON mid-stream
    buffer.append('{"domain": "do')
    assert buffer.parse() is None

    buffer.append('cumentation", "agen')
    assert buffer.parse() is None

    buffer.append('tName": "Test"}')
    result = buffer.parse()

    assert result is not None
    assert result["domain"] == "documentation"


def test_empty_buffer_returns_none():
    """Verify empty buffer returns None."""
    buffer = JSONStreamBuffer()
    assert buffer.parse() is None
