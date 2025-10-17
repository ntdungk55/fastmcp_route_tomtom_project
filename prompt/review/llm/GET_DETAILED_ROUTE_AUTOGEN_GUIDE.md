# Auto-Generate Code Guide - get_detailed_route Tool

**Branch:** `feature/auto-generate-get-detailed-route`  
**Date:** 2025-10-17  
**Status:** Ready for testing

---

## Objective

Test auto-code generation for the **`get_detailed_route`** tool following the workflow in `@LLM_GUIDE_FOR_AUTOMATIC_CODE_GENERATION.md`

---

## Tool Specification

### Input Parameters
```python
{
    "origin_address": str,      # Origin address (required)
    "destination_address": str, # Destination address (required)
    "travel_mode": str,         # "car" | "bicycle" | "foot" (required)
    "country_set": str,         # Country code (optional, default: "VN")
    "language": str             # "en" or "vi" (optional, default: "en")
}
```

### Output (Success)
```json
{
    "jsonrpc": "2.0",
    "id": "req-xxxxx",
    "result": {
        "origin": {
            "name": "Hanoi",
            "address": "Hanoi, Vietnam",
            "coordinates": {"lat": 21.0285, "lon": 105.8542}
        },
        "destination": {
            "name": "Ho Chi Minh City",
            "address": "Ho Chi Minh City, Vietnam",
            "coordinates": {"lat": 10.8231, "lon": 106.6297}
        },
        "travel_time": {
            "formatted": "20h 30m",
            "departure_time": "2025-10-17T15:30:00Z",
            "arrival_time": "2025-10-18T12:00:00Z"
        },
        "travel_mode": {
            "mode": "car",
            "description": "Driving"
        },
        "main_route": {
            "summary": "Hanoi to HCMC via Highway 1",
            "total_distance_meters": 1730000,
            "total_duration_seconds": 73800,
            "traffic_condition": {
                "description": "Moderate traffic",
                "delay_minutes": 30
            },
            "instructions": [...]
        },
        "alternative_routes": [...]
    }
}
```

### Output (Error)
```json
{
    "error": "Error message"
}
```

---

## Current Implementation Status

**File:** `app/interfaces/mcp/server.py` (lines 472-559)

Current tool implementation:
```python
@mcp.tool(name=MCPToolNames.GET_DETAILED_ROUTE)
async def get_detailed_route_tool(
    origin_address: str,
    destination_address: str,
    travel_mode: TravelModeLiteral = TravelModeConstants.CAR,
    country_set: str = CountryConstants.DEFAULT,
    language: str = LanguageConstants.DEFAULT
) -> dict:
```

**Status:** ✅ Already implemented but using integrated flow service

---

## Auto-Generation Workflow (Per LLM Guide)

### Phase 1: ANALYSIS & REPORT
1. Read current implementation in `app/interfaces/mcp/server.py`
2. Analyze architecture (Clean Architecture, Use Cases, Services)
3. Generate analysis report to `prompt/review/llm/get_detailed_route_analysis.md`
4. **WAIT** for user decision (ADD/MODIFY/DELETE/SKIP)

### Phase 2: EXECUTION
If decision = **MODIFY**, then:
1. Generate block descriptions from specification
2. Implement code based on:
   - `@LLM_GUIDE_FOR_AUTOMATIC_CODE_GENERATION.md` guidelines
   - `app/infrastructure/tomtom/adapters/routing_adapter.py` interface
   - Clean Architecture patterns
3. Update/create necessary files
4. Run tests
5. Commit with clear message

---

## Key Files to Reference

1. **`@LLM_GUIDE_FOR_AUTOMATIC_CODE_GENERATION.md`**
   - Phase 1 & 2 workflow
   - Architecture guidelines
   - Code conventions

2. **`app/interfaces/mcp/server.py`** (lines 472-559)
   - Current get_detailed_route implementation

3. **`app/infrastructure/tomtom/adapters/routing_adapter.py`**
   - TomTom routing interface

