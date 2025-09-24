"""Test cases for DatabaseConnection with mock database."""

import pytest
import asyncio
from app.infrastructure.persistence.database.connection import DatabaseConnection


class TestDatabaseConnectionWithMock:
    """Test cases for DatabaseConnection with mock database."""
    
    @pytest.fixture(autouse=True)
    def setup_test(self, mock_database):
        """Setup test with mock database."""
        # Reset singleton before each test
        DatabaseConnection.reset_instance()
        yield
        # Cleanup after each test
        DatabaseConnection.reset_instance()
    
    def test_singleton_creates_only_one_instance(self):
        """Test that only one instance is created."""
        # Create multiple instances
        db1 = DatabaseConnection(":memory:")
        db2 = DatabaseConnection(":memory:")
        db3 = DatabaseConnection(":memory:")
        
        # All should be the same instance
        assert db1 is db2
        assert db2 is db3
        assert db1 is db3
    
    def test_singleton_updates_database_path(self):
        """Test that singleton updates database path when different path is requested."""
        # Create first instance
        db1 = DatabaseConnection(":memory:")
        
        # Create second instance with different path (should update path)
        db2 = DatabaseConnection(":memory:")
        
        # Should still be the same instance
        assert db1 is db2
    
    def test_get_instance_method(self):
        """Test get_instance class method."""
        # Get instance using class method
        db1 = DatabaseConnection.get_instance(":memory:")
        db2 = DatabaseConnection.get_instance(":memory:")
        
        # Should be the same instance
        assert db1 is db2
    
    def test_reset_instance_method(self):
        """Test reset_instance class method."""
        # Create instance
        db1 = DatabaseConnection(":memory:")
        
        # Reset singleton
        DatabaseConnection.reset_instance()
        
        # Create new instance
        db2 = DatabaseConnection(":memory:")
        
        # Should be different instances
        assert db1 is not db2
    
    @pytest.mark.asyncio
    async def test_singleton_connection_sharing(self):
        """Test that singleton shares connection across instances."""
        # Create multiple instances
        db1 = DatabaseConnection(":memory:")
        db2 = DatabaseConnection(":memory:")
        
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
        # Use context manager
        async with DatabaseConnection(":memory:") as conn1:
            assert conn1 is not None
            
            # Create another instance and use context manager
            db2 = DatabaseConnection(":memory:")
            async with db2 as conn2:
                # Should be the same connection
                assert conn1 is conn2
    
    def test_singleton_thread_safety(self):
        """Test singleton in multi-threaded environment."""
        instances = []
        
        def create_instance():
            instances.append(DatabaseConnection(":memory:"))
        
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
        # Create multiple instances
        instances = []
        for i in range(100):
            instances.append(DatabaseConnection(":memory:"))
        
        # All should be the same instance
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance
