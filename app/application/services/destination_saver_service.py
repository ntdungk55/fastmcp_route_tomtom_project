"""
Destination Saver Service - BLK-1-08: SaveDestination
Lưu destination mới vào database.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from app.infrastructure.logging.logger import get_logger


@dataclass
class DestinationData:
    """Destination data structure."""
    id: str
    name: str
    address: str
    coordinates: Optional[Dict[str, float]] = None
    geocoded_at: Optional[str] = None
    created_at: str = None
    updated_at: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat() + "Z"


class DestinationSaverService:
    """
    BLK-1-08: SaveDestination - Lưu destination mới vào database
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self._logger = get_logger(__name__)
        self._db_path = db_path or "destinations_new.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize destinations table."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS destinations (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        address TEXT NOT NULL,
                        coordinates TEXT,  -- JSON string
                        geocoded_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT,
                        user_id TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_destinations_name ON destinations(name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_destinations_address ON destinations(address)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_destinations_user_id ON destinations(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_destinations_created_at ON destinations(created_at)")
                
                conn.commit()
                self._logger.info("Destinations database initialized successfully")
                
        except Exception as e:
            self._logger.error(f"Failed to initialize destinations database: {e}")
            raise
    
    async def save_destination(self, name: str, address: str, 
                             coordinates: Optional[Dict[str, float]] = None,
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        BLK-1-08: Save destination to database
        
        Args:
            name: Destination name
            address: Destination address
            coordinates: Optional coordinates
            user_id: Optional user ID
            
        Returns:
            Dict: Save result
        """
        self._logger.info(f"BLK-1-08: Saving destination '{name}' at '{address}'")
        
        try:
            # Check if destination already exists
            existing = await self._check_existing_destination(name, address, user_id)
            if existing:
                self._logger.info(f"BLK-1-08: Destination already exists: {existing['id']}")
                return {
                    "success": True,
                    "destination_id": existing["id"],
                    "message": "Destination already exists",
                    "action": "found_existing"
                }
            
            # Create new destination
            destination = DestinationData(
                id=str(uuid.uuid4()),
                name=name,
                address=address,
                coordinates=coordinates,
                user_id=user_id
            )
            
            # Save to database
            await self._insert_destination(destination)
            
            self._logger.info(f"BLK-1-08: Successfully saved destination {destination.id}")
            
            return {
                "success": True,
                "destination_id": destination.id,
                "message": "Destination saved successfully",
                "action": "created_new",
                "destination": {
                    "id": destination.id,
                    "name": destination.name,
                    "address": destination.address,
                    "coordinates": destination.coordinates,
                    "created_at": destination.created_at
                }
            }
            
        except Exception as e:
            self._logger.error(f"BLK-1-08: Failed to save destination: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save destination"
            }
    
    async def _check_existing_destination(self, name: str, address: str, 
                                        user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Check if destination already exists."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Check by name and address
                cursor = conn.execute("""
                    SELECT id, name, address, coordinates, created_at
                    FROM destinations
                    WHERE name = ? AND address = ?
                """, (name, address))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                
                return None
                
        except Exception as e:
            self._logger.error(f"Failed to check existing destination: {e}")
            return None
    
    async def _insert_destination(self, destination: DestinationData):
        """Insert destination into database."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    INSERT INTO destinations 
                    (id, name, address, coordinates, geocoded_at, created_at, updated_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    destination.id,
                    destination.name,
                    destination.address,
                    str(destination.coordinates) if destination.coordinates else None,
                    destination.geocoded_at,
                    destination.created_at,
                    destination.updated_at,
                    destination.user_id
                ))
                conn.commit()
                
        except Exception as e:
            self._logger.error(f"Failed to insert destination: {e}")
            raise
    
    async def update_destination_coordinates(self, destination_id: str, 
                                           coordinates: Dict[str, float]) -> Dict[str, Any]:
        """
        Update destination coordinates after geocoding
        
        Args:
            destination_id: Destination ID
            coordinates: New coordinates
            
        Returns:
            Dict: Update result
        """
        self._logger.info(f"BLK-1-08: Updating coordinates for destination {destination_id}")
        
        try:
            updated_at = datetime.utcnow().isoformat() + "Z"
            
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute("""
                    UPDATE destinations 
                    SET coordinates = ?, geocoded_at = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    str(coordinates),
                    updated_at,
                    updated_at,
                    destination_id
                ))
                
                if cursor.rowcount == 0:
                    return {
                        "success": False,
                        "error": "Destination not found",
                        "destination_id": destination_id
                    }
                
                conn.commit()
            
            self._logger.info(f"BLK-1-08: Successfully updated coordinates for destination {destination_id}")
            
            return {
                "success": True,
                "destination_id": destination_id,
                "coordinates": coordinates,
                "geocoded_at": updated_at,
                "message": "Coordinates updated successfully"
            }
            
        except Exception as e:
            self._logger.error(f"BLK-1-08: Failed to update coordinates: {e}")
            return {
                "success": False,
                "error": str(e),
                "destination_id": destination_id
            }
    
    async def get_destination(self, destination_id: str) -> Optional[Dict[str, Any]]:
        """
        Get destination by ID
        
        Args:
            destination_id: Destination ID
            
        Returns:
            Optional[Dict]: Destination data
        """
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT id, name, address, coordinates, geocoded_at, created_at, updated_at, user_id
                    FROM destinations
                    WHERE id = ?
                """, (destination_id,))
                
                row = cursor.fetchone()
                if row:
                    destination = dict(row)
                    # Parse coordinates JSON
                    if destination["coordinates"]:
                        import json
                        destination["coordinates"] = json.loads(destination["coordinates"])
                    return destination
                
                return None
                
        except Exception as e:
            self._logger.error(f"Failed to get destination {destination_id}: {e}")
            return None
    
    async def search_destinations(self, name: Optional[str] = None, 
                                address: Optional[str] = None,
                                user_id: Optional[str] = None,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search destinations
        
        Args:
            name: Search by name
            address: Search by address
            user_id: Filter by user ID
            limit: Maximum results
            
        Returns:
            List[Dict]: Matching destinations
        """
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query
                query = "SELECT id, name, address, coordinates, geocoded_at, created_at, updated_at, user_id FROM destinations WHERE 1=1"
                params = []
                
                if name:
                    query += " AND name LIKE ?"
                    params.append(f"%{name}%")
                
                if address:
                    query += " AND address LIKE ?"
                    params.append(f"%{address}%")
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                destinations = []
                for row in cursor.fetchall():
                    destination = dict(row)
                    # Parse coordinates JSON
                    if destination["coordinates"]:
                        import json
                        destination["coordinates"] = json.loads(destination["coordinates"])
                    destinations.append(destination)
                
                return destinations
                
        except Exception as e:
            self._logger.error(f"Failed to search destinations: {e}")
            return []
    
    async def delete_destination(self, destination_id: str) -> Dict[str, Any]:
        """
        Delete destination
        
        Args:
            destination_id: Destination ID
            
        Returns:
            Dict: Delete result
        """
        self._logger.info(f"BLK-1-08: Deleting destination {destination_id}")
        
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))
                
                if cursor.rowcount == 0:
                    return {
                        "success": False,
                        "error": "Destination not found",
                        "destination_id": destination_id
                    }
                
                conn.commit()
            
            self._logger.info(f"BLK-1-08: Successfully deleted destination {destination_id}")
            
            return {
                "success": True,
                "destination_id": destination_id,
                "message": "Destination deleted successfully"
            }
            
        except Exception as e:
            self._logger.error(f"BLK-1-08: Failed to delete destination: {e}")
            return {
                "success": False,
                "error": str(e),
                "destination_id": destination_id
            }


# Factory function
def get_destination_saver_service(db_path: Optional[str] = None) -> DestinationSaverService:
    """Factory function để lấy destination saver service."""
    return DestinationSaverService(db_path)
