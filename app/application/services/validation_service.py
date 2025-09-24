"""
Validation service cho input validation.
Thuộc Application layer - business logic validation.
"""
from typing import Union


class ValidationService:
    """Service để validate input data."""
    
    @staticmethod
    def safe_float_convert(value: Union[str, float, int]) -> float:
        """
        Convert string, int, or float to float safely.
        
        Args:
            value: Giá trị cần convert
            
        Returns:
            float: Giá trị đã convert
            
        Raises:
            ValueError: Nếu không thể convert
        """
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).strip())
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert '{value}' to float: {e}")
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> None:
        """
        Validate latitude và longitude.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Raises:
            ValueError: Nếu coordinates không hợp lệ
        """
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180")
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> None:
        """
        Validate string không rỗng.
        
        Args:
            value: Giá trị string
            field_name: Tên field để hiển thị trong error
            
        Raises:
            ValueError: Nếu string rỗng hoặc None
        """
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty")


# Factory function
def get_validation_service() -> ValidationService:
    """Factory function để lấy validation service."""
    return ValidationService()


