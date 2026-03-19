"""
Pre-configured logging trace formatter for the Health Coordinator.

Provides a unified logging configuration that strictly enforces the
zero-tolerance observability rules specified in HEALTH-COORDINATOR.md.
"""

import logging
import sys

def setup_global_logger() -> None:
    """
    Configures the root python logger to trace function name, file name, and line number.
    
    This function creates a robust output format to guarantee precise stack observability 
    for debugging unhandled exceptions or tracing deep executions.
    """
    trace_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    formatter = logging.Formatter(fmt=trace_format, datefmt=date_format)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate logs if run under uvicorn
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Returns a configured logger instance bound to the specific module.
    
    Args:
        module_name (str): The built-in __name__ variable of the invoking module.
        
    Returns:
        logging.Logger: The configured module-level logger.
    """
    return logging.getLogger(module_name)
