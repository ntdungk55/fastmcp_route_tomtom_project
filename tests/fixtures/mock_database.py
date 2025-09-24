"""Mock database for testing purposes."""

import sqlite3
import tempfile
import os
from pathlib import Path
from typing import Optional
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class MockDatabase:
    """Mock database for testing - sử dụng in-memory SQLite."""
    
    def __init__(self):
        """Initialize mock database."""
        self._connection: Optional[sqlite3.Connection] = None
        self._temp_file: Optional[str] = None
        logger.info("Initialized MockDatabase")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._connection is None:
            # Sử dụng in-memory database cho testing
            self._connection = sqlite3.connect(":memory:")
            self._create_tables()
            logger.info("Created in-memory test database")
        return self._connection
    
    def _create_tables(self):
        """Create test tables."""
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS destinations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self._connection.commit()
        logger.info("Created test tables")
    
    def clear_data(self):
        """Clear all test data."""
        if self._connection:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM destinations")
            self._connection.commit()
            logger.info("Cleared test data")
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Closed test database connection")
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_connection()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class TestDatabaseManager:
    """Manager for test database operations."""
    
    def __init__(self):
        """Initialize test database manager."""
        self._mock_db = MockDatabase()
        self._original_db_path = None
    
    def setup_test_database(self):
        """Setup test database."""
        # Lưu original database path
        self._original_db_path = os.getenv("DATABASE_PATH")
        
        # Set test database path
        os.environ["DATABASE_PATH"] = ":memory:"
        logger.info("Setup test database environment")
    
    def teardown_test_database(self):
        """Teardown test database."""
        # Restore original database path
        if self._original_db_path:
            os.environ["DATABASE_PATH"] = self._original_db_path
        else:
            os.environ.pop("DATABASE_PATH", None)
        
        # Close mock database
        self._mock_db.close()
        logger.info("Teardown test database environment")
    
    def get_mock_connection(self) -> sqlite3.Connection:
        """Get mock database connection."""
        return self._mock_db.get_connection()
    
    def clear_test_data(self):
        """Clear test data."""
        self._mock_db.clear_data()


# Global test database manager
test_db_manager = TestDatabaseManager()
