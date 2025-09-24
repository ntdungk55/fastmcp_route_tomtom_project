"""Scoped decorator for dependency injection."""

from typing import Any, Callable, TypeVar, get_type_hints
from functools import wraps
import threading

T = TypeVar('T')


class ScopedContext:
    """Scoped context manager."""
    
    def __init__(self):
        """Initialize scoped context."""
        self._local = threading.local()
    
    def get_instances(self):
        """Get instances for current scope."""
        if not hasattr(self._local, 'instances'):
            self._local.instances = {}
        return self._local.instances
    
    def clear_scope(self):
        """Clear current scope."""
        if hasattr(self._local, 'instances'):
            self._local.instances.clear()
    
    def begin_scope(self):
        """Begin new scope."""
        self.clear_scope()


# Global scoped context
_scoped_context = ScopedContext()


def scoped(cls: T) -> T:
    """Mark a class as scoped (one instance per scope)."""
    @wraps(cls)
    def get_scoped_instance(*args, **kwargs):
        instances = _scoped_context.get_instances()
        key = f"{cls.__name__}_{id(args)}_{id(kwargs)}"
        
        if key not in instances:
            instances[key] = cls(*args, **kwargs)
        
        return instances[key]
    
    return get_scoped_instance


def scoped_method(func: Callable) -> Callable:
    """Make a method return scoped instance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        instances = _scoped_context.get_instances()
        key = f"{func.__name__}_{id(args)}_{id(kwargs)}"
        
        if key not in instances:
            instances[key] = func(*args, **kwargs)
        
        return instances[key]
    
    return wrapper


def scoped_factory(factory_func: Callable) -> Callable:
    """Make a factory function return scoped instances."""
    @wraps(factory_func)
    def wrapper(*args, **kwargs):
        instances = _scoped_context.get_instances()
        key = f"{factory_func.__name__}_{hash(str(args) + str(kwargs))}"
        
        if key not in instances:
            instances[key] = factory_func(*args, **kwargs)
        
        return instances[key]
    
    return wrapper


def begin_scope():
    """Begin new scoped context."""
    _scoped_context.begin_scope()


def clear_scope():
    """Clear current scoped context."""
    _scoped_context.clear_scope()
