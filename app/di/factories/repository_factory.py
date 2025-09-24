"""Repository factory patterns."""

from typing import Dict, Any, Type, Protocol
from app.application.ports.destination_repository import DestinationRepository
from app.infrastructure.adapters.memory_destination_repository import MemoryDestinationRepository


class RepositoryFactory(Protocol):
    """Repository factory protocol."""
    
    def create_destination_repository(self) -> DestinationRepository:
        """Create destination repository."""
        ...


class MemoryRepositoryFactory:
    """Memory repository factory."""
    
    def __init__(self):
        """Initialize memory repository factory."""
        self._repositories: Dict[str, Any] = {}
    
    def create_destination_repository(self) -> DestinationRepository:
        """Create memory destination repository."""
        if "destination_repository" not in self._repositories:
            self._repositories["destination_repository"] = MemoryDestinationRepository()
        return self._repositories["destination_repository"]
    
    def get_all_repositories(self) -> Dict[str, Any]:
        """Get all repositories."""
        return {
            "destination_repository": self.create_destination_repository()
        }


class RepositoryFactoryManager:
    """Repository factory manager."""
    
    def __init__(self):
        """Initialize repository factory manager."""
        self._factory = MemoryRepositoryFactory()
    
    def get_factory(self) -> MemoryRepositoryFactory:
        """Get repository factory."""
        return self._factory
    
    def create_destination_repository(self) -> DestinationRepository:
        """Create destination repository."""
        return self._factory.create_destination_repository()
    
    def get_all_repositories(self) -> Dict[str, Any]:
        """Get all repositories."""
        return self._factory.get_all_repositories()
