from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.destination import Destination


class DestinationRepository(ABC):
    """Port for destination persistence operations"""
    
    @abstractmethod
    async def save(self, destination: Destination) -> Destination:
        """Save a destination and return the saved entity with ID"""
        pass
    
    @abstractmethod
    async def find_by_id(self, destination_id: str) -> Optional[Destination]:
        """Find a destination by its ID"""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Destination]:
        """Find a destination by its name"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Destination]:
        """List all saved destinations"""
        pass
    
    @abstractmethod
    async def delete(self, destination_id: str) -> bool:
        """Delete a destination by ID, return True if deleted"""
        pass
