"""WeatherAPI.com Weather Adapter - Triển khai weather provider."""

from app.application.ports.weather_provider import WeatherProvider
from app.domain.value_objects.latlon import LatLon
from app.domain.value_objects.weather_units import WeatherUnits
from app.domain.value_objects.temperature import Temperature
from app.domain.value_objects.humidity import Humidity
from app.domain.value_objects.pressure import Pressure
from app.domain.value_objects.wind_speed import WindSpeed
from app.domain.value_objects.weather_description import WeatherDescription
from app.domain.value_objects.location_name import LocationName
from app.domain.entities.weather import Weather
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.logging.logger import get_logger
from app.application.errors import ApplicationError
from datetime import datetime, timezone

logger = get_logger(__name__)


class WeatherAPIAdapter(WeatherProvider):
    """
    Adapter cho WeatherAPI.com API để lấy thông tin thời tiết.
    
    WeatherAPI.com là một trong những dịch vụ weather API tốt nhất:
    - Free tier: 1,000,000 calls/tháng
    - API đơn giản, ổn định và đáng tin cậy
    - Tài liệu rõ ràng và chi tiết
    
    Đầu vào: LatLon (coordinates), WeatherUnits (units), language (string)
    Đầu ra: Weather entity (domain entity) chứa thông tin thời tiết hiện tại
    Chức năng: Gọi WeatherAPI.com Current Weather API và chuyển đổi response thành domain Weather entity
    """
    
    BASE_URL = "https://api.weatherapi.com/v1"
    
    def __init__(self, api_key: str, http: AsyncApiClient, timeout_sec: int = 10):
        """Khởi tạo adapter với thông tin kết nối WeatherAPI.com API."""
        self._api_key = api_key
        self._http = http
        self._timeout_sec = timeout_sec
        
        if not self._api_key:
            raise ValueError("WeatherAPI.com API key is required")
    
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
        logger.info(f"Getting weather for coordinates: {coordinates.lat}, {coordinates.lon}")
        
        try:
            # Build API request
            # WeatherAPI.com uses query format: q=lat,lon or q=address
            path = "/current.json"
            params = {
                "key": self._api_key,
                "q": f"{coordinates.lat},{coordinates.lon}",
                "lang": language,
            }
            
            # WeatherAPI.com units: API returns both metric and imperial
            # We'll extract the appropriate values based on units
            params["aqi"] = "no"  # Air quality info (optional)
            
            req = RequestEntity(
                method=HttpMethod.GET,
                url=f"{self.BASE_URL}{path}",
                headers={"Accept": "application/json"},
                params=params,
                json=None,
                timeout_sec=self._timeout_sec,
            )
            
            # Send request
            logger.debug(f"Sending weather request to: {req.url} (masked API key)")
            payload = await self._http.send(req)
            
            # Parse response
            # WeatherAPI.com returns error in "error" object
            if "error" in payload:
                error_obj = payload.get("error", {})
                error_msg = error_obj.get("message", "Unknown error")
                error_code = error_obj.get("code", "UNKNOWN")
                logger.error(f"Weather API error: {error_code} - {error_msg}")
                raise ApplicationError(f"Weather API error: {error_msg}")
            
            # Transform API response to domain Weather entity
            weather_entity = self._transform_response(payload, coordinates, units)
            
            logger.info(f"Successfully retrieved weather for {weather_entity.location_name}")
            return weather_entity
            
        except ApplicationError:
            raise
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            raise ApplicationError(f"Failed to get weather data: {str(e)}")
    
    def _transform_response(
        self, 
        api_response: dict, 
        coordinates: LatLon,
        units: WeatherUnits
    ) -> Weather:
        """Chuyển đổi WeatherAPI.com API response thành Weather domain entity."""
        location_data = api_response.get("location", {})
        current_data = api_response.get("current", {})
        
        # WeatherAPI.com structure:
        # location: { name, country, lat, lon, localtime_epoch, ... }
        # current: { temp_c, temp_f, feelslike_c, feelslike_f, condition, humidity, ... }
        
        condition = current_data.get("condition", {})
        
        # Get temperature based on units
        units_str = units.value
        if units_str == "imperial":
            temp_value = current_data.get("temp_f", 0.0)
            feels_like_value = current_data.get("feelslike_f", 0.0)
        elif units_str == "kelvin":
            temp_c = current_data.get("temp_c", 0.0)
            temp_value = temp_c + 273.15
            feels_like_value = (current_data.get("feelslike_c", 0.0)) + 273.15
        else:  # metric (default)
            temp_value = current_data.get("temp_c", 0.0)
            feels_like_value = current_data.get("feelslike_c", 0.0)
        
        # Create domain value objects
        temperature = Temperature(temp_value, units_str)
        feels_like_temp = Temperature(feels_like_value, units_str)
        humidity = Humidity(current_data.get("humidity", 0))
        pressure = Pressure(current_data.get("pressure_mb", 1013))
        description = WeatherDescription(condition.get("text", ""))
        
        # Wind speed: WeatherAPI.com uses km/h, convert to m/s for metric
        wind_kph = current_data.get("wind_kph", 0)
        wind_mps = wind_kph / 3.6
        wind_speed = WindSpeed(wind_mps, "metric")
        
        # Location name
        location_name = None
        if location_data.get("name"):
            location_name = LocationName(
                location_data.get("name"),
                location_data.get("country")
            )
        
        # Wind direction
        wind_direction = current_data.get("wind_degree", None)
        
        # Visibility (convert km to meters)
        visibility_km = current_data.get("vis_km", None)
        visibility_m = int(visibility_km * 1000) if visibility_km is not None else None
        
        # Cloudiness
        cloudiness = current_data.get("cloud", None)
        
        # Sunrise/Sunset - not available in current weather API
        sunrise = None
        sunset = None
        
        # Icon code
        icon_url = condition.get("icon", "")
        icon_code = None
        if icon_url:
            # Extract icon code from URL: //cdn.weatherapi.com/weather/64x64/day/116.png -> 116
            icon_code = icon_url.split("/")[-1].replace(".png", "").split("_")[-1]
        
        # Observed timestamp
        observed_at = None
        last_updated_epoch = current_data.get("last_updated_epoch")
        if last_updated_epoch:
            observed_at = datetime.fromtimestamp(last_updated_epoch, tz=timezone.utc)
        
        # Create and return Weather domain entity
        return Weather(
            coordinates=coordinates,
            location_name=location_name,
            temperature=temperature,
            feels_like_temperature=feels_like_temp,
            humidity=humidity,
            pressure=pressure,
            description=description,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            visibility_meters=visibility_m,
            cloudiness_percent=cloudiness,
            sunrise=sunrise,
            sunset=sunset,
            icon_code=icon_code,
            observed_at=observed_at
        )

