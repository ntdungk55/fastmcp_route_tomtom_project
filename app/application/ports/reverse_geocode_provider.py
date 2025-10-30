"""Reverse Geocode Provider Port - Interface cho reverse geocoding services."""

from typing import Protocol
from app.application.dto.traffic_dto import ReverseGeocodeCommand, ReverseGeocodeResponse


class ReverseGeocodeProvider(Protocol):
    """Interface cho reverse geocoding services.
    
    Chức năng: Chuyển đổi coordinates thành địa chỉ
    """
    
    async def reverse_geocode(self, cmd: ReverseGeocodeCommand) -> ReverseGeocodeResponse:
        """Reverse geocode coordinates thành địa chỉ.
        
        Args:
            cmd: ReverseGeocodeCommand chứa coordinates cần geocode
            
        Returns:
            ReverseGeocodeResponse với danh sách địa chỉ
        """
        ...





