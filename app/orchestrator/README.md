# Subagent Orchestrator Module

This is the most critical and complex zone of the application. It handles spawning and interfacing with native `qwen` subprocesses using the `asyncio` module.

**Responsibilities:**
- `qwen_subprocess.py`: Raw execution, timeouts, and `stderr` capture.
- `stream_parser.py`: Safe, chunk-by-chunk buffering of `stream-json`.
- `registry.py`: Loading specific Subagent `.contract.json` bounds.
