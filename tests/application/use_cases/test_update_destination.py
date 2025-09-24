"""Test cases for UpdateDestinationUseCase."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from app.application.dto.update_destination_dto import UpdateDestinationRequest, UpdateDestinationResponse
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO, GeocodeResponseDTO, GeocodingResultDTO, AddressDTO
from app.application.use_cases.update_destination import UpdateDestinationUseCase
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon


class TestUpdateDestinationUseCase:
    """Test cases for UpdateDestinationUseCase."""
    
    @pytest.fixture
    def mock_destination_repository(self):
        """Mock destination repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_geocoding_provider(self):
        """Mock geocoding provider."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_destination_repository, mock_geocoding_provider):
        """Create use case with mocked dependencies."""
        return UpdateDestinationUseCase(
            destination_repository=mock_destination_repository,
            geocoding_provider=mock_geocoding_provider
        )
    
    @pytest.fixture
    def sample_request(self):
        """Sample update destination request."""
        return UpdateDestinationRequest(
            destination_id="test-id-123",
            name="Updated Office",
            address="456 New St"
        )
    
    @pytest.fixture
    def sample_destination(self):
        """Sample destination entity."""
        return Destination(
            id="test-id-123",
            name="Original Office",
            address="123 Old St",
            coordinates=LatLon(10.0, 106.0),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_geocode_response(self):
        """Sample geocode response."""
        return GeocodeResponseDTO(
            results=[
                GeocodingResultDTO(
                    position=LatLon(11.0, 107.0),
                    address=AddressDTO(
                        freeform_address="456 New St, New City, Vietnam"
                    )
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_update_destination_success(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request,
        sample_destination,
        sample_geocode_response
    ):
        """Test successful destination update."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_destination_repository.find_by_name.return_value = None  # No conflict with new name
        mock_geocoding_provider.geocode_address.return_value = sample_geocode_response
        mock_destination_repository.save.return_value = sample_destination
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is True
        assert result.destination_id == "test-id-123"
        assert "Updated Office" in result.message
        assert result.error is None
        
        # Verify geocoding was called
        mock_geocoding_provider.geocode_address.assert_called_once()
        geocode_call = mock_geocoding_provider.geocode_address.call_args[0][0]
        assert isinstance(geocode_call, GeocodeAddressCommandDTO)
        assert geocode_call.address == "456 New St"
        
        # Verify repository was called
        mock_destination_repository.find_by_id.assert_called_once_with("test-id-123")
        mock_destination_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_destination_not_found(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request
    ):
        """Test updating non-existent destination."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = None
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "not found" in result.error
        assert "test-id-123" in result.error
        
        # Verify geocoding was not called
        mock_geocoding_provider.geocode_address.assert_not_called()
        mock_destination_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_destination_geocoding_failed(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request,
        sample_destination
    ):
        """Test updating destination when geocoding fails."""
        # Arrange
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_geocoding_provider.geocode_address.return_value = GeocodeResponseDTO(results=[])
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "Could not find coordinates" in result.error
        assert "456 New St" in result.error
        
        # Verify save was not called
        mock_destination_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_destination_name_only(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_destination
    ):
        """Test updating destination name only."""
        # Arrange
        request = UpdateDestinationRequest(
            destination_id="test-id-123",
            name="New Name Only"
        )
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_destination_repository.find_by_name.return_value = None  # No conflict with new name
        mock_destination_repository.save.return_value = sample_destination
        
        # Act
        result = await use_case.execute(request)
        
        # Assert
        assert result.success is True
        assert result.destination_id == "test-id-123"
        assert "New Name Only" in result.message
        
        # Verify geocoding was not called (address not changed)
        mock_geocoding_provider.geocode_address.assert_not_called()
        
        # Verify save was called
        mock_destination_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_destination_name_conflict(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_destination
    ):
        """Test updating destination with conflicting name."""
        # Arrange
        request = UpdateDestinationRequest(
            destination_id="test-id-123",
            name="Conflicting Name"
        )
        conflicting_destination = Destination(
            id="other-id",
            name="Conflicting Name",
            address="Other Address",
            coordinates=LatLon(12.0, 108.0),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_destination_repository.find_by_id.return_value = sample_destination
        mock_destination_repository.find_by_name.return_value = conflicting_destination
        
        # Act
        result = await use_case.execute(request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "already exists" in result.error
        assert "Conflicting Name" in result.error
        
        # Verify save was not called
        mock_destination_repository.save.assert_not_called()
