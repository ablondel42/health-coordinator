# Test Suite

This directory contains the rigorously mandated `pytest` suite.

**Testing Philosophy:**
We do not write `assert True == True` tests.
Tests here must:
- Mock out raw `qwen` CLI calls via `asyncio` patched objects.
- Feed deliberately corrupted JSON streams to ensure `stream_parser` resilience.
- Trigger fake exceptions to observe the global Exception catcher.
