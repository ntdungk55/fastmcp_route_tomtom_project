"""Test cases for ListDestinationsUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.application.dto.list_destinations_dto import ListDestinationsRequest, ListDestinationsResponse, DestinationSummary
from app.application.use_cases.list_destinations import ListDestinationsUseCase
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon


class TestListDestinationsUseCase:
    """Test cases for ListDestinationsUseCase."""
    
    @pytest.fixture
    def mock_destination_repository(self):
        """Mock destination repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_destination_repository):
        """Create use case with mocked dependencies."""
        return ListDestinationsUseCase(mock_destination_repository)
    
    @pytest.fixture
    def sample_request(self):
        """Sample list destinations request."""
        return ListDestinationsRequest()
    
    @pytest.fixture
    def sample_destinations(self):
        """Sample destinations."""
        return [
            Destination(
                id="test-id-1",
                name="Office 1",
                address="123 Main St",
                coordinates=LatLon(10.0, 106.0),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            Destination(
                id="test-id-2",
                name="Office 2",
                address="456 Second St",
                coordinates=LatLon(11.0, 107.0),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]

    @pytest.mark.asyncio
    async def test_list_destinations_success(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request,
        sample_destinations
    ):
        """Test successful destination listing."""
        # Arrange
        mock_destination_repository.list_all.return_value = sample_destinations
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is True
        assert result.total_count == 2
        assert len(result.destinations) == 2
        assert "Found 2 destinations" in result.message
        assert result.error is None
        
        # Verify destinations are properly converted
        assert isinstance(result.destinations[0], DestinationSummary)
        assert result.destinations[0].id == "test-id-1"
        assert result.destinations[0].name == "Office 1"
        assert result.destinations[0].address == "123 Main St"
        assert result.destinations[0].latitude == 10.0
        assert result.destinations[0].longitude == 106.0
        
        # Verify repository was called
        mock_destination_repository.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_destinations_empty(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request
    ):
        """Test listing destinations when none exist."""
        # Arrange
        mock_destination_repository.list_all.return_value = []
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is True
        assert result.total_count == 0
        assert len(result.destinations) == 0
        assert "Found 0 destinations" in result.message
        assert result.error is None

    @pytest.mark.asyncio
    async def test_list_destinations_repository_exception(
        self, 
        use_case, 
        mock_destination_repository,
        sample_request
    ):
        """Test listing destinations when repository throws exception."""
        # Arrange
        mock_destination_repository.list_all.side_effect = Exception("Database error")
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.total_count == 0
        assert len(result.destinations) == 0
        assert "Failed to list destinations" in result.error
        assert "Database error" in result.error