4. **`app/application/services/route_traffic_service.py`**
   - Integrated flow service (14 blocks: BLK-1-00 to BLK-1-13)
   - Process routing traffic pattern

5. **`prompt/review/llm/MCP_TOOLS_RESPONSE_REFERENCE.md`**
   - Tool input/output specification

---

## Architecture Context

### Clean Architecture Layers

```
Interfaces (MCP Tools)
    ↓
Application (Use Cases)
    ↓
Domain (Entities, Value Objects)
    ↓
Infrastructure (TomTom Adapters, DB, HTTP)
```

### For get_detailed_route:

1. **Interface:** `get_detailed_route_tool()` in server.py
2. **Service:** Uses `RouteTrafficService.process_route_traffic()` (14 blocks)
3. **Adapter:** `TomTomRoutingAdapter` from infrastructure
4. **Domain:** `Destination`, `LatLon`, `RoutePlan` entities

---

## Testing Plan

### Manual Test
```bash
# Start MCP server
python start_server.py

# Call get_detailed_route via MCP client
{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/call",
    "params": {
        "name": "get_detailed_route",
        "arguments": {
            "origin_address": "Hanoi",
            "destination_address": "Ho Chi Minh City",
            "travel_mode": "car"
        }
    }
}
```

### Expected Behavior
✅ Returns complete route with:
- Origin/destination info
- Travel time (formatted + departure/arrival)
- Main route with instructions
- Traffic conditions
- Alternative routes

---

## Acceptance Criteria

- [ ] **Phase 1:** Analysis report generated and user reviews
- [ ] **Phase 2:** Code generated following guide
- [ ] **Functionality:** Tool returns all required fields
- [ ] **Error Handling:** Proper error responses
- [ ] **Performance:** Completes within timeout
- [ ] **Logging:** Appropriate log levels
- [ ] **Tests:** Unit/integration tests pass
- [ ] **Code Quality:** Follows conventions from architecture guide
- [ ] **Git:** Commits with clear messages

---

## Quick Reference: 14 Blocks in Flow

```
BLK-1-00: ListenMCPRequest → Parse JSON-RPC
BLK-1-01: ValidateInput → Validate coordinates
BLK-1-02: CheckError → Route on validation result
BLK-1-03: MapErrors → Map error codes (if error)
BLK-1-04: CheckDestination → Query DB (optimization)
BLK-1-05: ClassifyError → Classify error type
BLK-1-06: HandleSystemError → System error handling
BLK-1-07: SaveRequestHistory → Async save request
BLK-1-08: SaveDestination → Save new destination
BLK-1-09: RequestRoutingAPI → Call TomTom API
BLK-1-10: CheckAPISuccess → Check API response
BLK-1-11: FormatErrorOutput → Format error for client
BLK-1-12: TransformDataForAI → Transform success data
BLK-1-13: UpdateRequestResult → Async save result
```

---

## Getting Started

1. **Start on THIS branch:**
   ```bash
   git checkout feature/auto-generate-get-detailed-route
   ```

2. **Generate analysis report:**
   - Use LLM guide Phase 1
   - Save to `prompt/review/llm/get_detailed_route_analysis.md`

3. **Wait for user decision:** ADD/MODIFY/DELETE/SKIP

4. **If MODIFY, generate code:**
   - Follow Phase 2 in guide
   - Apply feedback from `prompt/review/developer/feedback.md`
   - Generate based on specification

5. **Test and commit:**
   ```bash
   git add .
   git commit -m "feat: [feature name] for get_detailed_route tool"
   git push origin feature/auto-generate-get-detailed-route
   ```

---

**Ready to test auto-code generation!** 🚀

Branch: `feature/auto-generate-get-detailed-route`  
Status: ✅ Ready  
Next: Follow Phase 1 of `@LLM_GUIDE_FOR_AUTOMATIC_CODE_GENERATION.md`
