"""Database connection management with Singleton pattern."""

import aiosqlite
import os
from pathlib import Path
from typing import AsyncContextManager, Optional
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """SQLite database connection manager with Singleton pattern."""
    
    _instance: Optional["DatabaseConnection"] = None
    _connection: Optional[aiosqlite.Connection] = None
    _database_path: Optional[str] = None
    
    def __new__(cls, database_path: str = "destinations.db"):
        """Singleton pattern - chỉ cho phép 1 instance duy nhất."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._database_path = database_path
            logger.info(f"Created singleton DatabaseConnection for: {database_path}")
        elif cls._instance._database_path != database_path:
            # Update database path if different
            logger.warning(f"DatabaseConnection path changed from {cls._instance._database_path} to {database_path}")
            cls._instance._database_path = database_path
        return cls._instance
    
    async def connect(self) -> aiosqlite.Connection:
        """Get database connection."""
        if self._connection is None:
            # Ensure database directory exists
            db_dir = Path(self._database_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            self._connection = await aiosqlite.connect(self._database_path)
            logger.info(f"Connected to SQLite database: {self._database_path}")
        
        return self._connection
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    async def __aenter__(self) -> aiosqlite.Connection:
        """Async context manager entry."""
        return await self.connect()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    @classmethod
    def get_instance(cls, database_path: str = "destinations.db") -> "DatabaseConnection":
        """Get singleton instance."""
        return cls(database_path)
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        if cls._instance and cls._instance._connection:
            # Close connection synchronously if possible
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create a task
                    loop.create_task(cls._instance.close())
                else:
                    # If no loop is running, we can't close async connection
                    pass
            except RuntimeError:
                # No event loop, can't close async connection
                pass
        
        cls._instance = None
        cls._connection = None
        cls._database_path = None
        logger.info("DatabaseConnection singleton reset")


# Global database connection instance
db_connection = DatabaseConnection()
