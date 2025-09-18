"""TomTom Routing ACL Mapper - Chuyển đổi dữ liệu routing cơ bản."""

from app.application.dto.calculate_route_dto import RoutePlan, RouteSection, RouteSummary


class TomTomMapper:
    """Mapper cơ bản cho TomTom routing responses.
    
    Chức năng: Chuyển đổi TomTom routing response thành domain RoutePlan
    """
    def to_domain_route_plan(self, payload: dict) -> RoutePlan:
        """Chuyển đổi TomTom routing response thành domain RoutePlan.
        
        Đầu vào: dict - Raw response từ TomTom Routing API
        Đầu ra: RoutePlan - Kế hoạch tuyến đường domain
        Xử lý: Lấy route đầu tiên, trích xuất summary và sections
        """
        # Lấy danh sách routes từ response
        routes = payload.get("routes", [])
        if not routes:
            # Trả về RoutePlan rỗng nếu không có route
            return RoutePlan(summary=RouteSummary(0, 0), sections=[])
        # Lấy route đầu tiên (tốt nhất)
        r0 = routes[0]
        s = r0.get("summary", {})
        
        # Trích xuất thông tin khoảng cách và thời gian
        distance = int(s.get("lengthInMeters", 0))
        duration = int(s.get("travelTimeInSeconds", 0))

        # Xử lý các sections của route
        sections: list[RouteSection] = []
        for sec in r0.get("sections", []) or []:
            # Xác định loại section (traffic hoặc thông thường)
            kind = str(sec.get("sectionType") or "")
            simple = sec.get("simpleCategory")
            if simple:
                # Nếu có traffic info, thêm prefix
                kind = f"traffic:{simple}"
            
            # Tạo RouteSection và thêm vào danh sách
            sections.append(RouteSection(kind=kind, start_index=0, end_index=0))

        # Trả về RoutePlan hoàn chỉnh
        return RoutePlan(summary=RouteSummary(distance, duration), sections=sections)
