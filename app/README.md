# App Root

This directory contains the central FastAPI server architecture. 

**Core Modules:**
- `main.py`: ASGI web application entry point.
- `config.py`: Single source of truth environment variables.
- `logger.py`: Militant stack-tracing log formatting mechanism.
- `database.py`: SQLAlchemy setup & SQLite driver boundaries.
- `models.py`: Pydantic definitions enforcing strict DB mapping.
- `cli.py`: Terminal entry point interface.
