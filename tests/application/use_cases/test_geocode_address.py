"""Tests cho GeocodeAddress Use Case."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.application.dto.geocoding_dto import (
    AddressDTO,
    GeocodeAddressCommandDTO,
    GeocodeResponseDTO,
    GeocodingResultDTO,
)
from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.use_cases.geocode_address import GeocodeAddress
from app.domain.value_objects.latlon import LatLon


class TestGeocodeAddress:
    """Test suite cho GeocodeAddress Use Case."""
    
    @pytest.fixture
    def mock_geocoding_provider(self):
        """Mock GeocodingProvider cho testing."""
        return Mock(spec=GeocodingProvider)
    
    @pytest.fixture
    def use_case(self, mock_geocoding_provider):
        """GeocodeAddress use case instance."""
        return GeocodeAddress(mock_geocoding_provider)
    
    @pytest.fixture
    def sample_command(self):
        """Sample command DTO."""
        return GeocodeAddressCommandDTO(
            address="123 Nguyen Hue, Ho Chi Minh City",
            country_set="VN",
            limit=1,
            language="vi-VN"
        )
    
    @pytest.fixture
    def sample_response(self):
        """Sample response DTO."""
        address = AddressDTO(
            freeform_address="123 Nguyen Hue, Ho Chi Minh City, Vietnam",
            country="Vietnam",
            country_code="VN",
            municipality="Ho Chi Minh City",
            street_name="Nguyen Hue"
        )
        
        result = GeocodingResultDTO(
            position=LatLon(10.7769, 106.7009),
            address=address,
            confidence=0.95
        )
        
        return GeocodeResponseDTO(
            results=[result],
            summary={"numResults": 1}
        )
    
    @pytest.mark.asyncio
    async def test_geocode_address_success(
        self, 
        use_case, 
        mock_geocoding_provider, 
        sample_command, 
        sample_response
    ):
        """Test geocoding thành công."""
        # Arrange
        mock_geocoding_provider.geocode_address = AsyncMock(return_value=sample_response)
        
        # Act
        result = await use_case.handle(sample_command)
        
        # Assert
        assert result == sample_response
        mock_geocoding_provider.geocode_address.assert_called_once_with(sample_command)
    
    @pytest.mark.asyncio
    async def test_geocode_address_empty_results(
        self, 
        use_case, 
        mock_geocoding_provider, 
        sample_command
    ):
        """Test geocoding trả về kết quả rỗng."""
        # Arrange
        empty_response = GeocodeResponseDTO(results=[], summary={"numResults": 0})
        mock_geocoding_provider.geocode_address = AsyncMock(return_value=empty_response)
        
        # Act
        result = await use_case.handle(sample_command)
        
        # Assert
        assert result.results == []
        assert len(result.results) == 0
        mock_geocoding_provider.geocode_address.assert_called_once_with(sample_command)
    
    @pytest.mark.asyncio
    async def test_geocode_address_provider_exception(
        self, 
        use_case, 
        mock_geocoding_provider, 
        sample_command
    ):
        """Test xử lý exception từ provider."""
        # Arrange
        mock_geocoding_provider.geocode_address = AsyncMock(
            side_effect=Exception("Provider error")
        )
        
        # Act & Assert
        with pytest.raises(Exception, match="Provider error"):
            await use_case.handle(sample_command)
