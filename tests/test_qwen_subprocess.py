"""
Strict validation of the heavily dangerous LLM `asyncio` subprocess boundaries.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.orchestrator.qwen_subprocess import spawn_and_execute_LLM_subprocess_for_audit

@pytest.fixture
def override_python_asyncio_subprocess_exec():
    """Mocks the core Python native subprocess execution engine routing securely."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mocked_exec_execution:
        # Generate a fake Process layer imitating raw asyncio instances strictly
        mock_process_manager = MagicMock()
        mock_process_manager.stdin = AsyncMock() 
        
        async def mock_async_stdout_stream_iterator():
            yield b'{"domain": "test", "agentName": "test-bot", "findings": []}'
            
        mock_process_manager.stdout = mock_async_stdout_stream_iterator()
        
        mock_process_manager.stderr = AsyncMock()
        mock_process_manager.stderr.read.return_value = b""
        
        mock_process_manager.wait = AsyncMock(return_value=0)
        mock_process_manager.returncode = 0
        mock_process_manager.pid = 9999
        
        mocked_exec_execution.return_value = mock_process_manager
        yield mocked_exec_execution

@pytest.mark.asyncio
async def test_qwen_subprocess_success_happy_path(override_python_asyncio_subprocess_exec) -> None:
    """Verify that a successful execution parses correctly while injecting system prompts."""
    result_dictionary_payload = await spawn_and_execute_LLM_subprocess_for_audit(
        domain_identifier="testing_domain",
        audit_rules_array=["Rule Scope 1"],
        target_output_schema_path="test.schema.json",
        hard_timeout_in_seconds=10
    )
    
    assert result_dictionary_payload["domain"] == "test"
    
    cli_args_tuple_extracted = override_python_asyncio_subprocess_exec.call_args[0]
    assert "qwen" in cli_args_tuple_extracted
    assert "--session-id" in cli_args_tuple_extracted
    assert "--system-prompt" in cli_args_tuple_extracted

@pytest.mark.asyncio
async def test_qwen_subprocess_throws_timeout_and_kills_process_zombies() -> None:
    """Inject an asyncio timeout by hijacking `wait_for` explicitly and verify `kill()` sweeps the PID."""
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mocked_exec_layer:
        mock_process_handler = MagicMock()
        mock_process_handler.stdin = AsyncMock()
        mock_process_handler.kill = MagicMock() 
        mocked_exec_layer.return_value = mock_process_handler
        
        with patch("asyncio.wait_for") as hooked_wait_for:
            hooked_wait_for.side_effect = asyncio.TimeoutError
            
            with pytest.raises(TimeoutError) as exception_thrown_info:
                await spawn_and_execute_LLM_subprocess_for_audit("test_timeout_domain", [], "schema", 3)
                
            assert "limits 3s limit bounds" in str(exception_thrown_info.value)
            
            # The absolute most important line: Ensures we don't bleed zombie RAM processes!
            mock_process_handler.kill.assert_called_once()
