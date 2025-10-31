"""Domain entity for Weather information."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.temperature import Temperature
from app.domain.value_objects.humidity import Humidity
from app.domain.value_objects.pressure import Pressure
from app.domain.value_objects.wind_speed import WindSpeed
from app.domain.value_objects.weather_description import WeatherDescription
from app.domain.value_objects.weather_units import WeatherUnits
from app.domain.value_objects.location_name import LocationName
from app.domain.errors import DomainError


class InvalidWeatherDataError(DomainError):
    """Raised when weather data is invalid."""
    pass


@dataclass
class Weather:
    """Domain entity representing weather information at a location."""
    
    # Location (required)
    coordinates: LatLon
    
    # Temperature (required fields - no defaults)
    temperature: Temperature
    feels_like_temperature: Temperature
    
    # Humidity and Pressure (required)
    humidity: Humidity
    pressure: Pressure
    
    # Weather description (required)
    description: WeatherDescription
    
    # Wind (required)
    wind_speed: WindSpeed
    
    # Optional fields (must come after required fields)
    location_name: Optional[LocationName] = None
    wind_direction: Optional[int] = None  # 0-360 degrees
    
    # Visibility and Cloudiness (optional)
    visibility_meters: Optional[int] = None
    cloudiness_percent: Optional[int] = None
    
    # Sunrise/Sunset (optional, ISO8601 strings)
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    
    # Icon code (optional)
    icon_code: Optional[str] = None
    
    # Timestamp
    observed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate weather entity."""
        self._validate_temperature_consistency()
        self._validate_wind_direction()
        self._validate_visibility()
        self._validate_cloudiness()
    
    def _validate_temperature_consistency(self) -> None:
        """Validate that temperature and feels_like use same units."""
        if self.temperature.units != self.feels_like_temperature.units:
            raise InvalidWeatherDataError(
                f"Temperature and feels_like_temperature must use same units. "
                f"Got {self.temperature.units} and {self.feels_like_temperature.units}",
                entity_id="weather",
                field="temperature_consistency",
                value=f"{self.temperature.units} vs {self.feels_like_temperature.units}"
            )
    
    def _validate_wind_direction(self) -> None:
        """Validate wind direction if provided."""
        if self.wind_direction is not None:
            if not isinstance(self.wind_direction, int):
                raise InvalidWeatherDataError(
                    f"Wind direction must be an integer, got {type(self.wind_direction)}",
                    entity_id="weather",
                    field="wind_direction",
                    value=self.wind_direction
                )
            
            if not (0 <= self.wind_direction <= 360):
                raise InvalidWeatherDataError(
                    f"Wind direction must be between 0 and 360 degrees, got {self.wind_direction}",
                    entity_id="weather",
                    field="wind_direction",
                    value=self.wind_direction
                )
    
    def _validate_visibility(self) -> None:
        """Validate visibility if provided."""
        if self.visibility_meters is not None:
            if not isinstance(self.visibility_meters, int):
                raise InvalidWeatherDataError(
                    f"Visibility must be an integer, got {type(self.visibility_meters)}",
                    entity_id="weather",
                    field="visibility_meters",
                    value=self.visibility_meters
                )
            
            if self.visibility_meters < 0:
                raise InvalidWeatherDataError(
                    f"Visibility cannot be negative: {self.visibility_meters}",
                    entity_id="weather",
                    field="visibility_meters",
                    value=self.visibility_meters
                )
            
            # Max visibility ~50km in perfect conditions
            if self.visibility_meters > 50000:
                raise InvalidWeatherDataError(
                    f"Visibility seems unreasonably high: {self.visibility_meters}m",
                    entity_id="weather",
                    field="visibility_meters",
                    value=self.visibility_meters
                )
    
    def _validate_cloudiness(self) -> None:
        """Validate cloudiness if provided."""
        if self.cloudiness_percent is not None:
            if not isinstance(self.cloudiness_percent, int):
                raise InvalidWeatherDataError(
                    f"Cloudiness must be an integer, got {type(self.cloudiness_percent)}",
                    entity_id="weather",
                    field="cloudiness_percent",
                    value=self.cloudiness_percent
                )
            
            if not (0 <= self.cloudiness_percent <= 100):
                raise InvalidWeatherDataError(
                    f"Cloudiness must be between 0 and 100 percent, got {self.cloudiness_percent}",
                    entity_id="weather",
                    field="cloudiness_percent",
                    value=self.cloudiness_percent
                )
    
    @property
    def units(self) -> WeatherUnits:
        """Get weather units from temperature."""
        return WeatherUnits(self.temperature.units)
    
    def get_temperature_difference(self) -> float:
        """Get difference between temperature and feels_like in Celsius."""
        temp_c = self.temperature.to_celsius()
        feels_like_c = self.feels_like_temperature.to_celsius()
        return abs(temp_c - feels_like_c)
    
    def is_hot(self, threshold_celsius: float = 30.0) -> bool:
        """Check if temperature is hot (above threshold)."""
        return self.temperature.to_celsius() > threshold_celsius
    
    def is_cold(self, threshold_celsius: float = 10.0) -> bool:
        """Check if temperature is cold (below threshold)."""
        return self.temperature.to_celsius() < threshold_celsius
    
    def is_windy(self, threshold_mps: float = 10.0) -> bool:
        """Check if wind speed is high (above threshold)."""
        return self.wind_speed.to_mps() > threshold_mps
    
    def is_humid(self, threshold_percent: int = 70) -> bool:
        """Check if humidity is high (above threshold)."""
        return self.humidity.value > threshold_percent
    
    def get_weather_summary(self) -> str:
        """Get human-readable weather summary."""
        temp_str = str(self.temperature)
        desc = str(self.description)
        location = str(self.location_name) if self.location_name else "Unknown location"
        
        return f"{location}: {temp_str}, {desc}, Humidity: {self.humidity}, Wind: {self.wind_speed}"

