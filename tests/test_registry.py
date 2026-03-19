"""
Tests the contract loading logic and bounding limits of the Agent Registry.
"""
import pytest
from unittest import mock
from app.orchestrator.registry import load_agent_contract_by_domain, _CONTRACT_CACHE

@pytest.fixture(autouse=True)
def wipe_contract_cache():
    """Ensure tests run cleanly with a zeroed-out memory state before each execution."""
    _CONTRACT_CACHE.clear()
    yield

def test_registry_raises_filenotfound_on_bogus_domain() -> None:
    """Ensure strict error bounds are followed if domain contract is missing."""
    with pytest.raises(FileNotFoundError) as error_payload:
        load_agent_contract_by_domain("bogus_domain_that_does_not_exist")
    assert "No contract found" in str(error_payload.value)

@mock.patch("os.listdir")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data='{"domain": "test_domain", "auditRules": []}')
def test_registry_successfully_caches_contract(mock_file_layer, mock_listdir_layer) -> None:
    """Verify registry caches files properly so IO is skipped successfully on next loop."""
    mock_listdir_layer.return_value = ["test-agent.contract.json"]
    
    first_load_result = load_agent_contract_by_domain("test_domain")
    assert first_load_result["domain"] == "test_domain"
    assert mock_file_layer.call_count == 1
    
    # Second call should bypass IO completely and hit the RAM cache.
    second_load_result = load_agent_contract_by_domain("test_domain")
    assert second_load_result["domain"] == "test_domain"
    
    # Prove that the memory hit worked! Still exactly 1.
    assert mock_file_layer.call_count == 1
