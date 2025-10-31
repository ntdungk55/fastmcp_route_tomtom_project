"""Port cho Weather Provider - Interface để lấy thông tin thời tiết."""

from typing import Protocol

from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.weather_units import WeatherUnits
from app.domain.entities.weather import Weather


class WeatherProvider(Protocol):
    """Interface cho weather provider (WeatherAPI.com, etc.)."""
    
    async def get_current_weather(
        self, 
        coordinates: LatLon,
        units: WeatherUnits,
        language: str
    ) -> Weather:
        """Lấy thông tin thời tiết hiện tại tại địa điểm.
        
        Args:
            coordinates: LatLon value object chứa tọa độ
            units: WeatherUnits value object chứa đơn vị đo lường
            language: Ngôn ngữ cho mô tả thời tiết (vi, en, etc.)
            
        Returns:
            Weather entity với thông tin thời tiết
            
        Raises:
            ApplicationError nếu có lỗi khi gọi API
            DomainError nếu dữ liệu không hợp lệ
        """
        ...

