"""WeatherAPI.com Geocoding Adapter - Triển khai geocoding provider sử dụng WeatherAPI.com Search API."""

from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.dto.geocoding_dto import (
    GeocodeAddressCommandDTO,
    GeocodeResponseDTO,
    GeocodingResultDTO,
    AddressDTO,
    StructuredGeocodeCommandDTO,
)
from app.domain.value_objects.latlon import LatLon
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.logging.logger import get_logger
from app.application.errors import ApplicationError

logger = get_logger(__name__)


class WeatherAPIGeocodingAdapter(GeocodingProvider):
    """
    Adapter cho WeatherAPI.com Search API để geocode địa chỉ.
    
    WeatherAPI.com Search API:
    - Endpoint: /search.json
    - Parameters: q (query), key (API key)
    - Returns: List of locations with coordinates
    
    Đầu vào: GeocodeAddressCommandDTO (address, country_set, limit, language)
    Đầu ra: GeocodeResponseDTO chứa danh sách tọa độ và thông tin địa chỉ
    Chức năng: Gọi WeatherAPI.com Search API và chuyển đổi response thành domain DTO
    """
    
    BASE_URL = "https://api.weatherapi.com/v1"
    
    def __init__(self, api_key: str, http: AsyncApiClient, timeout_sec: int = 10):
        """Khởi tạo adapter với thông tin kết nối WeatherAPI.com API."""
        self._api_key = api_key
        self._http = http
        self._timeout_sec = timeout_sec
        
        if not self._api_key:
            raise ValueError("WeatherAPI.com API key is required")
    
    async def geocode_address(self, cmd: GeocodeAddressCommandDTO) -> GeocodeResponseDTO:
        """Chuyển đổi địa chỉ thành tọa độ sử dụng WeatherAPI.com Search API."""
        try:
            logger.info(f"Geocoding address with WeatherAPI.com: {cmd.address}")
            
            # WeatherAPI.com Search API endpoint
            path = "/search.json"
            params = {
                "key": self._api_key,
                "q": cmd.address,
            }
            
            # Build request
            req = RequestEntity(
                method=HttpMethod.GET,
                url=f"{self.BASE_URL}{path}",
                headers={"Accept": "application/json"},
                params=params,
                json=None,
                timeout_sec=self._timeout_sec,
            )
            
            # Send request
            payload = await self._http.send(req)
            
            # Transform WeatherAPI.com response to domain DTO
            return self._transform_search_response(payload, cmd.limit, cmd.address)
            
        except Exception as e:
            logger.error(f"Error geocoding address with WeatherAPI.com: {e}")
            raise ApplicationError(f"Failed to geocode address: {str(e)}")
    
    def _transform_search_response(
        self, 
        api_response: dict, 
        limit: int,
        original_query: str = ""
    ) -> GeocodeResponseDTO:
        """Chuyển đổi WeatherAPI.com Search API response thành GeocodeResponseDTO."""
        results = []
        
        # WeatherAPI.com Search API returns array of locations
        # Format: [{"id": 1, "name": "Location", "region": "...", "country": "...", "lat": 10.8231, "lon": 106.6297, ...}, ...]
        locations = api_response if isinstance(api_response, list) else []
        
        # Limit results
        limited_locations = locations[:limit] if limit > 0 else locations
        
        for location in limited_locations:
            try:
                # Extract coordinates
                lat = location.get("lat", 0.0)
                lon = location.get("lon", 0.0)
                
                if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                    logger.warning(f"Invalid coordinates in WeatherAPI.com response: {location}")
                    continue
                
                # Build address information
                name = location.get("name", "")
                region = location.get("region", "")
                country = location.get("country", "")
                
                # Create full address string
                address_parts = [name, region, country]
                full_address = ", ".join(filter(None, address_parts))
                
                # Create AddressDTO
                address_dto = AddressDTO(
                    freeform_address=full_address or original_query,
                    country=country,
                    country_code=location.get("tz_id", ""),  # Timezone ID often contains country code
                    municipality=region,
                    street_name=name if not region else None,
                )
                
                # Create GeocodingResultDTO
                result = GeocodingResultDTO(
                    position=LatLon(lat=float(lat), lon=float(lon)),
                    address=address_dto,
                    confidence=None,  # WeatherAPI.com doesn't provide confidence score
                )
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error parsing location from WeatherAPI.com response: {e}")
                continue
        
        return GeocodeResponseDTO(results=results)
    
    async def structured_geocode(self, cmd: StructuredGeocodeCommandDTO) -> GeocodeResponseDTO:
        """Structured geocoding - not supported by WeatherAPI.com, fallback to address geocoding."""
        logger.warning("Structured geocoding not supported by WeatherAPI.com, using address geocoding")
        # Convert structured geocode command to address geocode command
        address_parts = []
        if cmd.street_name:
            address_parts.append(cmd.street_name)
        if cmd.cross_street:
            address_parts.append(cmd.cross_street)
        if cmd.municipality:
            address_parts.append(cmd.municipality)
        if cmd.country_code:
            address_parts.append(cmd.country_code)
        
        address = " ".join(address_parts) if address_parts else ""
        
        address_cmd = GeocodeAddressCommandDTO(
            address=address,
            country_set=getattr(cmd, 'country_set', ""),
            limit=getattr(cmd, 'limit', 1),
            language=getattr(cmd, 'language', "vi-VN"),
        )
        return await self.geocode_address(address_cmd)
    
    async def search_street_center(
        self, 
        street_name: str, 
        country_set: str = "",
        language: str = "vi-VN"
    ) -> GeocodeResponseDTO:
        """Get street center position - uses address geocoding."""
        address_cmd = GeocodeAddressCommandDTO(
            address=street_name,
            country_set=country_set,
            limit=1,
            language=language,
        )
        return await self.geocode_address(address_cmd)

