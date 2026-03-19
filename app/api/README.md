# App API Module

This directory isolates the REST API boundaries.

Files in this module (e.g., `routes_tasks.py`) map strictly to HTTP methods and FastAPI routers. Business logic and state changes should be delegated to `app/core/`, keeping these route definitions as thin transportation layers.
