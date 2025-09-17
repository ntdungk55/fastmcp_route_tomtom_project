#!/usr/bin/env node

/**
 * MCP Test Client for TomTom Route Server
 * Tests connection and functionality with the HTTP MCP server
 */

import fetch from 'node-fetch';

class MCPTestClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.requestId = 1;
    }

    /**
     * Send MCP request to server
     */
    async sendMCPRequest(method, params = {}) {
        const request = {
            jsonrpc: "2.0",
            id: this.requestId++,
            method: method,
            params: params
        };

        try {
            console.log(`📤 Sending MCP request: ${method}`);
            console.log(`   Params:`, JSON.stringify(params, null, 2));

            const response = await fetch(this.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log(`📥 Response:`, JSON.stringify(result, null, 2));
            return result;

        } catch (error) {
            console.error(`❌ Error sending MCP request:`, error.message);
            return { error: { message: error.message } };
        }
    }

    /**
     * Send simple HTTP request (non-MCP format)
     */
    async sendSimpleRequest(method, params = {}) {
        const request = {
            method: method,
            params: params
        };

        try {
            console.log(`📤 Sending simple request: ${method}`);
            console.log(`   Params:`, JSON.stringify(params, null, 2));

            const response = await fetch(this.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log(`📥 Response:`, JSON.stringify(result, null, 2));
            return result;

        } catch (error) {
            console.error(`❌ Error sending simple request:`, error.message);
            return { error: { message: error.message } };
        }
    }

    /**
     * Test server health
     */
    async testHealth() {
        console.log(`🏥 Testing server health...`);
        try {
            const response = await fetch(this.serverUrl.replace('/mcp', '/health'));
            const result = await response.json();
            console.log(`   Health status:`, result.status);
            console.log(`   API Key configured:`, result.api_key_configured ? '✅' : '❌');
            return result;
        } catch (error) {
            console.error(`❌ Health check failed:`, error.message);
            return null;
        }
    }

    /**
     * Test tools list with MCP protocol
     */
    async testToolsList() {
        console.log(`\n🛠️ Testing tools list (MCP format)...`);
        return await this.sendMCPRequest("tools/list");
    }

    /**
     * Test route calculation with MCP protocol
     */
    async testRouteCalculation() {
        console.log(`\n🗺️ Testing route calculation (MCP format)...`);
        
        const routeParams = {
            name: "calculate_route",
            arguments: {
                origin_lat: 21.0285,    // Hồ Gươm, Hà Nội
                origin_lon: 105.8542,
                dest_lat: 10.7720,      // Chợ Bến Thành, TP.HCM
                dest_lon: 106.6986,
                travel_mode: "car"
            }
        };

        return await this.sendMCPRequest("tools/call", routeParams);
    }

    /**
     * Test with MCP protocol format
     */
    async testMCPProtocol() {
        console.log(`\n🔄 Testing MCP protocol format...`);
        
        // Test 1: List tools with MCP format
        console.log(`\n--- MCP Tools List ---`);
        await this.sendMCPRequest("tools/list");

        // Test 2: Call tool with MCP format  
        console.log(`\n--- MCP Route Calculation ---`);
        const mcpRouteParams = {
            name: "calculate_route",
            arguments: {
                origin_lat: 21.0285,
                origin_lon: 105.8542,
                dest_lat: 21.0245,      // Short distance for quick test
                dest_lon: 105.8412,
                travel_mode: "bicycle"
            }
        };

        await this.sendMCPRequest("tools/call", mcpRouteParams);
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log(`🚀 TomTom Route MCP Client Test Suite`);
        console.log(`📍 Server URL: ${this.serverUrl}`);
        console.log(`${'='.repeat(60)}\n`);

        // Test 1: Health check
        await this.testHealth();

        // Test 2: Tools list
        await this.testToolsList();

        // Test 3: Route calculation
        await this.testRouteCalculation();

        // Test 4: MCP protocol
        await this.testMCPProtocol();

        console.log(`\n🎉 All tests completed!`);
    }
}

/**
 * Main function
 */
async function main() {
    const serverUrl = process.argv[2] || 'http://192.168.1.3:8081/mcp';
    
    console.log(`Starting MCP Test Client...`);
    console.log(`Target server: ${serverUrl}\n`);

    const client = new MCPTestClient(serverUrl);
    
    try {
        await client.runAllTests();
        process.exit(0);
    } catch (error) {
        console.error(`❌ Test suite failed:`, error);
        process.exit(1);
    }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
    console.log(`\n👋 Test interrupted by user`);
    process.exit(0);
});

// Run main function
main().catch(console.error);
