"""Use case for checking weather at a location."""

from app.application.dto.weather_dto import (
    WeatherCheckRequest,
    WeatherResponse,
    WeatherData,  # For DTO response mapping
)
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.application.constants.validation_constants import DefaultValues
from app.application.errors import ApplicationError
from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.ports.weather_provider import WeatherProvider
from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.weather_units import WeatherUnits
from app.domain.entities.weather import Weather
from app.infrastructure.logging.logger import get_logger
import re

logger = get_logger(__name__)


class GetWeatherUseCase:
    """Use case for checking current weather at a location."""
    
    def __init__(
        self,
        geocoding_provider: GeocodingProvider,
        weather_provider: WeatherProvider,
    ):
        self._geocoding_provider = geocoding_provider
        self._weather_provider = weather_provider
    
    async def execute(self, request: WeatherCheckRequest) -> WeatherResponse:
        """Execute weather check."""
        try:
            logger.info(f"Checking weather for location: {request.location}")
            
            # Step 1: Get coordinates from location
            coordinates = await self._get_coordinates(
                request.location,
                request.language
            )
            
            # Step 2: Create WeatherUnits value object
            weather_units = WeatherUnits(request.units)
            
            # Step 3: Get weather data from provider (returns Weather entity)
            logger.info(f"Requesting weather from weather provider")
            weather_entity = await self._weather_provider.get_current_weather(
                coordinates=coordinates,
                units=weather_units,
                language=request.language
            )
            
            # Step 4: Map Weather entity to DTO for response
            weather_data_dto = self._map_weather_entity_to_dto(weather_entity)
            
            # Step 5: Build response
            response = WeatherResponse(
                success=True,
                weather_data=weather_data_dto,
                location=request.location,
                coordinates={"lat": coordinates.lat, "lon": coordinates.lon}
            )
            
            location_name_str = str(weather_entity.location_name) if weather_entity.location_name else "Unknown"
            logger.info(f"Successfully retrieved weather for {location_name_str}")
            return response
            
        except ApplicationError as e:
            logger.error(f"Application error checking weather: {str(e)}")
            return WeatherResponse(
                success=False,
                error_message=str(e),
                error_code="APPLICATION_ERROR"
            )
        except Exception as e:
            logger.error(f"Error checking weather: {str(e)}")
            return WeatherResponse(
                success=False,
                error_message=f"Failed to check weather: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def _get_coordinates(self, location: str, language: str) -> LatLon:
        """Get coordinates from location string (address or coordinates)."""
        # Check if location is coordinates (lat,lon format)
        coord_pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
        if re.match(coord_pattern, location.strip()):
            # Parse coordinates directly
            parts = location.strip().split(',')
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                
                # Validate coordinate ranges
                if not (-90 <= lat <= 90):
                    raise ApplicationError(f"Invalid latitude: {lat}. Must be between -90 and 90")
                if not (-180 <= lon <= 180):
                    raise ApplicationError(f"Invalid longitude: {lon}. Must be between -180 and 180")
                
                logger.info(f"Parsed coordinates directly: {lat}, {lon}")
                return LatLon(lat=lat, lon=lon)
            except (ValueError, IndexError) as e:
                raise ApplicationError(f"Invalid coordinate format: {location}")
        
        # Otherwise, treat as address and geocode
        logger.info(f"Geocoding address: {location}")
        geocode_cmd = GeocodeAddressCommandDTO(
            address=location,
            country_set="",
            limit=DefaultValues.DEFAULT_LIMIT,
            language=language
        )
        
        geocode_result = await self._geocoding_provider.geocode_address(geocode_cmd)
        
        if not geocode_result.results or len(geocode_result.results) == 0:
            raise ApplicationError(f"Could not find coordinates for location: {location}")
        
        first_result = geocode_result.results[0]
        coordinates = first_result.position
        
        logger.info(f"Geocoded {location} to {coordinates.lat}, {coordinates.lon}")
        return coordinates
    
    def _map_weather_entity_to_dto(self, weather_entity: Weather) -> WeatherData:
        """Map Weather domain entity to WeatherData DTO for response."""
        return WeatherData(
            temperature=weather_entity.temperature.value,
            feels_like=weather_entity.feels_like_temperature.value,
            humidity=weather_entity.humidity.value,
            pressure=weather_entity.pressure.value,
            description=weather_entity.description.value,
            wind_speed=weather_entity.wind_speed.value,
            wind_direction=weather_entity.wind_direction,
            visibility=weather_entity.visibility_meters,
            cloudiness=weather_entity.cloudiness_percent,
            sunrise=weather_entity.sunrise,
            sunset=weather_entity.sunset,
            location_name=weather_entity.location_name.value if weather_entity.location_name else None,
            country=weather_entity.location_name.country if weather_entity.location_name else None,
            icon_code=weather_entity.icon_code,
            units=weather_entity.units.value
        )

