"""
Request handler service cho MCP requests.
Thuộc Application layer - orchestration logic.
"""
import logging
from typing import Any, Dict, Optional
from app.application.services.validation_service import get_validation_service
from app.infrastructure.logging.logger import get_logger


class RequestHandlerService:
    """Service để xử lý và validate MCP requests."""
    
    def __init__(self):
        self._validation_service = get_validation_service()
        self._logger = get_logger(__name__)
    
    def validate_mcp_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Validate MCP request format.
        
        Args:
            request_data: Raw request data
            
        Returns:
            Optional[str]: Error message nếu có lỗi, None nếu hợp lệ
        """
        try:
            # Kiểm tra required fields
            if "jsonrpc" not in request_data:
                return "Missing 'jsonrpc' field"
            
            if request_data.get("jsonrpc") != "2.0":
                return "Invalid jsonrpc version. Must be '2.0'"
            
            if "method" not in request_data:
                return "Missing 'method' field"
            
            if "id" not in request_data:
                return "Missing 'id' field"
            
            # Validate method-specific params
            method = request_data.get("method")
            if method == "initialize":
                return self._validate_initialize_request(request_data)
            elif method == "tools/call":
                return self._validate_tool_call_request(request_data)
            elif method == "tools/list":
                return self._validate_tools_list_request(request_data)
            
            return None  # Valid request
            
        except Exception as e:
            self._logger.error(f"Request validation error: {e}")
            return f"Request validation failed: {str(e)}"
    
    def _validate_initialize_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Validate initialize request."""
        params = request_data.get("params", {})
        
        if "protocolVersion" not in params:
            return "Missing 'protocolVersion' in initialize params"
        
        if "capabilities" not in params:
            return "Missing 'capabilities' in initialize params"
        
        # clientInfo is optional but if present should be valid
        client_info = params.get("clientInfo")
        if client_info is not None:
            if not isinstance(client_info, dict):
                return "clientInfo must be an object"
            if "name" not in client_info:
                return "clientInfo.name is required"
        
        return None
    
    def _validate_tool_call_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Validate tools/call request."""
        params = request_data.get("params", {})
        
        if "name" not in params:
            return "Missing 'name' in tool call params"
        
        if "arguments" not in params:
            return "Missing 'arguments' in tool call params"
        
        return None
    
    def _validate_tools_list_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Validate tools/list request."""
        # tools/list không cần params đặc biệt
        return None
    
    def log_validation_error(self, error_message: str, request_data: Dict[str, Any]) -> None:
        """Log validation error với context."""
        self._logger.warning(
            f"Request validation failed: {error_message}",
            extra={
                "request_method": request_data.get("method"),
                "request_id": request_data.get("id"),
                "error": error_message
            }
        )


# Factory function
def get_request_handler_service() -> RequestHandlerService:
    """Factory function để lấy request handler service."""
    return RequestHandlerService()


