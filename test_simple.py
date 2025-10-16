#!/usr/bin/env python3
"""
Simple test cho Integrated Flow Service
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.application.services.route_traffic_service import get_route_traffic_service


async def test_route_traffic():
    """Test route traffic processing."""
    print("Testing Route Traffic Service")
    print("=" * 50)
    
    # Initialize service
    route_service = get_route_traffic_service()
    
    # Test request data
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-001",
        "method": "tools/call",
        "params": {
            "name": "calculate_route",
            "arguments": {
                "origin_lat": 21.0285,  # Hanoi
                "origin_lon": 105.8542,
                "dest_lat": 10.8231,    # Ho Chi Minh City
                "dest_lon": 106.6297,
                "travel_mode": "car"
            }
        }
    }
    
    print("Input Request:")
    print(json.dumps(request_data, indent=2))
    print()
    
    try:
        # Process route traffic
        result = await route_service.process_route_traffic(request_data)
        
        print("Output Response:")
        print(json.dumps(result, indent=2))
        print()
        
        # Analyze result
        if "result" in result:
            print("SUCCESS: Flow completed successfully!")
            result_data = result["result"]
            
            if result_data.get("type") == "ROUTE_SUCCESS":
                summary = result_data.get("summary", {})
                print(f"Distance: {summary.get('distance', {}).get('formatted', 'N/A')}")
                print(f"Duration: {summary.get('duration', {}).get('formatted', 'N/A')}")
                print(f"Traffic: {summary.get('traffic_info', 'N/A')}")
            else:
                print(f"Unexpected result type: {result_data.get('type')}")
        else:
            print("ERROR: Flow failed!")
            error = result.get("error", {})
            print(f"Error code: {error.get('code')}")
            print(f"Error message: {error.get('message')}")
    
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Route Traffic Service Test")
    print()
    
    # Check API key
    api_key = os.getenv("TOMTOM_API_KEY")
    if api_key:
        print(f"API Key: ***{api_key[-4:] if len(api_key) > 4 else '***'}")
    else:
        print("WARNING: TOMTOM_API_KEY not configured")
    print()
    
    await test_route_traffic()
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())

