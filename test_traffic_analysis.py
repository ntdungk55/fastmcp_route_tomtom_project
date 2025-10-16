"""
Test Traffic Analysis Service - Kiểm tra việc lấy dữ liệu traffic thực từ server
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.application.services.traffic_analysis_service import get_traffic_analysis_service
from app.application.services.route_traffic_service import get_route_traffic_service


async def test_traffic_analysis():
    """Test traffic analysis service với dữ liệu thực."""
    print("Testing Traffic Analysis Service")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("TOMTOM_API_KEY")
    if api_key:
        print(f"API Key: ***{api_key[-4:] if len(api_key) > 4 else '***'}")
    else:
        print("WARNING: TOMTOM_API_KEY not configured")
    print()
    
    # Initialize traffic analysis service
    traffic_service = get_traffic_analysis_service()
    
    # Mock route data (tương tự như từ TomTom Routing API)
    mock_route_data = {
        "summary": {
            "length_in_meters": 1500000,  # 1500km
            "travel_time_in_seconds": 54000,  # 15 hours
            "traffic_delay_in_seconds": 1800,  # 30 minutes
            "departure_time": "2025-10-16T10:00:00+07:00",
            "arrival_time": "2025-10-17T01:00:00+07:00"
        },
        "legs": [
            {
                "summary": {"lengthInMeters": 1500000, "travelTimeInSeconds": 54000},
                "points": [
                    {"lat": 21.0285, "lon": 105.8542},  # Hanoi
                    {"lat": 18.7969, "lon": 98.9793},   # Chiang Mai (midpoint)
                    {"lat": 10.8231, "lon": 106.6297}   # Ho Chi Minh City
                ]
            }
        ],
        "guidance": {
            "instructions": [
                {
                    "message": "Head south on QL1A",
                    "maneuver": "DEPART",
                    "point": {"lat": 21.0285, "lon": 105.8542}
                },
                {
                    "message": "Continue on QL1A for 800km",
                    "maneuver": "CONTINUE", 
                    "point": {"lat": 18.7969, "lon": 98.9793}
                },
                {
                    "message": "Continue on QL1A for 700km",
                    "maneuver": "CONTINUE",
                    "point": {"lat": 15.5, "lon": 106.2}
                },
                {
                    "message": "Arrive at destination",
                    "maneuver": "ARRIVE",
                    "point": {"lat": 10.8231, "lon": 106.6297}
                }
            ]
        }
    }
    
    print("Input Route Data:")
    print(json.dumps(mock_route_data, indent=2))
    print()
    
    try:
        # Analyze traffic cho route
        print("Analyzing traffic for route...")
        traffic_result = await traffic_service.analyze_route_traffic(mock_route_data)
        
        print("Traffic Analysis Result:")
        print(f"Overall Condition: {traffic_result.overall_condition}")
        print(f"Total Delay: {traffic_result.total_delay_minutes} minutes")
        print(f"Confidence Level: {traffic_result.confidence_level}")
        print(f"Analysis Timestamp: {traffic_result.analysis_timestamp}")
        print(f"Number of Segments: {len(traffic_result.segments)}")
        print()
        
        # Show segment details
        for i, segment in enumerate(traffic_result.segments):
            print(f"Segment {i+1}:")
            print(f"  ID: {segment.segment_id}")
            print(f"  Condition: {segment.condition}")
            print(f"  Delay: {segment.delay_minutes} minutes")
            print(f"  Description: {segment.description}")
            if segment.speed_kmh:
                print(f"  Speed: {segment.speed_kmh} km/h")
            print(f"  Coordinates: ({segment.start_lat:.4f}, {segment.start_lon:.4f}) -> ({segment.end_lat:.4f}, {segment.end_lon:.4f})")
            print()
        
        # Test với route traffic service
        print("Testing with Route Traffic Service...")
        route_service = get_route_traffic_service()
        
        # Test get_detailed_route request
        request_data = {
            "jsonrpc": "2.0",
            "id": "test-traffic-001",
            "method": "tools/call",
            "params": {
                "name": "get_detailed_route",
                "arguments": {
                    "origin_address": "Hanoi, Vietnam",
                    "destination_address": "Ho Chi Minh City, Vietnam",
                    "travel_mode": "car",
                    "country_set": "VN",
                    "language": "vi"
                }
            }
        }
        
        result = await route_service.process_route_traffic(request_data)
        
        print("Route Traffic Service Result:")
        if "result" in result:
            response_data = result["result"]
            
            # Check traffic information in response
            main_route = response_data.get("main_route", {})
            if main_route:
                traffic = main_route.get("traffic_condition", {})
                print(f"Main Route Traffic:")
                print(f"  Condition: {traffic.get('condition', 'N/A')}")
                print(f"  Delay: {traffic.get('delay_minutes', 0)} minutes")
                print(f"  Description: {traffic.get('description', 'N/A')}")
                print()
            
            # Check instruction traffic
            instructions = main_route.get("instructions", [])
            if instructions:
                print("Instruction Traffic Details:")
                for inst in instructions[:3]:  # Show first 3
                    traffic_inst = inst.get("traffic_condition", {})
                    print(f"  Step {inst.get('step', 'N/A')}: {traffic_inst.get('description', 'N/A')} (delay: {traffic_inst.get('delay_minutes', 0)} min)")
                print()
            
            # Check alternative routes traffic
            alt_routes = response_data.get("alternative_routes", [])
            if alt_routes:
                print("Alternative Routes Traffic:")
                for i, alt_route in enumerate(alt_routes, 1):
                    alt_traffic = alt_route.get("traffic_condition", {})
                    print(f"  Route {i}: {alt_traffic.get('description', 'N/A')} (delay: {alt_traffic.get('delay_minutes', 0)} min)")
                print()
        else:
            print(f"Error: {result.get('error', {}).get('message', 'Unknown error')}")
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Traffic Analysis Service Test")
    print()
    
    await test_traffic_analysis()
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())
