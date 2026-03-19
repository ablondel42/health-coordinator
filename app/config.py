"""
Configuration management for the Health Coordinator application.

Handles environment variables and global application constants.
Provides a central Pydantic Settings implementation.
"""

import os
from pydantic import BaseModel

class ApplicationSettings(BaseModel):
    """
    Strict typing for global application settings.
    Default values allow for seamless localhost bootstrapping.
    """
    database_url: str = os.getenv("HC_DATABASE_URL", "sqlite:///./health_coordinator.db")
    app_title: str = "Repository Health Coordinator API"
    app_version: str = "0.1.0"
    subagent_execution_timeout_sek: int = int(os.getenv("HC_SUBAGENT_TIMEOUT", "600"))

# Global singleton configuration object
settings = ApplicationSettings()
