"""Tests for WeatherAPIAdapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.adapters.weather_adapter import WeatherAPIAdapter
from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.weather_units import WeatherUnits
from app.domain.entities.weather import Weather
from app.application.errors import ApplicationError


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    client = AsyncMock()
    return client


@pytest.fixture
def weather_adapter(mock_http_client):
    """Create WeatherAPIAdapter instance."""
    return WeatherAPIAdapter(
        api_key="test_api_key_12345678901234567890",
        http=mock_http_client,
        timeout_sec=10
    )


@pytest.mark.asyncio
async def test_get_current_weather_success(weather_adapter, mock_http_client):
    """Test successful weather retrieval."""
    # Mock WeatherAPI.com API response
    mock_response = {
        "location": {
            "name": "Ho Chi Minh City",
            "region": "Ho Chi Minh",
            "country": "Vietnam",
            "lat": 10.8231,
            "lon": 106.6297,
            "tz_id": "Asia/Ho_Chi_Minh",
            "localtime_epoch": 1697123456,
            "localtime": "2023-10-13 17:30:56"
        },
        "current": {
            "last_updated_epoch": 1697123456,
            "last_updated": "2023-10-13 17:30",
            "temp_c": 32.5,
            "temp_f": 90.5,
            "feelslike_c": 38.2,
            "feelslike_f": 100.8,
            "condition": {
                "text": "mây thưa",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                "code": 1003
            },
            "wind_mph": 11.6,
            "wind_kph": 18.7,
            "wind_degree": 180,
            "wind_dir": "S",
            "pressure_mb": 1010.0,
            "pressure_in": 29.83,
            "precip_mm": 0.0,
            "precip_in": 0.0,
            "humidity": 75,
            "cloud": 20,
            "vis_km": 10.0,
            "uv": 6.0
        }
    }
    
    mock_http_client.send = AsyncMock(return_value=mock_response)
    
    cmd = WeatherCheckCommand(
        latitude=10.8231,
        longitude=106.6297,
        units="metric",
        language="vi"
    )
    
    result = await weather_adapter.get_current_weather(cmd)
    
    assert isinstance(result, Weather)
    assert result.temperature.value == 32.5
    assert result.feels_like_temperature.value == 38.2
    assert result.humidity.value == 75
    assert result.pressure.value == 1010
    assert result.description.value == "mây thưa"
    assert result.wind_speed.value == pytest.approx(18.7 / 3.6, rel=0.01)  # Convert km/h to m/s
    assert result.wind_direction == 180
    assert result.visibility_meters == 10000  # 10.0 km = 10000 meters
    assert result.cloudiness_percent == 20
    assert result.location_name is not None
    assert result.location_name.value == "Ho Chi Minh City"
    assert result.location_name.country == "Vietnam"
    # Icon code extracted from URL path
    assert result.icon_code is not None
    assert result.units.value == "metric"
    
    # Verify HTTP client was called correctly
    mock_http_client.send.assert_called_once()
    call_args = mock_http_client.send.call_args[0][0]
    assert "current.json" in call_args.url
    assert call_args.params["q"] == "10.8231,106.6297"
    assert call_args.params["lang"] == "vi"
    
    # Verify domain entity properties
    assert result.coordinates.lat == 10.8231
    assert result.coordinates.lon == 106.6297


@pytest.mark.asyncio
async def test_get_current_weather_api_error(weather_adapter, mock_http_client):
    """Test weather retrieval when API returns error."""
    # Mock WeatherAPI.com API error response
    mock_response = {
        "error": {
            "code": 1002,
            "message": "API key is invalid."
        }
    }
    
    mock_http_client.send = AsyncMock(return_value=mock_response)
    
    coordinates = LatLon(lat=10.8231, lon=106.6297)
    units = WeatherUnits("metric")
    
    with pytest.raises(ApplicationError) as exc_info:
        await weather_adapter.get_current_weather(
            coordinates=coordinates,
            units=units,
            language="vi"
        )
    
    assert "Weather API error" in str(exc_info.value)
    assert "API key is invalid" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_http_exception(weather_adapter, mock_http_client):
    """Test weather retrieval when HTTP request fails."""
    # Mock HTTP exception
    mock_http_client.send = AsyncMock(side_effect=Exception("Network error"))
    
    coordinates = LatLon(lat=10.8231, lon=106.6297)
    units = WeatherUnits("metric")
    
    with pytest.raises(ApplicationError) as exc_info:
        await weather_adapter.get_current_weather(
            coordinates=coordinates,
            units=units,
            language="vi"
        )
    
    assert "Failed to get weather data" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_missing_api_key():
    """Test adapter initialization without API key."""
    mock_http_client = AsyncMock()
    
    with pytest.raises(ValueError) as exc_info:
        WeatherAPIAdapter(
            api_key="",
            http=mock_http_client,
            timeout_sec=10
        )
    
    assert "WeatherAPI.com API key is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_weather_different_units(weather_adapter, mock_http_client):
    """Test weather retrieval with different units."""
    mock_response = {
        "location": {
            "name": "Test City",
            "country": "US",
            "lat": 40.7128,
            "lon": -74.0060
        },
        "current": {
            "temp_c": 32.5,
            "temp_f": 90.5,
            "feelslike_c": 37.8,
            "feelslike_f": 100.0,
            "pressure_mb": 1010,
            "humidity": 75,
            "condition": {"text": "clear sky", "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png"},
            "wind_kph": 10.8,
            "wind_degree": 180,
            "cloud": 0,
            "vis_km": 10.0
        }
    }
    
    mock_http_client.send = AsyncMock(return_value=mock_response)
    
    coordinates = LatLon(lat=40.7128, lon=-74.0060)
    units = WeatherUnits("imperial")
    
    result = await weather_adapter.get_current_weather(
        coordinates=coordinates,
        units=units,
        language="en"
    )
    
    assert result.units.value == "imperial"
    assert result.temperature.units == "imperial"
    # Verify lang parameter was passed to API (WeatherAPI.com doesn't use units in params)
    call_args = mock_http_client.send.call_args[0][0]
    assert call_args.params["lang"] == "en"


@pytest.mark.asyncio
async def test_get_current_weather_missing_fields(weather_adapter, mock_http_client):
    """Test weather retrieval with minimal API response."""
    # Mock minimal WeatherAPI.com API response (missing optional fields)
    mock_response = {
        "location": {
            "name": "Test City",
            "country": "Vietnam",
            "lat": 10.8231,
            "lon": 106.6297
        },
        "current": {
            "temp_c": 25.0,
            "temp_f": 77.0,
            "feelslike_c": 27.0,
            "feelslike_f": 80.6,
            "pressure_mb": 1013,
            "humidity": 60,
            "condition": {"text": "clear sky", "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png"},
            "wind_kph": 7.2,
            "wind_degree": 90,
            "cloud": 10
        }
    }
    
    mock_http_client.send = AsyncMock(return_value=mock_response)
    
    coordinates = LatLon(lat=10.8231, lon=106.6297)
    units = WeatherUnits("metric")
    
    result = await weather_adapter.get_current_weather(
        coordinates=coordinates,
        units=units,
        language="vi"
    )
    
    assert result.temperature.value == 25.0
    assert result.wind_direction == 90
    assert result.visibility_meters is None  # vis_km not in response
    assert result.sunrise is None  # astro data not in minimal response
    assert result.sunset is None  # astro data not in minimal response

