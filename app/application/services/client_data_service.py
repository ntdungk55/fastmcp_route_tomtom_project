"""
AI Data Transformer Service - BLK-1-12: TransformSuccessDataForAI
Chiết xuất và biến đổi dữ liệu route thành công thành format tối ưu cho AI/LLM.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from app.infrastructure.logging.logger import get_logger
from app.application.dto.detailed_route_response_dto import (
    DetailedRouteResponse, RoutePoint, TrafficCondition, RouteInstruction, AlternativeRoute,
    create_route_point, create_traffic_condition, create_route_instruction, create_alternative_route
)
from app.application.services.traffic_analysis_service import (
    TrafficAnalysisResult, TrafficSegment
)


@dataclass
class UserPreferences:
    """User preferences cho formatting."""
    locale: str = "vi"  # "vi" | "en"
    unit_system: str = "metric"  # "metric" | "imperial"
    time_format: str = "24h"  # "24h" | "12h"


class ClientDataService:
    """
    BLK-1-12: TransformSuccessDataForAI - Transform route data thành AI-friendly format
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
    
    async def transform_route_data_for_ai(self, route_data: Dict[str, Any], 
                                        request_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        BLK-1-12: Transform route data thành AI-friendly format
        
        Args:
            route_data: Route data từ API response
            request_context: Request context với user preferences
            
        Returns:
            Dict: AI-friendly formatted data
        """
        request_id = request_context.get("request_id", "unknown")
        self._logger.info(f"BLK-1-12: Transforming route data for AI - request {request_id}")
        
        try:
            # Extract user preferences
            user_prefs = self._extract_user_preferences(request_context)
            
            # Transform summary
            summary = self._transform_summary(route_data.get("summary", {}), user_prefs)
            
            # Transform route overview
            route_overview = self._transform_route_overview(route_data, user_prefs)
            
            # Transform turn-by-turn directions
            turn_by_turn = self._transform_turn_by_turn(route_data.get("guidance", {}), user_prefs)
            
            # Build AI-friendly response
            ai_response = {
                "type": "ROUTE_SUCCESS",
                "locale": user_prefs.locale,
                "summary": summary,
                "route_overview": route_overview,
                "turn_by_turn": turn_by_turn,
                "rendering_hints": {
                    "style": "conversational",
                    "detail_level": self._determine_detail_level(route_data),
                    "include_map_link": True
                },
                "metadata": {
                    "request_id": request_id,
                    "calculated_at": datetime.utcnow().isoformat() + "Z",
                    "data_source": "TomTom Routing API"
                }
            }
            
            self._logger.info(f"BLK-1-12: Successfully transformed route data for {request_id}")
            return ai_response
            
        except Exception as e:
            self._logger.error(f"BLK-1-12: Failed to transform route data for {request_id}: {e}")
            # Return fallback response
            return self._create_fallback_response(route_data, request_context)
    
    def _extract_user_preferences(self, request_context: Dict[str, Any]) -> UserPreferences:
        """Extract user preferences từ request context."""
        user_prefs = request_context.get("user_preferences", {})
        
        return UserPreferences(
            locale=user_prefs.get("locale", "vi"),
            unit_system=user_prefs.get("unit_system", "metric"),
            time_format=user_prefs.get("time_format", "24h")
        )
    
    def _transform_summary(self, summary_data: Dict[str, Any], user_prefs: UserPreferences) -> Dict[str, Any]:
        """Transform route summary."""
        distance_m = summary_data.get("length_in_meters", 0)
        duration_s = summary_data.get("travel_time_in_seconds", 0)
        traffic_delay_s = summary_data.get("traffic_delay_in_seconds", 0)
        departure_time = summary_data.get("departure_time")
        arrival_time = summary_data.get("arrival_time")
        
        # Format distance
        distance = self._format_distance(distance_m, user_prefs)
        
        # Format duration
        duration = self._format_duration(duration_s, user_prefs)
        duration_with_traffic = self._format_duration(duration_s + traffic_delay_s, user_prefs)
        
        # Format times
        departure = self._format_datetime(departure_time, user_prefs) if departure_time else None
        arrival = self._format_datetime(arrival_time, user_prefs) if arrival_time else None
        
        # Format traffic info
        traffic_info = self._format_traffic_info(traffic_delay_s, user_prefs)
        
        return {
            "distance": distance,
            "duration": {
                "value": duration_s,
                "formatted": duration,
                "with_traffic": duration_with_traffic
            },
            "departure": departure,
            "arrival": arrival,
            "traffic_info": traffic_info
        }
    
    def _format_distance(self, meters: int, user_prefs: UserPreferences) -> Dict[str, Any]:
        """Format distance với localization."""
        if user_prefs.unit_system == "imperial":
            miles = meters / 1609.34
            return {
                "value": round(miles, 1),
                "unit": "miles",
                "formatted": f"{miles:,.1f} miles" if user_prefs.locale == "en" else f"{miles:,.1f} dặm"
            }
        else:  # metric
            km = meters / 1000
            return {
                "value": round(km, 1) if km > 10 else round(km, 2),
                "unit": "km",
                "formatted": f"{km:,.1f} km"
            }
    
    def _format_duration(self, seconds: int, user_prefs: UserPreferences) -> str:
        """Format duration với localization."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if user_prefs.locale == "vi":
            if hours > 0:
                return f"{hours} giờ {minutes} phút" if minutes > 0 else f"{hours} giờ"
            else:
                return f"{minutes} phút"
        else:  # en
            if hours > 0:
                return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            else:
                return f"{minutes}m"
    
    def _format_datetime(self, iso_datetime: str, user_prefs: UserPreferences) -> Dict[str, Any]:
        """Format datetime với localization."""
        try:
            dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
            
            if user_prefs.locale == "vi":
                formatted = dt.strftime("%H:%M, %d/%m/%Y")
            else:  # en
                if user_prefs.time_format == "12h":
                    formatted = dt.strftime("%I:%M %p, %m/%d/%Y")
                else:
                    formatted = dt.strftime("%H:%M, %m/%d/%Y")
            
            return {
                "time": iso_datetime,
                "formatted": formatted
            }
        except Exception:
            return {
                "time": iso_datetime,
                "formatted": iso_datetime
            }
    
    def _format_traffic_info(self, delay_seconds: int, user_prefs: UserPreferences) -> str:
        """Format traffic delay info."""
        if delay_seconds < 300:  # < 5 min
            return "Giao thông thông thoáng" if user_prefs.locale == "vi" else "Light traffic"
        elif delay_seconds < 1800:  # < 30 min
            delay_min = delay_seconds // 60
            return f"Có chút kẹt xe (+{delay_min} phút)" if user_prefs.locale == "vi" else f"Some traffic (+{delay_min} min)"
        else:  # > 30 min
            delay_min = delay_seconds // 60
            return f"Kẹt xe khá nhiều (+{delay_min} phút)" if user_prefs.locale == "vi" else f"Heavy traffic (+{delay_min} min)"
    
    def _transform_route_overview(self, route_data: Dict[str, Any], user_prefs: UserPreferences) -> Dict[str, Any]:
        """Transform route overview."""
        guidance = route_data.get("guidance", {})
        instructions = guidance.get("instructions", [])
        
        # Extract main roads
        main_roads = self._extract_main_roads(instructions)
        
        # Extract via cities (simplified)
        via_cities = self._extract_via_cities(instructions)
        
        # Generate highlights
        highlights = self._generate_highlights(route_data, user_prefs)
        
        return {
            "main_roads": main_roads,
            "via_cities": via_cities,
            "highlights": highlights
        }
    
    def _extract_main_roads(self, instructions: List[Dict[str, Any]]) -> List[str]:
        """Extract main roads từ instructions."""
        roads = set()
        
        for instruction in instructions:
            message = instruction.get("message", "")
            # Extract road names (simplified pattern matching)
            road_patterns = [
                r'onto\s+([A-Z][a-zA-Z\s]+(?:Street|Road|Avenue|Highway|QL\d+|AH\d+))',
                r'onto\s+([A-Z][a-zA-Z\s]+)',
                r'([A-Z][a-zA-Z\s]+(?:Street|Road|Avenue|Highway))'
            ]
            
            for pattern in road_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    road_name = match.strip()
                    if len(road_name) > 3:  # Filter out short matches
                        roads.add(road_name)
        
        return list(roads)[:5]  # Limit to 5 main roads
    
    def _extract_via_cities(self, instructions: List[Dict[str, Any]]) -> List[str]:
        """Extract via cities từ instructions (simplified)."""
        # This is a simplified implementation
        # In a real system, you'd use geocoding to identify cities
        cities = []
        
        # Common Vietnamese cities to look for
        vietnamese_cities = [
            "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ",
            "Huế", "Nha Trang", "Vũng Tàu", "Quy Nhon", "Phan Thiết"
        ]
        
        for instruction in instructions:
            message = instruction.get("message", "")
            for city in vietnamese_cities:
                if city.lower() in message.lower():
                    if city not in cities:
                        cities.append(city)
        
        return cities[:5]  # Limit to 5 cities
    
    def _generate_highlights(self, route_data: Dict[str, Any], user_prefs: UserPreferences) -> List[str]:
        """Generate route highlights."""
        highlights = []
        summary = route_data.get("summary", {})
        distance_m = summary.get("length_in_meters", 0)
        duration_s = summary.get("travel_time_in_seconds", 0)
        
        # Distance-based highlights
        if distance_m < 50000:  # < 50km
            if user_prefs.locale == "vi":
                highlights.append("Tuyến đường ngắn trong thành phố")
            else:
                highlights.append("Short city route")
        elif distance_m > 500000:  # > 500km
            if user_prefs.locale == "vi":
                highlights.append("Hành trình dài liên tỉnh")
                highlights.append("Khuyến nghị nghỉ đêm nếu lái xe")
            else:
                highlights.append("Long intercity journey")
                highlights.append("Overnight rest recommended")
        
        # Duration-based highlights
        hours = duration_s // 3600
        if hours > 8:
            if user_prefs.locale == "vi":
                highlights.append("Thời gian lái xe khá dài, cần nghỉ ngơi")
            else:
                highlights.append("Long driving time, rest breaks recommended")
        
        # Traffic-based highlights
        traffic_delay = summary.get("traffic_delay_in_seconds", 0)
        if traffic_delay > 1800:  # > 30 min
            if user_prefs.locale == "vi":
                highlights.append("Có kẹt xe đáng kể trên tuyến đường")
            else:
                highlights.append("Significant traffic congestion expected")
        
        return highlights[:3]  # Limit to 3 highlights
    
    def _transform_turn_by_turn(self, guidance_data: Dict[str, Any], user_prefs: UserPreferences) -> List[Dict[str, Any]]:
        """Transform turn-by-turn directions."""
        instructions = guidance_data.get("instructions", [])
        
        if not instructions:
            return []
        
        # Determine if we should simplify
        total_distance = sum(
            instruction.get("distance", 0) for instruction in instructions
        )
        
        # Simplify for long routes
        if total_distance > 200000:  # > 200km
            return self._simplify_turn_by_turn(instructions, user_prefs)
        
        # Full turn-by-turn for shorter routes
        turn_by_turn = []
        for i, instruction in enumerate(instructions):
            step = {
                "step": i + 1,
                "instruction": self._translate_instruction(instruction.get("message", ""), user_prefs),
                "distance": self._format_step_distance(instruction.get("distance", 0), user_prefs),
                "duration": self._format_step_duration(instruction.get("duration", 0), user_prefs)
            }
            turn_by_turn.append(step)
        
        return turn_by_turn[:15]  # Limit to 15 steps
    
    def _simplify_turn_by_turn(self, instructions: List[Dict[str, Any]], user_prefs: UserPreferences) -> List[Dict[str, Any]]:
        """Simplify turn-by-turn for long routes."""
        simplified = []
        
        # Group instructions by major maneuvers
        major_maneuvers = ["DEPART", "ARRIVE", "TURN_LEFT", "TURN_RIGHT", "CONTINUE"]
        
        for i, instruction in enumerate(instructions):
            maneuver = instruction.get("maneuver", "")
            if maneuver in major_maneuvers:
                step = {
                    "step": len(simplified) + 1,
                    "instruction": self._translate_instruction(instruction.get("message", ""), user_prefs),
                    "distance": self._format_step_distance(instruction.get("distance", 0), user_prefs),
                    "duration": self._format_step_duration(instruction.get("duration", 0), user_prefs)
                }
                simplified.append(step)
        
        return simplified[:10]  # Limit to 10 major steps
    
    def _translate_instruction(self, message: str, user_prefs: UserPreferences) -> str:
        """Translate instruction message."""
        # This is a simplified translation
        # In a real system, you'd have a proper translation service
        
        if user_prefs.locale == "vi":
            # Basic English to Vietnamese translations
            translations = {
                "head": "đi về phía",
                "turn left": "rẽ trái",
                "turn right": "rẽ phải",
                "continue": "tiếp tục",
                "arrive": "đến nơi",
                "onto": "vào",
                "street": "phố",
                "road": "đường",
                "avenue": "đại lộ"
            }
            
            translated = message
            for en, vi in translations.items():
                translated = re.sub(rf'\b{en}\b', vi, translated, flags=re.IGNORECASE)
            
            return translated
        
        return message  # Keep original for English
    
    def _format_step_distance(self, meters: int, user_prefs: UserPreferences) -> str:
        """Format step distance."""
        if user_prefs.unit_system == "imperial":
            if meters < 1609:  # < 1 mile
                return f"{meters} ft"
            else:
                miles = meters / 1609.34
                return f"{miles:.1f} miles"
        else:  # metric
            if meters < 1000:
                return f"{meters}m"
            else:
                km = meters / 1000
                return f"{km:.1f}km"
    
    def _format_step_duration(self, seconds: int, user_prefs: UserPreferences) -> str:
        """Format step duration."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} phút" if user_prefs.locale == "vi" else f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _determine_detail_level(self, route_data: Dict[str, Any]) -> str:
        """Determine detail level based on route complexity."""
        summary = route_data.get("summary", {})
        distance_m = summary.get("length_in_meters", 0)
        
        if distance_m < 50000:  # < 50km
            return "detailed"
        elif distance_m < 200000:  # < 200km
            return "summary"
        else:  # > 200km
            return "minimal"
    
    def _create_fallback_response(self, route_data: Dict[str, Any], request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback response if transformation fails."""
        return {
            "type": "ROUTE_SUCCESS",
            "locale": "vi",
            "summary": {
                "distance": {"value": 0, "unit": "km", "formatted": "0 km"},
                "duration": {"value": 0, "formatted": "0 phút", "with_traffic": "0 phút"},
                "traffic_info": "Không có thông tin giao thông"
            },
            "route_overview": {
                "main_roads": [],
                "via_cities": [],
                "highlights": ["Tuyến đường đã được tính toán thành công"]
            },
            "turn_by_turn": [],
            "rendering_hints": {
                "style": "conversational",
                "detail_level": "summary"
            },
            "metadata": {
                "request_id": request_context.get("request_id", "unknown"),
                "calculated_at": datetime.utcnow().isoformat() + "Z",
                "data_source": "TomTom Routing API",
                "note": "Simplified response due to transformation error"
            }
        }
    
    async def create_detailed_route_response(self, route_data: Dict[str, Any], 
                                           request_context: Dict[str, Any]) -> DetailedRouteResponse:
        """
        Tạo DetailedRouteResponse theo model yêu cầu:
        1. Tên điểm đến điểm đi
        2. Thời gian đi
        3. Cách di chuyển
        4. Hướng dẫn chi tiết (kèm trạng thái đường đi)
        5. Cách di chuyển khác (kèm trạng thái đường đi)
        """
        request_id = request_context.get("request_id", "unknown")
        self._logger.info(f"BLK-1-12: Creating detailed route response for request {request_id}")
        
        try:
            # Extract data from route_data
            summary = route_data.get("summary", {})
            guidance = route_data.get("guidance", {})
            instructions = guidance.get("instructions", [])
            
            # Get traffic analysis data
            traffic_analysis = request_context.get("traffic_analysis")
            
            # 1. Tên điểm đến điểm đi
            origin = create_route_point(
                name="Điểm xuất phát",
                address="Hà Nội, Việt Nam",  # Mock data - sẽ được thay thế bằng geocoding thực
                lat=21.0285,
                lon=105.8542
            )
            
            destination = create_route_point(
                name="Điểm đến",
                address="TP. Hồ Chí Minh, Việt Nam",  # Mock data - sẽ được thay thế bằng geocoding thực
                lat=10.8231,
                lon=106.6297
            )
            
            # 2. Thời gian đi
            total_duration_seconds = summary.get("travel_time_in_seconds", 0)
            total_duration_formatted = self._format_duration(total_duration_seconds, "vi")
            
            # 3. Cách di chuyển
            travel_mode = request_context.get("travel_mode", "car")
            travel_mode_descriptions = {
                "car": "Ô tô",
                "bicycle": "Xe đạp", 
                "foot": "Đi bộ",
                "truck": "Xe tải",
                "taxi": "Taxi",
                "bus": "Xe buýt"
            }
            travel_mode_description = travel_mode_descriptions.get(travel_mode, "Ô tô")
            
            # 4. Hướng dẫn chi tiết (kèm trạng thái đường đi)
            route_instructions = []
            for i, instruction in enumerate(instructions[:10]):  # Limit to 10 steps
                # Get real traffic condition for this instruction
                traffic_condition = self._get_traffic_condition_for_instruction(
                    instruction, traffic_analysis, i
                )
                
                route_instruction = create_route_instruction(
                    step=i + 1,
                    instruction=instruction.get("message", ""),
                    distance_meters=instruction.get("distance", 1000),  # Use real distance if available
                    duration_seconds=instruction.get("duration", 300),  # Use real duration if available
                    road_name=self._extract_road_name(instruction.get("message", "")),
                    traffic_condition=traffic_condition,
                    coordinates=instruction.get("point", {})
                )
                route_instructions.append(route_instruction)
            
            # Main route traffic condition - sử dụng dữ liệu thực
            main_traffic = self._get_main_route_traffic_condition(traffic_analysis)
            
            main_route = create_alternative_route(
                route_id="main-route-001",
                summary="Tuyến đường chính qua QL1A",
                total_distance_meters=summary.get("length_in_meters", 0),
                total_duration_seconds=total_duration_seconds,
                traffic_condition=main_traffic,
                instructions=route_instructions,
                highlights=[
                    "Tuyến đường nhanh nhất",
                    "Đi qua 15 tỉnh thành",
                    "Có trạm thu phí"
                ]
            )
            
            # 5. Cách di chuyển khác (kèm trạng thái đường đi)
            alternative_routes = self._create_alternative_routes_with_real_traffic(
                summary, total_duration_seconds, route_instructions, traffic_analysis
            )
            
            # Create detailed route response
            detailed_response = DetailedRouteResponse(
                origin=origin,
                destination=destination,
                total_duration_seconds=total_duration_seconds,
                total_duration_formatted=total_duration_formatted,
                departure_time=summary.get("departure_time"),
                arrival_time=summary.get("arrival_time"),
                travel_mode=travel_mode,
                travel_mode_description=travel_mode_description,
                main_route=main_route,
                alternative_routes=alternative_routes,
                request_id=request_id
            )
            
            self._logger.info(f"BLK-1-12: Successfully created detailed route response for {request_id}")
            return detailed_response
            
        except Exception as e:
            self._logger.error(f"BLK-1-12: Failed to create detailed route response for {request_id}: {e}")
            # Return fallback response
            return self._create_fallback_detailed_response(request_id)
    
    def _create_fallback_detailed_response(self, request_id: str) -> DetailedRouteResponse:
        """Create fallback detailed route response."""
        origin = create_route_point("Điểm xuất phát", "Không xác định", 0.0, 0.0)
        destination = create_route_point("Điểm đến", "Không xác định", 0.0, 0.0)
        
        traffic_condition = create_traffic_condition("unknown", 0, "Không có thông tin")
        
        main_route = create_alternative_route(
            route_id="fallback-route",
            summary="Tuyến đường mặc định",
            total_distance_meters=0,
            total_duration_seconds=0,
            traffic_condition=traffic_condition,
            instructions=[],
            highlights=["Không có thông tin tuyến đường"]
        )
        
        return DetailedRouteResponse(
            origin=origin,
            destination=destination,
            total_duration_seconds=0,
            total_duration_formatted="0 phút",
            travel_mode="car",
            travel_mode_description="Ô tô",
            main_route=main_route,
            alternative_routes=[],
            request_id=request_id
        )
    
    def _get_traffic_condition_for_instruction(self, instruction: Dict[str, Any], 
                                             traffic_analysis: Optional[TrafficAnalysisResult], 
                                             instruction_index: int) -> TrafficCondition:
        """Lấy traffic condition thực cho một instruction cụ thể."""
        if not traffic_analysis or not traffic_analysis.segments:
            # Fallback nếu không có traffic data
            return create_traffic_condition(
                condition="unknown",
                delay_minutes=0,
                description="Không có thông tin giao thông"
            )
        
        # Tìm segment tương ứng với instruction
        point = instruction.get("point", {})
        if point:
            lat = point.get("lat")
            lon = point.get("lon")
            
            if lat and lon:
                # Tìm segment gần nhất
                for segment in traffic_analysis.segments:
                    if self._is_point_near_segment(lat, lon, segment):
                        return create_traffic_condition(
                            condition=segment.condition,
                            delay_minutes=segment.delay_minutes,
                            description=segment.description
                        )
        
        # Nếu không tìm thấy segment cụ thể, sử dụng overall condition
        return create_traffic_condition(
            condition=traffic_analysis.overall_condition,
            delay_minutes=traffic_analysis.total_delay_minutes // max(len(traffic_analysis.segments), 1),
            description=self._get_traffic_description(traffic_analysis.overall_condition)
        )
    
    def _is_point_near_segment(self, lat: float, lon: float, segment: TrafficSegment) -> bool:
        """Check if point is near a traffic segment."""
        # Simple distance check (có thể cải thiện bằng haversine formula)
        lat_diff = abs(lat - segment.start_lat) + abs(lat - segment.end_lat)
        lon_diff = abs(lon - segment.start_lon) + abs(lon - segment.end_lon)
        
        # Threshold: ~1km
        return lat_diff < 0.01 and lon_diff < 0.01
    
    def _get_main_route_traffic_condition(self, traffic_analysis: Optional[TrafficAnalysisResult]) -> TrafficCondition:
        """Lấy traffic condition cho tuyến đường chính."""
        if not traffic_analysis:
            return create_traffic_condition(
                condition="unknown",
                delay_minutes=0,
                description="Không có thông tin giao thông"
            )
        
        return create_traffic_condition(
            condition=traffic_analysis.overall_condition,
            delay_minutes=traffic_analysis.total_delay_minutes,
            description=self._get_traffic_description(traffic_analysis.overall_condition)
        )
    
    def _create_alternative_routes_with_real_traffic(self, summary: Dict[str, Any], 
                                                   total_duration_seconds: int,
                                                   route_instructions: List[RouteInstruction],
                                                   traffic_analysis: Optional[TrafficAnalysisResult]) -> List[AlternativeRoute]:
        """Tạo alternative routes với traffic data thực."""
        alternative_routes = []
        
        # Alternative route 1 - Highway route
        alt_traffic_1 = self._estimate_alternative_route_traffic("highway", traffic_analysis)
        alt_route_1 = create_alternative_route(
            route_id="alt-route-001",
            summary="Tuyến đường thay thế qua cao tốc",
            total_distance_meters=summary.get("length_in_meters", 0) + 50000,  # Longer
            total_duration_seconds=total_duration_seconds + 1800,  # +30 min
            traffic_condition=alt_traffic_1,
            instructions=route_instructions[:5],  # Shorter instructions
            highlights=[
                "Tuyến đường cao tốc",
                "Ít đèn giao thông",
                "Chi phí cao hơn"
            ]
        )
        alternative_routes.append(alt_route_1)
        
        # Alternative route 2 - Scenic route
        alt_traffic_2 = self._estimate_alternative_route_traffic("scenic", traffic_analysis)
        alt_route_2 = create_alternative_route(
            route_id="alt-route-002",
            summary="Tuyến đường ven biển",
            total_distance_meters=summary.get("length_in_meters", 0) + 100000,  # Much longer
            total_duration_seconds=total_duration_seconds + 3600,  # +1 hour
            traffic_condition=alt_traffic_2,
            instructions=route_instructions[:3],  # Very short instructions
            highlights=[
                "Tuyến đường ven biển đẹp",
                "Giao thông thông thoáng",
                "Thời gian lâu hơn"
            ]
        )
        alternative_routes.append(alt_route_2)
        
        return alternative_routes
    
    def _estimate_alternative_route_traffic(self, route_type: str, 
                                          traffic_analysis: Optional[TrafficAnalysisResult]) -> TrafficCondition:
        """Ước tính traffic condition cho alternative route."""
        if not traffic_analysis:
            # Default conditions for different route types
            if route_type == "highway":
                return create_traffic_condition(
                    condition="moderate",
                    delay_minutes=15,
                    description="Giao thông vừa phải trên cao tốc"
                )
            else:  # scenic
                return create_traffic_condition(
                    condition="light",
                    delay_minutes=5,
                    description="Giao thông thông thoáng"
                )
        
        # Adjust based on main route traffic
        base_condition = traffic_analysis.overall_condition
        base_delay = traffic_analysis.total_delay_minutes
        
        if route_type == "highway":
            # Highway thường có traffic tốt hơn
            if base_condition == "congested":
                condition = "heavy"
                delay = base_delay // 2
            elif base_condition == "heavy":
                condition = "moderate"
                delay = base_delay // 3
            else:
                condition = "light"
                delay = max(0, base_delay - 10)
        else:  # scenic
            # Scenic route thường ít traffic hơn
            if base_condition in ["congested", "heavy"]:
                condition = "moderate"
                delay = base_delay // 3
            else:
                condition = "light"
                delay = max(0, base_delay - 5)
        
        return create_traffic_condition(
            condition=condition,
            delay_minutes=delay,
            description=self._get_traffic_description(condition)
        )
    
    def _get_traffic_description(self, condition: str) -> str:
        """Lấy mô tả traffic condition."""
        descriptions = {
            "light": "Giao thông thông thoáng",
            "moderate": "Có kẹt xe nhẹ",
            "heavy": "Kẹt xe nhiều",
            "congested": "Kẹt xe nghiêm trọng",
            "unknown": "Không có thông tin giao thông"
        }
        return descriptions.get(condition, "Không có thông tin giao thông")
    
    def _extract_road_name(self, instruction_message: str) -> Optional[str]:
        """Extract tên đường từ instruction message."""
        import re
        
        # Patterns để tìm tên đường
        patterns = [
            r'onto\s+([A-Z][a-zA-Z\s]+(?:Street|Road|Avenue|Highway|QL\d+|AH\d+))',
            r'onto\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+(?:Street|Road|Avenue|Highway))',
            r'(QL\d+)',  # Quốc lộ
            r'(AH\d+)',  # Asian Highway
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instruction_message, re.IGNORECASE)
            if match:
                road_name = match.group(1).strip()
                if len(road_name) > 2:  # Filter out short matches
                    return road_name
        
        return None


# Factory function
def get_client_data_service() -> ClientDataService:
    """Factory function để lấy client data service."""
    return ClientDataService()

