"""
Block Flow Service - Triển khai luồng xử lý theo sơ đồ .drawio
Thuộc Application layer - orchestration logic cho các block.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict

from app.application.services.validation_service import get_validation_service
from app.infrastructure.logging.logger import get_logger


@dataclass
class RequestContext:
    """Context cho request processing."""
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    timestamp: str = None
    trace_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.trace_id is None:
            self.trace_id = f"trace-{uuid.uuid4().hex[:8]}"


@dataclass
class ValidationResult:
    """Kết quả validation từ BLK-1-01."""
    is_valid: bool
    errors: Optional[list] = None
    validated_data: Optional[dict] = None


@dataclass
class APIResponse:
    """Response từ API call."""
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
    metadata: Optional[dict] = None


class RouteValidationService:
    """
    Service xử lý luồng theo các block trong sơ đồ .drawio
    
    Luồng chính:
    BLK-1-00 → BLK-1-01 → BLK-1-02 → BLK-1-04 → BLK-1-09 → BLK-1-10 → BLK-1-12
    """
    
    def __init__(self):
        self._validation_service = get_validation_service()
        self._logger = get_logger(__name__)
    
    async def process_mcp_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        BLK-1-00: ListenMCPRequest - Entry point xử lý MCP request
        
        Args:
            request_data: JSON-RPC 2.0 request từ MCP Client
            
        Returns:
            Dict: Response cho MCP Client
        """
        request_id = request_data.get("id", f"req-{uuid.uuid4().hex[:8]}")
        context = RequestContext(
            request_id=request_id,
            client_id=request_data.get("client_id", "unknown")
        )
        
        self._logger.info(f"BLK-1-00: Received request {request_id} for method {request_data.get('method')}")
        
        try:
            # Parse và validate JSON-RPC request
            parsed_request = await self._blk_1_00_parse_request(request_data, context)
            
            # Forward to validation
            validation_result = await self._blk_1_01_validate_input(parsed_request, context)
            
            # Check for errors
            if not validation_result.is_valid:
                return await self._blk_1_02_handle_validation_error(validation_result, context)
            
            # Continue with success flow
            return await self._blk_1_02_continue_success_flow(validation_result, context)
            
        except Exception as e:
            self._logger.error(f"BLK-1-00: Critical error processing request {request_id}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": "Server error occurred",
                    "data": {"internal_error": str(e)}
                }
            }
    
    async def _blk_1_00_parse_request(self, request_data: Dict[str, Any], context: RequestContext) -> Dict[str, Any]:
        """
        BLK-1-00: Parse và validate JSON-RPC request format
        """
        self._logger.debug(f"BLK-1-00: Parsing request {context.request_id}")
        
        # Validate JSON-RPC format
        if request_data.get("jsonrpc") != "2.0":
            raise ValueError("Invalid jsonrpc version. Must be '2.0'")
        
        if "method" not in request_data:
            raise ValueError("Missing 'method' field")
        
        if "id" not in request_data:
            raise ValueError("Missing 'id' field")
        
        # Parse method và params
        method = request_data.get("method")
        params = request_data.get("params", {})
        
        parsed_request = {
            "request_id": context.request_id,
            "method": method,
            "params": params,
            "context": context
        }
        
        # Log parsed request (sanitized)
        self._logger.info(f"BLK-1-00: Parsed request {context.request_id} - method: {method}")
        
        return parsed_request
    
    async def _blk_1_01_validate_input(self, parsed_request: Dict[str, Any], context: RequestContext) -> ValidationResult:
        """
        BLK-1-01: ValidateInputParams - Validate TomTom routing parameters
        """
        self._logger.debug(f"BLK-1-01: Validating input for request {context.request_id}")
        
        method = parsed_request.get("method")
        params = parsed_request.get("params", {})
        
        if method == "tools/call":
            return await self._validate_tool_call_params(params, context)
        elif method == "initialize":
            return ValidationResult(is_valid=True, validated_data=params)
        elif method == "tools/list":
            return ValidationResult(is_valid=True, validated_data={})
        else:
            return ValidationResult(
                is_valid=False,
                errors=[{"code": "UNKNOWN_METHOD", "message": f"Unknown method: {method}"}]
            )
    
    async def _validate_tool_call_params(self, params: Dict[str, Any], context: RequestContext) -> ValidationResult:
        """Validate tool call parameters."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return ValidationResult(
                is_valid=False,
                errors=[{"code": "MISSING_TOOL_NAME", "message": "Tool name is required"}]
            )
        
        # Validate specific tool parameters
        if tool_name == "calculate_route":
            return await self._validate_calculate_route_params(arguments, context)
        elif tool_name == "get_detailed_route":
            return await self._validate_detailed_route_params(arguments, context)
        else:
            # For other tools, basic validation
            return ValidationResult(is_valid=True, validated_data={"tool_name": tool_name, "arguments": arguments})
    
    async def _validate_calculate_route_params(self, arguments: Dict[str, Any], context: RequestContext) -> ValidationResult:
        """Validate calculate_route parameters."""
        errors = []
        
        # Check required coordinates
        required_coords = ["origin_lat", "origin_lon", "dest_lat", "dest_lon"]
        for coord in required_coords:
            if coord not in arguments:
                errors.append({
                    "code": "MISSING_COORDINATE",
                    "field": coord,
                    "message": f"Missing required coordinate: {coord}"
                })
        
        # Validate coordinate ranges
        if not errors:
            try:
                origin_lat = float(arguments.get("origin_lat"))
                origin_lon = float(arguments.get("origin_lon"))
                dest_lat = float(arguments.get("dest_lat"))
                dest_lon = float(arguments.get("dest_lon"))
                
                if not (-90 <= origin_lat <= 90):
                    errors.append({
                        "code": "INVALID_COORD_RANGE",
                        "field": "origin_lat",
                        "message": "Latitude must be between -90 and 90"
                    })
                
                if not (-180 <= origin_lon <= 180):
                    errors.append({
                        "code": "INVALID_COORD_RANGE", 
                        "field": "origin_lon",
                        "message": "Longitude must be between -180 and 180"
                    })
                
                if not (-90 <= dest_lat <= 90):
                    errors.append({
                        "code": "INVALID_COORD_RANGE",
                        "field": "dest_lat", 
                        "message": "Latitude must be between -90 and 90"
                    })
                
                if not (-180 <= dest_lon <= 180):
                    errors.append({
                        "code": "INVALID_COORD_RANGE",
                        "field": "dest_lon",
                        "message": "Longitude must be between -180 and 180"
                    })
                
            except (ValueError, TypeError):
                errors.append({
                    "code": "INVALID_COORDINATE_FORMAT",
                    "message": "Coordinates must be valid numbers"
                })
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        # Valid parameters
        validated_data = {
            "tool_name": "calculate_route",
            "origin": {
                "lat": float(arguments.get("origin_lat")),
                "lon": float(arguments.get("origin_lon"))
            },
            "destination": {
                "lat": float(arguments.get("dest_lat")),
                "lon": float(arguments.get("dest_lon"))
            },
            "travel_mode": arguments.get("travel_mode", "car")
        }
        
        return ValidationResult(is_valid=True, validated_data=validated_data)
    
    async def _validate_detailed_route_params(self, arguments: Dict[str, Any], context: RequestContext) -> ValidationResult:
        """Validate get_detailed_route parameters."""
        errors = []
        
        # Check required addresses
        if "origin_address" not in arguments:
            errors.append({
                "code": "MISSING_ORIGIN_ADDRESS",
                "message": "origin_address is required"
            })
        
        if "destination_address" not in arguments:
            errors.append({
                "code": "MISSING_DESTINATION_ADDRESS", 
                "message": "destination_address is required"
            })
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        validated_data = {
            "tool_name": "get_detailed_route",
            "origin_address": arguments.get("origin_address"),
            "destination_address": arguments.get("destination_address"),
            "travel_mode": arguments.get("travel_mode", "car"),
            "country_set": arguments.get("country_set", "VN"),
            "language": arguments.get("language", "vi")
        }
        
        return ValidationResult(is_valid=True, validated_data=validated_data)
    
    async def _blk_1_02_handle_validation_error(self, validation_result: ValidationResult, context: RequestContext) -> Dict[str, Any]:
        """
        BLK-1-02: CheckError - Handle validation errors
        """
        self._logger.warning(f"BLK-1-02: Validation failed for request {context.request_id} with {len(validation_result.errors)} errors")
        
        # Format error response
        error_messages = [error.get("message", "Unknown error") for error in validation_result.errors]
        
        return {
            "jsonrpc": "2.0",
            "id": context.request_id,
            "error": {
                "code": -32602,  # Invalid params
                "message": "Invalid parameters",
                "data": {
                    "validation_errors": validation_result.errors,
                    "summary": f"Validation failed: {'; '.join(error_messages)}"
                }
            }
        }
    
    async def _blk_1_02_continue_success_flow(self, validation_result: ValidationResult, context: RequestContext) -> Dict[str, Any]:
        """
        BLK-1-02: CheckError - Continue with success flow
        """
        self._logger.info(f"BLK-1-02: Validation passed for request {context.request_id}, continuing to next step")
        
        # For now, return success response
        # In full implementation, this would continue to BLK-1-04, BLK-1-09, etc.
        
        return {
            "jsonrpc": "2.0",
            "id": context.request_id,
            "result": {
                "status": "success",
                "message": "Request validated successfully",
                "validated_data": validation_result.validated_data
            }
        }


# Factory function
def get_route_validation_service() -> RouteValidationService:
    """Factory function để lấy route validation service."""
    return RouteValidationService()

