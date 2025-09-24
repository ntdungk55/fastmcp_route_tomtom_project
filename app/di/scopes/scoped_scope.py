"""Scoped scope management."""

from typing import Dict, Any, Callable, TypeVar, Generic
from threading import local

T = TypeVar('T')


class ScopedScope(Generic[T]):
    """Scoped scope implementation - one instance per scope."""
    
    def __init__(self):
        """Initialize scoped scope."""
        self._local = local()
    
    def get_instance(self, key: str, factory: Callable[[], T]) -> T:
        """Get scoped instance."""
        if not hasattr(self._local, 'instances'):
            self._local.instances = {}
        
        if key not in self._local.instances:
            self._local.instances[key] = factory()
        
        return self._local.instances[key]
    
    def clear_scope(self):
        """Clear current scope."""
        if hasattr(self._local, 'instances'):
            self._local.instances.clear()


class ScopedScopeManager:
    """Scoped scope manager."""
    
    def __init__(self):
        """Initialize scoped scope manager."""
        self._scope = ScopedScope()
    
    def get_scoped(self, key: str, factory: Callable[[], T]) -> T:
        """Get scoped instance."""
        return self._scope.get_instance(key, factory)
    
    def clear_scope(self):
        """Clear current scope."""
        self._scope.clear_scope()
    
    def begin_scope(self):
        """Begin new scope."""
        self.clear_scope()
