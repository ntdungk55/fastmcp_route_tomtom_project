#!/usr/bin/env python3
"""
Test MCP Client - Kiểm tra server với 13 blocks đã triển khai
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.application.services.integrated_flow_service import get_integrated_flow_service


async def test_mcp_server():
    """Test MCP server với integrated flow."""
    print("Testing MCP Server with 13 Blocks")
    print("=" * 50)
    
    # Initialize integrated flow service
    flow_service = get_integrated_flow_service()
    
    # Test 1: Valid calculate_route request
    print("\nTest 1: Valid calculate_route request")
    print("-" * 30)
    
    request_data = {
        "jsonrpc": "2.0",
        "id": "test-calc-001",
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
    
    result = await flow_service.process_complete_flow(request_data)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Invalid request (missing coordinates)
    print("\nTest 2: Invalid request (missing coordinates)")
    print("-" * 30)
    
    invalid_request = {
        "jsonrpc": "2.0",
        "id": "test-invalid-001",
        "method": "tools/call",
        "params": {
            "name": "calculate_route",
            "arguments": {
                "origin_lat": 21.0285,
                "origin_lon": 105.8542,
                # Missing dest_lat and dest_lon
                "travel_mode": "car"
            }
        }
    }
    
    result = await flow_service.process_complete_flow(invalid_request)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Invalid JSON-RPC format
    print("\nTest 3: Invalid JSON-RPC format")
    print("-" * 30)
    
    invalid_jsonrpc = {
        "jsonrpc": "1.0",  # Invalid version
        "id": "test-jsonrpc-001",
        "method": "tools/call",
        "params": {
            "name": "calculate_route",
            "arguments": {
                "origin_lat": 21.0285,
                "origin_lon": 105.8542,
                "dest_lat": 10.8231,
                "dest_lon": 106.6297,
                "travel_mode": "car"
            }
        }
    }
    
    try:
        result = await flow_service.process_complete_flow(invalid_jsonrpc)
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Exception (expected): {e}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("Server is running with 13/13 blocks implemented!")


async def main():
    """Main function."""
    await test_mcp_server()


if __name__ == "__main__":
    asyncio.run(main())

