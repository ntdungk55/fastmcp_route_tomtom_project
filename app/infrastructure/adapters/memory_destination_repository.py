from typing import List, Optional
from app.application.ports.destination_repository import DestinationRepository
from app.domain.entities.destination import Destination
from app.infrastructure.logging.logger import get_logger
import uuid

logger = get_logger(__name__)


class MemoryDestinationRepository(DestinationRepository):
    """In-memory implementation of destination repository"""
    
    def __init__(self):
        self._destinations: dict[str, Destination] = {}
        logger.info("Initialized MemoryDestinationRepository")
    
    async def save(self, destination: Destination) -> Destination:
        """Save a destination and return the saved entity with ID"""
        try:
            # Generate ID if not provided
            if destination.id is None:
                destination.id = str(uuid.uuid4())
            
            # Update timestamps
            now = destination.updated_at
            destination.updated_at = now
            
            # Store in memory
            self._destinations[destination.id] = destination
            
            logger.info(f"Saved destination with ID: {destination.id}")
            return destination
            
        except Exception as e:
            logger.error(f"Error saving destination: {str(e)}")
            raise
    
    async def find_by_id(self, destination_id: str) -> Optional[Destination]:
        """Find a destination by its ID"""
        try:
            destination = self._destinations.get(destination_id)
            if destination:
                logger.info(f"Found destination by ID: {destination_id}")
            else:
                logger.info(f"Destination not found by ID: {destination_id}")
            return destination
        except Exception as e:
            logger.error(f"Error finding destination by ID: {str(e)}")
            raise
    
    async def find_by_name(self, name: str) -> Optional[Destination]:
        """Find a destination by its name"""
        try:
            for destination in self._destinations.values():
                if destination.name.lower() == name.lower():
                    logger.info(f"Found destination by name: {name}")
                    return destination
            
            logger.info(f"Destination not found by name: {name}")
            return None
        except Exception as e:
            logger.error(f"Error finding destination by name: {str(e)}")
            raise
    
    async def list_all(self) -> List[Destination]:
        """List all saved destinations"""
        try:
            destinations = list(self._destinations.values())
            logger.info(f"Listed {len(destinations)} destinations")
            return destinations
        except Exception as e:
            logger.error(f"Error listing destinations: {str(e)}")
            raise
    
    async def delete(self, destination_id: str) -> bool:
        """Delete a destination by ID, return True if deleted"""
        try:
            if destination_id in self._destinations:
                del self._destinations[destination_id]
                logger.info(f"Deleted destination with ID: {destination_id}")
                return True
            else:
                logger.info(f"Destination not found for deletion: {destination_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting destination: {str(e)}")
            raise
    
    async def search_by_name_and_address(self, id: Optional[str] = None, name: Optional[str] = None, address: Optional[str] = None) -> List[Destination]:
        """Search destinations by ID, name and/or address (partial matching, case-insensitive)"""
        try:
            matching_destinations = []
            
            for destination in self._destinations.values():
                id_match = not id or (destination.id == id)
                name_match = not name or (name.lower() in destination.name.lower())
                address_match = not address or (address.lower() in destination.address.lower())
                
                if id_match and name_match and address_match:
                    matching_destinations.append(destination)
            
            logger.info(f"Found {len(matching_destinations)} destinations matching id='{id}', name='{name}', address='{address}'")
            return matching_destinations
            
        except Exception as e:
            logger.error(f"Error searching destinations: {str(e)}")
            raise