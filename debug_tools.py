#!/usr/bin/env python3
"""Debug tools issue"""

import asyncio
import json
import httpx

async def debug_tools():
    """Debug the tools issue"""
    print("🔍 Debugging Tools Issue")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Initialize session
        print("1. Initializing session...")
        init_response = await client.post(
            "http://192.168.1.3:8081/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "debug-client", "version": "1.0.0"}
                }
            }
        )
        
        session_id = init_response.headers.get('mcp-session-id')
        print(f"   Session ID: {session_id}")
        
        # Try tools/list with empty params
        print("\n2. Testing tools/list with empty params...")
        list_response = await client.post(
            "http://192.168.1.3:8081/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            },
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        )
        
        print(f"   Status: {list_response.status_code}")
        print(f"   Response: {list_response.text}")
        
        # Try tools/list without params
        print("\n3. Testing tools/list without params...")
        list_response2 = await client.post(
            "http://192.168.1.3:8081/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            },
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list"
            }
        )
        
        print(f"   Status: {list_response2.status_code}")
        print(f"   Response: {list_response2.text}")

if __name__ == "__main__":
    asyncio.run(debug_tools())
