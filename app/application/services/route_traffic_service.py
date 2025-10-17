"""
Integrated Flow Service - Kết nối tất cả các block theo sơ đồ .drawio
Service này orchestrate toàn bộ luồng xử lý từ BLK-1-00 đến BLK-1-12
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass

from app.application.services.route_validation_service import (
    RouteValidationService, RequestContext, ValidationResult, APIResponse
)
from app.application.services.request_history_service import (
    RequestHistoryService, RequestHistoryRecord
)
from app.application.services.routing_api_service import (
    RoutingAPIService, RouteRequest, RouteResponse
)
from app.application.services.client_data_service import (
    ClientDataService
)
from app.application.services.traffic_analysis_service import (
    TrafficAnalysisService, get_traffic_analysis_service
)
from app.application.services.error_mapping_service import (
    ErrorMappingService, get_error_mapping_service
)
from app.application.services.error_classification_service import (
    ErrorClassificationService, get_error_classification_service
)
from app.application.services.system_error_handler_service import (
    SystemErrorHandlerService, get_system_error_handler_service, SystemErrorContext, ErrorSeverity
)
from app.application.services.destination_saver_service import (
    DestinationSaverService, get_destination_saver_service
)
from app.application.services.api_response_handler_service import (
    APIResponseHandlerService, get_api_response_handler_service
)
from app.application.services.request_result_updater_service import (
    RequestResultUpdaterService, get_request_result_updater_service
)
from app.infrastructure.logging.logger import get_logger


@dataclass
class RouteTrafficResult:
    """Kết quả cuối cùng của flow."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class RouteTrafficService:
    """
    Service xử lý luồng tìm đường đi và kiểm tra tình trạng giao thông
    Kết nối tất cả các block theo sơ đồ .drawio
    
    Luồng chính:
    BLK-1-00 → BLK-1-01 → BLK-1-02 → BLK-1-04 → BLK-1-07 (async) → BLK-1-09 → BLK-1-10 → BLK-1-12
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._validation_service = RouteValidationService()
        self._request_history_service = RequestHistoryService()
        self._routing_api_service = RoutingAPIService()
        self._client_data_service = ClientDataService()
        self._traffic_analysis_service = get_traffic_analysis_service()
        self._error_mapping_service = get_error_mapping_service()
        self._error_classification_service = get_error_classification_service()
        self._system_error_handler_service = get_system_error_handler_service()
        self._destination_saver_service = get_destination_saver_service()
        self._api_response_handler_service = get_api_response_handler_service()
        self._request_result_updater_service = get_request_result_updater_service()
        self._destination_repository = None  # Will be injected if needed
    
    def set_destination_repository(self, repository):
        """Inject destination repository (for BLK-1-04)."""
        self._destination_repository = repository
    
    async def process_route_traffic(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý luồng tìm đường đi và kiểm tra tình trạng giao thông từ BLK-1-00 đến BLK-1-12
        
        Args:
            request_data: JSON-RPC 2.0 request từ MCP Client
            
        Returns:
            Dict: Final response cho MCP Client
        """
        request_id = request_data.get("id", f"req-{uuid.uuid4().hex[:8]}")
        context = RequestContext(
            request_id=request_id,
            client_id=request_data.get("client_id", "unknown")
        )
        
        self._logger.info(f"Starting route traffic processing for request {request_id}")
        
        try:
            # BLK-1-00: ListenMCPRequest - Parse request
            parsed_request = await self._blk_1_00_parse_request(request_data, context)
            
            # BLK-1-07: SaveRequestHistory - Save initial request (async)
            asyncio.create_task(self._blk_1_07_save_request_history(parsed_request, context))
            
            # BLK-1-01: ValidateInputParams - Validate input
            validation_result = await self._blk_1_01_validate_input(parsed_request, context)
            
            # BLK-1-02: CheckError - Check validation result
            if not validation_result.is_valid:
                return await self._blk_1_02_handle_validation_error(validation_result, context)
            
            # BLK-1-04: CheckDestinationExists - Check if destination exists
            destination_check = await self._blk_1_04_check_destination_exists(validation_result, context)
            
            # BLK-1-09: RequestRoutingAPI - Call TomTom API
            api_response = await self._blk_1_09_request_routing_api(validation_result, destination_check, context)
            
            # BLK-1-10: CheckAPISuccess - Check API response
            if not api_response.success:
                return await self._blk_1_10_handle_api_error(api_response, context)
            
            # BLK-1-12: TransformSuccessDataForAI - Transform data for AI
            validated_data = validation_result.validated_data
            tool_name = validated_data.get("tool_name")
            
            if tool_name == "get_detailed_route":
                # Analyze traffic data trước khi tạo response
                traffic_analysis = await self._traffic_analysis_service.analyze_route_traffic(api_response.route_data)
                
                # Use detailed route response format với traffic data thực
                detailed_response = await self._client_data_service.create_detailed_route_response(
                    api_response.route_data, 
                    {
                        "request_id": context.request_id,
                        "travel_mode": validated_data.get("travel_mode", "car"),
                        "traffic_analysis": traffic_analysis
                    }
                )
                ai_response = detailed_response.to_dict()
            else:
                # Use standard AI response format
                ai_response = await self._blk_1_12_transform_for_ai(api_response, context)
            
            # BLK-1-13: UpdateRequestResult - Update request history with success
            asyncio.create_task(self._blk_1_13_update_request_result(
                request_id, "SUCCESS", api_response.metadata, context
            ))
            
            self._logger.info(f"Route traffic processing successful for request {request_id}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": ai_response
            }
            
        except Exception as e:
            self._logger.error(f"Route traffic processing failed for request {request_id}: {e}")
            
            # Update request history with error
            asyncio.create_task(self._blk_1_13_update_request_result(
                request_id, "ERROR", {"error": str(e)}, context
            ))
            
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
        """BLK-1-00: Parse và validate JSON-RPC request."""
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
        
        self._logger.info(f"BLK-1-00: Parsed request {context.request_id} - method: {method}")
        return parsed_request
    
    async def _blk_1_07_save_request_history(self, parsed_request: Dict[str, Any], context: RequestContext):
        """BLK-1-07: Save request history async."""
        try:
            method = parsed_request.get("method")
            params = parsed_request.get("params", {})
            
            if method == "tools/call":
                tool_name = params.get("name", "unknown")
                arguments = params.get("arguments", {})
            else:
                tool_name = method
                arguments = params
            
            record = RequestHistoryRecord(
                id=str(uuid.uuid4()),
                request_id=context.request_id,
                tool_name=tool_name,
                arguments=arguments,
                user_id=context.user_id,
                session_id=context.session_id,
                client_id=context.client_id,
                status="RECEIVED"
            )
            
            await self._request_history_service.save_request_history(record)
            self._logger.debug(f"BLK-1-07: Saved request history for {context.request_id}")
            
        except Exception as e:
            self._logger.warning(f"BLK-1-07: Failed to save request history for {context.request_id}: {e}")
    
    async def _blk_1_01_validate_input(self, parsed_request: Dict[str, Any], context: RequestContext) -> ValidationResult:
        """BLK-1-01: Validate input parameters."""
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
        """BLK-1-02: Handle validation errors."""
        self._logger.warning(f"BLK-1-02: Validation failed for request {context.request_id}")
        
        # Update request history with error
        asyncio.create_task(self._blk_1_13_update_request_result(
            context.request_id, "ERROR", {"validation_errors": validation_result.errors}, context
        ))
        
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
    
    async def _blk_1_04_check_destination_exists(self, validation_result: ValidationResult, context: RequestContext) -> Dict[str, Any]:
        """
        BLK-1-04: Check if destination exists in database with retry logic.
        
        Queries destination repository by address or coordinates.
        If found, returns cached destination data to potentially skip geocoding.
        Implements retry logic: 2 retries with 50ms backoff on DB timeout.
        """
        self._logger.debug(f"BLK-1-04: Checking destination exists for request {context.request_id}")
        
        # If no repository injected, skip check
        if not self._destination_repository:
            self._logger.debug("BLK-1-04: No destination repository available, skipping destination check")
            return {
                "destination_exists": False,
                "destination_data": None
            }
        
        try:
            # Extract destination info from validated data
            validated_data = validation_result.validated_data or {}
            destination_address = validated_data.get("destination_address")
            destination_coords = validated_data.get("destination_coordinates")
            
            if not destination_address and not destination_coords:
                self._logger.debug("BLK-1-04: No destination address or coordinates provided")
                return {
                    "destination_exists": False,
                    "destination_data": None
                }
            
            # Try to find destination with retry logic
            destination = await self._find_destination_with_retry(
                address=destination_address,
                coordinates=destination_coords,
                request_id=context.request_id
            )
            
            if destination:
                self._logger.info(
                    f"BLK-1-04: Destination found in cache (id={destination.id}, "
                    f"address={destination.address})"
                )
                return {
                    "destination_exists": True,
                    "destination_id": destination.id,
                    "destination_data": {
                        "id": destination.id,
                        "name": str(destination.name),
                        "address": str(destination.address),
                        "coordinates": {
                            "lat": destination.coordinates.lat,
                            "lon": destination.coordinates.lon
                        },
                        "created_at": destination.created_at.isoformat(),
                        "updated_at": destination.updated_at.isoformat()
                    }
                }
            else:
                self._logger.debug(f"BLK-1-04: Destination not found in cache for request {context.request_id}")
                return {
                    "destination_exists": False,
                    "destination_data": None
                }
                
        except Exception as e:
            self._logger.warning(
                f"BLK-1-04: Error checking destination exists for request {context.request_id}: {e}. "
                "Proceeding without cache."
            )
            # Fail-open: continue without cache if error
            return {
                "destination_exists": False,
                "destination_data": None
            }
    
    async def _find_destination_with_retry(self, address: str = None, coordinates: Dict = None, 
                                          request_id: str = None, max_retries: int = 2) -> Optional[Dict[str, Any]]:
        """
        Find destination with retry logic: 2 retries with 50ms backoff on timeout.
        
        Tries to find by address first, then by coordinates if address search fails.
        """
        backoff_ms = 50
        for attempt in range(max_retries + 1):
            try:
                # Try to search by address first
                if address:
                    results = await asyncio.wait_for(
                        self._destination_repository.search_by_name_and_address(address=address),
                        timeout=0.1  # 100ms timeout per query
                    )
                    if results and len(results) > 0:
                        return results[0]  # Return first match
                
                # Try to search by coordinates if address search failed or address not provided
                if coordinates and "lat" in coordinates and "lon" in coordinates:
                    # For coordinate-based search, we'd need geospatial query
                    # For now, return first result or None
                    pass
                
                return None
                
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    wait_time = (backoff_ms * (attempt + 1)) / 1000.0  # Convert to seconds
                    self._logger.debug(
                        f"BLK-1-04: DB query timeout on attempt {attempt + 1}, "
                        f"retrying in {wait_time*1000:.0f}ms..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self._logger.warning(
                        f"BLK-1-04: DB query timeout after {max_retries + 1} attempts for request {request_id}"
                    )
                    return None
                    
            except Exception as e:
                self._logger.warning(f"BLK-1-04: Error querying destination: {e}")
                return None
        
        return None
    
    async def _blk_1_09_request_routing_api(self, validation_result: ValidationResult, 
                                           destination_check: Dict[str, Any], context: RequestContext) -> RouteResponse:
        """BLK-1-09: Request routing from TomTom API."""
        self._logger.info(f"BLK-1-09: Requesting routing API for request {context.request_id}")
        
        validated_data = validation_result.validated_data
        tool_name = validated_data.get("tool_name")
        
        if tool_name == "get_detailed_route":
            # For get_detailed_route, we need to geocode addresses first
            return await self._handle_detailed_route_request(validated_data, context)
        else:
            # For calculate_route, use coordinates directly
            route_request = RouteRequest(
                origin=validated_data["origin"],
                destination=validated_data["destination"],
                travel_mode=validated_data.get("travel_mode", "car"),
                traffic=True
            )
            
            # Request context for API
            api_context = {
                "request_id": context.request_id,
                "timeout": 10000
            }
            
            return await self._routing_api_service.request_routing(route_request, api_context)
    
    async def _handle_detailed_route_request(self, validated_data: Dict[str, Any], context: RequestContext) -> RouteResponse:
        """Handle get_detailed_route request with geocoding."""
        try:
            # For now, return a mock response since we don't have geocoding service integrated
            # In a real implementation, this would:
            # 1. Geocode origin_address to get coordinates
            # 2. Geocode destination_address to get coordinates  
            # 3. Call routing API with coordinates
            # 4. Return detailed route data
            
            self._logger.info(f"BLK-1-09: Handling detailed route request for {context.request_id}")
            
            # Mock response for demonstration
            return RouteResponse(
                success=True,
                route_data={
                    "summary": {
                        "length_in_meters": 1500000,  # 1500km
                        "travel_time_in_seconds": 54000,  # 15 hours
                        "traffic_delay_in_seconds": 1800,  # 30 minutes
                        "departure_time": "2025-10-16T10:00:00+07:00",
                        "arrival_time": "2025-10-17T01:00:00+07:00"
                    },
                    "legs": [
                        {
                            "summary": {"lengthInMeters": 1500000, "travelTimeInSeconds": 54000},
                            "points": [
                                {"lat": 21.0285, "lon": 105.8542},
                                {"lat": 10.8231, "lon": 106.6297}
                            ]
                        }
                    ],
                    "sections": [
                        {
                            "start_point_index": 0,
                            "end_point_index": 1,
                            "section_type": "TRAVEL_MODE",
                            "travel_mode": "car"
                        }
                    ],
                    "guidance": {
                        "instructions": [
                            {
                                "message": "Head south on QL1A",
                                "maneuver": "DEPART",
                                "point": {"lat": 21.0285, "lon": 105.8542}
                            },
                            {
                                "message": "Continue on QL1A for 1500km",
                                "maneuver": "CONTINUE", 
                                "point": {"lat": 15.5, "lon": 106.2}
                            },
                            {
                                "message": "Arrive at destination",
                                "maneuver": "ARRIVE",
                                "point": {"lat": 10.8231, "lon": 106.6297}
                            }
                        ]
                    }
                },
                metadata={
                    "provider": "tomtom",
                    "api_version": "1",
                    "request_duration_ms": 2000,
                    "cached": False
                }
            )
            
        except Exception as e:
            self._logger.error(f"BLK-1-09: Failed to handle detailed route request: {e}")
            return RouteResponse(
                success=False,
                error={
                    "code": "DETAILED_ROUTE_ERROR",
                    "message": f"Failed to process detailed route: {str(e)}",
                    "status_code": None
                }
            )
    
    async def _blk_1_10_handle_api_error(self, api_response: RouteResponse, context: RequestContext) -> Dict[str, Any]:
        """BLK-1-10: Handle API errors."""
        self._logger.warning(f"BLK-1-10: API error for request {context.request_id}: {api_response.error}")
        
        # Update request history with error
        asyncio.create_task(self._blk_1_13_update_request_result(
            context.request_id, "ERROR", {"api_error": api_response.error}, context
        ))
        
        return {
            "jsonrpc": "2.0",
            "id": context.request_id,
            "error": {
                "code": -32000,
                "message": "External API error",
                "data": api_response.error
            }
        }
    
    async def _blk_1_12_transform_for_ai(self, api_response: RouteResponse, context: RequestContext) -> Dict[str, Any]:
        """BLK-1-12: Transform route data for AI."""
        self._logger.info(f"BLK-1-12: Transforming route data for AI - request {context.request_id}")
        
        # Build request context with user preferences
        request_context = {
            "request_id": context.request_id,
            "user_preferences": {
                "locale": "vi",
                "unit_system": "metric",
                "time_format": "24h"
            }
        }
        
        return await self._client_data_service.transform_route_data_for_ai(
            api_response.route_data, request_context
        )
    
    async def _blk_1_13_update_request_result(self, request_id: str, status: str, 
                                            metadata: Dict[str, Any], context: RequestContext):
        """BLK-1-13: Update request result in history."""
        try:
            await self._request_history_service.update_request_status(
                request_id=request_id,
                status=status,
                completed_at=datetime.utcnow().isoformat() + "Z",
                metadata=metadata
            )
            self._logger.debug(f"BLK-1-13: Updated request result for {request_id} to {status}")
        except Exception as e:
            self._logger.warning(f"BLK-1-13: Failed to update request result for {request_id}: {e}")


# Factory function
def get_route_traffic_service() -> RouteTrafficService:
    """Factory function để lấy route traffic service."""
    return RouteTrafficService()
