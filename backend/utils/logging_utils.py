"""
Structured JSON Logging Utility
Provides consistent logging format with request IDs and context
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable to store request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request ID if available
        req_id = request_id_var.get()
        if req_id:
            log_data["req_id"] = req_id
        
        # Add extra fields from record
        extra_fields = ['path', 'method', 'status_code', 'agent', 'node', 'tool', 
                       'tokens', 'latency_ms', 'task_id', 'user_id']
        
        for key in extra_fields:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """
    Setup application logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ('json' or 'plain')
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on format type
    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def set_request_id(req_id: str):
    """Set request ID for current context"""
    request_id_var.set(req_id)


def get_request_id() -> Optional[str]:
    """Get request ID from current context"""
    return request_id_var.get()


class LogContext:
    """Context manager for structured logging"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.data = kwargs
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.log("error", f"Exception occurred: {exc_val}", exception=str(exc_val))
        return False
    
    def log(self, level: str, message: str, **extra):
        """Log with context data"""
        log_data = {**self.data, **extra}
        
        # Create LogRecord with extra fields
        getattr(self.logger, level.lower())(message, extra=log_data)
