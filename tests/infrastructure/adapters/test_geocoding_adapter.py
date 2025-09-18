"""Tests cho TomTomGeocodingAdapter."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.tomtom.acl.geocoding_mapper import TomTomGeocodingMapper
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter


class TestTomTomGeocodingAdapter:
    """Test suite cho TomTomGeocodingAdapter."""
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client."""
        return Mock(spec=AsyncApiClient)
    
    @pytest.fixture
    def mock_mapper(self):
        """Mock geocoding mapper."""
        return Mock(spec=TomTomGeocodingMapper)
    
    @pytest.fixture
    def adapter(self, mock_http_client):
        """TomTomGeocodingAdapter instance."""
        return TomTomGeocodingAdapter(
            base_url="https://api.tomtom.com",
            api_key="test_api_key",
            http=mock_http_client,
            timeout_sec=10
        )
    
    @pytest.fixture
    def sample_command(self):
        """Sample geocoding command."""
        return GeocodeAddressCommandDTO(
            address="123 Nguyen Hue",
            country_set="VN",
            limit=1,
            language="vi-VN"
        )
    
    @pytest.fixture
    def sample_tomtom_response(self):
        """Sample TomTom API response."""
        return {
            "summary": {"numResults": 1},
            "results": [
                {
                    "position": {"lat": 10.7769, "lon": 106.7009},
                    "address": {
                        "freeformAddress": "123 Nguyen Hue, Ho Chi Minh City, Vietnam",
                        "country": "Vietnam",
                        "countryCode": "VN",
                        "municipality": "Ho Chi Minh City",
                        "streetName": "Nguyen Hue"
                    },
                    "score": 0.95
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_geocode_address_success(
        self, 
        adapter, 
        mock_http_client,
        sample_command, 
        sample_tomtom_response
    ):
        """Test geocode address thành công."""
        # Arrange
        mock_http_client.send = AsyncMock(return_value=sample_tomtom_response)
        
        # Act
        result = await adapter.geocode_address(sample_command)
        
        # Assert
        assert mock_http_client.send.called
        call_args = mock_http_client.send.call_args[0][0]
        assert isinstance(call_args, RequestEntity)
        assert "123 Nguyen Hue" in call_args.url
        assert call_args.params["key"] == "test_api_key"
        assert call_args.params["countrySet"] == "VN"
        assert call_args.params["limit"] == "1"
        assert call_args.params["language"] == "vi-VN"
    
    @pytest.mark.asyncio
    async def test_geocode_address_http_error(
        self, 
        adapter, 
        mock_http_client,
        sample_command
    ):
        """Test xử lý HTTP error."""
        # Arrange
        mock_http_client.send = AsyncMock(side_effect=Exception("HTTP Error"))
        
        # Act & Assert
        with pytest.raises(Exception, match="HTTP Error"):
            await adapter.geocode_address(sample_command)
    
    def test_adapter_initialization(self, mock_http_client):
        """Test khởi tạo adapter đúng cách."""
        # Act
        adapter = TomTomGeocodingAdapter(
            base_url="https://api.tomtom.com/",  # có trailing slash
            api_key="test_key",
            http=mock_http_client,
            timeout_sec=15
        )
        
        # Assert
        assert adapter._base_url == "https://api.tomtom.com"  # stripped trailing slash
        assert adapter._api_key == "test_key"
        assert adapter._timeout_sec == 15
        assert isinstance(adapter._mapper, TomTomGeocodingMapper)
