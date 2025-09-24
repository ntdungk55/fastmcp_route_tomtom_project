"""Test cases for SaveDestinationUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.application.dto.save_destination_dto import SaveDestinationRequest, SaveDestinationResponse
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO, GeocodeResponseDTO, GeocodingResultDTO, AddressDTO
from app.application.use_cases.save_destination import SaveDestinationUseCase
from app.domain.entities.destination import Destination
from app.domain.value_objects.latlon import LatLon


class TestSaveDestinationUseCase:
    """Test cases for SaveDestinationUseCase."""
    
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
        return SaveDestinationUseCase(
            destination_repository=mock_destination_repository,
            geocoding_provider=mock_geocoding_provider
        )
    
    @pytest.fixture
    def sample_request(self):
        """Sample save destination request."""
        return SaveDestinationRequest(
            name="Nơi làm việc",
            address="98A Nguyễn Như Kon Tum"
        )
    
    @pytest.fixture
    def sample_geocode_response(self):
        """Sample geocode response."""
        return GeocodeResponseDTO(
            results=[
                GeocodingResultDTO(
                    position=LatLon(14.361411, 108.001137),
                    address=AddressDTO(
                        freeform_address="98A Nguyễn Như Kon Tum, Kon Tum, Vietnam"
                    )
                )
            ]
        )
    
    @pytest.fixture
    def sample_destination(self):
        """Sample destination entity."""
        return Destination(
            id="test-id-123",
            name="Nơi làm việc",
            address="98A Nguyễn Như Kon Tum",
            coordinates=LatLon(14.361411, 108.001137),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_save_destination_success(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request,
        sample_geocode_response,
        sample_destination
    ):
        """Test successful destination saving."""
        # Arrange
        mock_destination_repository.find_by_name.return_value = None
        mock_geocoding_provider.geocode_address.return_value = sample_geocode_response
        mock_destination_repository.save.return_value = sample_destination
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is True
        assert result.destination_id == "test-id-123"
        assert "Nơi làm việc" in result.message
        assert "14.361411" in result.message
        assert "108.001137" in result.message
        assert result.error is None
        
        # Verify geocoding was called with correct parameters
        mock_geocoding_provider.geocode_address.assert_called_once()
        geocode_call = mock_geocoding_provider.geocode_address.call_args[0][0]
        assert isinstance(geocode_call, GeocodeAddressCommandDTO)
        assert geocode_call.address == "98A Nguyễn Như Kon Tum"
        assert geocode_call.country_set == "VN"
        assert geocode_call.limit == 1
        assert geocode_call.language == "vi-VN"
        
        # Verify repository was called
        mock_destination_repository.find_by_name.assert_called_once_with("Nơi làm việc")
        mock_destination_repository.save.assert_called_once()
        
        # Verify saved destination has correct coordinates
        saved_destination = mock_destination_repository.save.call_args[0][0]
        assert isinstance(saved_destination, Destination)
        assert saved_destination.name == "Nơi làm việc"
        assert saved_destination.address == "98A Nguyễn Như Kon Tum"
        assert saved_destination.coordinates.lat == 14.361411
        assert saved_destination.coordinates.lon == 108.001137

    @pytest.mark.asyncio
    async def test_save_destination_duplicate_name(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request,
        sample_destination
    ):
        """Test saving destination with duplicate name."""
        # Arrange
        mock_destination_repository.find_by_name.return_value = sample_destination
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "already exists" in result.error
        assert "Nơi làm việc" in result.error
        
        # Verify geocoding was not called
        mock_geocoding_provider.geocode_address.assert_not_called()
        mock_destination_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_destination_geocoding_failed(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request
    ):
        """Test saving destination when geocoding fails."""
        # Arrange
        mock_destination_repository.find_by_name.return_value = None
        mock_geocoding_provider.geocode_address.return_value = GeocodeResponseDTO(results=[])
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "Could not find coordinates" in result.error
        assert "98A Nguyễn Như Kon Tum" in result.error
        
        # Verify repository save was not called
        mock_destination_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_destination_geocoding_exception(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request
    ):
        """Test saving destination when geocoding throws exception."""
        # Arrange
        mock_destination_repository.find_by_name.return_value = None
        mock_geocoding_provider.geocode_address.side_effect = Exception("Geocoding API error")
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "Failed to save destination" in result.error
        assert "Geocoding API error" in result.error
        
        # Verify repository save was not called
        mock_destination_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_destination_repository_exception(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider,
        sample_request,
        sample_geocode_response
    ):
        """Test saving destination when repository throws exception."""
        # Arrange
        mock_destination_repository.find_by_name.return_value = None
        mock_geocoding_provider.geocode_address.return_value = sample_geocode_response
        mock_destination_repository.save.side_effect = Exception("Database error")
        
        # Act
        result = await use_case.execute(sample_request)
        
        # Assert
        assert result.success is False
        assert result.destination_id is None
        assert "Failed to save destination" in result.error
        assert "Database error" in result.error

    @pytest.mark.asyncio
    async def test_save_destination_with_different_address(
        self, 
        use_case, 
        mock_destination_repository, 
        mock_geocoding_provider
    ):
        """Test saving destination with different address (Ho Chi Minh)."""
        # Arrange
        request = SaveDestinationRequest(
            name="Nhà tôi",
            address="12 Lý Thái Tổ, Ho Chi Minh"
        )
        
        geocode_response = GeocodeResponseDTO(
            results=[
                GeocodingResultDTO(
                    position=LatLon(10.7680826, 106.6678283),
                    address=AddressDTO(
                        freeform_address="12 Lý Thái Tổ, Quận 1, Ho Chi Minh, Vietnam"
                    )
                )
            ]
        )
        
        destination = Destination(
            id="test-id-456",
            name="Nhà tôi",
            address="12 Lý Thái Tổ, Ho Chi Minh",
            coordinates=LatLon(10.7680826, 106.6678283),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_destination_repository.find_by_name.return_value = None
        mock_geocoding_provider.geocode_address.return_value = geocode_response
        mock_destination_repository.save.return_value = destination
        
        # Act
        result = await use_case.execute(request)
        
        # Assert
        assert result.success is True
        assert result.destination_id == "test-id-456"
        assert "Nhà tôi" in result.message
        assert "10.7680826" in result.message
        assert "106.6678283" in result.message
        
        # Verify geocoding was called with correct address
        geocode_call = mock_geocoding_provider.geocode_address.call_args[0][0]
        assert geocode_call.address == "12 Lý Thái Tổ, Ho Chi Minh"
