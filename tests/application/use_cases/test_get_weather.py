"""Tests for GetWeatherUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.get_weather import GetWeatherUseCase
from app.application.dto.weather_dto import (
    WeatherCheckRequest,
    WeatherResponse,
    WeatherData,
)
from app.application.dto.geocoding_dto import GeocodeResponseDTO, GeocodeResultDTO, AddressDTO, PositionDTO
from app.application.errors import ApplicationError
from app.domain.value_objects.latlon import LatLon


@pytest.fixture
def mock_geocoding_provider():
    """Mock geocoding provider."""
    provider = AsyncMock()
    
    # Mock successful geocoding response
    mock_response = GeocodeResponseDTO(
        results=[
            GeocodeResultDTO(
                position=PositionDTO(lat=10.8231, lon=106.6297),
                address=AddressDTO(
                    freeform_address="Ho Chi Minh City, Vietnam"
                )
            )
        ]
    )
    provider.geocode_address = AsyncMock(return_value=mock_response)
    
    return provider


@pytest.fixture
def mock_weather_provider():
    """Mock weather provider."""
    provider = AsyncMock()
    
    # Mock successful weather response
    mock_weather_data = WeatherData(
        temperature=32.5,
        feels_like=38.2,
        humidity=75,
        pressure=1010,
        description="mây thưa",
        wind_speed=5.2,
        wind_direction=180,
        visibility=10000,
        cloudiness=20,
        location_name="Ho Chi Minh City",
        country="VN",
        icon_code="02d",
        units="metric"
    )
    provider.get_current_weather = AsyncMock(return_value=mock_weather_data)
    
    return provider


@pytest.fixture
def use_case(mock_geocoding_provider, mock_weather_provider):
    """Create GetWeatherUseCase instance."""
    return GetWeatherUseCase(
        geocoding_provider=mock_geocoding_provider,
        weather_provider=mock_weather_provider
    )


@pytest.mark.asyncio
async def test_get_weather_by_address_success(use_case, mock_geocoding_provider, mock_weather_provider):
    """Test successful weather check by address."""
    request = WeatherCheckRequest(
        location="Ho Chi Minh City, Vietnam",
        units="metric",
        language="vi"
    )
    
    result = await use_case.execute(request)
    
    assert result.success is True
    assert result.location == "Ho Chi Minh City, Vietnam"
    assert result.coordinates == {"lat": 10.8231, "lon": 106.6297}
    assert result.weather_data is not None
    assert result.weather_data.temperature == 32.5
    assert result.weather_data.description == "mây thưa"
    assert result.weather_data.location_name == "Ho Chi Minh City"
    
    # Verify providers were called
    mock_geocoding_provider.geocode_address.assert_called_once()
    mock_weather_provider.get_current_weather.assert_called_once()


@pytest.mark.asyncio
async def test_get_weather_by_coordinates_success(use_case, mock_weather_provider):
    """Test successful weather check by coordinates."""
    request = WeatherCheckRequest(
        location="10.8231,106.6297",
        units="metric",
        language="vi"
    )
    
    result = await use_case.execute(request)
    
    assert result.success is True
    assert result.location == "10.8231,106.6297"
    assert result.coordinates == {"lat": 10.8231, "lon": 106.6297}
    assert result.weather_data is not None
    
    # Geocoding should not be called when coordinates are provided directly
    # Weather provider should be called with correct coordinates
    mock_weather_provider.get_current_weather.assert_called_once()


@pytest.mark.asyncio
async def test_get_weather_geocoding_failure(use_case, mock_geocoding_provider, mock_weather_provider):
    """Test weather check when geocoding fails."""
    # Mock geocoding failure
    mock_geocoding_provider.geocode_address = AsyncMock(
        return_value=GeocodeResponseDTO(results=[])
    )
    
    request = WeatherCheckRequest(
        location="InvalidLocation12345",
        units="metric",
        language="vi"
    )
    
    result = await use_case.execute(request)
    
    assert result.success is False
    assert result.error_message is not None
    assert "Could not find coordinates" in result.error_message
    
    # Weather provider should not be called
    mock_weather_provider.get_current_weather.assert_not_called()


@pytest.mark.asyncio
async def test_get_weather_weather_api_failure(use_case, mock_weather_provider):
    """Test weather check when weather API fails."""
    # Mock weather API failure
    mock_weather_provider.get_current_weather = AsyncMock(
        side_effect=ApplicationError("Weather API error")
    )
    
    request = WeatherCheckRequest(
        location="10.8231,106.6297",
        units="metric",
        language="vi"
    )
    
    result = await use_case.execute(request)
    
    assert result.success is False
    assert result.error_message is not None
    assert "Weather API error" in result.error_message


@pytest.mark.asyncio
async def test_get_weather_invalid_coordinates(use_case):
    """Test weather check with invalid coordinates."""
    request = WeatherCheckRequest(
        location="999,999",  # Invalid coordinates
        units="metric",
        language="vi"
    )
    
    result = await use_case.execute(request)
    
    assert result.success is False
    assert result.error_message is not None
    assert "Invalid" in result.error_message


@pytest.mark.asyncio
async def test_get_weather_different_units(use_case, mock_weather_provider):
    """Test weather check with different units."""
    request = WeatherCheckRequest(
        location="10.8231,106.6297",
        units="imperial",
        language="en"
    )
    
    result = await use_case.execute(request)
    
    assert result.success is True
    # Verify units are passed to weather provider
    call_args = mock_weather_provider.get_current_weather.call_args[0][0]
    assert call_args.units == "imperial"
    assert call_args.language == "en"


@pytest.mark.asyncio
async def test_get_weather_coordinate_parsing_edge_cases(use_case):
    """Test weather check with edge cases in coordinate parsing."""
    # Test with spaces
    request1 = WeatherCheckRequest(
        location="10.8231, 106.6297",  # Space after comma
        units="metric",
        language="vi"
    )
    result1 = await use_case.execute(request1)
    assert result1.success is True
    
    # Test invalid format
    request2 = WeatherCheckRequest(
        location="10.8231;106.6297",  # Semicolon instead of comma
        units="metric",
        language="vi"
    )
    result2 = await use_case.execute(request2)
    # Should try geocoding instead
    assert result2.success is False  # Will fail geocoding


