"""
Application configuration.

Loads settings from environment variables with defaults.
"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings."""
    database_url: str = os.getenv("HC_DATABASE_URL", "sqlite:///./health_coordinator.db")
    app_title: str = "Repository Health Coordinator API"
    app_version: str = "0.1.0"
    subagent_execution_timeout_sec: int = int(os.getenv("HC_SUBAGENT_TIMEOUT", "600"))
    
    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    log_handler: str = os.getenv("LOG_HANDLER", "console")
    log_file_path: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    log_max_bytes: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))


settings = Settings()
