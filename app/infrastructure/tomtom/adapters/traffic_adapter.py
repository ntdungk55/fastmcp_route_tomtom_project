"""TomTom Traffic Adapter - Triển khai traffic provider."""

from app.application.dto.calculate_route_dto import RoutePlan
from app.application.dto.traffic_dto import (
    RouteWithTrafficCommandDTO,
    TrafficAnalysisCommandDTO,
    TrafficAnalysisResultDTO,
    TrafficConditionCommandDTO,
    TrafficConditionResultDTO,
    ViaRouteCommandDTO,
)
from app.application.ports.traffic_provider import TrafficProvider
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.tomtom.acl.traffic_mapper import TomTomTrafficMapper
from app.infrastructure.tomtom.endpoint import (
    CALCULATE_ROUTE_PATH,
    TRAFFIC_FLOW_PATH,
)


class TomTomTrafficAdapter(TrafficProvider):
    """Adapter TomTom cho traffic - xử lý thông tin giao thông.
    
    Đầu vào: Các DTO commands cho traffic operations
    Đầu ra: RoutePlan, TrafficConditionResultDTO, TrafficAnalysisResultDTO
    Chức năng: Gọi TomTom Traffic APIs và chuyển đổi responses thành domain DTOs
    """
    
    def __init__(self, base_url: str, api_key: str, http: AsyncApiClient, timeout_sec: int = 12):
        """Khởi tạo adapter với thông tin kết nối TomTom API."""
        self._base_url = base_url.rstrip("/")
        self._http = http
        self._timeout_sec = timeout_sec
        self._api_key = api_key
        self._mapper = TomTomTrafficMapper()
    
    async def get_traffic_condition(self, cmd: TrafficConditionCommandDTO) -> TrafficConditionResultDTO:
        """Lấy thông tin tình trạng giao thông tại một vị trí cụ thể.
        
        Đầu vào: TrafficConditionCommandDTO (location, zoom)
        Đầu ra: TrafficConditionResultDTO chứa thông tin lưu lượng giao thông
        Xử lý: Gọi TomTom Traffic Flow API để lấy dữ liệu tốc độ và thời gian di chuyển
        """
        # Tạo đường dẫn API với mức zoom
        path = TRAFFIC_FLOW_PATH.format(zoom=cmd.zoom)
        
        # Tạo HTTP request với tọa độ điểm cần kiểm tra
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "point": f"{cmd.location.lat},{cmd.location.lon}",
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và chuyển đổi response thành domain DTO
        payload = await self._http.send(req)
        return self._mapper.to_domain_traffic_condition(payload, cmd.location)
    
    async def get_route_with_traffic(self, cmd: RouteWithTrafficCommandDTO) -> RoutePlan:
        """Tính toán tuyến đường có kèm thông tin giao thông.
        
        Đầu vào: RouteWithTrafficCommandDTO (origin, destination, travel_mode, etc.)
        Đầu ra: RoutePlan chứa tuyến đường và thông tin traffic
        Xử lý: Gọi TomTom Routing API với traffic=true để có thông tin giao thông realtime
        """
        # Chuyển đổi tọa độ thành format string cho TomTom API
        origin = f"{cmd.origin.lat},{cmd.origin.lon}"
        dest = f"{cmd.destination.lat},{cmd.destination.lon}"
        path = CALCULATE_ROUTE_PATH.format(origin=origin, destination=dest)
        
        # Tạo request với đầy đủ tham số traffic
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "traffic": "true",  # Bật thông tin giao thông realtime
                "sectionType": "traffic",  # Chia route thành sections theo traffic
                "instructionsType": "text",  # Lấy hướng dẫn dạng text
                "language": cmd.language,
                "maxAlternatives": str(cmd.max_alternatives),
                "travelMode": cmd.travel_mode,
                "routeType": cmd.route_type,
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và chuyển đổi response thành RoutePlan
        payload = await self._http.send(req)
        return self._mapper.to_domain_route_plan(payload)
    
    async def get_via_route(self, cmd: ViaRouteCommandDTO) -> RoutePlan:
        """Tính toán tuyến đường qua điểm trung gian (A → B → C).
        
        Đầu vào: ViaRouteCommandDTO (origin, via_point, destination, travel_mode)
        Đầu ra: RoutePlan chứa tuyến đường qua điểm trung gian
        Xử lý: Gọi TomTom Routing API với format origin:via:destination
        """
        # Chuyển đổi các tọa độ thành format string
        origin = f"{cmd.origin.lat},{cmd.origin.lon}"
        via = f"{cmd.via_point.lat},{cmd.via_point.lon}"
        dest = f"{cmd.destination.lat},{cmd.destination.lon}"
        
        # TomTom via route format: origin:via:destination
        path = f"/routing/1/calculateRoute/{origin}:{via}:{dest}/json"
        
        # Tạo request cho via route
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "traffic": "true",  # Bao gồm thông tin giao thông
                "sectionType": "traffic",
                "instructionsType": "text",
                "language": cmd.language,
                "travelMode": cmd.travel_mode,
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và chuyển đổi response
        payload = await self._http.send(req)
        return self._mapper.to_domain_route_plan(payload)
    
    async def analyze_route_traffic(self, cmd: TrafficAnalysisCommandDTO) -> TrafficAnalysisResultDTO:
        """Phân tích tình trạng giao thông trên tuyến đường.
        
        Đầu vào: TrafficAnalysisCommandDTO (origin, destination, language)
        Đầu ra: TrafficAnalysisResultDTO chứa phân tích chi tiết về traffic
        Xử lý: Gọi TomTom API, phân tích traffic sections và tạo recommendations
        """
        # Chuyển đổi tọa độ và tạo đường dẫn API
        origin = f"{cmd.origin.lat},{cmd.origin.lon}"
        dest = f"{cmd.destination.lat},{cmd.destination.lon}"
        path = CALCULATE_ROUTE_PATH.format(origin=origin, destination=dest)
        
        # Tạo request với focus vào traffic analysis
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "traffic": "true",  # Bắt buộc để có traffic data
                "sectionType": "traffic",  # Chia nhỏ route theo traffic conditions
                "instructionsType": "text",
                "language": cmd.language,
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        
        # Gửi request và phân tích traffic qua mapper
        payload = await self._http.send(req)
        return self._mapper.to_domain_traffic_analysis(payload)