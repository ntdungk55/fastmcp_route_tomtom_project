"""TomTom Reverse Geocode Adapter - Triển khai reverse geocoding cho BLK-1-17."""

from app.application.dto.traffic_dto import ReverseGeocodeCommand, ReverseGeocodeResponse, GeocodedAddress
from app.application.ports.reverse_geocode_provider import ReverseGeocodeProvider
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.logging.logger import get_logger
import asyncio

logger = get_logger(__name__)


class TomTomReverseGeocodeAdapter(ReverseGeocodeProvider):
    """Adapter TomTom cho reverse geocoding - chuyển đổi coordinates thành địa chỉ.
    
    Chức năng: Gọi TomTom Reverse Geocode API để lấy địa chỉ từ coordinates
    """
    
    def __init__(self, base_url: str, api_key: str, http: AsyncApiClient, timeout_sec: int = 5):
        """Khởi tạo adapter với thông tin kết nối TomTom API."""
        self._base_url = base_url.rstrip("/")
        self._http = http
        self._timeout_sec = timeout_sec
        self._api_key = api_key

    async def reverse_geocode(self, cmd: ReverseGeocodeCommand) -> ReverseGeocodeResponse:
        """Reverse geocode coordinates thành địa chỉ.
        
        Args:
            cmd: ReverseGeocodeCommand chứa coordinates cần geocode
            
        Returns:
            ReverseGeocodeResponse với danh sách địa chỉ
        """
        logger.info(f"Reverse geocoding {len(cmd.coordinates)} coordinates")
        try:
            # Xử lý song song nhiều coordinates
            tasks = []
            for coord in cmd.coordinates:
                task = self._reverse_geocode_single(coord, cmd.language)
                tasks.append(task)
            
            # Chờ tất cả tasks hoàn thành
            logger.debug(f"Starting parallel geocoding of {len(tasks)} coordinates")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Xử lý kết quả
            addresses = []
            error_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Error geocoding coordinate {i}: {result}")
                    error_count += 1
                    # Tạo địa chỉ mặc định cho lỗi
                    addresses.append(GeocodedAddress(
                        coordinate=cmd.coordinates[i],
                        address="Địa chỉ không xác định",
                        freeform_address="Địa chỉ không xác định"
                    ))
                else:
                    addresses.append(result)
            
            success = error_count < len(cmd.coordinates)  # Success nếu ít nhất 1 coordinate thành công
            logger.info(f"Reverse geocoding completed: {len(addresses) - error_count} successful, {error_count} failed")
            
            return ReverseGeocodeResponse(
                success=success,
                addresses=addresses,
                error_message=f"{error_count} coordinates failed to geocode" if error_count > 0 else None
            )
            
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}", exc_info=True)
            return ReverseGeocodeResponse(
                success=False,
                addresses=[],
                error_message=f"Reverse geocoding failed: {str(e)}"
            )

    async def _reverse_geocode_single(self, coord, language: str) -> GeocodedAddress:
        """Reverse geocode một coordinate đơn lẻ."""
        try:
            lat, lon = coord.lat, coord.lon
            path = f"/search/2/reverseGeocode/{lat},{lon}.json"
            
            # Tạo HTTP request
            req = RequestEntity(
                method=HttpMethod.GET,
                url=f"{self._base_url}{path}",
                headers={"Accept": "application/json"},
                params={
                    "key": self._api_key,
                    "radius": "100",
                    "language": language
                },
                json=None,
                timeout_sec=self._timeout_sec,
            )
            
            # Gửi request và parse response
            payload = await self._http.send(req)
            return self._parse_geocode_response(coord, payload)
            
        except Exception as e:
            logger.error(f"Error geocoding single coordinate: {e}")
            return GeocodedAddress(
                coordinate=coord,
                address="Địa chỉ không xác định",
                freeform_address="Địa chỉ không xác định"
            )

    def _parse_geocode_response(self, coord, payload: dict) -> GeocodedAddress:
        """Parse TomTom reverse geocode response."""
        try:
            addresses = payload.get("addresses", [])
            if not addresses:
                return GeocodedAddress(
                    coordinate=coord,
                    address="Địa chỉ không xác định",
                    freeform_address="Địa chỉ không xác định"
                )
            
            # Lấy địa chỉ đầu tiên
            address_data = addresses[0]
            address_info = address_data.get("address", {})
            
            # Lấy freeform address
            freeform_address = address_info.get("freeformAddress", "")
            
            # Tạo địa chỉ đầy đủ từ các thành phần
            address_parts = []
            if address_info.get("streetName"):
                address_parts.append(address_info["streetName"])
            if address_info.get("municipality"):
                address_parts.append(address_info["municipality"])
            if address_info.get("countrySubdivision"):
                address_parts.append(address_info["countrySubdivision"])
            if address_info.get("country"):
                address_parts.append(address_info["country"])
            
            full_address = ", ".join(address_parts) if address_parts else freeform_address
            
            # Cắt bỏ các số ở cuối chuỗi địa chỉ
            cleaned_address = self._clean_address(full_address)
            cleaned_freeform = self._clean_address(freeform_address)
            
            return GeocodedAddress(
                coordinate=coord,
                address=cleaned_address,
                freeform_address=cleaned_freeform
            )
            
        except Exception as e:
            logger.error(f"Error parsing geocode response: {e}")
            return GeocodedAddress(
                coordinate=coord,
                address="Địa chỉ không xác định",
                freeform_address="Địa chỉ không xác định"
            )

    def _clean_address(self, address: str) -> str:
        """Cắt bỏ các số ở cuối chuỗi địa chỉ."""
        if not address:
            return address
        
        # Tìm vị trí cuối cùng của số
        import re
        # Tìm pattern số ở cuối chuỗi
        pattern = r'\s+\d+$'
        cleaned = re.sub(pattern, '', address.strip())
        
        return cleaned if cleaned else address
