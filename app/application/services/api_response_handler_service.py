"""
API Response Handler Service - BLK-1-10: CheckAPISuccess & BLK-1-11: ClassifyAndFormatErrorOutput
Kiểm tra kết quả API và format errors cho AI.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass

from app.application.services.error_classification_service import (
    ErrorClassificationService, get_error_classification_service
)
from app.application.services.error_mapping_service import (
    ErrorMappingService, get_error_mapping_service
)
from app.infrastructure.logging.logger import get_logger


@dataclass
class APIResponseResult:
    """API response result."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FormattedError:
    """Formatted error for AI."""
    error_category: str  # "USER_ERROR" | "SYSTEM_ERROR"
    error_type: str
    user_facing_error: Dict[str, Any]
    internal_error: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class APIResponseHandlerService:
    """
    BLK-1-10: CheckAPISuccess - Kiểm tra kết quả API call
    BLK-1-11: ClassifyAndFormatErrorOutput - Format API errors cho AI
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._error_classification_service = get_error_classification_service()
        self._error_mapping_service = get_error_mapping_service()
    
    async def check_api_success(self, api_response: Dict[str, Any], 
                              request_id: str) -> APIResponseResult:
        """
        BLK-1-10: Check API success
        
        Args:
            api_response: API response dictionary
            request_id: Request ID for logging
            
        Returns:
            APIResponseResult: Checked API response
        """
        self._logger.info(f"BLK-1-10: Checking API success for request {request_id}")
        
        success = api_response.get("success", False)
        
        if success:
            self._logger.info(f"BLK-1-10: API call successful for request {request_id}")
            return APIResponseResult(
                success=True,
                data=api_response.get("route_data"),
                metadata=api_response.get("metadata")
            )
        else:
            error = api_response.get("error", {})
            self._logger.warning(f"BLK-1-10: API call failed for request {request_id}: {error.get('code')}")
            
            return APIResponseResult(
                success=False,
                error=error,
                metadata=api_response.get("metadata")
            )
    
    async def classify_and_format_error_output(self, api_error: Dict[str, Any], 
                                             request_id: str,
                                             locale: str = "vi") -> FormattedError:
        """
        BLK-1-11: Classify and format error output for AI
        
        Args:
            api_error: API error dictionary
            request_id: Request ID for logging
            locale: Language locale
            
        Returns:
            FormattedError: Formatted error for AI
        """
        self._logger.info(f"BLK-1-11: Classifying and formatting error for request {request_id}")
        
        error_code = api_error.get("code", "UNKNOWN_ERROR")
        
        # Classify error
        classified_error = await self._error_classification_service.classify_api_error(
            api_error, locale
        )
        
        # Format for AI
        formatted_error = FormattedError(
            error_category=classified_error.category.value,
            error_type=classified_error.error_type.value,
            user_facing_error=classified_error.user_facing_error,
            internal_error=classified_error.internal_error,
            retry_after=classified_error.retry_after
        )
        
        self._logger.info(f"BLK-1-11: Formatted error {error_code} as {classified_error.category.value}")
        
        return formatted_error
    
    async def handle_api_response(self, api_response: Dict[str, Any], 
                                request_id: str,
                                locale: str = "vi") -> Dict[str, Any]:
        """
        Combined handler for API response (BLK-1-10 + BLK-1-11)
        
        Args:
            api_response: API response dictionary
            request_id: Request ID for logging
            locale: Language locale
            
        Returns:
            Dict: Processed response
        """
        # BLK-1-10: Check API success
        api_result = await self.check_api_success(api_response, request_id)
        
        if api_result.success:
            # Success path
            return {
                "api_success": True,
                "route_data": api_result.data,
                "metadata": api_result.metadata
            }
        else:
            # Error path - BLK-1-11: Format error
            formatted_error = await self.classify_and_format_error_output(
                api_result.error, request_id, locale
            )
            
            return {
                "api_success": False,
                "error": {
                    "category": formatted_error.error_category,
                    "type": formatted_error.error_type,
                    "user_facing": formatted_error.user_facing_error,
                    "internal": formatted_error.internal_error,
                    "retry_after": formatted_error.retry_after
                },
                "metadata": api_result.metadata
            }
    
    async def format_validation_errors_for_ai(self, validation_errors: list, 
                                            request_id: str,
                                            locale: str = "vi") -> Dict[str, Any]:
        """
        Format validation errors for AI (BLK-1-11 for validation errors)
        
        Args:
            validation_errors: List of validation errors
            request_id: Request ID for logging
            locale: Language locale
            
        Returns:
            Dict: Formatted validation errors
        """
        self._logger.info(f"BLK-1-11: Formatting {len(validation_errors)} validation errors for request {request_id}")
        
        # Classify validation errors (always USER_ERROR)
        classified_error = await self._error_classification_service.classify_validation_errors(
            validation_errors, locale
        )
        
        # Map to user-friendly messages
        user_errors = await self._error_mapping_service.map_validation_errors_to_user_messages(
            validation_errors, locale
        )
        
        # Format for AI
        return {
            "api_success": False,
            "error": {
                "category": "USER_ERROR",
                "type": "VALIDATION_ERROR",
                "user_facing": {
                    "type": "USER_ERROR",
                    "code": "VALIDATION_ERROR",
                    "message": "Thông tin đầu vào không hợp lệ",
                    "hint": "Vui lòng kiểm tra lại dữ liệu đã nhập",
                    "details": {
                        "validation_errors": [
                            {
                                "code": error.code,
                                "message": error.message,
                                "hint": error.hint,
                                "field": error.details.get("field", "")
                            }
                            for error in user_errors
                        ],
                        "error_count": len(validation_errors),
                        "locale": locale
                    }
                }
            }
        }
    
    async def create_success_response_for_ai(self, route_data: Dict[str, Any], 
                                           metadata: Dict[str, Any],
                                           request_id: str) -> Dict[str, Any]:
        """
        Create success response for AI
        
        Args:
            route_data: Route data from API
            metadata: API metadata
            request_id: Request ID
            
        Returns:
            Dict: Success response for AI
        """
        return {
            "api_success": True,
            "route_data": route_data,
            "metadata": metadata,
            "request_id": request_id
        }
    
    async def create_error_response_for_ai(self, error_category: str,
                                         error_type: str,
                                         user_message: str,
                                         hint: str,
                                         internal_error: Optional[Dict[str, Any]] = None,
                                         retry_after: Optional[int] = None) -> Dict[str, Any]:
        """
        Create error response for AI
        
        Args:
            error_category: Error category (USER_ERROR | SYSTEM_ERROR)
            error_type: Error type
            user_message: User-facing message
            hint: User hint
            internal_error: Internal error details
            retry_after: Retry after seconds
            
        Returns:
            Dict: Error response for AI
        """
        return {
            "api_success": False,
            "error": {
                "category": error_category,
                "type": error_type,
                "user_facing": {
                    "type": error_category,
                    "code": error_type,
                    "message": user_message,
                    "hint": hint,
                    "retry_after": retry_after
                },
                "internal": internal_error
            }
        }


# Factory function
def get_api_response_handler_service() -> APIResponseHandlerService:
    """Factory function để lấy API response handler service."""
    return APIResponseHandlerService()

