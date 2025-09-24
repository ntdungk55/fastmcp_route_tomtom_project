"""Singleton scope management."""

from typing import Dict, Any, Callable, TypeVar, Generic
from threading import Lock

T = TypeVar('T')


class SingletonScope(Generic[T]):
    """Singleton scope implementation."""
    
    def __init__(self):
        """Initialize singleton scope."""
        self._instances: Dict[str, T] = {}
        self._lock = Lock()
    
    def get_instance(self, key: str, factory: Callable[[], T]) -> T:
        """Get singleton instance."""
        if key not in self._instances:
            with self._lock:
                if key not in self._instances:
                    self._instances[key] = factory()
        return self._instances[key]
    
    def clear(self):
        """Clear all instances."""
        with self._lock:
            self._instances.clear()
    
    def remove(self, key: str):
        """Remove specific instance."""
        with self._lock:
            self._instances.pop(key, None)


class SingletonScopeManager:
    """Singleton scope manager."""
    
    def __init__(self):
        """Initialize singleton scope manager."""
        self._scope = SingletonScope()
    
    def get_singleton(self, key: str, factory: Callable[[], T]) -> T:
        """Get singleton instance."""
        return self._scope.get_instance(key, factory)
    
    def clear_all(self):
        """Clear all singletons."""
        self._scope.clear()
    
    def remove_singleton(self, key: str):
        """Remove specific singleton."""
        self._scope.remove(key)
