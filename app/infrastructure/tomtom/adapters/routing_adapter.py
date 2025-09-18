"""TomTom Routing Adapter - Triển khai routing provider cơ bản."""

from app.application.dto.calculate_route_dto import CalculateRouteCommand, RoutePlan
from app.application.ports.routing_provider import RoutingProvider
from app.infrastructure.http.client import AsyncApiClient
from app.infrastructure.http.http_method import HttpMethod
from app.infrastructure.http.request_entity import RequestEntity
from app.infrastructure.tomtom.acl.mappers import TomTomMapper
from app.infrastructure.tomtom.endpoint import CALCULATE_ROUTE_PATH, DEFAULT_TRAVEL_MODE


class TomTomRoutingAdapter(RoutingProvider):
    """Adapter TomTom cho routing cơ bản - tính toán tuyến đường.
    
    Đầu vào: CalculateRouteCommand (origin, destination, travel_mode, waypoints)
    Đầu ra: RoutePlan chứa summary và sections của tuyến đường
    Chức năng: Gọi TomTom Routing API và chuyển đổi response thành domain RoutePlan
    """
    def __init__(self, base_url: str, api_key: str, http: AsyncApiClient, timeout_sec: int = 12):
        """Khởi tạo adapter với thông tin kết nối TomTom API."""
        self._base_url = base_url.rstrip("/")
        self._http = http
        self._timeout_sec = timeout_sec
        self._api_key = api_key
        self._mapper = TomTomMapper()

    async def calculate_route(self, cmd: CalculateRouteCommand) -> RoutePlan:
        """Tính toán tuyến đường cơ bản.
        
        Đầu vào: CalculateRouteCommand chứa điểm đi, điểm đến, phương tiện
        Đầu ra: RoutePlan với thông tin khoảng cách, thời gian và các đoạn đường
        Xử lý: Gọi TomTom Routing API với traffic=true để có thông tin realtime
        """
        # Chuyển đổi tọa độ thành format string cho TomTom API
        origin = f"{cmd.origin.lat},{cmd.origin.lon}"
        dest = f"{cmd.destination.lat},{cmd.destination.lon}"
        path = CALCULATE_ROUTE_PATH.format(origin=origin, destination=dest)
        
        # Map travel mode từ domain enum sang TomTom format
        travel_mode = DEFAULT_TRAVEL_MODE.get(cmd.travel_mode.value, "car")
        # Tạo HTTP request với các tham số routing
        req = RequestEntity(
            method=HttpMethod.GET,
            url=f"{self._base_url}{path}",
            headers={"Accept": "application/json"},
            params={
                "key": self._api_key,
                "traffic": "true",  # Bật thông tin giao thông realtime
                "sectionType": "traffic",  # Chia route theo traffic sections
                "travelMode": travel_mode,
                "maxAlternatives": "0",  # Chỉ lấy 1 route tốt nhất
            },
            json=None,
            timeout_sec=self._timeout_sec,
        )
        # Gửi request và chuyển đổi response thành domain RoutePlan
        payload = await self._http.send(req)
        return self._mapper.to_domain_route_plan(payload)
