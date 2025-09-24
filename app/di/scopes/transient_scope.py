"""Transient scope management."""

from typing import Callable, TypeVar

T = TypeVar('T')


class TransientScope:
    """Transient scope implementation - creates new instance each time."""
    
    def get_instance(self, factory: Callable[[], T]) -> T:
        """Get new instance."""
        return factory()


class TransientScopeManager:
    """Transient scope manager."""
    
    def __init__(self):
        """Initialize transient scope manager."""
        self._scope = TransientScope()
    
    def get_transient(self, factory: Callable[[], T]) -> T:
        """Get transient instance."""
        return self._scope.get_instance(factory)
