"""Singleton decorator for dependency injection."""

from typing import Any, Callable, TypeVar, get_type_hints
from functools import wraps
import threading

T = TypeVar('T')


def singleton(cls: T) -> T:
    """Mark a class as singleton."""
    _instances = {}
    _lock = threading.Lock()
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in _instances:
            with _lock:
                if cls not in _instances:
                    _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]
    
    return get_instance


def singleton_method(func: Callable) -> Callable:
    """Make a method return singleton instance."""
    _instances = {}
    _lock = threading.Lock()
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = f"{func.__name__}_{id(args)}_{id(kwargs)}"
        if key not in _instances:
            with _lock:
                if key not in _instances:
                    _instances[key] = func(*args, **kwargs)
        return _instances[key]
    
    return wrapper


def singleton_factory(factory_func: Callable) -> Callable:
    """Make a factory function return singleton instances."""
    _instances = {}
    _lock = threading.Lock()
    
    @wraps(factory_func)
    def wrapper(*args, **kwargs):
        key = f"{factory_func.__name__}_{hash(str(args) + str(kwargs))}"
        if key not in _instances:
            with _lock:
                if key not in _instances:
                    _instances[key] = factory_func(*args, **kwargs)
        return _instances[key]
    
    return wrapper
