"""TomTom Routing ACL Mapper - Chuyển đổi dữ liệu routing cơ bản."""

from app.application.dto.calculate_route_dto import RoutePlan, RouteSection, RouteSummary, RouteGuidance, RouteInstruction
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class TomTomMapper:
    """Mapper cơ bản cho TomTom routing responses.
    
    Chức năng: Chuyển đổi TomTom routing response thành domain RoutePlan
    """
    def to_domain_route_plan(self, payload: dict) -> RoutePlan:
        """Chuyển đổi TomTom routing response thành domain RoutePlan.
        
        Đầu vào: dict - Raw response từ TomTom Routing API
        Đầu ra: RoutePlan - Kế hoạch tuyến đường domain
        Xử lý: Lấy route đầu tiên, trích xuất summary, sections và guidance
        """
        # Lấy danh sách routes từ response
        routes = payload.get("routes", [])
        if not routes:
            # Trả về RoutePlan rỗng nếu không có route
            logger.warning("No routes found in TomTom response")
            return RoutePlan(summary=RouteSummary(0, 0), sections=[], guidance=RouteGuidance(instructions=[]))
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

        # Trích xuất guidance và instructions
        guidance_data = r0.get("guidance", {})
        logger.info(f"DEBUG: guidance_data keys = {list(guidance_data.keys())}")
        logger.info(f"DEBUG: full guidance_data = {guidance_data}")
        
        instructions_data = guidance_data.get("instructions", [])
        logger.info(f"DEBUG: Found {len(instructions_data)} instructions")
        
        instructions: list[RouteInstruction] = []
        
        for idx, inst in enumerate(instructions_data, 1):
            instr = RouteInstruction(
                step=idx,
                message=inst.get("message", "Continue"),
                distance_in_meters=int(inst.get("distanceInMeters", 0)),
                duration_in_seconds=int(inst.get("durationInSeconds", 0))
            )
            instructions.append(instr)

        # Trả về RoutePlan hoàn chỉnh với guidance
        return RoutePlan(
            summary=RouteSummary(distance, duration), 
            sections=sections,
            guidance=RouteGuidance(instructions=instructions)
        )
    
    def to_domain_route_plan_with_guidance(self, payload: dict) -> dict:
        """Chuyển đổi TomTom routing response thành dict với guidance chi tiết.
        
        Đầu vào: dict - Raw response từ TomTom Routing API
        Đầu ra: dict - Route plan với guidance và instructions
        """
        routes = payload.get("routes", [])
        if not routes:
            return {
                "summary": {"distance_m": 0, "duration_s": 0},
                "sections": [],
                "guidance": {"instructions": []},
                "legs": []
            }
        
        route = routes[0]
        summary_data = route.get("summary", {})
        
        # Trích xuất guidance và instructions từ TomTom response
        guidance = route.get("guidance", {})
        instructions = guidance.get("instructions", [])
        
        # Trích xuất legs (các đoạn đường)
        legs = route.get("legs", [])
        
        # Xử lý sections
        sections = []
        for sec in route.get("sections", []) or []:
            kind = str(sec.get("sectionType") or "")
            simple = sec.get("simpleCategory")
            if simple:
                kind = f"traffic:{simple}"
            
            sections.append({
                "kind": kind,
                "start_index": sec.get("startPointIndex", 0),
                "end_index": sec.get("endPointIndex", 0)
            })
        
        # Xử lý instructions từ TomTom response
        processed_instructions = []
        for inst in instructions:
            point_data = inst.get("point", {})
            
            # Lấy road name từ TomTom response - thử nhiều trường khác nhau
            road_name = ""
            
            # Thử các trường có thể chứa tên đường
            road_fields = ["roadName", "streetName", "routeName", "name", "displayName"]
            for field in road_fields:
                if inst.get(field):
                    road_name = inst.get(field)
                    break
            
            # Nếu vẫn không có, thử lấy từ combinedMessage
            if not road_name and inst.get("combinedMessage"):
                combined_msg = inst.get("combinedMessage", "")
                # Trích xuất tên đường từ combinedMessage
                # Ví dụ: "Turn left onto Phố Ngụy Như Kon Tum then turn right onto Đường Vũ Trọng Phụng"
                if "onto " in combined_msg:
                    parts = combined_msg.split("onto ")
                    if len(parts) > 1:
                        # Lấy phần sau "onto " và trước " then"
                        road_part = parts[1].split(" then")[0]
                        road_name = road_part.strip()
            
            # Lấy instruction text từ TomTom response
            instruction_text = inst.get("instruction", "")
            if not instruction_text:
                # Fallback: tạo instruction từ maneuver với road name
                maneuver = inst.get("maneuver", "")
                if maneuver:
                    instruction_text = self._get_instruction_from_maneuver(maneuver, road_name)
            
            # Nếu có combinedMessage, sử dụng nó thay vì instruction đơn giản
            if inst.get("combinedMessage"):
                combined_msg = inst.get("combinedMessage", "")
                if combined_msg and len(combined_msg) > len(instruction_text):
                    instruction_text = combined_msg
            
            # Nếu vẫn không có, thử lấy từ instruction text
            if not road_name and inst.get("instruction"):
                instruction_text = inst.get("instruction", "")
                # Tìm pattern "onto [road name]"
                if "onto " in instruction_text:
                    parts = instruction_text.split("onto ")
                    if len(parts) > 1:
                        road_part = parts[1].split(" then")[0].split(" and")[0]
                        road_name = road_part.strip()
            
            processed_instructions.append({
                "instruction": instruction_text,
                "distance_m": inst.get("routeOffsetInMeters", 0),
                "duration_s": inst.get("travelTimeInSeconds", 0),
                "point": {
                    "lat": point_data.get("latitude", 0),
                    "lon": point_data.get("longitude", 0)
                },
                "maneuver": inst.get("maneuver", ""),
                "road_name": road_name
            })
        
        # Xử lý legs từ TomTom response
        processed_legs = []
        for leg in legs:
            start_data = leg.get("start", {})
            end_data = leg.get("end", {})
            
            # Lấy coordinates từ start và end points
            start_lat = start_data.get("latitude", 0)
            start_lon = start_data.get("longitude", 0)
            end_lat = end_data.get("latitude", 0)
            end_lon = end_data.get("longitude", 0)
            
            # Nếu không có coordinates trong leg, lấy từ instructions
            if start_lat == 0 and start_lon == 0 and instructions:
                first_inst = instructions[0]
                first_point = first_inst.get("point", {})
                start_lat = first_point.get("latitude", 0)
                start_lon = first_point.get("longitude", 0)
            
            if end_lat == 0 and end_lon == 0 and instructions:
                last_inst = instructions[-1]
                last_point = last_inst.get("point", {})
                end_lat = last_point.get("latitude", 0)
                end_lon = last_point.get("longitude", 0)
            
            processed_legs.append({
                "start_point": {
                    "lat": start_lat,
                    "lon": start_lon
                },
                "end_point": {
                    "lat": end_lat,
                    "lon": end_lon
                },
                "distance_m": leg.get("lengthInMeters", 0),
                "duration_s": leg.get("travelTimeInSeconds", 0)
            })
        
        return {
            "summary": {
                "distance_m": int(summary_data.get("lengthInMeters", 0)),
                "duration_s": int(summary_data.get("travelTimeInSeconds", 0))
            },
            "sections": sections,
            "guidance": {
                "instructions": processed_instructions
            },
            "legs": processed_legs
        }
    
    def _get_instruction_from_maneuver(self, maneuver: str, road_name: str = "") -> str:
        """Tạo instruction text từ maneuver type với tên đường."""
        maneuver_instructions = {
            "DEPART": "Bắt đầu từ điểm xuất phát",
            "ARRIVE": "Đến điểm đích",
            "TURN_LEFT": "Rẽ trái",
            "TURN_RIGHT": "Rẽ phải",
            "SHARP_LEFT": "Rẽ trái gấp",
            "SHARP_RIGHT": "Rẽ phải gấp",
            "SLIGHT_LEFT": "Rẽ trái nhẹ",
            "SLIGHT_RIGHT": "Rẽ phải nhẹ",
            "KEEP_LEFT": "Giữ bên trái",
            "KEEP_RIGHT": "Giữ bên phải",
            "KEEP_STRAIGHT": "Đi thẳng",
            "ROUNDABOUT_LEFT": "Rẽ trái tại vòng xoay",
            "ROUNDABOUT_RIGHT": "Rẽ phải tại vòng xoay",
            "UTURN_LEFT": "Quay đầu bên trái",
            "UTURN_RIGHT": "Quay đầu bên phải",
            "MERGE_LEFT": "Nhập làn bên trái",
            "MERGE_RIGHT": "Nhập làn bên phải",
            "FORK_LEFT": "Rẽ trái tại ngã ba",
            "FORK_RIGHT": "Rẽ phải tại ngã ba",
            "RAMP_LEFT": "Rẽ trái lên đường dốc",
            "RAMP_RIGHT": "Rẽ phải lên đường dốc"
        }
        
        base_instruction = maneuver_instructions.get(maneuver, f"Thực hiện {maneuver}")
        
        # Thêm tên đường nếu có
        if road_name and road_name.strip():
            if maneuver in ["TURN_LEFT", "TURN_RIGHT", "SHARP_LEFT", "SHARP_RIGHT", "SLIGHT_LEFT", "SLIGHT_RIGHT"]:
                base_instruction = f"{base_instruction} vào {road_name}"
            elif maneuver in ["KEEP_LEFT", "KEEP_RIGHT", "KEEP_STRAIGHT"]:
                base_instruction = f"{base_instruction} trên {road_name}"
            elif maneuver in ["ROUNDABOUT_LEFT", "ROUNDABOUT_RIGHT"]:
                base_instruction = f"{base_instruction} vào {road_name}"
        
        return base_instruction