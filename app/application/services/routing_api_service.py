"""
Routing API Service - BLK-1-09: RequestRoutingAPI
Gọi API TomTom (hoặc routing provider khác) để tính toán tuyến đường.
"""

import asyncio
import json
import os
import random
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientTimeout, ClientError

from app.infrastructure.logging.logger import get_logger


@dataclass
class RouteRequest:
    """Request data cho routing API."""
    origin: Dict[str, float]  # {"lat": float, "lon": float}
    destination: Dict[str, float]
    waypoints: Optional[list] = None
    travel_mode: str = "car"
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    route_type: str = "fastest"
    avoid: Optional[list] = None
    traffic: bool = True


@dataclass
class RouteResponse:
    """Response từ routing API."""
    success: bool
    route_data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class RoutingAPIService:
    """
    BLK-1-09: RequestRoutingAPI - Gọi TomTom API với retry logic
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._api_key = None
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None
        self._circuit_breaker_open = False
        self._rate_limiter_last_request = None
        self._rate_limiter_count = 0
        
        # Load API key
        self._load_api_key()
    
    def _load_api_key(self):
        """Load TomTom API key từ environment."""
        self._api_key = os.getenv("TOMTOM_API_KEY")
        
        if not self._api_key:
            self._logger.error("BLK-1-09: TOMTOM_API_KEY environment variable not found")
            return
        
        # Validate API key format
        if not self._validate_api_key_format(self._api_key):
            self._logger.error("BLK-1-09: Invalid API key format")
            self._api_key = None
            return
        
        # Log masked key for debugging
        masked_key = f"***{self._api_key[-4:]}" if len(self._api_key) > 4 else "***"
        self._logger.info(f"BLK-1-09: TomTom API key loaded: {masked_key}")
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format."""
        if not api_key or len(api_key) < 20:
            return False
        
        # Check if alphanumeric
        if not re.match(r'^[a-zA-Z0-9]+$', api_key):
            return False
        
        return True
    
    async def request_routing(self, route_request: RouteRequest, 
                           request_context: Dict[str, Any]) -> RouteResponse:
        """
        BLK-1-09: Request routing từ TomTom API
        
        Args:
            route_request: Route request data
            request_context: Request context (request_id, timeout, etc.)
            
        Returns:
            RouteResponse: API response
        """
        request_id = request_context.get("request_id", "unknown")
        timeout_ms = request_context.get("timeout", 10000)
        
        self._logger.info(f"BLK-1-09: Requesting routing for {request_id}")
        
        # Check circuit breaker
        if self._circuit_breaker_open:
            self._logger.warning(f"BLK-1-09: Circuit breaker open, failing fast for {request_id}")
            return RouteResponse(
                success=False,
                error={
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Routing service temporarily unavailable",
                    "status_code": None
                }
            )
        
        # Check API key
        if not self._api_key:
            return RouteResponse(
                success=False,
                error={
                    "code": "API_KEY_NOT_CONFIGURED",
                    "message": "TomTom API key not found in environment or config",
                    "status_code": None
                }
            )
        
        # Rate limiting
        if not await self._check_rate_limit():
            return RouteResponse(
                success=False,
                error={
                    "code": "RATE_LIMIT",
                    "message": "API rate limit exceeded, please try again later",
                    "status_code": 429,
                    "retry_after": 60
                }
            )
        
        # Build API URL
        try:
            url = self._build_routing_url(route_request)
        except Exception as e:
            return RouteResponse(
                success=False,
                error={
                    "code": "INVALID_REQUEST",
                    "message": f"Failed to build API URL: {str(e)}",
                    "status_code": None
                }
            )
        
        # Make API call with retries
        return await self._make_api_call_with_retries(url, request_id, timeout_ms)
    
    def _build_routing_url(self, route_request: RouteRequest) -> str:
        """Build TomTom routing API URL."""
        base_url = "https://api.tomtom.com/routing/1/calculateRoute"
        
        # Build locations string
        locations = f"{route_request.origin['lat']},{route_request.origin['lon']}:{route_request.destination['lat']},{route_request.destination['lon']}"
        
        # Build query parameters
        params = {
            "key": self._api_key,
            "travelMode": route_request.travel_mode,
            "routeType": route_request.route_type,
            "traffic": "true" if route_request.traffic else "false",
            "computeTravelTimeFor": "all",
            "instructionsType": "text"
        }
        
        # Add optional parameters
        if route_request.avoid:
            params["avoid"] = ",".join(route_request.avoid)
        
        if route_request.departure_time:
            params["departAt"] = route_request.departure_time
        
        if route_request.arrival_time:
            params["arriveAt"] = route_request.arrival_time
        
        # Build full URL
        url = f"{base_url}/{locations}/json?{urlencode(params)}"
        return url
    
    async def _make_api_call_with_retries(self, url: str, request_id: str, timeout_ms: int) -> RouteResponse:
        """Make API call with retry logic."""
        max_retries = 3
        base_backoff = 1.0  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                start_time = datetime.utcnow()
                
                async with aiohttp.ClientSession() as session:
                    timeout = ClientTimeout(total=timeout_ms / 1000)
                    
                    async with session.get(url, timeout=timeout) as response:
                        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        
                        if response.status == 200:
                            data = await response.json()
                            self._reset_circuit_breaker()
                            
                            return RouteResponse(
                                success=True,
                                route_data=self._parse_route_response(data),
                                metadata={
                                    "provider": "tomtom",
                                    "api_version": "1",
                                    "request_duration_ms": duration_ms,
                                    "cached": False,
                                    "attempt": attempt + 1
                                }
                            )
                        
                        elif response.status == 403:
                            # API key unauthorized
                            return RouteResponse(
                                success=False,
                                error={
                                    "code": "API_KEY_UNAUTHORIZED",
                                    "message": "TomTom API key is not authorized",
                                    "status_code": 403
                                }
                            )
                        
                        elif response.status == 429:
                            # Rate limit
                            retry_after = int(response.headers.get("Retry-After", 60))
                            return RouteResponse(
                                success=False,
                                error={
                                    "code": "RATE_LIMIT",
                                    "message": "API rate limit exceeded",
                                    "status_code": 429,
                                    "retry_after": retry_after
                                }
                            )
                        
                        elif 400 <= response.status < 500:
                            # Client error - don't retry
                            error_data = await response.json() if response.content_type == 'application/json' else {}
                            return RouteResponse(
                                success=False,
                                error={
                                    "code": "INVALID_REQUEST",
                                    "message": error_data.get("message", f"Client error: {response.status}"),
                                    "status_code": response.status
                                }
                            )
                        
                        else:
                            # Server error - retry
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
            
            except asyncio.TimeoutError:
                self._logger.warning(f"BLK-1-09: Timeout on attempt {attempt + 1} for {request_id}")
                if attempt < max_retries:
                    backoff = base_backoff * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(backoff)
                    continue
                else:
                    return RouteResponse(
                        success=False,
                        error={
                            "code": "TIMEOUT",
                            "message": f"Request timeout after {timeout_ms}ms",
                            "status_code": 0
                        }
                    )
            
            except ClientError as e:
                self._logger.warning(f"BLK-1-09: Client error on attempt {attempt + 1} for {request_id}: {e}")
                if attempt < max_retries:
                    backoff = base_backoff * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(backoff)
                    continue
                else:
                    self._handle_circuit_breaker_failure()
                    return RouteResponse(
                        success=False,
                        error={
                            "code": "API_ERROR",
                            "message": f"API call failed: {str(e)}",
                            "status_code": None
                        }
                    )
            
            except Exception as e:
                self._logger.error(f"BLK-1-09: Unexpected error on attempt {attempt + 1} for {request_id}: {e}")
                return RouteResponse(
                    success=False,
                    error={
                        "code": "UNEXPECTED_ERROR",
                        "message": f"Unexpected error: {str(e)}",
                        "status_code": None
                    }
                )
        
        # All retries exhausted
        self._handle_circuit_breaker_failure()
        return RouteResponse(
            success=False,
            error={
                "code": "MAX_RETRIES_EXCEEDED",
                "message": f"Max retries ({max_retries}) exceeded",
                "status_code": None
            }
        )
    
    def _parse_route_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TomTom API response."""
        try:
            routes = api_response.get("routes", [])
            if not routes:
                raise ValueError("No routes in API response")
            
            route = routes[0]  # First route
            summary = route.get("summary", {})
            
            return {
                "summary": {
                    "length_in_meters": summary.get("lengthInMeters", 0),
                    "travel_time_in_seconds": summary.get("travelTimeInSeconds", 0),
                    "traffic_delay_in_seconds": summary.get("trafficDelayInSeconds", 0),
                    "departure_time": summary.get("departureTime"),
                    "arrival_time": summary.get("arrivalTime")
                },
                "legs": self._parse_legs(route.get("legs", [])),
                "sections": self._parse_sections(route.get("sections", [])),
                "guidance": self._parse_guidance(route.get("guidance", {}))
            }
            
        except Exception as e:
            self._logger.error(f"Failed to parse route response: {e}")
            raise ValueError(f"Invalid API response format: {str(e)}")
    
    def _parse_legs(self, legs_data: list) -> list:
        """Parse route legs."""
        parsed_legs = []
        for leg in legs_data:
            parsed_legs.append({
                "summary": leg.get("summary", {}),
                "points": leg.get("points", [])
            })
        return parsed_legs
    
    def _parse_sections(self, sections_data: list) -> list:
        """Parse route sections."""
        parsed_sections = []
        for section in sections_data:
            parsed_sections.append({
                "start_point_index": section.get("startPointIndex"),
                "end_point_index": section.get("endPointIndex"),
                "section_type": section.get("sectionType"),
                "travel_mode": section.get("travelMode")
            })
        return parsed_sections
    
    def _parse_guidance(self, guidance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse route guidance."""
        instructions = []
        for instruction in guidance_data.get("instructions", []):
            instructions.append({
                "message": instruction.get("message"),
                "maneuver": instruction.get("maneuver"),
                "point": instruction.get("point", {})
            })
        
        return {"instructions": instructions}
    
    async def _check_rate_limit(self) -> bool:
        """Check rate limiting (10 requests per second)."""
        now = datetime.utcnow()
        
        # Reset counter if more than 1 second has passed
        if (self._rate_limiter_last_request is None or 
            (now - self._rate_limiter_last_request).total_seconds() >= 1):
            self._rate_limiter_count = 0
            self._rate_limiter_last_request = now
        
        # Check if we're at the limit
        if self._rate_limiter_count >= 10:
            return False
        
        self._rate_limiter_count += 1
        return True
    
    def _handle_circuit_breaker_failure(self):
        """Handle circuit breaker failure."""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = datetime.utcnow()
        
        # Open circuit breaker after 10 failures in 60 seconds
        if self._circuit_breaker_failures >= 10:
            self._circuit_breaker_open = True
            self._logger.warning("BLK-1-09: Circuit breaker opened due to repeated failures")
            
            # Schedule auto-close after 120 seconds
            asyncio.create_task(self._auto_close_circuit_breaker())
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker on success."""
        self._circuit_breaker_failures = 0
        self._circuit_breaker_open = False
    
    async def _auto_close_circuit_breaker(self):
        """Auto-close circuit breaker after recovery period."""
        await asyncio.sleep(120)  # 120 seconds recovery period
        self._circuit_breaker_open = False
        self._circuit_breaker_failures = 0
        self._logger.info("BLK-1-09: Circuit breaker auto-closed after recovery period")


# Factory function
def get_routing_api_service() -> RoutingAPIService:
    """Factory function để lấy routing API service."""
    return RoutingAPIService()

