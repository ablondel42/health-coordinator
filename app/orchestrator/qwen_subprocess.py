"""
Qwen Subprocess Orchestrator

Spawns and manages Qwen CLI subprocesses using asyncio.
Enforces timeouts and captures output safely.
"""
import asyncio
import json
import uuid
import logging
import os
from pathlib import Path
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


def validate_workspace_path(workspace: str) -> str:
    """
    Validate and resolve workspace path to prevent path traversal.
    
    Args:
        workspace: User-provided workspace path.
    
    Returns:
        Resolved absolute path.
    
    Raises:
        ValueError: If path is invalid or attempts traversal outside allowed scope.
    """
    # Resolve to absolute path
    resolved = Path(workspace).resolve()
    
    # Check if path exists
    if not resolved.exists():
        raise ValueError(f"Workspace path does not exist: {workspace}")
    
    # Check if path is a directory
    if not resolved.is_dir():
        raise ValueError(f"Workspace path is not a directory: {workspace}")
    
    # Check if path is readable
    if not os.access(resolved, os.R_OK):
        raise ValueError(f"Workspace path is not readable: {workspace}")
    
    return str(resolved)


async def run_subagent_audit(
    domain: str,
    rules: list[str],
    schema_path: str,
    workspace: str = None,
    timeout: int = None
) -> Dict[str, Any]:
    """
    Run a Qwen CLI subprocess to perform an audit.

    Args:
        domain: The audit domain (e.g., 'documentation').
        rules: List of audit rules to pass as system prompt.
        schema_path: Path to the expected output JSON schema.
        workspace: Working directory for the subprocess.
        timeout: Maximum execution time in seconds.

    Returns:
        Parsed JSON output from the subagent.

    Raises:
        TimeoutError: If the subprocess exceeds the timeout.
        ValueError: If the output is not valid JSON or workspace is invalid.
        RuntimeError: If the subprocess exits with an error code.
    """
    if timeout is None:
        timeout = settings.subagent_execution_timeout_sec

    session_id = str(uuid.uuid4())
    logger.info(f"Starting subagent: session={session_id}, domain={domain}")

    prompt = (
        f"RULES: {json.dumps(rules)}.\n"
        f"Output JSON strictly matching the schema: {schema_path}\n\n"
        f"Run the {domain} audit. Return only valid JSON matching the schema, no markdown."
    )

    cmd = [
        "qwen", "-p", prompt,
        "--input-format", "text",
        "--output-format", "text",
        "--session-id", session_id
    ]

    # Validate and resolve workspace path
    cwd = None
    if workspace:
        try:
            cwd = validate_workspace_path(workspace)
            logger.debug(f"Resolved workspace path: {cwd}")
        except ValueError as e:
            logger.error(f"Invalid workspace path '{workspace}': {e}")
            raise

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )

        async def read_stdout() -> str:
            chunks = []
            async for line in process.stdout:
                chunks.append(line.decode('utf-8').strip())
            return "".join(chunks)

        stdout, _ = await asyncio.wait_for(
            asyncio.gather(read_stdout(), process.wait()),
            timeout=timeout
        )

        if process.returncode != 0:
            stderr = await process.stderr.read()
            stderr_text = stderr.decode('utf-8', errors='replace').strip()
            logger.error(f"Subprocess exited with code {process.returncode}: {stderr_text}")
            raise RuntimeError(f"Subagent failed with exit code {process.returncode}")

        # Strip markdown code blocks if present
        json_text = stdout.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        # Extract JSON object from text (handle conversational wrapper)
        start = json_text.find('{')
        end = json_text.rfind('}')
        if start != -1 and end != -1:
            json_text = json_text[start:end + 1]

        result = json.loads(json_text)
        logger.info(f"Subagent completed: domain={domain}")
        return result

    except asyncio.TimeoutError:
        try:
            process.kill()
        except OSError as e:
            logger.warning(f"Failed to kill subprocess (PID {process.pid}): {e}")
        logger.error(f"Subagent timed out after {timeout}s (PID: {process.pid})")
        raise TimeoutError(f"Subagent timed out after {timeout}s") from None

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from subagent: {stdout}")
        raise ValueError(f"Subagent returned invalid JSON: {e}") from e
