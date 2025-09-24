"""Injectable decorator for dependency injection."""

from typing import Any, Callable, TypeVar, get_type_hints
from functools import wraps

T = TypeVar('T')


def injectable(cls: T) -> T:
    """Mark a class as injectable."""
    cls._injectable = True
    return cls


def inject_dependencies(func: Callable) -> Callable:
    """Inject dependencies into function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints for dependency injection
        hints = get_type_hints(func)
        
        # Inject dependencies based on type hints
        for param_name, param_type in hints.items():
            if param_name not in kwargs:
                # Here you would resolve the dependency from DI container
                # This is a simplified version
                pass
        
        return func(*args, **kwargs)
    
    return wrapper


def auto_inject(cls: T) -> T:
    """Auto-inject dependencies into class constructor."""
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        # Get type hints for constructor
        hints = get_type_hints(original_init)
        
        # Inject dependencies based on type hints
        for param_name, param_type in hints.items():
            if param_name not in kwargs and param_name != 'self':
                # Here you would resolve the dependency from DI container
                # This is a simplified version
                pass
        
        original_init(self, *args, **kwargs)
    
    cls.__init__ = new_init
    return cls
