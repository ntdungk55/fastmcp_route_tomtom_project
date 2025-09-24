"""Integration tests from SQLite to MCP tools."""

import pytest
import asyncio
from unittest.mock import patch
from app.di.container import Container
from app.application.dto.save_destination_dto import SaveDestinationRequest
from app.application.dto.list_destinations_dto import ListDestinationsRequest
from app.application.dto.update_destination_dto import UpdateDestinationRequest
from app.application.dto.delete_destination_dto import DeleteDestinationRequest


class TestSQLiteToMCPIntegration:
    """Integration tests from SQLite persistence to MCP tools."""
    
    @pytest.fixture
    def container_with_db(self):
        """Create container with initialized database."""
        async def _create_container():
            container = Container()
            await container.initialize_database()
            return container
        return _create_container
    
    @pytest.mark.asyncio
    async def test_save_destination_sqlite_persistence(self, container_with_db):
        """Test saving destination with SQLite persistence."""
        # Arrange
        container = await container_with_db()
        
        # Act
        import uuid
        unique_name = f"Integration Test Office {uuid.uuid4().hex[:8]}"
        result = await container.save_destination.execute(SaveDestinationRequest(
            name=unique_name,
            address="123 Test Street, Ho Chi Minh City"
        ))
        
        # Assert
        assert result.success is True
        assert result.destination_id is not None
        assert "Integration Test Office" in result.message
        assert result.error is None
        
        # Verify data is persisted in SQLite
        list_result = await container.list_destinations.execute(ListDestinationsRequest())
        assert list_result.success is True
        assert list_result.total_count >= 1
        
        # Find our test destination
        test_dest = None
        for dest in list_result.destinations:
            if "Integration Test Office" in dest.name:
                test_dest = dest
                break
        
        assert test_dest is not None
        assert test_dest.address == "123 Test Street, Ho Chi Minh City"
        assert test_dest.latitude is not None
        assert test_dest.longitude is not None
        
        return result.destination_id
    
    @pytest.mark.asyncio
    async def test_list_destinations_sqlite_persistence(self, container_with_db):
        """Test listing destinations from SQLite."""
        # Arrange
        container = await container_with_db()
        
        # Save a test destination first
        import uuid
        unique_name = f"List Test Office {uuid.uuid4().hex[:8]}"
        await container.save_destination.execute(SaveDestinationRequest(
            name=unique_name,
            address="456 List Street, Ho Chi Minh City"
        ))
        
        # Act
        result = await container.list_destinations.execute(ListDestinationsRequest())
        
        # Assert
        assert result.success is True
        assert result.total_count >= 1
        assert len(result.destinations) >= 1
        assert "Found" in result.message
        assert result.error is None
        
        # Verify destination data
        test_dest = None
        for dest in result.destinations:
            if "List Test Office" in dest.name:
                test_dest = dest
                break
        
        assert test_dest is not None
        assert test_dest.address == "456 List Street, Ho Chi Minh City"
        assert test_dest.latitude is not None
        assert test_dest.longitude is not None
    
    @pytest.mark.asyncio
    async def test_update_destination_sqlite_persistence(self, container_with_db):
        """Test updating destination with SQLite persistence."""
        # Arrange
        container = await container_with_db()
        
        # Save a test destination first
        import uuid
        unique_name = f"Update Test Office {uuid.uuid4().hex[:8]}"
        save_result = await container.save_destination.execute(SaveDestinationRequest(
            name=unique_name,
            address="789 Update Street, Ho Chi Minh City"
        ))
        assert save_result.success is True
        destination_id = save_result.destination_id
        
        # Act
        import uuid
        unique_update_name = f"Updated Test Office {uuid.uuid4().hex[:8]}"
        update_result = await container.update_destination.execute(UpdateDestinationRequest(
            destination_id=destination_id,
            name=unique_update_name,
            address="999 New Street, Ho Chi Minh City"
        ))
        
        # Assert
        assert update_result.success is True
        assert update_result.destination_id == destination_id
        assert "Updated Test Office" in update_result.message
        assert update_result.error is None
        
        # Verify update is persisted in SQLite
        list_result = await container.list_destinations.execute(ListDestinationsRequest())
        assert list_result.success is True
        
        # Find updated destination
        updated_dest = None
        for dest in list_result.destinations:
            if dest.id == destination_id:
                updated_dest = dest
                break
        
        assert updated_dest is not None
        assert updated_dest.name == unique_update_name
        assert updated_dest.address == "999 New Street, Ho Chi Minh City"
    
    @pytest.mark.asyncio
    async def test_delete_destination_sqlite_persistence(self, container_with_db):
        """Test deleting destination with SQLite persistence."""
        # Arrange
        container = await container_with_db()
        
        # Save a test destination first
        import uuid
        unique_name = f"Delete Test Office {uuid.uuid4().hex[:8]}"
        save_result = await container.save_destination.execute(SaveDestinationRequest(
            name=unique_name,
            address="111 Delete Street, Ho Chi Minh City"
        ))
        assert save_result.success is True
        destination_id = save_result.destination_id
        
        # Verify destination exists
        list_result_before = await container.list_destinations.execute(ListDestinationsRequest())
        initial_count = list_result_before.total_count
        
        # Act
        delete_result = await container.delete_destination.execute(DeleteDestinationRequest(
            destination_id=destination_id
        ))
        
        # Assert
        assert delete_result.success is True
        assert delete_result.deleted is True
        assert "Delete Test Office" in delete_result.message
        assert delete_result.error is None
        
        # Verify deletion is persisted in SQLite
        list_result_after = await container.list_destinations.execute(ListDestinationsRequest())
        assert list_result_after.success is True
        assert list_result_after.total_count == initial_count - 1
        
        # Verify destination is no longer in the list
        deleted_dest = None
        for dest in list_result_after.destinations:
            if dest.id == destination_id:
                deleted_dest = dest
                break
        
        assert deleted_dest is None
    
    @pytest.mark.asyncio
    async def test_full_workflow_sqlite_persistence(self, container_with_db):
        """Test complete workflow with SQLite persistence."""
        # Arrange
        container = await container_with_db()
        
        # 1. Save multiple destinations
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        destinations = [
            (f"Workflow Office 1 {unique_id}", "123 Workflow Street, Ho Chi Minh City"),
            (f"Workflow Office 2 {unique_id}", "456 Workflow Avenue, Ho Chi Minh City"),
            (f"Workflow Office 3 {unique_id}", "789 Workflow Boulevard, Ho Chi Minh City")
        ]
        
        saved_ids = []
        for name, address in destinations:
            result = await container.save_destination.execute(SaveDestinationRequest(
                name=name,
                address=address
            ))
            assert result.success is True
            saved_ids.append(result.destination_id)
        
        # 2. List all destinations
        list_result = await container.list_destinations.execute(ListDestinationsRequest())
        assert list_result.success is True
        assert list_result.total_count >= 3
        
        # 3. Update first destination
        import uuid
        unique_update_name = f"Updated Workflow Office 1 {uuid.uuid4().hex[:8]}"
        update_result = await container.update_destination.execute(UpdateDestinationRequest(
            destination_id=saved_ids[0],
            name=unique_update_name
        ))
        assert update_result.success is True
        
        # 4. Verify update
        list_result_after_update = await container.list_destinations.execute(ListDestinationsRequest())
        updated_dest = None
        for dest in list_result_after_update.destinations:
            if dest.id == saved_ids[0]:
                updated_dest = dest
                break
        
        assert updated_dest is not None
        assert updated_dest.name == unique_update_name
        
        # 5. Delete second destination
        delete_result = await container.delete_destination.execute(DeleteDestinationRequest(
            destination_id=saved_ids[1]
        ))
        assert delete_result.success is True
        
        # 6. Verify final state
        final_list_result = await container.list_destinations.execute(ListDestinationsRequest())
        assert final_list_result.success is True
        
        # Count remaining destinations
        remaining_count = 0
        for dest in final_list_result.destinations:
            if dest.id in saved_ids:
                remaining_count += 1
        
        assert remaining_count == 2  # 3 - 1 deleted = 2 remaining
    
    @pytest.mark.asyncio
    async def test_sqlite_database_file_creation(self, container_with_db):
        """Test that SQLite database file is created."""
        import os
        from pathlib import Path
        
        # Check if database file exists
        db_path = Path("destinations.db")
        assert db_path.exists() is True
        assert db_path.stat().st_size > 0  # File is not empty
        
        # Test that we can read from the file
        container = await container_with_db()
        list_result = await container.list_destinations.execute(ListDestinationsRequest())
        assert list_result.success is True
    
    @pytest.mark.asyncio
    async def test_sqlite_persistence_across_containers(self):
        """Test that data persists across different container instances."""
        # First container - save data
        container1 = Container()
        await container1.initialize_database()
        
        import uuid
        unique_name = f"Persistence Test Office {uuid.uuid4().hex[:8]}"
        save_result = await container1.save_destination.execute(SaveDestinationRequest(
            name=unique_name,
            address="999 Persistence Street, Ho Chi Minh City"
        ))
        assert save_result.success is True
        destination_id = save_result.destination_id
        
        # Second container - read data
        container2 = Container()
        await container2.initialize_database()
        
        list_result = await container2.list_destinations.execute(ListDestinationsRequest())
        assert list_result.success is True
        
        # Find our test destination
        test_dest = None
        for dest in list_result.destinations:
            if dest.id == destination_id:
                test_dest = dest
                break
        
        assert test_dest is not None
        assert test_dest.name == unique_name
        assert test_dest.address == "999 Persistence Street, Ho Chi Minh City"
        
        # Clean up
        await container2.delete_destination.execute(DeleteDestinationRequest(
            destination_id=destination_id
        ))
