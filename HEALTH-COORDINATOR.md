# Repository Health Coordinator (Qwen CLI Native)

Build **only the coordinator first**, with a hard approval pause before fixes, strict JSON schemas on every file, and a fully functional Task Create Read Update Delete (CRUD) API built from day one. 

**Core Architecture Shift:** This coordinator does *not* use "fake" subagents or external LLM REST APIs for its audits. Instead, it natively orchestrates **Qwen Code CLI** subprocesses on your host machine. It spawns `qwen` instances using `--input-format stream-json --output-format stream-json --session-id <uuid>` to safely command and receive structured data streaming from independent auditing/fixing subagents.

## Recommended Architecture: The Agent Swarm

Keep the design clean, robust, and local-first:
- **Web Framework:** Python FastAPI (for strict typing with Pydantic and async by default).
- **Database:** A lightweight local SQLite database (using raw `sqlite3` or `SQLAlchemy`). Store nested JSON schema objects in SQLite `JSON` or `TEXT` columns.
- **CLI Interface:** A terminal tool (e.g., built with `Typer` or `Click`) exposed globally as `hc` to trigger audits.
- **Orchestration layer:** `qwen_subprocess.py` module, which manages the execution, timeout, and state of the Master-Worker agent swarm via `asyncio`.
- **API Boundary:** Strict REST endpoints mapping directly to the frontend GUI's needs.

## Observability & Error Handling (Zero-Tolerance Policy)

This system orchestrates unpredictable external subagents. It must be built with militant error handling:
1. **No Silent Errors:** Every `try/except` block must either handle the error completely or re-raise it. No bare `except:` or `except Exception: pass`. 
2. **No Meaningless Logs:** Log messages like `"Error occurred"` are forbidden. Every error log **must** include the contextual `taskId`, `agentName`, or `findingId` that failed, exactly what was attempted, and the stringified exception payload.
3. **Structured Tracing:** Configure Python's `logging` module with a consistent formatter that traces `[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s`.
4. **Subprocess Stderr Capture:** When Qwen crashes or stdout pipelines sever, `stderr` and internal process exit codes (`process.returncode`) must be logged thoroughly for tracing.
5. **API Contract Enforcement:** When subagent schemas fail Pydantic validation, the API/logs must print exactly *which schema field* failed validation, not just a generic `ValidationError`.

---

## Documentation Strategy & Code Quality

Every piece of the project must be self-documenting, maintainable, and strictly engineered:
1. **Short READMEs Everywhere:** Every core directory (e.g., `app/api/`, `app/core/`, `app/orchestrator/`, `schemas/`) must contain a short `README.md` file explicitly detailing the purpose of that boundaries' modules.
2. **Comprehensive Docstrings:** Every Python class, method, function, and module must have a clear Python docstring (e.g., Google or Sphinx style) outlining its purpose, arguments, and return types. Hand-waved "self-documenting" code is forbidden.
3. **Single Responsibility Principle (SRP):** Every function should handle exactly **one topic** or **one piece of functionality**. Do not build monolithic "God functions" that do four things—extract logic into distinct, modular functions.
4. **Plain-English Naming:** Do not abbreviate. All functions, classes, and variable names should be incredibly meaningful, distinct, and readable like plain English. For example, use `fetch_active_audit_tasks_from_database()` instead of `get_tasks()`, and `subagent_stdout_pipe` instead of `out`.

---

## Rigorous Testing Strategy

Every part of the application must be covered by comprehensive unit testing (e.g., via `pytest`). Tests must ensure the underlying system stability by testing real edge cases, not simply asserting that `2 == 2`.

**Testing Requirements:**
- **Database & State Machine:** Tests must assert that the database rolls back on failure and that state machine transitions strictly fail if preconditions are unmet (e.g., transitioning to `Fix` without `Review`).
- **Subprocess Mocking:** The `qwen_subprocess.py` logic must be heavily tested using mock `asyncio.subprocess` objects. You must write test cases that simulate timeouts, corrupted `stdout` JSON chunks, and non-zero exit codes to prove the orchestrator catches them gracefully.
- **Model Validation:** Inject intentionally malformed data into Pydantic unit tests to prove that `additionalProperties: false` fails requests appropriately.
- **FastAPI Endpoints:** Use `TestClient` to verify that API routes return proper HTTP 400/500 status codes with clean, formatted error messages when given invalid input.

---

## Command Line Interface (CLI): `hc`

To make testing and running the system frictionless, the project must include a CLI tool named `hc`.

The CLI should use a library like `Typer` or `Click` and provide commands that either directly call the coordinator's core logic or hit the FastAPI endpoints if the server is running.

**Required `hc` commands:**
- `hc server start`: Boots the FastAPI database and API server on localhost.
- `hc audit`: Scans the `agent-registry` folder, summons the Swarm Orchestrator, launches the Qwen subagents (like the Documentation Auditor), collects their raw streaming output, and consolidates the findings into the database.
- `hc audit --domain documentation`: Runs a targeted audit summoning *only* the documentation subagent.
- `hc tasks list`: Prints a table of the SQLite task list to the terminal so you can verify findings without a GUI.

---

## Detailed Project Structure

```text
repo-health-coordinator/
├─ agent-registry/         <-- Instructions and rules for specialized subagents
│  ├─ README.md
│  ├─ docs-auditor.contract.json   <-- The primary documentation subagent definition
│  ├─ code-quality-auditor.contract.json
│  └─ test-coverage-auditor.contract.json
├─ schemas/                <-- Master JSON schemas for database mapping & validation
│  ├─ README.md
│  ├─ health-report.schema.json
│  ├─ task-record.schema.json
│  ├─ task-crud-request.schema.json
│  ├─ task-crud-response.schema.json
│  ├─ approval-state.schema.json
│  ├─ subagent-audit-output.schema.json
│  ├─ subagent-fix-output.schema.json
│  └─ subagent-verify-output.schema.json
├─ app/
│  ├─ README.md            <-- App root architecture overview
│  ├─ main.py              <-- FastAPI entry point, logger initialization, global Exception Handlers
│  ├─ cli.py               <-- The `hc` CLI definition using Typer/Click
│  ├─ config.py            <-- Env vars and app configuration
│  ├─ logger.py            <-- Pre-configured logging trace formatter
│  ├─ database.py          <-- SQLite connection pooling / SQLAlchemy setup
│  ├─ models.py            <-- Pydantic models aligning 1:1 with JSON schemas
│  ├─ api/
│  │  ├─ README.md            <-- API boundaries explanation
│  │  ├─ routes_tasks.py      <-- CRUD /tasks
│  │  ├─ routes_runs.py       <-- Start/Stop/Status of Swarm Runs
│  │  └─ routes_approval.py   <-- Approval gate APIs
│  ├─ core/
│  │  ├─ README.md            <-- Core business logic guidelines
│  │  ├─ state_machine.py     <-- Enforces Audit -> Review -> Fix -> Verify
│  │  └─ validator.py         <-- Validates incoming subagent payloads against `/schemas/`
│  └─ orchestrator/
│     ├─ README.md            <-- Subprocess and agent lifecycle documentation
│     ├─ registry.py          <-- Loads and caches `/agent-registry/` definitions
│     ├─ qwen_subprocess.py   <-- Core execution engine: Spawns subagents & multiplexes FDs
│     └─ stream_parser.py     <-- Safely accumulates JSON streams chunk-by-chunk without corrupting
├─ tests/
│  ├─ README.md
│  ├─ test_database.py     <-- SQL / Transaction rollbacks
│  ├─ test_models.py       <-- Pydantic schema validation rejection testing
│  ├─ test_state_machine.py<-- Workflow step preconditions
│  ├─ test_api_routes.py   <-- FastAPI TestClient assertions
│  ├─ test_registry.py     <-- Contract JSON loading and caching
│  ├─ test_stream_parser.py<-- Chunk manipulation and JSON buffering testing
│  └─ test_qwen_subprocess.py<-- asyncio Mocking of subprocesses, timeouts, and corrupted stdout
├─ pyproject.toml          <-- (Must configure `[project.scripts] hc = "app.cli:app"`)
└─ README.md
```

---

## The First Agent Contract: Documentation Auditor

The `agent-registry` folder holds the definition files for each specialized subagent. The Coordinator `registry.py` loads this JSON file, passes the `auditRules` to Qwen as its System Prompt, and enforces that Qwen's output perfectly matches `subagent-audit-output.schema.json`.

### `agent-registry/docs-auditor.contract.json`
```json
{
  "name": "Documentation Auditor",
  "domain": "documentation",
  "auditRules": [
    "You are the strict Documentation Auditor for this repository.",
    "Your objective is to verify that the project's documentation is consistent with its actual codebase state.",
    "1. Verify that a comprehensive REST API documentation exists if API routes are present.",
    "2. Verify that all core Python classes and public functions have standard docstrings (Google/Sphinx format).",
    "3. Check for any missing README.md files in fundamental subdirectories.",
    "4. Highlight any mismatch between the code logic and what the documentation claims it does.",
    "5. Output your findings strictly matching the provided JSON schema. If the documentation is perfect, assign a score of 100 returning an empty findings array."
  ],
  "outputSchema": "subagent-audit-output.schema.json"
}
```

