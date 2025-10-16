"""
Error Classification Service - BLK-1-05: ClassifyErrorType
Phân loại lỗi thành USER_ERROR hoặc SYSTEM_ERROR.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from app.infrastructure.logging.logger import get_logger


class ErrorCategory(Enum):
    """Error categories."""
    USER_ERROR = "USER_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class ErrorType(Enum):
    """Error types."""
    # User errors
    INVALID_INPUT = "INVALID_INPUT"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    
    # System errors
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"


@dataclass
class ClassifiedError:
    """Classified error result."""
    category: ErrorCategory
    error_type: ErrorType
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    user_facing_error: Dict[str, Any]
    internal_error: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class ErrorClassificationService:
    """
    BLK-1-05: ClassifyErrorType - Phân loại lỗi thành USER_ERROR hoặc SYSTEM_ERROR
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._classification_rules = self._initialize_classification_rules()
    
    def _initialize_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error classification rules."""
        return {
            # User errors (4xx)
            "MISSING_COORDINATE": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "LOW",
                "user_message": "Thiếu thông tin tọa độ",
                "hint": "Vui lòng cung cấp đầy đủ tọa độ điểm xuất phát và điểm đến"
            },
            "INVALID_COORD_RANGE": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "LOW",
                "user_message": "Tọa độ không hợp lệ",
                "hint": "Vĩ độ phải từ -90 đến 90, kinh độ phải từ -180 đến 180"
            },
            "INVALID_COORDINATE_FORMAT": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "LOW",
                "user_message": "Định dạng tọa độ không đúng",
                "hint": "Tọa độ phải là số hợp lệ"
            },
            "MISSING_ORIGIN_ADDRESS": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "LOW",
                "user_message": "Thiếu địa chỉ điểm xuất phát",
                "hint": "Vui lòng cung cấp địa chỉ điểm xuất phát"
            },
            "MISSING_DESTINATION_ADDRESS": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "LOW",
                "user_message": "Thiếu địa chỉ điểm đến",
                "hint": "Vui lòng cung cấp địa chỉ điểm đến"
            },
            "UNKNOWN_METHOD": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "MEDIUM",
                "user_message": "Phương thức không được hỗ trợ",
                "hint": "Vui lòng sử dụng các phương thức được hỗ trợ"
            },
            
            # System errors (5xx, timeouts, config)
            "API_KEY_NOT_CONFIGURED": {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.CONFIGURATION_ERROR,
                "severity": "CRITICAL",
                "user_message": "Dịch vụ tạm thời không khả dụng",
                "hint": "Vui lòng thử lại sau hoặc liên hệ hỗ trợ",
                "internal_message": "TomTom API key not configured"
            },
            "API_KEY_INVALID": {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.CONFIGURATION_ERROR,
                "severity": "CRITICAL",
                "user_message": "Dịch vụ tạm thời không khả dụng",
                "hint": "Vui lòng thử lại sau hoặc liên hệ hỗ trợ",
                "internal_message": "TomTom API key format invalid"
            },
            "API_KEY_UNAUTHORIZED": {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.CONFIGURATION_ERROR,
                "severity": "HIGH",
                "user_message": "Dịch vụ tạm thời không khả dụng",
                "hint": "Vui lòng thử lại sau hoặc liên hệ hỗ trợ",
                "internal_message": "TomTom API key unauthorized"
            },
            "RATE_LIMIT": {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.SERVICE_UNAVAILABLE,
                "severity": "MEDIUM",
                "user_message": "Dịch vụ tạm thời quá tải",
                "hint": "Vui lòng thử lại sau",
                "retry_after": 60
            },
            "TIMEOUT": {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.TIMEOUT,
                "severity": "MEDIUM",
                "user_message": "Yêu cầu mất quá nhiều thời gian",
                "hint": "Vui lòng thử lại hoặc chọn tuyến đường ngắn hơn"
            },
            "SERVICE_UNAVAILABLE": {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.SERVICE_UNAVAILABLE,
                "severity": "HIGH",
                "user_message": "Dịch vụ tạm thời không khả dụng",
                "hint": "Vui lòng thử lại sau"
            },
            "INVALID_REQUEST": {
                "category": ErrorCategory.USER_ERROR,
                "error_type": ErrorType.INVALID_INPUT,
                "severity": "LOW",
                "user_message": "Thông tin yêu cầu không hợp lệ",
                "hint": "Vui lòng kiểm tra lại dữ liệu đầu vào"
            }
        }
    
    async def classify_error(self, error_code: str, error_data: Dict[str, Any], 
                           locale: str = "vi") -> ClassifiedError:
        """
        BLK-1-05: Classify error type
        
        Args:
            error_code: Error code
            error_data: Error data dictionary
            locale: Language locale
            
        Returns:
            ClassifiedError: Classified error result
        """
        self._logger.info(f"BLK-1-05: Classifying error {error_code}")
        
        # Get classification rule
        rule = self._classification_rules.get(error_code, {})
        
        if not rule:
            # Default classification for unknown errors
            rule = {
                "category": ErrorCategory.SYSTEM_ERROR,
                "error_type": ErrorType.EXTERNAL_API_ERROR,
                "severity": "MEDIUM",
                "user_message": "Lỗi hệ thống không xác định",
                "hint": "Vui lòng thử lại sau hoặc liên hệ hỗ trợ",
                "internal_message": f"Unknown error: {error_code}"
            }
        
        # Build classified error
        classified_error = ClassifiedError(
            category=rule["category"],
            error_type=rule["error_type"],
            severity=rule["severity"],
            user_facing_error={
                "type": rule["category"].value,
                "code": error_code,
                "message": rule["user_message"],
                "hint": rule["hint"],
                "details": {
                    "original_error": error_data.get("message", ""),
                    "locale": locale
                }
            },
            retry_after=rule.get("retry_after")
        )
        
        # Add internal error for system errors
        if rule["category"] == ErrorCategory.SYSTEM_ERROR:
            classified_error.internal_error = {
                "code": error_code,
                "message": rule.get("internal_message", rule["user_message"]),
                "severity": rule["severity"],
                "context": {
                    "original_error": error_data.get("message", ""),
                    "status_code": error_data.get("status_code"),
                    "retry_after": error_data.get("retry_after")
                }
            }
        
        self._logger.info(f"BLK-1-05: Classified error {error_code} as {rule['category'].value}")
        return classified_error
    
    async def classify_validation_errors(self, validation_errors: list, 
                                       locale: str = "vi") -> ClassifiedError:
        """
        Classify validation errors (always USER_ERROR)
        
        Args:
            validation_errors: List of validation errors
            locale: Language locale
            
        Returns:
            ClassifiedError: Classified error result
        """
        if not validation_errors:
            raise ValueError("No validation errors provided")
        
        # Validation errors are always user errors
        first_error = validation_errors[0]
        error_code = first_error.get("code", "VALIDATION_ERROR")
        
        return ClassifiedError(
            category=ErrorCategory.USER_ERROR,
            error_type=ErrorType.INVALID_INPUT,
            severity="LOW",
            user_facing_error={
                "type": "USER_ERROR",
                "code": "VALIDATION_ERROR",
                "message": "Thông tin đầu vào không hợp lệ",
                "hint": "Vui lòng kiểm tra lại dữ liệu đã nhập",
                "details": {
                    "validation_errors": validation_errors,
                    "error_count": len(validation_errors),
                    "locale": locale
                }
            }
        )
    
    async def classify_api_error(self, api_error: Dict[str, Any], 
                               locale: str = "vi") -> ClassifiedError:
        """
        Classify API error based on status code and error type
        
        Args:
            api_error: API error dictionary
            locale: Language locale
            
        Returns:
            ClassifiedError: Classified error result
        """
        error_code = api_error.get("code", "UNKNOWN_ERROR")
        status_code = api_error.get("status_code")
        
        # Classify based on HTTP status code if available
        if status_code:
            if 400 <= status_code < 500:
                # Client errors are user errors
                return await self._classify_client_error(error_code, api_error, locale)
            elif 500 <= status_code < 600:
                # Server errors are system errors
                return await self._classify_server_error(error_code, api_error, locale)
        
        # Fallback to error code classification
        return await self.classify_error(error_code, api_error, locale)
    
    async def _classify_client_error(self, error_code: str, api_error: Dict[str, Any], 
                                   locale: str) -> ClassifiedError:
        """Classify client error (4xx)."""
        return ClassifiedError(
            category=ErrorCategory.USER_ERROR,
            error_type=ErrorType.INVALID_INPUT,
            severity="LOW",
            user_facing_error={
                "type": "USER_ERROR",
                "code": error_code,
                "message": "Thông tin yêu cầu không hợp lệ",
                "hint": "Vui lòng kiểm tra lại dữ liệu đầu vào",
                "details": {
                    "original_error": api_error.get("message", ""),
                    "status_code": api_error.get("status_code"),
                    "locale": locale
                }
            }
        )
    
    async def _classify_server_error(self, error_code: str, api_error: Dict[str, Any], 
                                   locale: str) -> ClassifiedError:
        """Classify server error (5xx)."""
        return ClassifiedError(
            category=ErrorCategory.SYSTEM_ERROR,
            error_type=ErrorType.SERVICE_UNAVAILABLE,
            severity="HIGH",
            user_facing_error={
                "type": "SYSTEM_ERROR",
                "code": "SERVICE_TEMPORARILY_UNAVAILABLE",
                "message": "Dịch vụ tạm thời không khả dụng",
                "hint": "Vui lòng thử lại sau",
                "retry_after": api_error.get("retry_after")
            },
            internal_error={
                "code": error_code,
                "message": api_error.get("message", "Server error"),
                "severity": "HIGH",
                "context": {
                    "status_code": api_error.get("status_code"),
                    "retry_after": api_error.get("retry_after")
                }
            }
        )


# Factory function
def get_error_classification_service() -> ErrorClassificationService:
    """Factory function để lấy error classification service."""
    return ErrorClassificationService()

