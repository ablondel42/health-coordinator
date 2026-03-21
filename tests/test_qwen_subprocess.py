"""
Tests for the Qwen subprocess orchestrator.

Verifies subprocess spawning, timeout handling, and JSON parsing.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.orchestrator.qwen_subprocess import run_subagent_audit


@pytest.fixture
def mock_subprocess_exec():
    """Mock asyncio.create_subprocess_exec."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()

        async def mock_stdout_stream():
            yield b'{"domain": "test", "agentName": "test-bot", "findings": []}'

        mock_process.stdout = mock_stdout_stream()
        mock_process.stderr = AsyncMock()
        mock_process.stderr.read.return_value = b""
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = 0
        mock_process.pid = 9999

        mock_exec.return_value = mock_process
        yield mock_exec


@pytest.mark.asyncio
async def test_subagent_success(mock_subprocess_exec):
    """Verify successful subagent execution returns parsed JSON."""
    result = await run_subagent_audit(
        domain="test_domain",
        rules=["Rule 1"],
        schema_path="test.schema.json",
        timeout=10
    )

    assert result["domain"] == "test"
    assert result["agentName"] == "test-bot"

    call_args = mock_subprocess_exec.call_args[0]
    assert "qwen" in call_args
    assert "--session-id" in call_args


@pytest.mark.asyncio
async def test_subagent_timeout_kills_process():
    """Verify timeout kills the subprocess to prevent zombies."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()
        mock_process.stdout = AsyncMock()
        mock_process.stdout.__aiter__.return_value = []
        mock_process.stderr = AsyncMock()
        mock_process.stderr.read = AsyncMock(return_value=b"")
        mock_process.returncode = 0
        mock_process.pid = 9999
        mock_exec.return_value = mock_process

        with patch("asyncio.wait_for") as mock_wait_for:
            mock_wait_for.side_effect = asyncio.TimeoutError

            with pytest.raises(TimeoutError):
                await run_subagent_audit("test", [], "schema", timeout=3)

            mock_process.kill.assert_called_once()