---

## Detailed REST API Endpoints

The FastAPI service should expose at least the following to support a localhost GUI in the future:

**Swarm Execution Controls**
- `POST /runs` -> Launch a new full repository audit swarm (moves state to `audit`).
- `GET /runs/active` -> Fetch real-time status of the currently spinning subagents.

**Task Operations**
- `GET /tasks` -> List tasks with filters (domain, priority, state).
- `POST /tasks` -> Manually create a task.
- `GET /tasks/{taskId}` -> Get task details.
- `PATCH /tasks/{taskId}` -> Update editable fields (owner, priority, scope).
- `DELETE /tasks/{taskId}` -> Hard delete if not started, soft cancel if executing.
- `GET /tasks/{taskId}/history` -> Get audit trail history.

**Approval Gate (User Intervention)**
- `GET /approval` -> Get tasks awaiting user signature.
- `POST /tasks/{taskId}/approve` -> Mark finding as approved for Fixing phase.
- `POST /tasks/{taskId}/reject` -> Mark finding as false positive/ignored.
- `POST /tasks/{taskId}/ignore` -> Mark finding as ignored for this run.

---

## Execution Engine Details (`qwen_subprocess.py`)

A robust local agent execution requires careful handling of raw streams. Subagents output using `stream-json`. Your engine must:
1. **Handle Chunking:** Raw `stdout` over pipes might arrive in broken byte headers. Do not blindly `json.loads(line)`. You must accumulate the buffer until a newline `\n` or complete JSON block is formed, then parse it.
2. **Handle Timeouts:** If a Qwen subprocess hangs on file I/O or an LLM call, the `asyncio` loop must enforce a timeout (e.g. 10 minutes) and forcefully terminate the PID to prevent memory leaks.
3. **Capture Telemetry (Stderr):** Pipe `stderr` separately to capture critical crashes or warnings from the generic CLI binary.

```python
import asyncio
import json
import uuid
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def run_qwen_subagent_for_audit_contract(contract_path: str, timeout_in_seconds: int = 600) -> Dict[str, Any]:
    """
    Spawns a Qwen CLI subprocess to act as an auditing subagent safely.
    
    Args:
        contract_path (str): The absolute path to the .contract.json defining the subagent's rules.
        timeout_in_seconds (int): Hard termination limit in seconds.
        
    Returns:
        Dict[str, Any]: The fully parsed and schema-compliant JSON output from the subagent.
        
    Raises:
        FileNotFoundError: If the subagent contract cannot be found in the registry.
        TimeoutError: If the subagent hangs beyond the specified timeout_sec boundary.
        ValueError: If the streaming output cannot be parsed strictly into JSON.
        RuntimeError: If the subprocess exits with an error code (1).
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Qwen subagent. Session: {session_id}, Contract: {contract_path}")
    
    # Load contract
    try:
        with open(contract_path, "r") as contract_file_handle:
            agent_contract = json.load(contract_file_handle)
    except FileNotFoundError as file_error:
        logger.error(f"Agent contract not found at {contract_path}. Cannot launch subprocess.", exc_info=True)
        raise file_error
        
    system_prompt_instruction = f"RULES: {json.dumps(agent_contract['auditRules'])}. Output JSON strictly matching the schema: {agent_contract['outputSchema']}"
    cli_command_arguments = [
        "qwen", "--input-format", "stream-json", "--output-format", "stream-json",
        "--session-id", session_id, "--system-prompt", system_prompt_instruction
    ]
    
    instruction_payload = {"type": "content", "value": f"Run the {agent_contract['domain']} audit. Return schema-compliant JSON."}
    
    try:
        qwen_subprocess = await asyncio.create_subprocess_exec(
            *cli_command_arguments,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Dispatch input asynchronously 
        qwen_subprocess.stdin.write(json.dumps(instruction_payload).encode() + b'\n')
        await qwen_subprocess.stdin.drain()
        qwen_subprocess.stdin.close() # Signal EOF to child process
        
        async def safely_read_stdout_stream():
            output_buffer_chunks = []
            async for data_line in qwen_subprocess.stdout:
                output_buffer_chunks.append(data_line.decode('utf-8').strip())
            return "".join(output_buffer_chunks)
            
        # Securely read streams with hard timeout enforcement
        consolidated_stdout_string, _ = await asyncio.wait_for(
            asyncio.gather(safely_read_stdout_stream(), qwen_subprocess.wait()), 
            timeout=timeout_in_seconds
        )
        
        if qwen_subprocess.returncode != 0:
            stderr_error_string = await qwen_subprocess.stderr.read()
            logger.error(f"Qwen subprocess ({agent_contract['domain']}) exited with code {qwen_subprocess.returncode}. Stderr: {stderr_error_string.decode('utf-8')}")
            raise RuntimeError(f"Subagent execution failed. See logs for session {session_id}")

        final_parsed_json_payload = json.loads(consolidated_stdout_string)
        logger.info(f"Successfully received valid JSON payload from {agent_contract['domain']} subagent.")
        return final_parsed_json_payload
        
    except asyncio.TimeoutError:
        qwen_subprocess.kill()
        logger.error(f"Subagent '{agent_contract['domain']}' completely timed out after {timeout_in_seconds}s. Terminated PID {qwen_subprocess.pid}.")
        raise TimeoutError(f"Subagent for {agent_contract['domain']} timed out after {timeout_in_seconds}s.")
    except json.JSONDecodeError as decode_error:
        logger.error(f"Failed to decode subagent {agent_contract['domain']} output as JSON. Raw data: {consolidated_stdout_string}", exc_info=True)
        raise ValueError(f"Subagent returned invalid JSON payload") from decode_error
```

