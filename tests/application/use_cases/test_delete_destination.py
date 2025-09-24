"""Test cases for DeleteDestinationUseCase."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from app.application.dto.delete_destination_dto import DeleteDestinationRequest, DeleteDestinationResponse
from app.application.use_cases.delete_destination import DeleteDestinationUseCase
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon


class TestDeleteDestinationUseCase:
    """Test cases for DeleteDestinationUseCase."""
    
    @pytest.fixture
    def mock_destination_repository(self):
        """Mock destination repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_destination_repository):
        """Create use case with mocked dependencies."""
        return DeleteDestinationUseCase(mock_destination_repository)
    
    @pytest.fixture
    def sample_request(self):
        """Sample delete destination request."""
        return DeleteDestinationRequest(destination_id="test-id-123")
    
    @pytest.fixture
    def sample_destination(self):
        """Sample destination entity."""
        return Destination(
            id="test-id-123",
            name="Test Office",
            address="123 Test St",
            coordinates=LatLon(10.0, 106.0),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_delete_destination_success(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request,
        sample_destination
    ):
        """Test successful destination deletion."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_destination_repository.delete.return_value = True
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is True
        assert result.deleted is True
        assert "Test Office" in result.message
        assert result.error is None
        
        # Verify repository was called
        mock_destination_repository.find_by_id.assert_called_once_with("test-id-123")
        mock_destination_repository.delete.assert_called_once_with("test-id-123")

    @pytest.mark.asyncio
    async def test_delete_destination_not_found(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request
    ):
        """Test deleting non-existent destination."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = None
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.deleted is False
        assert "not found" in result.error
        assert "test-id-123" in result.error
        
        # Verify delete was not called
        mock_destination_repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_destination_repository_exception(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request,
        sample_destination
    ):
        """Test deleting destination when repository throws exception."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_destination_repository.delete.side_effect = Exception("Database error")
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.deleted is False
        assert "Failed to delete destination" in result.error
        assert "Database error" in result.error

    @pytest.mark.asyncio
    async def test_delete_destination_delete_failed(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request,
        sample_destination
    ):
        """Test deleting destination when delete operation fails."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_destination_repository.delete.return_value = False
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.deleted is False
        assert "Failed to delete destination" in result.error
