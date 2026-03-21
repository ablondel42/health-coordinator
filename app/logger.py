"""
Production-ready logging configuration.

Supports:
- JSON and text formatting
- Multiple handlers (console, file, rotating file)
- Environment-based configuration
- Pluggable handler architecture via dictConfig
- Sensitive field filtering for security
"""
import logging
import logging.config
import os
import sys
import re
from typing import Optional, Any, Dict


# Sensitive field patterns to filter from logs
SENSITIVE_FIELD_PATTERNS = [
    re.compile(r'\b(password|passwd|pwd)\b', re.IGNORECASE),
    re.compile(r'\b(secret|secrets)\b', re.IGNORECASE),
    re.compile(r'\b(api[_-]?key|apikey)\b', re.IGNORECASE),
    re.compile(r'\b(token|tokens|auth[_-]?token)\b', re.IGNORECASE),
    re.compile(r'\b(credentials?|creds)\b', re.IGNORECASE),
    re.compile(r'\b(private[_-]?key)\b', re.IGNORECASE),
    re.compile(r'\b(access[_-]?token)\b', re.IGNORECASE),
    re.compile(r'\b(refresh[_-]?token)\b', re.IGNORECASE),
    re.compile(r'\b(bearer\s+[A-Za-z0-9\-_\.]+)', re.IGNORECASE),
    re.compile(r'\b[A-Za-z0-9+\/]{40,}={0,2}\b'),  # Base64-encoded secrets
]

REDACTED_VALUE = "[REDACTED]"


class SensitiveDataFilter(logging.Filter):
    """
    Filter that redacts sensitive data from log records.
    
    Scans log messages and extra fields for sensitive patterns
    and replaces them with [REDACTED].
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Redact sensitive data in the message
        record.msg = self._redact_sensitive(str(record.msg))
        
        # Redact sensitive data in args
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._redact_sensitive(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact_sensitive(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        # Redact sensitive data in extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "thread", "threadName", "message",
                "asctime", "exc_text"
            ):
                if isinstance(value, str):
                    setattr(record, key, self._redact_sensitive(value))
                elif isinstance(value, dict):
                    setattr(record, key, self._redact_dict(value))
        
        # Redact sensitive data in exception text
        if record.exc_text:
            record.exc_text = self._redact_sensitive(record.exc_text)
        
        return True
    
    def _redact_sensitive(self, text: str) -> str:
        """Redact sensitive patterns from text."""
        if not text:
            return text
        
        result = text
        for pattern in SENSITIVE_FIELD_PATTERNS:
            result = pattern.sub(REDACTED_VALUE, result)
        
        return result
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive data from dictionaries."""
        if not data:
            return data
        
        result = {}
        for key, value in data.items():
            # Skip redacting known safe fields
            if key.lower() in ("request_id", "status_code", "elapsed_ms", "method", "path"):
                result[key] = value
                continue
            
            if isinstance(value, str):
                result[key] = self._redact_sensitive(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self._redact_sensitive(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs logs as JSON objects for easy parsing by ELK, Datadog, CloudWatch, etc.
    Includes sensitive field filtering.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)
        
        # Add extra fields from record (excluding sensitive ones)
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "thread", "threadName", "message",
                "asctime"
            ):
                # Redact sensitive values
                if isinstance(value, str):
                    log_data[key] = SensitiveDataFilter()._redact_sensitive(value)
                elif isinstance(value, dict):
                    log_data[key] = SensitiveDataFilter()._redact_dict(value)
                else:
                    log_data[key] = value
        
        return json.dumps(log_data)


def get_log_config() -> dict:
    """
    Build logging configuration from environment variables.
    
    Environment variables:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
        LOG_FORMAT: json, text (default: json for production)
        LOG_HANDLER: console, file, both (default: console)
        LOG_FILE_PATH: Path to log file (default: logs/app.log)
        LOG_MAX_BYTES: Max file size before rotation (default: 10MB)
        LOG_BACKUP_COUNT: Number of backup files (default: 5)
    
    Returns:
        dictConfig-compatible configuration dictionary.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()
    log_handler = os.getenv("LOG_HANDLER", "console").lower()
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/app.log")
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Validate log level
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        log_level = "INFO"
    
    # Select formatter
    formatter_name = "json" if log_format == "json" else "text"
    
    # Build handlers config
    handlers = {}
    root_handlers = []
    
    if log_handler in ("console", "both"):
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": formatter_name,
            "stream": "ext://sys.stdout",
        }
        root_handlers.append("console")
    
    if log_handler in ("file", "both"):
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": formatter_name,
            "filename": log_file_path,
            "maxBytes": log_max_bytes,
            "backupCount": log_backup_count,
            "encoding": "utf-8",
            "delay": True,
        }
        root_handlers.append("file")
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "text": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "filters": {
            "sensitive": {
                "()": SensitiveDataFilter,
            },
        },
        "handlers": handlers,
        "root": {
            "level": log_level,
            "handlers": root_handlers,
            "filters": ["sensitive"],
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": root_handlers,
                "propagate": False,
                "filters": ["sensitive"],
            },
        },
    }


def setup_global_logger() -> None:
    """
    Configure logging using dictConfig for production-ready pluggability.
    
    This function should be called once at application startup.
    Configuration is controlled via environment variables.
    Includes sensitive data filtering for security.
    """
    config = get_log_config()
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module.
    
    Args:
        name: Typically __name__ of the calling module.
    
    Returns:
        Configured logger instance with sensitive data filtering.
    """
    return logging.getLogger(name)
