"""DTOs cho Weather Check feature."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherCheckRequest:
    """Request để kiểm tra thời tiết tại một địa điểm."""
    location: str  # Địa chỉ hoặc "lat,lon"
    units: str = "metric"  # "metric", "imperial", "kelvin"
    language: str = "vi"  # Ngôn ngữ cho mô tả thời tiết


@dataclass
class WeatherCheckCommand:
    """Command để query weather API."""
    latitude: float
    longitude: float
    units: str = "metric"
    language: str = "vi"


@dataclass
class WeatherData:
    """Thông tin thời tiết từ weather provider."""
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    description: str
    wind_speed: float
    wind_direction: Optional[int] = None
    visibility: Optional[int] = None
    cloudiness: Optional[int] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    location_name: Optional[str] = None
    country: Optional[str] = None
    icon_code: Optional[str] = None
    units: str = "metric"


@dataclass
class WeatherResponse:
    """Response từ weather checking service."""
    success: bool
    weather_data: Optional[WeatherData] = None
    location: Optional[str] = None
    coordinates: Optional[dict] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None



