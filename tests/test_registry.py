"""
Tests for the agent registry loader.

Verifies contract loading and caching behavior.
"""
import pytest
from unittest import mock

from app.orchestrator.registry import load_contract, _contract_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the contract cache before each test."""
    _contract_cache.clear()
    yield


def test_load_contract_raises_on_missing_domain():
    """Verify FileNotFoundError for unknown domains."""
    with pytest.raises(FileNotFoundError) as exc_info:
        load_contract("nonexistent_domain")
    assert "No contract found" in str(exc_info.value)


@mock.patch("os.listdir")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data='{"domain": "test", "auditRules": []}')
def test_load_contract_caches_result(mock_open, mock_listdir):
    """Verify contracts are cached to avoid repeated disk I/O."""
    mock_listdir.return_value = ["test.contract.json"]

    # First call loads from disk
    result = load_contract("test")
    assert result["domain"] == "test"
    assert mock_open.call_count == 1

    # Second call uses cache
    result = load_contract("test")
    assert result["domain"] == "test"
    assert mock_open.call_count == 1  # Still 1, cache hit