---

## Initial Core Schemas

Ensure Python Pydantic models cleanly translate to/from these schemas, enforcing `additionalProperties: false`.

### `schemas/task-record.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://localhost/schemas/task-record.schema.json",
  "title": "Task Record",
  "description": "Canonical task object owned by the coordinator.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "sourceType", "domain", "title", "description", "priority", "approvalState", "executionState", "verificationState", "owner"],
  "properties": {
    "id": { "type": "string", "pattern": "^TASK-[0-9]{4,}$" },
    "sourceType": { "type": "string", "enum": ["finding", "manual"] },
    "findingId": { "type": ["string", "null"] },
    "manualReason": { "type": ["string", "null"] },
    "domain": { "type": "string" },
    "title": { "type": "string", "maxLength": 160 },
    "description": { "type": "string", "maxLength": 2000 },
    "priority": { "type": "string", "enum": ["P0", "P1", "P2", "P3"] },
    "severity": { "type": ["string", "null"], "enum": ["critical", "high", "medium", "low", "info", null] },
    "approvalState": { "type": "string", "enum": ["pending_review", "approved", "rejected", "ignored", "edited"] },
    "executionState": { "type": "string", "enum": ["not_started", "ready", "in_progress", "done", "failed", "skipped", "cancelled"] },
    "verificationState": { "type": "string", "enum": ["not_applicable", "pending", "passed", "failed", "partial", "unverifiable"] },
    "owner": { "type": "string" },
    "scopeNote": { "type": ["string", "null"] },
    "tags": { "type": "array", "items": { "type": "string" } }
  }
}
```

### `schemas/subagent-audit-output.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://localhost/schemas/subagent-audit-output.schema.json",
  "title": "Subagent Audit Output",
  "description": "Output contract for one Qwen audit subagent.",
  "type": "object",
  "additionalProperties": false,
  "required": ["domain", "agentName", "score", "findings"],
  "properties": {
    "domain": { "type": "string" },
    "agentName": { "type": "string" },
    "score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["title", "description", "severity", "priority", "evidence", "affectedFiles", "suggestedFix", "autoFixable"],
        "properties": {
          "title": { "type": "string" },
          "description": { "type": "string" },
          "severity": { "type": "string", "enum": ["critical", "high", "medium", "low", "info"] },
          "priority": { "type": "string", "enum": ["P0", "P1", "P2", "P3"] },
          "evidence": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["type", "path", "snippet"],
              "properties": {
                "type": { "type": "string", "enum": ["file", "command", "test", "config", "log"] },
                "path": { "type": "string" },
                "line": { "type": ["integer", "null"] },
                "snippet": { "type": "string" }
              }
            }
          },
          "affectedFiles": { "type": "array", "items": { "type": "string" } },
          "suggestedFix": { "type": "string" },
          "autoFixable": { "type": "boolean" }
        }
      }
    }
  }
}
```

### `schemas/subagent-fix-output.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://localhost/schemas/subagent-fix-output.schema.json",
  "title": "Subagent Fix Output",
  "description": "Output contract for one Qwen fix subagent.",
  "type": "object",
  "additionalProperties": false,
  "required": ["domain", "agentName", "fixes"],
  "properties": {
    "domain": { "type": "string" },
    "agentName": { "type": "string" },
    "fixes": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["taskId", "findingId", "status", "changedFiles", "testsRun", "patchSummary"],
        "properties": {
          "taskId": { "type": "string" },
          "findingId": { "type": ["string", "null"] },
          "status": { "type": "string", "enum": ["applied", "partial", "failed", "skipped"] },
          "changedFiles": { "type": "array", "items": { "type": "string" } },
          "testsRun": { "type": "array", "items": { "type": "string" } },
          "patchSummary": { "type": "string" }
        }
      }
    }
  }
}
```

### `schemas/approval-state.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://localhost/schemas/approval-state.schema.json",
  "title": "Approval State",
  "description": "User review decisions recorded between audit and fix.",
  "type": "object",
  "additionalProperties": false,
  "required": ["schemaVersion", "runId", "status", "reviewedAt", "taskDecisions", "summary"],
  "properties": {
    "schemaVersion": { "type": "string" },
    "runId": { "type": "string" },
    "status": { "type": "string", "enum": ["awaiting_user_approval", "review_complete"] },
    "reviewedAt": { "type": ["string", "null"], "format": "date-time" },
    "taskDecisions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["taskId", "decision"],
        "properties": {
          "taskId": { "type": "string" },
          "decision": { "type": "string", "enum": ["approved", "rejected", "ignored", "edited"] },
          "note": { "type": ["string", "null"] },
          "editedPriority": { "type": ["string", "null"], "enum": ["P0", "P1", "P2", "P3", null] },
          "editedOwner": { "type": ["string", "null"] },
          "editedScope": { "type": ["string", "null"] }
        }
      }
    },
    "summary": {
      "type": "object",
      "additionalProperties": false,
      "required": ["approved", "rejected", "ignored", "edited"],
      "properties": {
        "approved": { "type": "integer", "minimum": 0 },
        "rejected": { "type": "integer", "minimum": 0 },
        "ignored": { "type": "integer", "minimum": 0 },
        "edited": { "type": "integer", "minimum": 0 }
      }
    }
  }
}
```

---

## Direct Build Prompt for Qwen Code

Instead of breaking this into tiny manual steps, feed this entire specification document to Qwen Code in one shot using this overarching prompt:

> "I want to build a local repository health coordinator in Python (FastAPI). It must use a **lightweight local SQLite database** (e.g., using `SQLAlchemy`) for state management, mapping the provided JSON schemas directly to ORM models and strictly enforcing `additionalProperties: false` via Pydantic. Note: No GUI or Dashboard projections are needed for V1, just the core APIs and CLI.
> 
> **CRITICAL CONSTRAINTS:**
> 1. **Zero Silent Errors:** Use systematic error handling. No bare `except:` or `except Exception: pass`. Handle or re-raise.
> 2. **Tracing:** Implement consistent logging with context (trace `taskId`, `findingId`, specific Pydantic schema field drops, etc.).
> 3. **Documentation:** Every Python file must include comprehensive class/function-level docstrings. Furthermore, generate a short but clear `README.md` for *every fundamental subdirectory* (`app/core/`, `app/api/`, etc.) explaining its responsibilities.
> 4. **Code Quality (SRP & Naming):** Every function **must** handle exactly one topic or functionality. All function names and variables must be extremely meaningful, unabbreviated, and readable like plain English (e.g., `fetch_active_audit_tasks_from_database()`).
> 5. **Rigorous Testing:** Generate comprehensive `pytest` test files for *every* module. Do not write dummy `assert True == True` tests. Construct tests that mock out Qwen subprocess timeouts/crashes in `qwen_subprocess.py`, assert FastAPI rejection of invalid Pydantic JSON schemas, and verify SQLite rollbacks.
> 
> The central piece is the orchestration module (`orchestrator/qwen_subprocess.py`). It must span concurrent `qwen` CLI subprocesses with `--input-format stream-json --output-format stream-json --session-id <UUID>`. It should load contracts from the `agent-registry`, gather the `stream-json` responses iteratively to prevent chunk corruption, enforce timeouts, capture `stderr` if a subprocess crashes, and commit validated models into SQLite.
> 
> You must also provide a fully featured `hc` CLI tool built with Typer or Click that exposes `hc server start`, `hc audit`, and `hc tasks list`.
> 
> Read the architecture outline, project structure, and schemas in `HEALTH-COORDINATOR.md`. Scaffold the FastAPI app, the Database/Pydantic layer, the `hc` CLI interface (`app/cli.py`), the state machine, the agent-registry loading logic, the CRUD API routes specified under 'Detailed REST API Endpoints', and the master Qwen subprocess orchestrator. Ensure the `tests/` directory is fully fleshed out per constraint #5."
