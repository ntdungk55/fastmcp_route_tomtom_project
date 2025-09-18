"""TomTom Geocoding ACL Mapper - Chuyển đổi dữ liệu geocoding."""

from typing import Optional

from app.application.dto.geocoding_dto import (
    AddressDTO,
    GeocodeResponseDTO,
    GeocodingResultDTO,
)
from app.domain.value_objects.latlon import LatLon


class TomTomGeocodingMapper:
    """Mapper chuyển đổi TomTom geocoding responses thành domain DTOs.
    
    Chức năng: Tránh vendor lock-in bằng cách map TomTom format sang domain format
    """
    
    def to_domain_geocode_response(self, payload: dict) -> GeocodeResponseDTO:
        """Chuyển đổi TomTom geocoding response thành domain DTO.
        
        Đầu vào: dict - Raw response từ TomTom Geocoding API
        Đầu ra: GeocodeResponseDTO - Domain DTO với cấu trúc chuẩn
        Xử lý: Lấy thông tin position, address và confidence từ TomTom format
        """
        # Khởi tạo danh sách kết quả domain
        results = []
        
        # Duyệt qua tất cả kết quả từ TomTom và chuyển đổi
        for item in payload.get("results", []):
            # Trích xuất dữ liệu position và address từ TomTom format
            position_data = item.get("position", {})
            address_data = item.get("address", {})
            
            # Chuyển đổi tọa độ thành domain value object
            position = LatLon(
                lat=float(position_data.get("lat", 0.0)),
                lon=float(position_data.get("lon", 0.0))
            )
            
            # Chuyển đổi thông tin địa chỉ thành domain DTO
            address = AddressDTO(
                freeform_address=address_data.get("freeformAddress", ""),
                country=address_data.get("country"),
                country_code=address_data.get("countryCode"),
                municipality=address_data.get("municipality"),
                street_name=address_data.get("streetName")
            )
            
            # Trích xuất confidence score nếu có
            confidence = None
            score = item.get("score")
            if score is not None:
                confidence = float(score)
            
            # Tạo domain result DTO và thêm vào danh sách
            result = GeocodingResultDTO(
                position=position,
                address=address,
                confidence=confidence
            )
            results.append(result)
        
        # Trả về domain response DTO hoàn chỉnh
        return GeocodeResponseDTO(
            results=results,
            summary=payload.get("summary")
        )
