"""Use Case cho Process Traffic Sections - BLK-1-16."""

from app.application.dto.traffic_dto import (
    TrafficSectionsCommand, 
    TrafficSectionsResponse, 
    JamPair,
    ReverseGeocodeCommand
)
from app.application.ports.reverse_geocode_provider import ReverseGeocodeProvider
from app.domain.value_objects.latlon import LatLon
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ProcessTrafficSectionsUseCase:
    """Use Case để xử lý traffic sections - BLK-1-16.
    
    Chức năng: Nhận route_data từ BLK-1-09, chuẩn hoá request gửi đến BLK-1-17,
    rồi tổng hợp kết quả để trả cho BLK-1-13
    """
    
    def __init__(self, reverse_geocode_provider: ReverseGeocodeProvider):
        """Khởi tạo use case với reverse geocode provider."""
        self._reverse_geocode_provider = reverse_geocode_provider

    async def execute(self, cmd: TrafficSectionsCommand) -> TrafficSectionsResponse:
        """Thực hiện xử lý traffic sections.
        
        Args:
            cmd: TrafficSectionsCommand chứa route_data và request_context
            
        Returns:
            TrafficSectionsResponse với jam_pairs và metadata
        """
        request_id = cmd.request_context.get("request_id", "unknown")
        logger.info(f"Processing traffic sections for request {request_id}")
        try:
            
            # Validate input
            if not self._validate_input(cmd):
                return TrafficSectionsResponse(
                    success=False,
                    jam_pairs=[],
                    route_summary={},
                    guidance={},
                    metadata={},
                    error_message="Invalid input data"
                )
            
            # Extract traffic sections
            traffic_sections = self._extract_traffic_sections(cmd.route_data)
            logger.debug(f"Found {len(traffic_sections)} traffic sections")
            
            if not traffic_sections:
                logger.info("No traffic sections found - returning empty result")
                return TrafficSectionsResponse(
                    success=True,
                    jam_pairs=[],
                    route_summary=self._extract_route_summary(cmd.route_data),
                    guidance=cmd.route_data.get("guidance", {}),
                    metadata={
                        "processed_at": self._get_current_timestamp(),
                        "request_id": request_id,
                        "sections_count": 0
                    }
                )
            
            # Extract coordinates for reverse geocoding
            coordinates = self._extract_coordinates_for_geocoding(cmd.route_data, traffic_sections)
            logger.debug(f"Extracted {len(coordinates)} coordinates for geocoding")
            
            # Reverse geocode coordinates
            geocode_cmd = ReverseGeocodeCommand(
                coordinates=coordinates,
                language="vi-VN"
            )
            
            logger.debug("Starting reverse geocoding process")
            geocode_response = await self._reverse_geocode_provider.reverse_geocode(geocode_cmd)
            
            if not geocode_response.success:
                logger.warning(f"Reverse geocoding failed: {geocode_response.error_message}")
                return TrafficSectionsResponse(
                    success=False,
                    jam_pairs=[],
                    route_summary={},
                    guidance={},
                    metadata={},
                    error_message=f"Reverse geocoding failed: {geocode_response.error_message}"
                )
            
            # Create jam pairs
            jam_pairs = self._create_jam_pairs(traffic_sections, geocode_response.addresses)
            logger.info(f"Successfully processed {len(jam_pairs)} jam pairs for request {request_id}")
            
            return TrafficSectionsResponse(
                success=True,
                jam_pairs=jam_pairs,
                route_summary=self._extract_route_summary(cmd.route_data),
                guidance=cmd.route_data.get("guidance", {}),
                metadata={
                    "processed_at": self._get_current_timestamp(),
                    "request_id": cmd.request_context.get("request_id", ""),
                    "sections_count": len(traffic_sections)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ProcessTrafficSectionsUseCase: {e}")
            return TrafficSectionsResponse(
                success=False,
                jam_pairs=[],
                route_summary={},
                guidance={},
                metadata={},
                error_message=f"Use case error: {e}"
            )

    def _validate_input(self, cmd: TrafficSectionsCommand) -> bool:
        """Validate input data."""
        try:
            route_data = cmd.route_data
            if not route_data:
                return False
            
            legs = route_data.get("legs", [])
            if not legs or not legs[0].get("points"):
                return False
            
            sections = route_data.get("sections", [])
            if not sections:
                return False
            
            return True
        except Exception:
            return False

    def _extract_traffic_sections(self, route_data: dict) -> list:
        """Extract traffic sections from route data."""
        sections = route_data.get("sections", [])
        traffic_sections = []
        
        for section in sections:
            if section.get("sectionType") == "TRAFFIC":
                traffic_sections.append(section)
        
        return traffic_sections

    def _extract_coordinates_for_geocoding(self, route_data: dict, traffic_sections: list) -> list:
        """Extract coordinates for reverse geocoding."""
        coordinates = []
        legs = route_data.get("legs", [])
        
        if not legs or not legs[0].get("points"):
            return coordinates
        
        points = legs[0]["points"]
        
        for section in traffic_sections:
            start_idx = section.get("startPointIndex", 0)
            end_idx = section.get("endPointIndex", 0)
            
            # Add start and end coordinates
            if start_idx < len(points):
                start_point = points[start_idx]
                coordinates.append(LatLon(
                    start_point.get("lat", 0),
                    start_point.get("lon", 0)
                ))
            
            if end_idx < len(points):
                end_point = points[end_idx]
                coordinates.append(LatLon(
                    end_point.get("lat", 0),
                    end_point.get("lon", 0)
                ))
        
        return coordinates

    def _create_jam_pairs(self, traffic_sections: list, addresses: list) -> list:
        """Create jam pairs from traffic sections and addresses."""
        jam_pairs = []
        
        for i, section in enumerate(traffic_sections):
            start_idx = section.get("startPointIndex", 0)
            end_idx = section.get("endPointIndex", 0)
            
            # Get coordinates for this section
            start_coord = None
            end_coord = None
            start_address = "Địa chỉ không xác định"
            end_address = "Địa chỉ không xác định"
            
            # Find corresponding addresses (simplified - assumes 2 addresses per section)
            if i * 2 < len(addresses):
                start_address = addresses[i * 2].address
                start_coord = addresses[i * 2].coordinate
            if i * 2 + 1 < len(addresses):
                end_address = addresses[i * 2 + 1].address
                end_coord = addresses[i * 2 + 1].coordinate
            
            if start_coord and end_coord:
                jam_pairs.append(JamPair(
                    section_index=i,
                    start=start_coord,
                    end=end_coord,
                    start_address=start_address,
                    end_address=end_address
                ))
        
        return jam_pairs

    def _extract_route_summary(self, route_data: dict) -> dict:
        """Extract route summary from route data."""
        summary = route_data.get("summary", {})
        return {
            "total_length_meters": summary.get("length_in_meters", 0),
            "total_travel_time_seconds": summary.get("travel_time_in_seconds", 0),
            "total_traffic_delay_seconds": summary.get("traffic_delay_in_seconds", 0),
            "traffic_sections_count": len(self._extract_traffic_sections(route_data))
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
