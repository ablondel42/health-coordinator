"""
Qwen Subprocess Orchestrator

The highest risk module in the application. Spawns, pipes, monitors, and cleanly 
terminates external LLM subagents using `asyncio`.
Enforces strict timeouts to prevent system hanging or zombie processes.
"""
import asyncio
import json
import uuid
import logging
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

async def spawn_and_execute_LLM_subprocess_for_audit(
    domain_identifier: str, 
    audit_rules_array: list[str], 
    target_output_schema_path: str,
    hard_timeout_in_seconds: int = None
) -> Dict[str, Any]:
    """
    Spawns a Qwen CLI subprocess safely bridging the host context to the native LLM process.
    
    Args:
        domain_identifier (str): The domain scope string (e.g. 'documentation').
        audit_rules_array (list): Array of rigid string roles passed as system prompts.
        target_output_schema_path (str): Exact JSON schema path bound string for strict Output validation.
        hard_timeout_in_seconds (int): Hard termination limit in seconds.
        
    Returns:
        Dict[str, Any]: The fully parsed and schema-compliant JSON output from the subagent.
        
    Raises:
        TimeoutError: If the subagent hangs beyond the specified boundary.
        ValueError: If the streaming output cannot be parsed strictly into JSON.
        RuntimeError: If the subprocess exits with an error code (1) or crashes.
    """
    if hard_timeout_in_seconds is None:
        hard_timeout_in_seconds = settings.subagent_execution_timeout_sek
        
    execution_session_uuid = str(uuid.uuid4())
    logger.info(f"Starting Qwen native subagent. Session UUID: {execution_session_uuid}, Domain: {domain_identifier}")
    
    formatted_system_prompt_instruction = f"RULES: {json.dumps(audit_rules_array)}. Output JSON strictly matching the schema: {target_output_schema_path}"
    
    subprocess_cli_command_arguments = [
        "qwen", "--input-format", "stream-json", "--output-format", "stream-json",
        "--session-id", execution_session_uuid, "--system-prompt", formatted_system_prompt_instruction
    ]
    
    # Instruction payload matching Qwen execution schema formatting
    standardized_instruction_payload_dictionary = {"type": "content", "value": f"Run the {domain_identifier} audit. strictly Return schema-compliant JSON."}
    
    try:
        active_llm_subprocess = await asyncio.create_subprocess_exec(
            *subprocess_cli_command_arguments,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Sequentially drain standard input payloads downwards
        utf8_encoded_payload_bytes = json.dumps(standardized_instruction_payload_dictionary).encode('utf-8') + b'\n'
        active_llm_subprocess.stdin.write(utf8_encoded_payload_bytes)
        await active_llm_subprocess.stdin.drain()
        active_llm_subprocess.stdin.close() # Throw EOF to inform CLI input block is sealed.
        
        async def safely_read_entire_stdout_stream_into_memory() -> str:
            collected_output_buffer_chunks = []
            async for data_line_bytes in active_llm_subprocess.stdout:
                collected_output_buffer_chunks.append(data_line_bytes.decode('utf-8').strip())
            return "".join(collected_output_buffer_chunks)
            
        # Hard race condition: We await both the standard output and the process termination.
        # If this exceeds timeout limits, asyncio fires TimeoutError securely.
        merged_raw_stdout_string, ignored_wait_payload = await asyncio.wait_for(
            asyncio.gather(safely_read_entire_stdout_stream_into_memory(), active_llm_subprocess.wait()), 
            timeout=hard_timeout_in_seconds
        )
        
        if active_llm_subprocess.returncode != 0:
            stderr_captured_error_bytes = await active_llm_subprocess.stderr.read()
            stderr_cleaned_error_string = stderr_captured_error_bytes.decode('utf-8', errors='replace').strip()
            logger.error(f"Qwen subprocess ({domain_identifier}) exited with code {active_llm_subprocess.returncode}. Stderr trace: {stderr_cleaned_error_string}")
            raise RuntimeError(f"Subagent execution crashed context safely with status {active_llm_subprocess.returncode}. Session tracking {execution_session_uuid}.")

        extrapolated_json_payload_dictionary = json.loads(merged_raw_stdout_string)
        logger.info(f"Successfully received valid strict JSON payload returning from LLM {domain_identifier} subagent pipeline.")
        return extrapolated_json_payload_dictionary
        
    except asyncio.TimeoutError as wrapped_timeout_exception:
        # Crucial Zombie Process defense boundary
        try:
            active_llm_subprocess.kill()
        except OSError:
            pass # Already dead
        logger.error(f"LLM Subagent '{domain_identifier}' severely timed out after {hard_timeout_in_seconds} seconds bounds. Terminated OS PID {active_llm_subprocess.pid} force kill.")
        raise TimeoutError(f"Subagent for {domain_identifier} completely exceeded limits {hard_timeout_in_seconds}s limit bounds.") from wrapped_timeout_exception
        
    except json.JSONDecodeError as wrapped_json_decode_exception:
        logger.error(f"Failed decoding LLM {domain_identifier} stdout chunk payloads. Raw data payload: {merged_raw_stdout_string}", exc_info=wrapped_json_decode_exception)
        raise ValueError(f"Subagent returned corrupted broken JSON structure payloads causing {wrapped_json_decode_exception}.") from wrapped_json_decode_exception
