
"""
Unified Logging System cho toàn bộ dự án.
Tuân thủ Clean Architecture và có thể sử dụng chung cho tất cả layers.
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Log levels enum"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogContext:
    """Context information for logging"""
    
    def __init__(self, 
                 layer: str = None,
                 component: str = None,
                 entity_id: str = None,
                 operation: str = None,
                 user_id: str = None,
                 request_id: str = None,
                 **kwargs):
        self.layer = layer
        self.component = component
        self.entity_id = entity_id
        self.operation = operation
        self.user_id = user_id
        self.request_id = request_id
        self.extra = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "layer": self.layer,
            "component": self.component,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "user_id": self.user_id,
            "request_id": self.request_id,
            **self.extra
        }


class Logger:
    """
    Unified logging system cho toàn bộ dự án.
    Cung cấp structured logging với context và formatting.
    """
    
    _instance: Optional['Logger'] = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger configuration"""
        # Get log level from environment
        log_level = self._get_log_level()
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _get_log_level(self) -> str:
        """Get log level from environment"""
        import os
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    def get_logger(self, 
                   name: str, 
                   context: Optional[LogContext] = None) -> 'ContextualLogger':
        """
        Get a contextual logger for a specific component.
        
        Args:
            name: Logger name (usually module name)
            context: Optional context information
            
        Returns:
            ContextualLogger instance
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return ContextualLogger(self._loggers[name], context or LogContext())
    
    def configure_file_logging(self, 
                              log_file: str = "app.log",
                              max_bytes: int = 10 * 1024 * 1024,  # 10MB
                              backup_count: int = 5):
        """
        Configure file logging with rotation.
        
        Args:
            log_file: Log file path
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
        """
        from logging.handlers import RotatingFileHandler
        
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        # Set formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to all existing loggers
        for logger in self._loggers.values():
            logger.addHandler(file_handler)
    
    def set_log_level(self, level: Union[str, LogLevel]):
        """Set log level for all loggers"""
        if isinstance(level, LogLevel):
            level = level.value
        
        for logger in self._loggers.values():
            logger.setLevel(getattr(logging, level.upper()))


class ContextualLogger:
    """
    Logger with context information.
    Wraps standard Python logger with additional context.
    """
    
    def __init__(self, logger: logging.Logger, context: LogContext):
        self.logger = logger
        self.context = context
    
    def _format_message(self, message: str, extra_context: Optional[Dict[str, Any]] = None) -> str:
        """Format message with context"""
        context_dict = self.context.to_dict()
        if extra_context:
            context_dict.update(extra_context)
        
        # Create context string
        context_parts = []
        for key, value in context_dict.items():
            if value is not None:
                context_parts.append(f"{key}={value}")
        
        if context_parts:
            return f"[{' '.join(context_parts)}] {message}"
        return message
    
    def debug(self, message: str, extra_context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        formatted_message = self._format_message(message, extra_context)
        self.logger.debug(formatted_message, **kwargs)
    
    def info(self, message: str, extra_context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        formatted_message = self._format_message(message, extra_context)
        self.logger.info(formatted_message, **kwargs)
    
    def warning(self, message: str, extra_context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        formatted_message = self._format_message(message, extra_context)
        self.logger.warning(formatted_message, **kwargs)
    
    def error(self, message: str, extra_context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        formatted_message = self._format_message(message, extra_context)
        self.logger.error(formatted_message, **kwargs)
    
    def critical(self, message: str, extra_context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message"""
        formatted_message = self._format_message(message, extra_context)
        self.logger.critical(formatted_message, **kwargs)
    
    def exception(self, message: str, extra_context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log exception with traceback"""
        formatted_message = self._format_message(message, extra_context)
        self.logger.exception(formatted_message, **kwargs)
    
    def with_context(self, **context_updates) -> 'ContextualLogger':
        """Create new logger with updated context"""
        new_context = LogContext(
            layer=context_updates.get('layer', self.context.layer),
            component=context_updates.get('component', self.context.component),
            entity_id=context_updates.get('entity_id', self.context.entity_id),
            operation=context_updates.get('operation', self.context.operation),
            user_id=context_updates.get('user_id', self.context.user_id),
            request_id=context_updates.get('request_id', self.context.request_id),
            **{**self.context.extra, **{k: v for k, v in context_updates.items() 
                                       if k not in ['layer', 'component', 'entity_id', 
                                                   'operation', 'user_id', 'request_id']}}
        )
        return ContextualLogger(self.logger, new_context)


# Global unified logger instance
logger = Logger()


def get_logger(name: str = "app", 
               layer: str = None,
               component: str = None,
               entity_id: str = None,
               operation: str = None,
               user_id: str = None,
               request_id: str = None,
               **context_kwargs) -> ContextualLogger:
    """
    Get logger with context.
    
    Args:
        name: Logger name
        layer: Layer name (domain, application, infrastructure, interfaces)
        component: Component name
        entity_id: Entity ID
        operation: Operation name
        user_id: User ID
        request_id: Request ID
        **context_kwargs: Additional context
        
    Returns:
        ContextualLogger instance
    """
    context = LogContext(
        layer=layer,
        component=component,
        entity_id=entity_id,
        operation=operation,
        user_id=user_id,
        request_id=request_id,
        **context_kwargs
    )
    return logger.get_logger(name, context)


# Backward compatibility
def get_unified_logger(name: str = "app", 
                      layer: str = None,
                      component: str = None,
                      entity_id: str = None,
                      operation: str = None,
                      user_id: str = None,
                      request_id: str = None,
                      **context_kwargs) -> ContextualLogger:
    """Backward compatibility function"""
    return get_logger(name, layer, component, entity_id, operation, user_id, request_id, **context_kwargs)
