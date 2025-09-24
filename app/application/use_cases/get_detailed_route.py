from typing import Optional
from app.application.dto.detailed_route_dto import (
    DetailedRouteRequest, 
    DetailedRouteResponse,
    RoutePoint,
    RouteInstruction,
    RouteLeg,
    GuidanceInfo,
    DetailedRouteSummary
)
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.application.dto.calculate_route_dto import CalculateRouteCommand
from app.application.ports.destination_repository import DestinationRepository
from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.ports.routing_provider import RoutingProvider
from app.domain.value_objects.latlon import LatLon
from app.domain.enums.travel_mode import TravelMode
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class GetDetailedRouteUseCase:
    """Use case: Get detailed route between two addresses using saved destinations if available"""
    
    def __init__(
        self, 
        destination_repository: DestinationRepository,
        geocoding_provider: GeocodingProvider,
        routing_provider: RoutingProvider
    ):
        self._destination_repository = destination_repository
        self._geocoding_provider = geocoding_provider
        self._routing_provider = routing_provider

    async def handle(self, request: DetailedRouteRequest) -> DetailedRouteResponse:
        """Handle detailed route calculation between two addresses"""
        try:
            logger.info(f"Calculating detailed route from '{request.origin_address}' to '{request.destination_address}'")
            
            # Try to find saved destinations first
            origin_destination = await self._find_destination_by_address(request.origin_address)
            dest_destination = await self._find_destination_by_address(request.destination_address)
            
            # Get coordinates for origin
            if origin_destination:
                logger.info(f"Found saved origin destination: {origin_destination.name}")
                origin_coords = origin_destination.coordinates
                origin_address = origin_destination.address
            else:
                logger.info(f"Geocoding origin address: {request.origin_address}")
                origin_coords, origin_address = await self._geocode_address(request.origin_address, request.country_set)
            
            # Get coordinates for destination
            if dest_destination:
                logger.info(f"Found saved destination: {dest_destination.name}")
                dest_coords = dest_destination.coordinates
                dest_address = dest_destination.address
            else:
                logger.info(f"Geocoding destination address: {request.destination_address}")
                dest_coords, dest_address = await self._geocode_address(request.destination_address, request.country_set)
            
            # Calculate route with guidance
            route_cmd = CalculateRouteCommand(
                origin=origin_coords,
                destination=dest_coords,
                travel_mode=request.travel_mode
            )
            
            # Get route plan with guidance from TomTom API
            route_plan = await self._routing_provider.calculate_route(route_cmd)
            
            # Get detailed guidance from TomTom API
            guidance_data = await self._routing_provider.calculate_route_with_guidance(route_cmd)
            
            # Create detailed response
            origin_point = RoutePoint(
                lat=origin_coords.lat,
                lon=origin_coords.lon,
                address=origin_address
            )
            
            destination_point = RoutePoint(
                lat=dest_coords.lat,
                lon=dest_coords.lon,
                address=dest_address
            )
            
            # Create route instructions from guidance data
            instructions = self._create_route_instructions_from_guidance(guidance_data)
            
            # Create traffic sections
            traffic_sections = self._create_traffic_sections(route_plan.sections)
            
            # Create guidance info
            guidance_info = GuidanceInfo(instructions=instructions)
            
            # Create route legs
            legs = self._create_route_legs(guidance_data)
            
            summary = DetailedRouteSummary(
                distance_m=route_plan.summary.distance_m,
                duration_s=route_plan.summary.duration_s,
                traffic_delay_s=0  # Will be calculated from traffic sections
            )
            
            response = DetailedRouteResponse(
                summary=summary,
                instructions=instructions,
                waypoints=[origin_point, destination_point],
                origin=origin_point,
                destination=destination_point,
                traffic_sections=traffic_sections,
                guidance=guidance_info,
                legs=legs
            )
            
            logger.info(f"Detailed route calculated successfully. Distance: {summary.distance_m}m, Duration: {summary.duration_s}s")
            return response
            
        except Exception as e:
            logger.error(f"Error calculating detailed route: {str(e)}")
            raise

    async def _find_destination_by_address(self, address: str) -> Optional[object]:
        """Find saved destination by address (fuzzy matching)"""
        try:
            # Get all saved destinations
            destinations = await self._destination_repository.list_all()
            
            # Simple fuzzy matching - look for partial address matches
            address_lower = address.lower().strip()
            for destination in destinations:
                if (address_lower in destination.address.lower() or 
                    destination.address.lower() in address_lower):
                    return destination
            
            return None
        except Exception as e:
            logger.warning(f"Error finding saved destination for address '{address}': {str(e)}")
            return None

    async def _geocode_address(self, address: str, country_set: str) -> tuple[LatLon, str]:
        """Geocode an address to get coordinates"""
        try:
            geocode_cmd = GeocodeAddressCommandDTO(
                address=address,
                country_set=country_set,
                limit=1
            )
            
            geocode_result = await self._geocoding_provider.geocode_address(geocode_cmd)
            
            if not geocode_result.results:
                raise ValueError(f"No geocoding results found for address: {address}")
            
            result = geocode_result.results[0]
            coords = LatLon(result.position.lat, result.position.lon)
            formatted_address = result.address.freeform_address
            
            return coords, formatted_address
            
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {str(e)}")
            raise

    async def _get_route_guidance(self, origin: LatLon, destination: LatLon, travel_mode: TravelMode) -> dict:
        """Get detailed guidance from TomTom API"""
        try:
            # Create a new routing command for guidance
            route_cmd = CalculateRouteCommand(
                origin=origin,
                destination=destination,
                travel_mode=travel_mode
            )
            
            # Use the routing provider to get guidance
            # We'll need to modify the routing provider to return guidance data
            # For now, we'll return empty guidance
            return {
                "guidance": {"instructions": []},
                "legs": []
            }
        except Exception as e:
            logger.warning(f"Error getting route guidance: {str(e)}")
            return {
                "guidance": {"instructions": []},
                "legs": []
            }

    def _create_route_instructions_from_guidance(self, guidance_data: dict) -> list[RouteInstruction]:
        """Create turn-by-turn instructions from guidance data"""
        instructions = []
        
        guidance = guidance_data.get("guidance", {})
        guidance_instructions = guidance.get("instructions", [])
        
        for inst in guidance_instructions:
            point = RoutePoint(
                lat=inst.get("point", {}).get("lat", 0),
                lon=inst.get("point", {}).get("lon", 0)
            )
            
            instruction = RouteInstruction(
                instruction=inst.get("instruction", ""),
                distance_m=inst.get("distance_m", 0),
                duration_s=inst.get("duration_s", 0),
                point=point,
                maneuver=inst.get("maneuver"),
                road_name=inst.get("road_name")
            )
            instructions.append(instruction)
        
        return instructions

    def _create_route_legs(self, guidance_data: dict) -> list[RouteLeg]:
        """Create route legs from guidance data"""
        legs = []
        
        for leg_data in guidance_data.get("legs", []):
            start_point = RoutePoint(
                lat=leg_data.get("start_point", {}).get("lat", 0),
                lon=leg_data.get("start_point", {}).get("lon", 0)
            )
            
            end_point = RoutePoint(
                lat=leg_data.get("end_point", {}).get("lat", 0),
                lon=leg_data.get("end_point", {}).get("lon", 0)
            )
            
            leg = RouteLeg(
                start_point=start_point,
                end_point=end_point,
                distance_m=leg_data.get("distance_m", 0),
                duration_s=leg_data.get("duration_s", 0)
            )
            legs.append(leg)
        
        return legs

    def _create_route_instructions(self, route_plan) -> list[RouteInstruction]:
        """Create turn-by-turn instructions from route plan (fallback)"""
        # This is a simplified implementation
        # In a real implementation, you would parse the route geometry
        # and create detailed turn-by-turn instructions
        
        instructions = []
        
        # Add a simple start instruction
        instructions.append(RouteInstruction(
            instruction="Bắt đầu từ điểm xuất phát",
            distance_m=0,
            duration_s=0,
            point=RoutePoint(lat=0, lon=0)  # Will be filled with actual coordinates
        ))
        
        # Add a simple end instruction
        instructions.append(RouteInstruction(
            instruction="Đến điểm đích",
            distance_m=route_plan.summary.distance_m,
            duration_s=route_plan.summary.duration_s,
            point=RoutePoint(lat=0, lon=0)  # Will be filled with actual coordinates
        ))
        
        return instructions

    def _create_traffic_sections(self, sections) -> list[dict]:
        """Create traffic sections from route plan sections"""
        traffic_sections = []
        
        for section in sections:
            traffic_sections.append({
                "kind": section.kind,
                "start_index": section.start_index,
                "end_index": section.end_index,
                "description": self._get_traffic_description(section.kind)
            })
        
        return traffic_sections

    def _get_traffic_description(self, kind: str) -> str:
        """Get Vietnamese description for traffic kind"""
        traffic_descriptions = {
            "traffic:JAM": "Kẹt xe",
            "traffic:HEAVY": "Giao thông đông đúc",
            "traffic:MODERATE": "Giao thông vừa phải",
            "traffic:FLOWING": "Giao thông thông suốt",
            "traffic:FREE_FLOW": "Giao thông tự do"
        }
        
        return traffic_descriptions.get(kind, "Thông tin giao thông không xác định")
