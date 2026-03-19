# App Core Logic Module

This directory houses the pure Python business logic and state machine.

**Responsibilities:**
- `state_machine.py`: Enforces the Audit -> Review -> Fix -> Verify pipeline safely.
- `validator.py`: Handles strict checks merging Pydantic boundaries.
Functions here should be framework-agnostic where possible.
