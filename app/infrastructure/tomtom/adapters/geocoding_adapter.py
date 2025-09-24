"""TomTom Geocoding Adapter - Triển khai geocoding provider."""

from app.application.dto.geocoding_dto import (
    GeocodeAddressCommandDTO,
    GeocodeResponseDTO,
    StructuredGeocodeCommandDTO,
)
from app.application.ports.geocoding_provider import GeocodingProvider
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.domain.constants.api_constants import CountryConstants
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.tomtom.acl.geocoding_mapper import TomTomGeocodingMapper
from app.infrastructure.tomtom.endpoint import (
    GEOCODE_ADDRESS_PATH,
    SEARCH_STREET_PATH,
    STRUCTURED_GEOCODE_PATH,
)


class TomTomGeocodingAdapter(GeocodingProvider):
    """Adapter TomTom cho geocoding - chuyển đổi địa chỉ thành tọa độ.
    
    Đầu vào: GeocodeAddressCommandDTO, StructuredGeocodeCommandDTO
    Đầu ra: GeocodeResponseDTO chứa tọa độ và thông tin địa chỉ
    Chức năng: Gọi TomTom Geocoding API và chuyển đổi response thành domain DTOs
    """
    
    def __init__(self, base_url: str, api_key: str, http: AsyncApiClient, timeout_sec: int = 12):
        """Khởi tạo adapter với thông tin kết nối TomTom API."""
        self._base_url = base_url.rstrip("/")
        self._http = http
        self._timeout_sec = timeout_sec
        self._api_key = api_key
        self._mapper = TomTomGeocodingMapper()
    
    async def geocode_address(self, cmd: GeocodeAddressCommandDTO) -> GeocodeResponseDTO:
        """Chuyển đổi địa chỉ thành tọa độ.
        
        Đầu vào: GeocodeAddressCommandDTO (address, country_set, limit, language)
        Đầu ra: GeocodeResponseDTO chứa danh sách tọa độ và thông tin địa chỉ
        Xử lý: Gọi TomTom Geocoding API và map response sang domain DTO
        """
        # Tạo đường dẫn API với địa chỉ cần geocoding
        path = GEOCODE_ADDRESS_PATH.format(address=cmd.address)
        
        # Tạo HTTP request với các tham số geocoding
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "countrySet": cmd.country_set,
                "limit": str(cmd.limit),
                "language": cmd.language,
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và nhận response từ TomTom API
        payload = await self._http.send(req)
        
        # Chuyển đổi TomTom response thành domain DTO qua ACL mapper
        return self._mapper.to_domain_geocode_response(payload)
    
    async def structured_geocode(self, cmd: StructuredGeocodeCommandDTO) -> GeocodeResponseDTO:
        """Geocoding có cấu trúc cho giao lộ (intersection).
        
        Đầu vào: StructuredGeocodeCommandDTO (street_name, cross_street, municipality, etc.)
        Đầu ra: GeocodeResponseDTO chứa tọa độ giao lộ
        Xử lý: Gọi TomTom Structured Geocoding API để tìm giao lộ
        """
        # Tạo HTTP request cho structured geocoding
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{STRUCTURED_GEOCODE_PATH}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "countryCode": cmd.country_code,
                "streetName": cmd.street_name,
                "crossStreet": cmd.cross_street,
                "municipality": cmd.municipality,
                "limit": str(cmd.limit),
                "language": cmd.language,
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và chuyển đổi response
        payload = await self._http.send(req)
        return self._mapper.to_domain_geocode_response(payload)
    
    async def search_street_center(
        self, 
        street_name: str, 
        country_set: str = CountryConstants.DEFAULT,
        language: str = "vi-VN"
    ) -> GeocodeResponseDTO:
        """Tìm tọa độ trung tâm của đường phố.
        
        Đầu vào: street_name (tên đường), country_set, language
        Đầu ra: GeocodeResponseDTO chứa tọa độ trung tâm đường
        Xử lý: Gọi TomTom Search API với filter chỉ tìm đường (idxSet=Str)
        """
        # Tạo đường dẫn tìm kiếm với tên đường
        path = SEARCH_STREET_PATH.format(query=street_name)
        
        # Tạo request với filter chỉ tìm đường phố
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "countrySet": country_set,
                "idxSet": "Str",  # Chỉ tìm trong chỉ mục đường phố
                "limit": "1",
                "language": language,
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và chuyển đổi kết quả
        payload = await self._http.send(req)
        return self._mapper.to_domain_geocode_response(payload)