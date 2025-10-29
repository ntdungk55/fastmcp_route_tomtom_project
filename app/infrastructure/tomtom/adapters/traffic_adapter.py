"""TomTom Traffic Adapter - Triển khai traffic checking cho BLK-1-15."""

from app.application.dto.traffic_dto import TrafficCheckCommand, TrafficResponse, TrafficSection
from app.application.ports.traffic_provider import TrafficProvider
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class TomTomTrafficAdapter(TrafficProvider):
    """Adapter TomTom cho traffic checking - kiểm tra tình trạng giao thông.
    
    Chức năng: Gọi TomTom Routing API với traffic=true để lấy thông tin giao thông
    """
    
    def __init__(self, base_url: str, api_key: str, http: AsyncApiClient, timeout_sec: int = 5):
        """Khởi tạo adapter với thông tin kết nối TomTom API."""
        self._base_url = base_url.rstrip("/")
        self._http = http
        self._timeout_sec = timeout_sec
        self._api_key = api_key

    async def check_severe_traffic(self, cmd: TrafficCheckCommand) -> TrafficResponse:
        """Kiểm tra tình trạng giao thông nghiêm trọng trên tuyến đường.
        
        Args:
            cmd: TrafficCheckCommand chứa thông tin tuyến đường cần kiểm tra
            
        Returns:
            TrafficResponse với thông tin traffic sections và mức độ nghiêm trọng
        """
        logger.info(f"Checking severe traffic for route: {cmd.origin} -> {cmd.destination}")
        try:
            # Chuyển đổi tọa độ thành format string cho TomTom API
            origin = f"{cmd.origin.lat},{cmd.origin.lon}"
            dest = f"{cmd.destination.lat},{cmd.destination.lon}"
            path = f"/routing/1/calculateRoute/{origin}:{dest}/json"
            
            # Tạo HTTP request với các tham số traffic
            req = RequestEntity(
                method=HttpMethod.GET,
                url=f"{self._base_url}{path}",
                headers={"Accept": "application/json"},
                params={
                    "key": self._api_key,
                    "traffic": "true",
                    "sectionType": "traffic",
                    "instructionsType": "text",
                    "language": cmd.language,
                    "travelMode": cmd.travel_mode,
                },
                json=None,
                timeout_sec=self._timeout_sec,
            )
            
            # Gửi request và xử lý response
            logger.debug(f"Sending traffic check request to: {req.url}")
            payload = await self._http.send(req)
            logger.debug(f"Received traffic response with {len(payload.get('routes', []))} routes")
            
            result = self._parse_traffic_response(payload)
            logger.info(f"Traffic check completed: {len(result.traffic_sections)} sections found, {result.total_delay_seconds}s total delay")
            return result
            
        except Exception as e:
            logger.error(f"Error checking traffic: {e}", exc_info=True)
            return TrafficResponse(
                success=False,
                traffic_sections=[],
                total_delay_seconds=0,
                total_traffic_length_meters=0,
                error_message=f"Traffic check failed: {str(e)}"
            )

    def _parse_traffic_response(self, payload: dict) -> TrafficResponse:
        """Parse TomTom traffic response thành TrafficResponse."""
        try:
            routes = payload.get("routes", [])
            
            # DEBUG: Log raw response structure
            logger.info(f"🔍 RAW TOMTOM RESPONSE DEBUG:")
            logger.info(f"  - Routes count: {len(routes)}")
            
            if not routes:
                logger.warning("No routes in TomTom response")
                return TrafficResponse(
                    success=True,
                    traffic_sections=[],
                    total_delay_seconds=0,
                    total_traffic_length_meters=0
                )
            
            route = routes[0]
            summary = route.get("summary", {})
            sections = route.get("sections", [])
            
            # DEBUG: Log sections info
            logger.info(f"  - Sections count: {len(sections)}")
            logger.info(f"  - Route keys: {list(route.keys())}")
            if sections:
                logger.info(f"  - First section type: {sections[0].get('sectionType')}")
                logger.info(f"  - First section keys: {list(sections[0].keys())}")
                logger.info(f"  - First section data: {sections[0]}")
            
            # Trích xuất traffic sections
            traffic_sections = []
            total_delay = 0
            total_traffic_length = 0
            
            logger.info(f"🚦 PARSING TRAFFIC SECTIONS:")
            for idx, section in enumerate(sections):
                section_type = section.get("sectionType")
                logger.info(f"  - Section {idx}: type={section_type}, delayInSeconds={section.get('delayInSeconds', 0)}")
                
                if section_type == "TRAFFIC":
                    traffic_section = TrafficSection(
                        section_type=section.get("sectionType", ""),
                        start_point_index=section.get("startPointIndex", 0),
                        end_point_index=section.get("endPointIndex", 0),
                        simple_category=section.get("simpleCategory", ""),
                        effective_speed_kmh=section.get("effectiveSpeedInKmh", 0.0),
                        delay_seconds=section.get("delayInSeconds", 0),
                        magnitude_of_delay=section.get("magnitudeOfDelay", 0),
                        event_id=section.get("eventId")
                    )
                    traffic_sections.append(traffic_section)
                    total_delay += traffic_section.delay_seconds
                    total_traffic_length += section.get("lengthInMeters", 0)
                    logger.info(f"    ✓ Added TRAFFIC section with {traffic_section.delay_seconds}s delay")
            
            logger.info(f"📊 TRAFFIC PARSING COMPLETE:")
            logger.info(f"  - Total sections found: {len(traffic_sections)}")
            logger.info(f"  - Total delay: {total_delay}s")
            logger.info(f"  - Total traffic length: {total_traffic_length}m")
            
            return TrafficResponse(
                success=True,
                traffic_sections=traffic_sections,
                total_delay_seconds=total_delay,
                total_traffic_length_meters=total_traffic_length
            )
            
        except Exception as e:
            logger.error(f"Error parsing traffic response: {e}")
            return TrafficResponse(
                success=False,
                traffic_sections=[],
                total_delay_seconds=0,
                total_traffic_length_meters=0,
                error_message=f"Failed to parse response: {e}"
            )