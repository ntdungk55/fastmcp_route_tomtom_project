"""TomTom Traffic ACL Mapper - Chuyển đổi dữ liệu traffic."""

from app.application.dto.calculate_route_dto import RoutePlan, RouteSection, RouteSummary
from app.application.dto.traffic_dto import (
    TrafficAnalysisResultDTO,
    TrafficConditionResultDTO,
    TrafficFlowDataDTO,
    TrafficSectionDTO,
)
from app.domain.value_objects.latlon import LatLon


class TomTomTrafficMapper:
    """Mapper chuyển đổi TomTom traffic responses thành domain DTOs.
    
    Chức năng: Tránh vendor lock-in bằng cách map TomTom traffic format sang domain format
    """
    
    def to_domain_traffic_condition(self, payload: dict, location: LatLon) -> TrafficConditionResultDTO:
        """Chuyển đổi TomTom traffic flow response thành domain DTO.
        
        Đầu vào: dict - Raw response từ TomTom Traffic Flow API, location
        Đầu ra: TrafficConditionResultDTO - Thông tin tình trạng giao thông
        Xử lý: Lấy dữ liệu tốc độ, thời gian di chuyển và tình trạng đường
        """
        flow_segment = payload.get("flowSegmentData", {})
        
        flow_data = TrafficFlowDataDTO(
            current_speed=flow_segment.get("currentSpeed"),
            free_flow_speed=flow_segment.get("freeFlowSpeed"),
            current_travel_time=flow_segment.get("currentTravelTime"),
            free_flow_travel_time=flow_segment.get("freeFlowTravelTime"),
            confidence=flow_segment.get("confidence")
        )
        
        return TrafficConditionResultDTO(
            location=location,
            flow_data=flow_data,
            road_closure=flow_segment.get("roadClosure")
        )
    
    def to_domain_route_plan(self, payload: dict) -> RoutePlan:
        """Chuyển đổi TomTom route response thành domain RoutePlan.
        
        Đầu vào: dict - Raw response từ TomTom Routing API
        Đầu ra: RoutePlan - Kế hoạch tuyến đường với summary và sections
        Xử lý: Trích xuất khoảng cách, thời gian và các đoạn đường
        """
        routes = payload.get("routes", [])
        if not routes:
            return RoutePlan(summary=RouteSummary(distance_m=0, duration_s=0), sections=[])
        
        route = routes[0]
        summary_data = route.get("summary", {})
        distance = int(summary_data.get("lengthInMeters", 0))
        duration = int(summary_data.get("travelTimeInSeconds", 0))
        
        sections: list[RouteSection] = []
        for sec in route.get("sections", []) or []:
            kind = str(sec.get("sectionType") or "")
            simple = sec.get("simpleCategory")
            if simple:
                kind = f"traffic:{simple}"
            
            sections.append(RouteSection(
                kind=kind,
                start_index=sec.get("startPointIndex", 0),
                end_index=sec.get("endPointIndex", 0)
            ))
        
        return RoutePlan(
            summary=RouteSummary(distance_m=distance, duration_s=duration),
            sections=sections
        )
    
    def to_domain_traffic_analysis(self, payload: dict) -> TrafficAnalysisResultDTO:
        """Chuyển đổi TomTom route response thành phân tích traffic.
        
        Đầu vào: dict - Raw response từ TomTom Routing API với traffic data
        Đầu ra: TrafficAnalysisResultDTO - Phân tích chi tiết về giao thông
        Xử lý: Đếm các loại traffic, tính điểm, tạo khuyến nghị
        """
        routes = payload.get("routes", [])
        if not routes:
            return TrafficAnalysisResultDTO(
                overall_status="UNKNOWN",
                traffic_score=0.0,
                conditions_count={},
                heavy_traffic_sections=[],
                total_sections=0,
                recommendations=[]
            )
        
        route = routes[0]
        sections = route.get("sections", [])
        
        # Đếm số lượng các loại tình trạng giao thông
        traffic_conditions = {
            "FLOWING": 0,
            "SLOW": 0,
            "JAM": 0,
            "CLOSED": 0,
            "UNKNOWN": 0
        }
        
        heavy_traffic_sections = []
        for i, section in enumerate(sections):
            simple_category = section.get("simpleCategory", "UNKNOWN")
            traffic_conditions[simple_category] = traffic_conditions.get(simple_category, 0) + 1
            
            if simple_category in ["SLOW", "JAM", "CLOSED"]:
                traffic_section = TrafficSectionDTO(
                    section_index=i,
                    condition=simple_category,
                    start_index=section.get("startPointIndex", 0),
                    end_index=section.get("endPointIndex", 0),
                    delay_seconds=section.get("travelTimeInSeconds")
                )
                heavy_traffic_sections.append(traffic_section)
        
        # Tính điểm mức độ nghiêm trọng của giao thông (0-100, cao hơn = tệ hơn)
        total_sections = len(sections)
        if total_sections > 0:
            traffic_score = (
                traffic_conditions["SLOW"] * 30 +
                traffic_conditions["JAM"] * 70 +
                traffic_conditions["CLOSED"] * 100
            ) / total_sections
        else:
            traffic_score = 0
        
        # Xác định tình trạng giao thông tổng thể
        if traffic_score >= 70:
            overall_status = "HEAVY_TRAFFIC"
        elif traffic_score >= 30:
            overall_status = "MODERATE_TRAFFIC"
        else:
            overall_status = "LIGHT_TRAFFIC"
        
        # Tạo các khuyến nghị dựa trên phân tích
        recommendations = self._generate_traffic_recommendations(
            overall_status, traffic_score, heavy_traffic_sections
        )
        
        return TrafficAnalysisResultDTO(
            overall_status=overall_status,
            traffic_score=round(traffic_score, 2),
            conditions_count=traffic_conditions,
            heavy_traffic_sections=heavy_traffic_sections,
            total_sections=total_sections,
            recommendations=recommendations
        )
    
    def _generate_traffic_recommendations(
        self, 
        status: str, 
        score: float, 
        heavy_sections: list[TrafficSectionDTO]
    ) -> list[str]:
        """Tạo khuyến nghị giao thông dựa trên phân tích.
        
        Đầu vào: status (tình trạng), score (điểm), heavy_sections (các đoạn kẹt xe)
        Đầu ra: list[str] - Danh sách khuyến nghị bằng tiếng Việt
        Xử lý: Dựa vào mức độ nghiêm trọng để đưa ra lời khuyên
        """
        # Khởi tạo danh sách khuyến nghị
        recommendations = []
        
        if status == "HEAVY_TRAFFIC":
            recommendations.append("🚨 Tình trạng giao thông rất tệ - nên tránh tuyến đường này")
            recommendations.append("⏰ Nên đi sớm hơn hoặc muộn hơn để tránh giờ cao điểm")
            recommendations.append("🔄 Cân nhắc sử dụng phương tiện công cộng")
        elif status == "MODERATE_TRAFFIC":
            recommendations.append("⚠️ Tình trạng giao thông trung bình - có thể có kẹt xe nhẹ")
            recommendations.append("📱 Theo dõi tình hình giao thông trong quá trình di chuyển")
        else:
            recommendations.append("✅ Tình trạng giao thông tốt - có thể di chuyển bình thường")
        
        if heavy_sections:
            recommendations.append(f"🚧 Có {len(heavy_sections)} đoạn đường bị kẹt xe nặng")
        
        if score > 50:
            recommendations.append("🕐 Thời gian di chuyển có thể tăng 50% so với bình thường")
        
        return recommendations
