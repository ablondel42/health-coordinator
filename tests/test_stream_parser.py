"""
Tests the resilience of the JSON stream patching logic.
"""
from app.orchestrator.stream_parser import JSONStreamBuffer

def test_buffer_recovers_fragmented_json_objects_robustly() -> None:
    """Ensure that the buffer perfectly mitigates crashes occurring from pipe chunks splitting."""
    buffer_test_instance = JSONStreamBuffer()
    
    buffer_test_instance.append_chunk('{"domain": "do')
    # Validates it suppresses JSONDecodeError
    assert buffer_test_instance.attempt_parse() is None
    
    buffer_test_instance.append_chunk('cumentation", "agen')
    assert buffer_test_instance.attempt_parse() is None
    
    buffer_test_instance.append_chunk('tName": "Test"}')
    parsed_reconstructed_dictionary = buffer_test_instance.attempt_parse()
    
    assert parsed_reconstructed_dictionary is not None
    assert parsed_reconstructed_dictionary["domain"] == "documentation"

def test_empty_buffer_returns_none_gracefully() -> None:
    """Proves it fails fast."""
    buffer_test_instance = JSONStreamBuffer()
    assert buffer_test_instance.attempt_parse() is None
