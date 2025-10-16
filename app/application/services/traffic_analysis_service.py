"""
Traffic Analysis Service - Phân tích trạng thái giao thông thực từ server
Service này lấy dữ liệu traffic thực từ TomTom Traffic API cho từng đoạn đường
"""

import asyncio
import aiohttp
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.logging.logger import get_logger


@dataclass
class TrafficSegment:
    """Đoạn đường với thông tin traffic."""
    segment_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    condition: str  # "light", "moderate", "heavy", "congested", "unknown"
    delay_minutes: int
    speed_kmh: Optional[int] = None
    description: str = ""


@dataclass
class TrafficAnalysisResult:
    """Kết quả phân tích traffic."""
    overall_condition: str
    total_delay_minutes: int
    segments: List[TrafficSegment]
    analysis_timestamp: str
    confidence_level: str  # "high", "medium", "low"


class TrafficAnalysisService:
    """
    Service phân tích trạng thái giao thông thực từ TomTom Traffic API
    """
    
    def __init__(self):
        self._logger = get_logger(__name__)
        self._api_key = None
        self._base_url = "https://api.tomtom.com/traffic/services/4"
        self._load_api_key()
    
    def _load_api_key(self):
        """Load TomTom API key từ environment."""
        self._api_key = os.getenv("TOMTOM_API_KEY")
        
        if not self._api_key:
            self._logger.error("TrafficAnalysis: TOMTOM_API_KEY environment variable not found")
            return
        
        # Validate API key format
        if not self._validate_api_key_format(self._api_key):
            self._logger.error("TrafficAnalysis: Invalid API key format")
            self._api_key = None
            return
        
        masked_key = f"***{self._api_key[-4:]}" if len(self._api_key) > 4 else "***"
        self._logger.info(f"TrafficAnalysis: TomTom API key loaded: {masked_key}")
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format."""
        if not api_key or len(api_key) < 10:
            return False
        # TomTom API keys are typically alphanumeric
        return api_key.replace('-', '').replace('_', '').isalnum()
    
    async def analyze_route_traffic(self, route_data: Dict[str, Any]) -> TrafficAnalysisResult:
        """
        Phân tích traffic cho toàn bộ tuyến đường từ route data.
        
        Args:
            route_data: Dữ liệu route từ TomTom Routing API
            
        Returns:
            TrafficAnalysisResult: Kết quả phân tích traffic
        """
        self._logger.info("TrafficAnalysis: Starting route traffic analysis")
        
        try:
            # Extract route segments từ route data
            segments = self._extract_route_segments(route_data)
            
            if not segments:
                self._logger.warning("TrafficAnalysis: No route segments found")
                return self._create_fallback_result()
            
            # Analyze traffic cho từng segment
            traffic_segments = []
            total_delay = 0
            
            for segment in segments:
                traffic_segment = await self._analyze_segment_traffic(segment)
                traffic_segments.append(traffic_segment)
                total_delay += traffic_segment.delay_minutes
            
            # Determine overall condition
            overall_condition = self._determine_overall_condition(traffic_segments)
            
            result = TrafficAnalysisResult(
                overall_condition=overall_condition,
                total_delay_minutes=total_delay,
                segments=traffic_segments,
                analysis_timestamp=datetime.utcnow().isoformat() + "Z",
                confidence_level="high" if len(traffic_segments) > 0 else "low"
            )
            
            self._logger.info(f"TrafficAnalysis: Analysis completed - {overall_condition}, {total_delay}min delay")
            return result
            
        except Exception as e:
            self._logger.error(f"TrafficAnalysis: Failed to analyze route traffic: {e}")
            return self._create_fallback_result()
    
    def _extract_route_segments(self, route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract route segments từ route data."""
        segments = []
        
        try:
            # Extract từ legs
            legs = route_data.get("legs", [])
            for leg in legs:
                points = leg.get("points", [])
                if len(points) >= 2:
                    for i in range(len(points) - 1):
                        segment = {
                            "start_lat": points[i].get("lat"),
                            "start_lon": points[i].get("lon"),
                            "end_lat": points[i + 1].get("lat"),
                            "end_lon": points[i + 1].get("lon"),
                            "segment_id": f"leg_{len(segments)}"
                        }
                        segments.append(segment)
            
            # Nếu không có legs, extract từ guidance instructions
            if not segments:
                guidance = route_data.get("guidance", {})
                instructions = guidance.get("instructions", [])
                
                for i, instruction in enumerate(instructions):
                    point = instruction.get("point", {})
                    if point and i > 0:  # Skip first instruction
                        prev_instruction = instructions[i - 1]
                        prev_point = prev_instruction.get("point", {})
                        
                        if prev_point:
                            segment = {
                                "start_lat": prev_point.get("lat"),
                                "start_lon": prev_point.get("lon"),
                                "end_lat": point.get("lat"),
                                "end_lon": point.get("lon"),
                                "segment_id": f"instruction_{i}"
                            }
                            segments.append(segment)
            
            self._logger.info(f"TrafficAnalysis: Extracted {len(segments)} route segments")
            return segments
            
        except Exception as e:
            self._logger.error(f"TrafficAnalysis: Failed to extract route segments: {e}")
            return []
    
    async def _analyze_segment_traffic(self, segment: Dict[str, Any]) -> TrafficSegment:
        """Phân tích traffic cho một đoạn đường cụ thể."""
        try:
            # Gọi TomTom Traffic API cho segment này
            traffic_data = await self._get_traffic_data_for_segment(
                segment["start_lat"], segment["start_lon"],
                segment["end_lat"], segment["end_lon"]
            )
            
            # Parse traffic data
            condition, delay_minutes, speed_kmh, description = self._parse_traffic_data(traffic_data)
            
            return TrafficSegment(
                segment_id=segment["segment_id"],
                start_lat=segment["start_lat"],
                start_lon=segment["start_lon"],
                end_lat=segment["end_lat"],
                end_lon=segment["end_lon"],
                condition=condition,
                delay_minutes=delay_minutes,
                speed_kmh=speed_kmh,
                description=description
            )
            
        except Exception as e:
            self._logger.warning(f"TrafficAnalysis: Failed to analyze segment {segment['segment_id']}: {e}")
            # Return fallback segment
            return TrafficSegment(
                segment_id=segment["segment_id"],
                start_lat=segment["start_lat"],
                start_lon=segment["start_lon"],
                end_lat=segment["end_lat"],
                end_lon=segment["end_lon"],
                condition="unknown",
                delay_minutes=0,
                description="Không có thông tin giao thông"
            )
    
    async def _get_traffic_data_for_segment(self, start_lat: float, start_lon: float, 
                                          end_lat: float, end_lon: float) -> Dict[str, Any]:
        """Lấy dữ liệu traffic từ TomTom Traffic API cho một đoạn đường."""
        if not self._api_key:
            raise ValueError("TomTom API key not available")
        
        # Build traffic API URL
        url = f"{self._base_url}/flowSegmentData/absolute/10/json"
        
        # Calculate bounding box cho segment
        min_lat = min(start_lat, end_lat)
        max_lat = max(start_lat, end_lat)
        min_lon = min(start_lon, end_lon)
        max_lon = max(start_lon, end_lon)
        
        # Expand bounding box slightly để đảm bảo có data
        lat_expand = (max_lat - min_lat) * 0.1
        lon_expand = (max_lon - min_lon) * 0.1
        
        bbox = f"{min_lat - lat_expand},{min_lon - lon_expand},{max_lat + lat_expand},{max_lon + lon_expand}"
        
        params = {
            "key": self._api_key,
            "bbox": bbox,
            "unit": "KMPH"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self._logger.debug(f"TrafficAnalysis: Got traffic data for segment")
                    return data
                else:
                    error_text = await response.text()
                    self._logger.error(f"TrafficAnalysis: API error {response.status}: {error_text}")
                    raise Exception(f"Traffic API error: {response.status}")
    
    def _parse_traffic_data(self, traffic_data: Dict[str, Any]) -> Tuple[str, int, Optional[int], str]:
        """Parse dữ liệu traffic từ API response."""
        try:
            flow_segments = traffic_data.get("flowSegmentData", [])
            
            if not flow_segments:
                return "unknown", 0, None, "Không có dữ liệu giao thông"
            
            # Lấy segment đầu tiên (thường là segment chính)
            segment = flow_segments[0]
            
            # Extract thông tin traffic
            current_speed = segment.get("currentSpeed", 0)
            free_flow_speed = segment.get("freeFlowSpeed", 0)
            
            # Calculate delay
            if free_flow_speed > 0 and current_speed > 0:
                # Estimate delay based on speed difference
                speed_ratio = current_speed / free_flow_speed
                if speed_ratio < 0.3:
                    condition = "congested"
                    delay_minutes = 15
                    description = "Kẹt xe nghiêm trọng"
                elif speed_ratio < 0.6:
                    condition = "heavy"
                    delay_minutes = 8
                    description = "Kẹt xe nhiều"
                elif speed_ratio < 0.8:
                    condition = "moderate"
                    delay_minutes = 3
                    description = "Có kẹt xe nhẹ"
                else:
                    condition = "light"
                    delay_minutes = 0
                    description = "Giao thông thông thoáng"
            else:
                condition = "unknown"
                delay_minutes = 0
                description = "Không có thông tin tốc độ"
            
            return condition, delay_minutes, current_speed, description
            
        except Exception as e:
            self._logger.error(f"TrafficAnalysis: Failed to parse traffic data: {e}")
            return "unknown", 0, None, "Lỗi phân tích dữ liệu giao thông"
    
    def _determine_overall_condition(self, segments: List[TrafficSegment]) -> str:
        """Xác định trạng thái giao thông tổng thể."""
        if not segments:
            return "unknown"
        
        # Count conditions
        condition_counts = {}
        for segment in segments:
            condition = segment.condition
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        
        # Determine overall condition based on majority
        total_segments = len(segments)
        
        if condition_counts.get("congested", 0) > total_segments * 0.3:
            return "congested"
        elif condition_counts.get("heavy", 0) > total_segments * 0.4:
            return "heavy"
        elif condition_counts.get("moderate", 0) > total_segments * 0.5:
            return "moderate"
        elif condition_counts.get("light", 0) > total_segments * 0.6:
            return "light"
        else:
            return "moderate"  # Default
    
    def _create_fallback_result(self) -> TrafficAnalysisResult:
        """Tạo kết quả fallback khi không thể phân tích."""
        return TrafficAnalysisResult(
            overall_condition="unknown",
            total_delay_minutes=0,
            segments=[],
            analysis_timestamp=datetime.utcnow().isoformat() + "Z",
            confidence_level="low"
        )
    
    async def get_traffic_for_instruction(self, instruction: Dict[str, Any], 
                                        route_data: Dict[str, Any]) -> TrafficSegment:
        """Lấy thông tin traffic cho một instruction cụ thể."""
        try:
            point = instruction.get("point", {})
            if not point:
                return self._create_fallback_segment("instruction_no_point")
            
            # Tìm segment tương ứng với instruction này
            segments = self._extract_route_segments(route_data)
            
            for segment in segments:
                # Check if instruction point is within this segment
                if self._is_point_in_segment(point, segment):
                    return await self._analyze_segment_traffic(segment)
            
            # Nếu không tìm thấy segment, tạo fallback
            return self._create_fallback_segment("instruction_not_found")
            
        except Exception as e:
            self._logger.error(f"TrafficAnalysis: Failed to get traffic for instruction: {e}")
            return self._create_fallback_segment("instruction_error")
    
    def _is_point_in_segment(self, point: Dict[str, Any], segment: Dict[str, Any]) -> bool:
        """Check if point is within segment bounds."""
        try:
            lat = point.get("lat")
            lon = point.get("lon")
            
            if not lat or not lon:
                return False
            
            # Simple bounding box check
            min_lat = min(segment["start_lat"], segment["end_lat"])
            max_lat = max(segment["start_lat"], segment["end_lat"])
            min_lon = min(segment["start_lon"], segment["end_lon"])
            max_lon = max(segment["start_lon"], segment["end_lon"])
            
            return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
            
        except Exception:
            return False
    
    def _create_fallback_segment(self, segment_id: str) -> TrafficSegment:
        """Tạo fallback segment."""
        return TrafficSegment(
            segment_id=segment_id,
            start_lat=0.0,
            start_lon=0.0,
            end_lat=0.0,
            end_lon=0.0,
            condition="unknown",
            delay_minutes=0,
            description="Không có thông tin giao thông"
        )


# Factory function
def get_traffic_analysis_service() -> TrafficAnalysisService:
    """Factory function để lấy traffic analysis service."""
    return TrafficAnalysisService()
