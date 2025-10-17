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
from app.domain.enums.travel_mode import TravelMode
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class GetDetailedRouteUseCase:
    """Use case for calculating detailed route with traffic info."""
    
    def __init__(
        self,
        destination_repository: DestinationRepository,
        geocoding_provider: GeocodingProvider,
        routing_provider: RoutingProvider
    ):
        self._destination_repository = destination_repository
        self._geocoding_provider = geocoding_provider
        self._routing_provider = routing_provider
    
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
            # Convert travel_mode string to TravelMode enum
            travel_mode_enum = TravelMode[request.travel_mode.upper()] if isinstance(request.travel_mode, str) else request.travel_mode
            route_cmd = CalculateRouteCommand(
                origin=origin_coords,
                destination=dest_coords,
                travel_mode=travel_mode_enum
            )
            route_plan = await self._routing_provider.calculate_route(route_cmd)
            
            # Step 4: Build response
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
            
            # Build main route from route plan
            main_route = MainRoute(
                summary=f"Route via {request.travel_mode}",
                total_distance_meters=route_plan.summary.distance_m,
                total_duration_seconds=route_plan.summary.duration_s,
                traffic_condition=TrafficCondition(
                    description="Normal traffic",
                    delay_minutes=0
                ),
                instructions=self._extract_instructions(route_plan),
                sections=[]
            )
            
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
        try:
            # Handle TomTom response structure via RoutePlan.guidance
            if hasattr(route_plan, 'guidance') and hasattr(route_plan.guidance, 'instructions'):
                for idx, instruction in enumerate(route_plan.guidance.instructions, 1):
                    instr_obj = RouteInstruction(
                        step=idx,
                        instruction=getattr(instruction, 'message', 'Continue'),
                        distance_meters=int(getattr(instruction, 'distance_in_meters', 0)),
                        duration_seconds=int(getattr(instruction, 'duration_in_seconds', 0)),
                        traffic_condition=None
                    )
                    instructions.append(instr_obj)
            # Fallback: If no guidance, create basic instruction
            elif hasattr(route_plan, 'summary'):
                instr_obj = RouteInstruction(
                    step=1,
                    instruction=f"Head towards destination",
                    distance_meters=getattr(route_plan.summary, 'distance_m', 0),
                    duration_seconds=getattr(route_plan.summary, 'duration_s', 0),
                    traffic_condition=None
                )
                instructions.append(instr_obj)
        except Exception as e:
            logger.warning(f"Failed to extract instructions: {str(e)}")
        
        return instructions
    
    def _extract_alternative_routes(self, route_plan) -> list:
        """Extract alternative routes from route plan."""
        alternatives = []
        try:
            # TomTom may return alternative routes in response
            # This is a placeholder - extend based on actual API response
            if hasattr(route_plan, 'legs') and len(getattr(route_plan, 'legs', [])) > 1:
                for leg in route_plan.legs[1:]:  # Skip first (main route)
                    alt_route = AlternativeRoute(
                        summary=f"Alternative route",
                        total_distance_meters=getattr(leg, 'summary', {}).get('distance_m', 0),
                        total_duration_seconds=getattr(leg, 'summary', {}).get('duration_s', 0),
                        traffic_condition=None
                    )
                    alternatives.append(alt_route)
        except Exception as e:
            logger.warning(f"Failed to extract alternative routes: {str(e)}")
        
        return alternatives
