"""SQLite implementation of destination repository."""

from typing import List, Optional
from app.application.ports.destination_repository import DestinationRepository
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.destination_name import DestinationName
from app.domain.value_objects.address import Address
from app.infrastructure.persistence.database.connection import DatabaseConnection
from app.infrastructure.logging.logger import get_logger
from datetime import datetime, timezone
import uuid

logger = get_logger(__name__)


class SQLiteDestinationRepository(DestinationRepository):
    """SQLite implementation of destination repository."""
    
    def __init__(self, database_path: str = "destinations.db"):
        """Initialize SQLite repository."""
        self.database_path = database_path
        self._db_connection = DatabaseConnection.get_instance(database_path)
        logger.info(f"Initialized SQLiteDestinationRepository with database: {database_path}")
    
    async def save(self, destination: Destination) -> Destination:
        """Save a destination and return the saved entity with ID."""
        try:
            async with self._db_connection as conn:
                cursor = await conn.cursor()
                
                # Idempotent check: prefer unique by NAME, then by ADDRESS
                # 1) Try match by name (case-insensitive exact)
                if destination.id is None:
                    await cursor.execute(
                        "SELECT id FROM destinations WHERE LOWER(name) = LOWER(?)",
                        (str(destination.name),)
                    )
                    row = await cursor.fetchone()
                    if row:
                        destination.id = row[0]

                # 2) If still no id, try match by address (case-insensitive exact)
                if destination.id is None:
                    await cursor.execute(
                        "SELECT id FROM destinations WHERE LOWER(address) = LOWER(?)",
                        (str(destination.address),)
                    )
                    row = await cursor.fetchone()
                    if row:
                        destination.id = row[0]

                # 3) If still no id, generate a new one for insert
                if destination.id is None:
                    destination.id = str(uuid.uuid4())
                
                # Check if destination exists (for updates)
                await cursor.execute(
                    "SELECT id FROM destinations WHERE id = ?",
                    (destination.id,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    # Update existing destination - convert value objects to strings
                    await cursor.execute("""
                        UPDATE destinations 
                        SET name = ?, address = ?, latitude = ?, longitude = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        str(destination.name),  # Convert DestinationName to string
                        str(destination.address),  # Convert Address to string
                        destination.coordinates.lat,
                        destination.coordinates.lon,
                        destination.updated_at.isoformat(),
                        destination.id
                    ))
                    logger.info(f"Updated destination with ID: {destination.id}")
                else:
                    # Insert new destination - convert value objects to strings
                    await cursor.execute("""
                        INSERT INTO destinations 
                        (id, name, address, latitude, longitude, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        destination.id,
                        str(destination.name),  # Convert DestinationName to string
                        str(destination.address),  # Convert Address to string
                        destination.coordinates.lat,
                        destination.coordinates.lon,
                        destination.created_at.isoformat(),
                        destination.updated_at.isoformat()
                    ))
                    logger.info(f"Inserted new destination with ID: {destination.id}")
                
                await conn.commit()
                return destination
                
        except Exception as e:
            logger.error(f"Error saving destination: {str(e)}")
            raise
    
    async def find_by_id(self, destination_id: str) -> Optional[Destination]:
        """Find a destination by its ID."""
        try:
            async with self._db_connection as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT id, name, address, latitude, longitude, created_at, updated_at FROM destinations WHERE id = ?",
                    (destination_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    destination = self._row_to_destination(row)
                    logger.info(f"Found destination by ID: {destination_id}")
                    return destination
                else:
                    logger.info(f"Destination not found by ID: {destination_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error finding destination by ID: {str(e)}")
            raise
    
    async def find_by_name(self, name: str) -> Optional[Destination]:
        """Find a destination by its name."""
        try:
            async with self._db_connection as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT id, name, address, latitude, longitude, created_at, updated_at FROM destinations WHERE name = ?",
                    (name,)
                )
                row = await cursor.fetchone()
                
                if row:
                    destination = self._row_to_destination(row)
                    logger.info(f"Found destination by name: {name}")
                    return destination
                else:
                    logger.info(f"Destination not found by name: {name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error finding destination by name: {str(e)}")
            raise
    
    async def list_all(self) -> List[Destination]:
        """List all saved destinations."""
        try:
            async with self._db_connection as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT id, name, address, latitude, longitude, created_at, updated_at FROM destinations ORDER BY created_at DESC"
                )
                rows = await cursor.fetchall()
                
                destinations = [self._row_to_destination(row) for row in rows]
                logger.info(f"Listed {len(destinations)} destinations")
                return destinations
                
        except Exception as e:
            logger.error(f"Error listing destinations: {str(e)}")
            raise
    
    async def delete(self, destination_id: str) -> bool:
        """Delete a destination by ID, return True if deleted."""
        try:
            async with self._db_connection as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "DELETE FROM destinations WHERE id = ?",
                    (destination_id,)
                )
                
                deleted_count = cursor.rowcount
                await conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Deleted destination with ID: {destination_id}")
                    return True
                else:
                    logger.info(f"Destination not found for deletion: {destination_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting destination: {str(e)}")
            raise
    
    async def search_by_name_and_address(self, id: Optional[str] = None, name: Optional[str] = None, address: Optional[str] = None) -> List[Destination]:
        """Search destinations by ID, name and/or address (partial matching, case-insensitive)."""
        try:
            async with self._db_connection as conn:
                cursor = await conn.cursor()
                
                # Build dynamic query based on provided criteria
                query = "SELECT id, name, address, latitude, longitude, created_at, updated_at FROM destinations WHERE 1=1"
                params = []
                
                if id:
                    query += " AND id = ?"
                    params.append(id)
                
                if name:
                    query += " AND LOWER(name) LIKE LOWER(?)"
                    params.append(f"%{name}%")
                
                if address:
                    query += " AND LOWER(address) LIKE LOWER(?)"
                    params.append(f"%{address}%")
                
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                
                destinations = [self._row_to_destination(row) for row in rows]
                logger.info(f"Found {len(destinations)} destinations matching id='{id}', name='{name}', address='{address}'")
                return destinations
                
        except Exception as e:
            logger.error(f"Error searching destinations: {str(e)}")
            raise
    
    def _row_to_destination(self, row: tuple) -> Destination:
        """Convert database row to Destination entity."""
        # Parse datetimes and add timezone if not present
        created_at = datetime.fromisoformat(row[5])
        updated_at = datetime.fromisoformat(row[6])
        
        # Add UTC timezone if datetime is naive
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        return Destination(
            id=row[0],
            name=DestinationName(row[1]),  # Convert string to DestinationName
            address=Address(row[2]),  # Convert string to Address
            coordinates=LatLon(row[3], row[4]),
            created_at=created_at,
            updated_at=updated_at
        )
