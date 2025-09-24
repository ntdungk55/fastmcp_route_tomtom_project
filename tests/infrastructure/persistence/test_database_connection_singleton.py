"""Test cases for DatabaseConnection singleton pattern."""

import pytest
import asyncio
from app.infrastructure.persistence.database.connection import DatabaseConnection


class TestDatabaseConnectionSingleton:
    """Test cases for DatabaseConnection singleton pattern."""
    
    def test_singleton_creates_only_one_instance(self):
        """Test that only one instance is created."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        # Create multiple instances
        db1 = DatabaseConnection("test1.db")
        db2 = DatabaseConnection("test2.db")
        db3 = DatabaseConnection("test1.db")
        
        # All should be the same instance
        assert db1 is db2
        assert db2 is db3
        assert db1 is db3
        
        # Should use the first database path
        assert db1._database_path == "test1.db"
    
    def test_singleton_updates_database_path(self):
        """Test that singleton updates database path when different path is requested."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        # Create first instance
        db1 = DatabaseConnection("test1.db")
        
        # Create second instance with different path (should update path)
        db2 = DatabaseConnection("test2.db")
        
        # Should still be the same instance but with updated path
        assert db1 is db2
        assert db1._database_path == "test2.db"
    
    def test_get_instance_method(self):
        """Test get_instance class method."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        # Get instance using class method
        db1 = DatabaseConnection.get_instance("test.db")
        db2 = DatabaseConnection.get_instance("test.db")
        
        # Should be the same instance
        assert db1 is db2
        assert db1._database_path == "test.db"
    
    def test_reset_instance_method(self):
        """Test reset_instance class method."""
        # Create instance
        db1 = DatabaseConnection("test1.db")
        
        # Reset singleton
        DatabaseConnection.reset_instance()
        
        # Create new instance
        db2 = DatabaseConnection("test2.db")
        
        # Should be different instances
        assert db1 is not db2
        assert db2._database_path == "test2.db"
    
    @pytest.mark.asyncio
    async def test_singleton_connection_sharing(self):
        """Test that singleton shares connection across instances."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        # Create multiple instances
        db1 = DatabaseConnection("test.db")
        db2 = DatabaseConnection("test.db")
        
        # Connect first instance
        conn1 = await db1.connect()
        
        # Connect second instance (should reuse same connection)
        conn2 = await db2.connect()
        
        # Should be the same connection object
        assert conn1 is conn2
        
        # Close connection
        await db1.close()
    
    @pytest.mark.asyncio
    async def test_singleton_context_manager(self):
        """Test singleton with context manager."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        # Use context manager
        async with DatabaseConnection("test.db") as conn1:
            assert conn1 is not None
            
            # Create another instance and use context manager
            db2 = DatabaseConnection("test.db")
            async with db2 as conn2:
                # Should be the same connection
                assert conn1 is conn2
    
    def test_singleton_thread_safety(self):
        """Test singleton in multi-threaded environment."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        instances = []
        
        def create_instance():
            instances.append(DatabaseConnection("test.db"))
        
        # Create multiple threads
        import threading
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        for instance in instances:
            assert instance is instances[0]
    
    def test_singleton_memory_efficiency(self):
        """Test that singleton doesn't create multiple objects."""
        # Reset singleton before test
        DatabaseConnection.reset_instance()
        
        # Create multiple instances
        instances = []
        for i in range(100):
            instances.append(DatabaseConnection(f"test{i}.db"))
        
        # All should be the same instance
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance
        
        # Should have the last database path (the last one)
        assert first_instance._database_path == "test99.db"
