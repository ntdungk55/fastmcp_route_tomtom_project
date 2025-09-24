"""Migration to create destinations table."""

from app.infrastructure.persistence.database.connection import DatabaseConnection
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def create_destinations_table():
    """Create destinations table."""
    async with DatabaseConnection() as conn:
        cursor = await conn.cursor()
        
        # Create destinations table
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS destinations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create indexes for better performance
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_destinations_name 
            ON destinations(name)
        """)
        
        await cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_destinations_created_at 
            ON destinations(created_at)
        """)
        
        await conn.commit()
        logger.info("Destinations table created successfully")


async def drop_destinations_table():
    """Drop destinations table (for testing)."""
    async with DatabaseConnection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("DROP TABLE IF EXISTS destinations")
        await conn.commit()
        logger.info("Destinations table dropped")


async def run_migrations():
    """Run all migrations."""
    logger.info("Running database migrations...")
    await create_destinations_table()
    logger.info("Database migrations completed")
