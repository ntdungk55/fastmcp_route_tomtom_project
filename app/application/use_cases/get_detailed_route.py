"""Use case for calculating detailed route between two addresses."""

from typing import Optional
from app.application.dto.detailed_route_dto import (
    DetailedRouteRequest,
    DetailedRouteResponse,
    RoutePoint,
    MainRoute,
    AlternativeRoute,
    RouteInstruction,
    TrafficCondition,
)
from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.application.dto.calculate_route_dto import CalculateRouteCommand
from app.application.constants.validation_constants import DefaultValues
from app.application.errors import ApplicationError
from app.application.ports.destination_repository import DestinationRepository
from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.ports.routing_provider import RoutingProvider
from app.application.ports.traffic_provider import TrafficProvider
from app.application.ports.reverse_geocode_provider import ReverseGeocodeProvider
from app.application.dto.traffic_dto import TrafficCheckCommand, ReverseGeocodeCommand, TrafficSectionsCommand
from app.domain.enums.travel_mode import TravelMode
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class GetDetailedRouteUseCase:
    """Use case for calculating detailed route with traffic info."""
    
    def __init__(
        self,
        destination_repository: DestinationRepository,
        geocoding_provider: GeocodingProvider,
        routing_provider: RoutingProvider,
        traffic_provider: TrafficProvider,
        reverse_geocode_provider: ReverseGeocodeProvider
    ):
        self._destination_repository = destination_repository
        self._geocoding_provider = geocoding_provider
        self._routing_provider = routing_provider
        self._traffic_provider = traffic_provider
        self._reverse_geocode_provider = reverse_geocode_provider
    
    async def execute(self, request: DetailedRouteRequest) -> DetailedRouteResponse:
        """Execute detailed route calculation."""
        try:
            logger.info(f"Calculating detailed route from {request.origin_address} to {request.destination_address}")
            
            # Step 1: Get origin coordinates
            origin_coords, origin_name = await self._get_coordinates(
                request.origin_address,
                request.country_set,
                request.language
            )
            
            # Step 2: Get destination coordinates
            dest_coords, dest_name = await self._get_coordinates(
                request.destination_address,
                request.country_set,
                request.language
            )
            
            # Step 3: Calculate route
            logger.info(f"Requesting route from routing provider")
            # Fixed: Convert travel_mode string to TravelMode enum
            travel_mode_enum = TravelMode[request.travel_mode.upper()] if isinstance(request.travel_mode, str) else request.travel_mode
            route_cmd = CalculateRouteCommand(
                origin=origin_coords,
                destination=dest_coords,
                travel_mode=travel_mode_enum # Fixed type error
            )
            # Use calculate_route_with_guidance to get turn-by-turn instructions
            route_plan = await self._routing_provider.calculate_route_with_guidance(route_cmd)
            
            # Step 4: Check traffic conditions (BLK-1-15)
            logger.info("Checking traffic conditions")
            traffic_cmd = TrafficCheckCommand(
                origin=origin_coords,
                destination=dest_coords,
                travel_mode=request.travel_mode,
                language=request.language
            )
            traffic_response = await self._traffic_provider.check_severe_traffic(traffic_cmd)
            
            # DEBUG: Log traffic response
            logger.info(f"🚦 TRAFFIC RESPONSE DEBUG:")
            logger.info(f"  - Success: {traffic_response.success}")
            logger.info(f"  - Has traffic_sections: {hasattr(traffic_response, 'traffic_sections')}")
            if hasattr(traffic_response, 'traffic_sections'):
                logger.info(f"  - Traffic sections count: {len(traffic_response.traffic_sections) if traffic_response.traffic_sections else 0}")
                if traffic_response.traffic_sections:
                    logger.info(f"  - First section: {traffic_response.traffic_sections[0]}")
            
            # Step 5: Process traffic sections if found (BLK-1-16, BLK-1-17)
            jam_pairs = []
            if traffic_response.success and traffic_response.traffic_sections:
                logger.info(f"Found {len(traffic_response.traffic_sections)} traffic sections, processing...")
                jam_pairs = await self._process_traffic_sections(route_plan, traffic_response.traffic_sections)
            else:
                logger.warning("No traffic sections found in response")
            
            # Step 6: Build response
            origin_point = RoutePoint(
                address=request.origin_address,
                name=str(origin_name) if origin_name else None,
                lat=origin_coords.lat,
                lon=origin_coords.lon
            )
            
            destination_point = RoutePoint(
                address=request.destination_address,
                name=str(dest_name) if dest_name else None,
                lat=dest_coords.lat,
                lon=dest_coords.lon
            )
            
            # Build main route from route plan with traffic info
            traffic_description = "Normal traffic"
            delay_minutes = 0
            if traffic_response.success:
                delay_minutes = traffic_response.total_delay_seconds // 60
                if traffic_response.traffic_sections:
                    traffic_description = f"Traffic delays: {delay_minutes} minutes, {len(traffic_response.traffic_sections)} sections affected"
                else:
                    traffic_description = "No traffic delays"
            
            # DEBUG: Log jam pairs before building sections
            logger.info(f"🏗️ BUILDING TRAFFIC SECTIONS:")
            logger.info(f"  - Jam pairs count: {len(jam_pairs)}")
            if jam_pairs:
                logger.info(f"  - First jam pair: {jam_pairs[0]}")
            
            main_route = MainRoute(
                summary=f"Route via {request.travel_mode}",
                total_distance_meters=route_plan.summary.distance_m,
                total_duration_seconds=route_plan.summary.duration_s,
                traffic_condition=TrafficCondition(
                    description=traffic_description,
                    delay_minutes=delay_minutes
                ),
                instructions=self._extract_instructions(route_plan),
                sections=self._build_traffic_sections(route_plan, jam_pairs)
            )
            
            # DEBUG: Log final sections
            logger.info(f"📦 MAIN ROUTE SECTIONS:")
            logger.info(f"  - Sections count: {len(main_route.sections) if main_route.sections else 0}")
            if main_route.sections:
                logger.info(f"  - First section: {main_route.sections[0]}")
            
            # Build alternative routes if available
            alternative_routes = self._extract_alternative_routes(route_plan)
            
            response = DetailedRouteResponse(
                origin=origin_point,
                destination=destination_point,
                main_route=main_route,
                alternative_routes=alternative_routes,
                travel_mode=request.travel_mode,
                total_alternative_count=len(alternative_routes)
            )
            
            logger.info(f"Successfully calculated detailed route with {len(alternative_routes)} alternatives")
            return response
            
        except ApplicationError as e:
            logger.error(f"Application error calculating route: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error calculating detailed route: {str(e)}")
            raise ApplicationError(f"Failed to calculate detailed route: {str(e)}")
    
    async def _get_coordinates(self, address: str, country_set: str, language: str):
        """Get coordinates for an address, checking saved destinations first."""
        # Try to find in saved destinations first via search
        try:
            saved_dests = await self._destination_repository.search_by_name_and_address(address=address)
            if saved_dests:
                logger.info(f"Found saved destination for {address}")
                saved_dest = saved_dests[0]
                return saved_dest.coordinates, saved_dest.name
        except Exception as e:
            logger.debug(f"Could not find saved destination: {str(e)}")
        
        # Fallback to geocoding
        logger.info(f"Geocoding address: {address}")
        geocode_cmd = GeocodeAddressCommandDTO(
            address=address,
            country_set=country_set,
            limit=DefaultValues.DEFAULT_LIMIT,
            language=language
        )
        
        geocode_result = await self._geocoding_provider.geocode_address(geocode_cmd)
        
        if not geocode_result.results or len(geocode_result.results) == 0:
            raise ApplicationError(f"Could not find coordinates for address: {address}")
        
        first_result = geocode_result.results[0]
        coordinates = first_result.position
        geocoded_address = first_result.address.freeform_address if hasattr(first_result.address, 'freeform_address') else address
        
        logger.info(f"Geocoded {address} to {coordinates.lat}, {coordinates.lon}")
        return coordinates, geocoded_address
    
    def _extract_instructions(self, route_plan) -> list:
        """Extract turn-by-turn instructions from route plan."""
        instructions = []
        if hasattr(route_plan, 'guidance') and hasattr(route_plan.guidance, 'instructions'):
            for idx, instruction in enumerate(route_plan.guidance.instructions, 1):
                instr_obj = RouteInstruction(
                    step=idx,
                    instruction=getattr(instruction, 'message', 'Continue'),
                    distance_meters=getattr(instruction, 'distance_in_meters', 0),
                    duration_seconds=getattr(instruction, 'duration_in_seconds', 0),
                    traffic_condition=None
                )
                instructions.append(instr_obj)
        return instructions
    
    def _extract_alternative_routes(self, route_plan) -> list:
        """Extract alternative routes from route plan."""
        alternatives = []
        # Placeholder for alternative routes extraction
        # Can be extended based on routing provider response structure
        return alternatives
    
    async def _process_traffic_sections(self, route_plan, traffic_sections) -> list:
        """Process traffic sections and create jam pairs (BLK-1-16, BLK-1-17)."""
        try:
            # Extract coordinates for reverse geocoding
            coordinates = []
            for section in traffic_sections:
                # Get start and end coordinates from route plan
                start_idx = section.start_point_index
                end_idx = section.end_point_index
                
                # Add coordinates (simplified - would need actual route points)
                if hasattr(route_plan, 'guidance') and hasattr(route_plan.guidance, 'instructions'):
                    instructions = route_plan.guidance.instructions
                    if start_idx < len(instructions):
                        start_inst = instructions[start_idx]
                        if hasattr(start_inst, 'point'):
                            coordinates.append(start_inst.point)
                    if end_idx < len(instructions):
                        end_inst = instructions[end_idx]
                        if hasattr(end_inst, 'point'):
                            coordinates.append(end_inst.point)
            
            if not coordinates:
                logger.warning("No coordinates found for traffic sections")
                return []
            
            # Reverse geocode coordinates
            geocode_cmd = ReverseGeocodeCommand(
                coordinates=coordinates,
                language="vi-VN"
            )
            
            geocode_response = await self._reverse_geocode_provider.reverse_geocode(geocode_cmd)
            
            if not geocode_response.success:
                logger.warning(f"Reverse geocoding failed: {geocode_response.error_message}")
                return []
            
            # Create jam pairs
            jam_pairs = []
            for i, section in enumerate(traffic_sections):
                if i * 2 + 1 < len(geocode_response.addresses):
                    start_addr = geocode_response.addresses[i * 2]
                    end_addr = geocode_response.addresses[i * 2 + 1]
                    
                    jam_pairs.append({
                        "section_index": i,
                        "start": {"lat": start_addr.coordinate.lat, "lon": start_addr.coordinate.lon},
                        "end": {"lat": end_addr.coordinate.lat, "lon": end_addr.coordinate.lon},
                        "start_address": start_addr.address,
                        "end_address": end_addr.address,
                        "delay_seconds": section.delay_seconds,
                        "magnitude": section.magnitude_of_delay
                    })
            
            logger.info(f"Created {len(jam_pairs)} jam pairs")
            return jam_pairs
            
        except Exception as e:
            logger.error(f"Error processing traffic sections: {e}")
            return []
    
    def _build_traffic_sections(self, route_plan, jam_pairs) -> list:
        """Build traffic sections for the route."""
        sections = []
        for jam_pair in jam_pairs:
            sections.append({
                "type": "traffic",
                "start_address": jam_pair["start_address"],
                "end_address": jam_pair["end_address"],
                "delay_seconds": jam_pair["delay_seconds"],
                "magnitude": jam_pair["magnitude"],
                "coordinates": {
                    "start": jam_pair["start"],
                    "end": jam_pair["end"]
                }
            })
        return sections
