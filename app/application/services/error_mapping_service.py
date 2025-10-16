"""
Error Mapping Service - BLK-1-03: MapValidationErrorsToUserMessages
Map validation errors thành user-friendly messages cho AI.
"""

from typing import Any, Dict, List
from dataclasses import dataclass

from app.infrastructure.logging.logger import get_logger


@dataclass
class UserFriendlyError:
    """User-friendly error message."""
    code: str
    message: str
    hint: str
    details: Dict[str, Any] = None


class ErrorMappingService:
    """
    BLK-1-03: MapValidationErrorsToUserMessages - Map validation errors to user messages
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._error_mappings = self._initialize_error_mappings()
    
    def _initialize_error_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize error code mappings."""
        return {
            # Validation errors
            "MISSING_COORDINATE": {
                "vi": "Thiếu tọa độ bắt buộc",
                "en": "Missing required coordinate",
                "hint_vi": "Vui lòng cung cấp đầy đủ tọa độ điểm xuất phát và điểm đến",
                "hint_en": "Please provide complete coordinates for origin and destination"
            },
            "INVALID_COORD_RANGE": {
                "vi": "Tọa độ không hợp lệ",
                "en": "Invalid coordinate range",
                "hint_vi": "Vĩ độ phải từ -90 đến 90, kinh độ phải từ -180 đến 180",
                "hint_en": "Latitude must be between -90 and 90, longitude between -180 and 180"
            },
            "INVALID_COORDINATE_FORMAT": {
                "vi": "Định dạng tọa độ không đúng",
                "en": "Invalid coordinate format",
                "hint_vi": "Tọa độ phải là số hợp lệ (ví dụ: 21.0285, 105.8542)",
                "hint_en": "Coordinates must be valid numbers (e.g., 21.0285, 105.8542)"
            },
            "MISSING_TOOL_NAME": {
                "vi": "Thiếu tên công cụ",
                "en": "Missing tool name",
                "hint_vi": "Vui lòng chỉ định tên công cụ cần sử dụng",
                "hint_en": "Please specify the tool name to use"
            },
            "MISSING_ORIGIN_ADDRESS": {
                "vi": "Thiếu địa chỉ điểm xuất phát",
                "en": "Missing origin address",
                "hint_vi": "Vui lòng cung cấp địa chỉ điểm xuất phát",
                "hint_en": "Please provide the origin address"
            },
            "MISSING_DESTINATION_ADDRESS": {
                "vi": "Thiếu địa chỉ điểm đến",
                "en": "Missing destination address",
                "hint_vi": "Vui lòng cung cấp địa chỉ điểm đến",
                "hint_en": "Please provide the destination address"
            },
            "UNKNOWN_METHOD": {
                "vi": "Phương thức không được hỗ trợ",
                "en": "Unknown method",
                "hint_vi": "Vui lòng sử dụng các phương thức được hỗ trợ",
                "hint_en": "Please use supported methods"
            },
            
            # API errors
            "API_KEY_NOT_CONFIGURED": {
                "vi": "Chưa cấu hình API key",
                "en": "API key not configured",
                "hint_vi": "Hệ thống chưa được cấu hình API key. Vui lòng liên hệ quản trị viên",
                "hint_en": "System not configured with API key. Please contact administrator"
            },
            "API_KEY_INVALID": {
                "vi": "API key không hợp lệ",
                "en": "Invalid API key",
                "hint_vi": "API key có định dạng không đúng. Vui lòng kiểm tra cấu hình",
                "hint_en": "API key has invalid format. Please check configuration"
            },
            "API_KEY_UNAUTHORIZED": {
                "vi": "API key không được ủy quyền",
                "en": "API key unauthorized",
                "hint_vi": "API key không có quyền truy cập. Vui lòng kiểm tra quyền hạn",
                "hint_en": "API key lacks access permissions. Please check permissions"
            },
            "RATE_LIMIT": {
                "vi": "Vượt quá giới hạn truy cập",
                "en": "Rate limit exceeded",
                "hint_vi": "Đã vượt quá giới hạn số lượng yêu cầu. Vui lòng thử lại sau",
                "hint_en": "Request limit exceeded. Please try again later"
            },
            "TIMEOUT": {
                "vi": "Yêu cầu quá thời gian chờ",
                "en": "Request timeout",
                "hint_vi": "Yêu cầu mất quá nhiều thời gian. Vui lòng thử lại hoặc chọn tuyến đường ngắn hơn",
                "hint_en": "Request took too long. Please try again or choose a shorter route"
            },
            "SERVICE_UNAVAILABLE": {
                "vi": "Dịch vụ tạm thời không khả dụng",
                "en": "Service temporarily unavailable",
                "hint_vi": "Dịch vụ bản đồ tạm thời gặp sự cố. Vui lòng thử lại sau",
                "hint_en": "Mapping service temporarily unavailable. Please try again later"
            },
            "INVALID_REQUEST": {
                "vi": "Yêu cầu không hợp lệ",
                "en": "Invalid request",
                "hint_vi": "Thông tin yêu cầu không đúng. Vui lòng kiểm tra lại dữ liệu đầu vào",
                "hint_en": "Request information is incorrect. Please check input data"
            }
        }
    
    async def map_validation_errors_to_user_messages(self, validation_errors: List[Dict[str, Any]], 
                                                   locale: str = "vi") -> List[UserFriendlyError]:
        """
        BLK-1-03: Map validation errors to user-friendly messages
        
        Args:
            validation_errors: List of validation errors
            locale: Language locale ("vi" | "en")
            
        Returns:
            List[UserFriendlyError]: User-friendly error messages
        """
        self._logger.info(f"BLK-1-03: Mapping {len(validation_errors)} validation errors to user messages")
        
        user_errors = []
        
        for error in validation_errors:
            error_code = error.get("code", "UNKNOWN_ERROR")
            field = error.get("field", "")
            
            # Get error mapping
            mapping = self._error_mappings.get(error_code, {})
            
            if not mapping:
                # Fallback for unknown errors
                mapping = {
                    "vi": f"Lỗi không xác định: {error_code}",
                    "en": f"Unknown error: {error_code}",
                    "hint_vi": "Vui lòng thử lại hoặc liên hệ hỗ trợ",
                    "hint_en": "Please try again or contact support"
                }
            
            # Create user-friendly error
            user_error = UserFriendlyError(
                code=error_code,
                message=mapping.get(locale, mapping.get("vi", "Unknown error")),
                hint=mapping.get(f"hint_{locale}", mapping.get("hint_vi", "Please try again")),
                details={
                    "field": field,
                    "original_error": error.get("message", ""),
                    "locale": locale
                }
            )
            
            user_errors.append(user_error)
        
        self._logger.info(f"BLK-1-03: Mapped to {len(user_errors)} user-friendly errors")
        return user_errors
    
    async def map_api_error_to_user_message(self, api_error: Dict[str, Any], 
                                          locale: str = "vi") -> UserFriendlyError:
        """
        Map API error to user-friendly message
        
        Args:
            api_error: API error dictionary
            locale: Language locale
            
        Returns:
            UserFriendlyError: User-friendly error message
        """
        error_code = api_error.get("code", "UNKNOWN_ERROR")
        
        # Get error mapping
        mapping = self._error_mappings.get(error_code, {})
        
        if not mapping:
            # Fallback for unknown errors
            mapping = {
                "vi": "Lỗi hệ thống không xác định",
                "en": "Unknown system error",
                "hint_vi": "Vui lòng thử lại sau hoặc liên hệ hỗ trợ",
                "hint_en": "Please try again later or contact support"
            }
        
        return UserFriendlyError(
            code=error_code,
            message=mapping.get(locale, mapping.get("vi", "Unknown error")),
            hint=mapping.get(f"hint_{locale}", mapping.get("hint_vi", "Please try again")),
            details={
                "original_error": api_error.get("message", ""),
                "status_code": api_error.get("status_code"),
                "retry_after": api_error.get("retry_after"),
                "locale": locale
            }
        )
    
    def format_errors_for_ai(self, user_errors: List[UserFriendlyError]) -> Dict[str, Any]:
        """
        Format user errors for AI consumption
        
        Args:
            user_errors: List of user-friendly errors
            
        Returns:
            Dict: Formatted errors for AI
        """
        if not user_errors:
            return {"has_errors": False}
        
        return {
            "has_errors": True,
            "error_count": len(user_errors),
            "errors": [
                {
                    "code": error.code,
                    "message": error.message,
                    "hint": error.hint,
                    "details": error.details
                }
                for error in user_errors
            ],
            "summary": f"Gặp {len(user_errors)} lỗi: {'; '.join([e.message for e in user_errors])}"
        }


# Factory function
def get_error_mapping_service() -> ErrorMappingService:
    """Factory function để lấy error mapping service."""
    return ErrorMappingService()

