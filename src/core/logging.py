"""
Enterprise logging configuration with structured logging.
Provides consistent logging across the application with context.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import LoggerFactory

from src.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.environment == "production" 
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get a logger for this class."""
        return get_logger(self.__class__.__name__)


def log_execution_time(func_name: str, execution_time: float, **kwargs) -> None:
    """Log function execution time with context."""
    logger = get_logger("performance")
    logger.info(
        "Function execution completed",
        function=func_name,
        execution_time_seconds=round(execution_time, 4),
        **kwargs
    )


def log_api_request(
    method: str,
    endpoint: str,
    status_code: Optional[int] = None,
    response_time: Optional[float] = None,
    **kwargs
) -> None:
    """Log API request with standardized format."""
    logger = get_logger("api")
    logger.info(
        "API request processed",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        response_time_seconds=round(response_time, 4) if response_time else None,
        **kwargs
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Log error with context and stack trace."""
    logger = get_logger("error")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        **kwargs,
        exc_info=True
    ) 