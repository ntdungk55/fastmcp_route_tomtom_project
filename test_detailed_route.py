#!/usr/bin/env python3
"""
Test Detailed Route Response theo model yêu cầu
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.application.services.route_traffic_service import get_route_traffic_service


async def test_detailed_route():
    """Test get_detailed_route với model response mới."""
    print("Testing Detailed Route Response Model")
    print("=" * 50)
    
    # Initialize route traffic service
    route_service = get_route_traffic_service()
    
    # Test get_detailed_route request
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-detailed-001",
        "method": "tools/call",
        "params": {
            "name": "get_detailed_route",
            "arguments": {
                "origin_address": "Hà Nội, Việt Nam",
                "destination_address": "TP. Hồ Chí Minh, Việt Nam",
                "travel_mode": "car",
                "country_set": "VN",
                "language": "vi"
            }
        }
    }
    
    print("Input Request:")
    print(json.dumps(request_data, indent=2))
    print()
    
    try:
        # Process qua tất cả 13 blocks
        result = await route_service.process_route_traffic(request_data)
        
        print("Output Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        
        # Analyze result theo model mới
        if "result" in result:
            print("SUCCESS: Detailed route response created!")
            response_data = result['result']
            
            # 1. Tên điểm đến điểm đi
            origin = response_data.get('origin', {})
            destination = response_data.get('destination', {})
            print(f"\n1. ĐIỂM XUẤT PHÁT VÀ ĐIỂM ĐẾN:")
            print(f"   Xuất phát: {origin.get('name', 'N/A')} - {origin.get('address', 'N/A')}")
            print(f"   Điểm đến: {destination.get('name', 'N/A')} - {destination.get('address', 'N/A')}")
            
            # 2. Thời gian đi
            travel_time = response_data.get('travel_time', {})
            print(f"\n2. THỜI GIAN ĐI:")
            print(f"   Tổng thời gian: {travel_time.get('formatted', 'N/A')}")
            print(f"   Thời gian khởi hành: {travel_time.get('departure_time', 'N/A')}")
            print(f"   Thời gian đến nơi: {travel_time.get('arrival_time', 'N/A')}")
            
            # 3. Cách di chuyển
            travel_mode = response_data.get('travel_mode', {})
            print(f"\n3. CÁCH DI CHUYỂN:")
            print(f"   Phương tiện: {travel_mode.get('description', 'N/A')} ({travel_mode.get('mode', 'N/A')})")
            
            # 4. Hướng dẫn chi tiết (kèm trạng thái đường đi)
            main_route = response_data.get('main_route', {})
            if main_route:
                print(f"\n4. HƯỚNG DẪN CHI TIẾT:")
                print(f"   Tuyến đường: {main_route.get('summary', 'N/A')}")
                print(f"   Khoảng cách: {main_route.get('total_distance_meters', 0):,}m")
                print(f"   Thời gian: {main_route.get('total_duration_seconds', 0):,}s")
                
                traffic = main_route.get('traffic_condition', {})
                print(f"   Trạng thái giao thông: {traffic.get('description', 'N/A')} (chậm {traffic.get('delay_minutes', 0)} phút)")
                
                instructions = main_route.get('instructions', [])
                if instructions:
                    print(f"   Hướng dẫn từng bước ({len(instructions)} bước):")
                    for inst in instructions[:5]:  # Show first 5 steps
                        print(f"      {inst.get('step')}. {inst.get('instruction')}")
                        print(f"         Khoảng cách: {inst.get('distance_meters', 0)}m")
                        print(f"         Thời gian: {inst.get('duration_seconds', 0)}s")
                        if inst.get('road_name'):
                            print(f"         Đường: {inst.get('road_name')}")
                        if inst.get('traffic_condition'):
                            traffic_inst = inst['traffic_condition']
                            print(f"         Giao thông: {traffic_inst.get('description', 'N/A')}")
                
                highlights = main_route.get('highlights', [])
                if highlights:
                    print(f"   Điểm nổi bật:")
                    for highlight in highlights:
                        print(f"      - {highlight}")
            
            # 5. Cách di chuyển khác (kèm trạng thái đường đi)
            alt_routes = response_data.get('alternative_routes', [])
            if alt_routes:
                print(f"\n5. TUYẾN ĐƯỜNG THAY THẾ ({len(alt_routes)} tuyến):")
                for i, alt_route in enumerate(alt_routes, 1):
                    print(f"   Tuyến {i}: {alt_route.get('summary', 'N/A')}")
                    print(f"      Khoảng cách: {alt_route.get('total_distance_meters', 0):,}m")
                    print(f"      Thời gian: {alt_route.get('total_duration_seconds', 0):,}s")
                    
                    alt_traffic = alt_route.get('traffic_condition', {})
                    print(f"      Trạng thái giao thông: {alt_traffic.get('description', 'N/A')} (chậm {alt_traffic.get('delay_minutes', 0)} phút)")
                    
                    alt_highlights = alt_route.get('highlights', [])
                    if alt_highlights:
                        print(f"      Điểm nổi bật:")
                        for highlight in alt_highlights:
                            print(f"         - {highlight}")
        else:
            print("ERROR: Detailed route response failed!")
            error = result.get("error", {})
            print(f"Error code: {error.get('code')}")
            print(f"Error message: {error.get('message')}")
    
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Detailed Route Response Model Test")
    print("Testing 5 components:")
    print("1. Tên điểm đến điểm đi")
    print("2. Thời gian đi")
    print("3. Cách di chuyển")
    print("4. Hướng dẫn chi tiết (kèm trạng thái đường đi)")
    print("5. Cách di chuyển khác (kèm trạng thái đường đi)")
    print()
    
    await test_detailed_route()
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())
