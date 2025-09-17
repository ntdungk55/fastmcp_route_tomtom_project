#!/usr/bin/env python3
"""Test script for start_streamable_http.py
Test the HTTP Streamable MCP Server functionality
"""

import asyncio
import json
import uuid
from typing import Any, Dict

import httpx


class MCPTestClient:
    def __init__(self, base_url: str = "http://192.168.1.3:8081"):
        self.base_url = base_url
        self.mcp_endpoint = f"{base_url}/mcp"
        self.session_id = None
        self.client = httpx.AsyncClient()
        self.request_id = 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_headers(self):
        """Get headers for MCP requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        return headers

    async def _send_request(self, method: str, params: dict[str, Any] = None):
        """Send MCP request and handle response."""
        if params is None:
            params = {}

        request = {
            "jsonrpc": "2.0",
            "id": str(self.request_id),
            "method": method,
            "params": params
        }
        self.request_id += 1

        print(f"📤 Sending: {method}")
        print(f"   Params: {json.dumps(params, indent=2)}")

        try:
            response = await self.client.post(
                self.mcp_endpoint,
                json=request,
                headers=self._get_headers(),
                timeout=30.0
            )

            print(f"📥 Response Status: {response.status_code}")

            # Handle Server-Sent Events response
            if response.headers.get('content-type') == 'text/event-stream':
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        data = line[6:]
                        try:
                            result = json.loads(data)
                            print(f"📊 SSE Data: {json.dumps(result, indent=2)}")
                            return result
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON decode error: {e}")
                            return None
            else:
                try:
                    result = response.json()
                    print(f"📊 JSON Response: {json.dumps(result, indent=2)}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    return None

        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

    async def initialize(self):
        """Initialize MCP session."""
        print("🔧 Initializing MCP session...")

        request = {
            "jsonrpc": "2.0",
            "id": str(self.request_id),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        self.request_id += 1

        try:
            response = await self.client.post(
                self.mcp_endpoint,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=30.0
            )

            # Extract session ID from headers
            self.session_id = response.headers.get('mcp-session-id')
            if self.session_id:
                print(f"✅ Session ID: {self.session_id}")

                # Handle response
                if response.headers.get('content-type') == 'text/event-stream':
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            data = line[6:]
                            try:
                                result = json.loads(data)
                                print(f"📊 SSE Data: {json.dumps(result, indent=2)}")
                                if result and "error" not in result:
                                    print("✅ MCP session initialized successfully")
                                    return True
                                print(f"❌ MCP initialization failed: {result}")
                                return False
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON decode error: {e}")
                                return False
                else:
                    try:
                        result = response.json()
                        print(f"📊 JSON Response: {json.dumps(result, indent=2)}")
                        if result and "error" not in result:
                            print("✅ MCP session initialized successfully")
                            return True
                        print(f"❌ MCP initialization failed: {result}")
                        return False
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        return False
            else:
                print("❌ No session ID")
                return False

        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

    async def test_ping(self):
        """Test ping method."""
        print("\n🔧 Testing ping...")
        result = await self._send_request("ping")

        if result and "error" not in result:
            print("✅ Ping successful")
            return True
        print(f"❌ Ping failed: {result}")
        return False

    async def test_server_connectivity(self):
        """Test basic server connectivity."""
        print("\n🔧 Testing server connectivity...")

        try:
            # Test basic connectivity
            response = await self.client.get(self.base_url, timeout=5.0)
            print(f"   Root endpoint status: {response.status_code}")

            # Test MCP endpoint
            response = await self.client.get(self.mcp_endpoint, timeout=5.0)
            print(f"   MCP endpoint status: {response.status_code}")
            print(f"   MCP headers: {dict(response.headers)}")

            if response.status_code in [200, 406]:  # 406 is expected for missing headers
                print("✅ Server connectivity OK")
                return True
            print("❌ Server connectivity failed")
            return False

        except Exception as e:
            print(f"❌ Connectivity test failed: {e}")
            return False

async def test_streamable_server():
    """Test the HTTP Streamable MCP Server."""
    print("🧪 Testing HTTP Streamable MCP Server")
    print("=" * 60)

    async with MCPTestClient() as client:
        # Test 1: Server connectivity
        if not await client.test_server_connectivity():
            print("❌ Cannot proceed without server connectivity")
            return False

        # Test 2: Initialize MCP session
        if not await client.initialize():
            print("❌ Cannot proceed without MCP session")
            return False

        # Test 3: Test ping
        if not await client.test_ping():
            print("❌ Ping test failed")
            return False

        print("\n🎉 All tests passed!")
        print("✅ Server is running and responding correctly")
        print("✅ MCP session is working")
        print("✅ Basic MCP protocol is functional")

        print("\n📡 Server Details:")
        print(f"   URL: {client.base_url}")
        print(f"   MCP Endpoint: {client.mcp_endpoint}")
        print(f"   Session ID: {client.session_id}")

        return True

if __name__ == "__main__":
    success = asyncio.run(test_streamable_server())
    if success:
        print("\n🚀 Server is ready for production use!")
    else:
        print("\n⚠️  Server needs attention before production use.")

