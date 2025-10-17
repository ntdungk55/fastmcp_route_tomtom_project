"""Use case for checking traffic between addresses."""

from app.application.dto.geocoding_dto import GeocodeAddressCommandDTO
from app.application.dto.traffic_dto import AddressTrafficCommandDTO, AddressTrafficResultDTO, TrafficAnalysisCommandDTO
from app.application.errors import ApplicationError
from app.application.ports.geocoding_provider import GeocodingProvider
from app.application.ports.traffic_provider import TrafficProvider


class CheckAddressTraffic:
    """Use case: check traffic conditions between two addresses."""
    
    def __init__(self, geocoding: GeocodingProvider, traffic: TrafficProvider):
        self._geocoding = geocoding
        self._traffic = traffic
    
    async def execute(self, cmd: AddressTrafficCommandDTO) -> AddressTrafficResultDTO:
        """Handle address-to-address traffic check."""
        # Step 1: Geocode both addresses
        from app.application.constants.validation_constants import DefaultValues
        origin_cmd = GeocodeAddressCommandDTO(
            address=cmd.origin_address,
            country_set=cmd.country_set,
            limit=DefaultValues.DEFAULT_LIMIT,
            language=cmd.language
        )
        dest_cmd = GeocodeAddressCommandDTO(
            address=cmd.destination_address,
            country_set=cmd.country_set,
            limit=DefaultValues.DEFAULT_LIMIT,
            language=cmd.language
        )
        
        origin_geocode = await self._geocoding.geocode_address(origin_cmd)
        dest_geocode = await self._geocoding.geocode_address(dest_cmd)
        
        # Validate geocoding results
        if not origin_geocode.results:
            raise ApplicationError(f"No results found for origin address: {cmd.origin_address}")
        if not dest_geocode.results:
            raise ApplicationError(f"No results found for destination address: {cmd.destination_address}")
        
        origin_result = origin_geocode.results[0]
        dest_result = dest_geocode.results[0]
        
        # Step 2: Analyze traffic
        traffic_cmd = TrafficAnalysisCommandDTO(
            origin=origin_result.position,
            destination=dest_result.position,
            language=cmd.language
        )
        traffic_analysis = await self._traffic.analyze_route_traffic(traffic_cmd)
        
        # Step 3: Build result
        return AddressTrafficResultDTO(
            origin_info={
                "address": cmd.origin_address,
                "coordinates": {"lat": origin_result.position.lat, "lon": origin_result.position.lon},
                "geocoded_address": origin_result.address.freeform_address
            },
            destination_info={
                "address": cmd.destination_address,
                "coordinates": {"lat": dest_result.position.lat, "lon": dest_result.position.lon},
                "geocoded_address": dest_result.address.freeform_address
            },
            route_summary={
                "distance_meters": 0,  # Will be filled by traffic analysis
                "duration_seconds": 0,
                "duration_traffic_seconds": 0
            },
            traffic_analysis=traffic_analysis
        )
