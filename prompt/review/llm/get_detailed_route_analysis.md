# Feature Analysis Report: get_detailed_route Tool

**Generated:** 2025-10-17  
**Status:** 🔄 READY FOR PHASE 2 EXECUTION

---

## 1. Executive Summary

The `get_detailed_route` tool has been cleaned up from the codebase (all 14 services, use case, DTOs removed). This report analyzes the requirements and recommends a fresh implementation following the Clean Architecture v5 pattern.

**Recommendation:** ✅ **PROCEED WITH ADD**

---

## 2. Feature Overview

### 2.1 Current Status
- **Diagram:** ❌ NOT FOUND in `prompt/specs/diagrams/`
- **Blocks:** 0 files (all removed)
- **Code:** ❌ REMOVED
- **DTOs:** ❌ REMOVED (deleted `detailed_route_dto.py`, `detailed_route_response_dto.py`)
- **Use Case:** ❌ REMOVED (deleted `get_detailed_route.py`)

### 2.2 Tool Purpose
Calculate a detailed route between two addresses:
- Accept two addresses (origin, destination)
- Use saved destinations from database if available
- Geocode addresses if not found in database
- Return detailed route with:
  - Turn-by-turn instructions
  - Traffic information per segment
  - Alternative routes
  - Time estimates

### 2.3 Architecture Type
**Composite Use Case** - Requires multiple adapters:
- `GeocodingProvider` (from geocoding_adapter)
- `RoutingProvider` (from routing_adapter)
- `DestinationRepository` (from SQLite repository)

---

## 3. Dependencies & Integration Points

### 3.1 Required Adapters
- ✅ **TomTomGeocodingAdapter** - Already exists in `infrastructure/tomtom/adapters/geocoding_adapter.py`
- ✅ **TomTomRoutingAdapter** - Already exists in `infrastructure/tomtom/adapters/routing_adapter.py`
- ✅ **SQLiteDestinationRepository** - Already exists in `infrastructure/persistence/repositories/sqlite_destination_repository.py`

### 3.2 Similar Use Cases to Reference
- ✅ **SaveDestinationUseCase** - Composite, uses geocoding_adapter + destination_repository
  - Location: `app/application/use_cases/save_destination.py`
  - Pattern: Multiple adapters injected via constructor

- ✅ **CheckAddressTraffic** - Composite, uses geocoding_adapter + traffic_adapter
  - Location: `app/application/use_cases/check_address_traffic.py`
  - Pattern: Multiple adapters + orchestration

### 3.3 Existing Ports to Extend
- `DestinationRepository` port exists
- `GeocodingProvider` port exists  
- `RoutingProvider` port exists

---

## 4. Implementation Plan

### 4.1 Layer-by-Layer Structure

#### **Layer 1: Domain (No Changes)**
- ✅ Use existing `LatLon` value object
- ✅ Use existing `TravelMode` enum
- ✅ No new domain entities needed

#### **Layer 2: Application**
**New Files to Create:**

1. **DTO Layer:**
   - `app/application/dto/detailed_route_dto.py`
     - Request: `DetailedRouteRequest` with origin_address, dest_address, travel_mode, etc.
     - Response: `DetailedRouteResponse` with origin, destination, main_route, alternative_routes, etc.
     - Supporting types: `RoutePoint`, `RouteInstruction`, `RouteLeg`, `TrafficSection`, `GuidanceInfo`

2. **Use Case Layer:**
   - `app/application/use_cases/get_detailed_route.py`
     - Class: `GetDetailedRouteUseCase`
     - Constructor: inject DestinationRepository, GeocodingProvider, RoutingProvider
     - Method: `execute(request: DetailedRouteRequest) → DetailedRouteResponse`
     - Logic:
       1. Check if origin_address exists in database
       2. If not, geocode origin_address
       3. Check if destination_address exists in database
       4. If not, geocode destination_address
       5. Calculate route using routing_provider
       6. Get guidance/instructions from routing_provider
       7. Build DetailedRouteResponse
       8. Return response

#### **Layer 3: Infrastructure**
- ✅ Already has all adapters needed
- ✅ No new infrastructure files needed

#### **Layer 4: Interfaces (MCP)**
**New File to Update:**

1. **`app/interfaces/mcp/server.py`**
   - Add: `get_detailed_route_tool` function
   - Decorator: `@mcp.tool(name=MCPToolNames.GET_DETAILED_ROUTE)`
   - Parameters: origin_address, destination_address, travel_mode, country_set, language
   - Call: `await _container.get_detailed_route.execute(request)`
   - Return: DetailedRouteResponse as dict

#### **Layer 5: DI Container**
**Update: `app/di/container.py`**

1. Import: `from app.application.use_cases.get_detailed_route import GetDetailedRouteUseCase`
2. In `_init_use_cases()` method:
   ```python
   # Detailed Route Use Case (composite use case)
   self.get_detailed_route = GetDetailedRouteUseCase(
       destination_repository=self.destination_repository,
       geocoding_provider=self.geocoding_adapter,
       routing_provider=self.routing_adapter
   )
   ```

---

## 5. Reference Implementation Pattern

### 5.1 Example: CheckAddressTraffic (Composite Use Case)
Location: `app/application/use_cases/check_address_traffic.py`

```python
class CheckAddressTraffic:
    def __init__(self, geocoding: GeocodingProvider, traffic: TrafficProvider):
        self._geocoding = geocoding
        self._traffic = traffic
    
    async def handle(self, cmd: AddressTrafficCommandDTO) -> TrafficAnalysisResponse:
        # Geocode origin address
        origin_geocode = await self._geocoding.geocode_address(...)
        # Get traffic for origin
        traffic_data = await self._traffic.get_traffic(...)
        # Return combined response
        return TrafficAnalysisResponse(...)
```

### 5.2 Example: SaveDestinationUseCase (Multi-Adapter)
Location: `app/application/use_cases/save_destination.py`

```python
class SaveDestinationUseCase:
    def __init__(self, destination_repository: DestinationRepository, 
                 geocoding_provider: GeocodingProvider):
        self._repository = destination_repository
        self._geocoding = geocoding_provider
    
    async def execute(self, request: SaveDestinationRequest) -> SaveDestinationResponse:
        # Geocode address
        geocoding_result = await self._geocoding.geocode_address(...)
        # Save to repository
        destination = await self._repository.save(...)
        # Return response
        return SaveDestinationResponse(...)
```

---

## 6. DTO Requirements

### 6.1 Input DTO: DetailedRouteRequest
```json
{
  "origin_address": "string",
  "destination_address": "string",
  "travel_mode": "car|bicycle|foot",
  "country_set": "string (default: VN)",
  "language": "string (default: vi-VN)"
}
```

### 6.2 Output DTO: DetailedRouteResponse
```json
{
  "origin": {
    "address": "string",
    "name": "string (from database if saved)",
    "lat": number,
    "lon": number
  },
  "destination": {
    "address": "string",
    "name": "string (from database if saved)",
    "lat": number,
    "lon": number
  },
  "main_route": {
    "summary": "string",
    "total_distance_meters": number,
    "total_duration_seconds": number,
    "traffic_condition": {
      "description": "string",
      "delay_minutes": number
    },
    "instructions": [
      {
        "step": number,
        "instruction": "string",
        "distance_meters": number,
        "duration_seconds": number,
        "traffic_condition": {
          "description": "string"
        }
      }
    ]
  },
  "alternative_routes": [
    {
      "summary": "string",
      "total_distance_meters": number,
      "total_duration_seconds": number,
      "traffic_condition": {
        "description": "string",
        "delay_minutes": number
      }
    }
  ]
}
```

---

## 7. MCP Tool Definition

### 7.1 Tool Signature
```python
@mcp.tool(name="get_detailed_route")
async def get_detailed_route_tool(
    origin_address: str,
    destination_address: str,
    travel_mode: TravelModeLiteral = "car",
    country_set: str = "VN",
    language: str = "vi-VN"
) -> dict:
    """Calculate detailed route between two addresses with traffic info."""
```

### 7.2 Tool Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| origin_address | string | ✅ | - | Starting address |
| destination_address | string | ✅ | - | Destination address |
| travel_mode | string | ❌ | "car" | Travel mode: car, bicycle, foot |
| country_set | string | ❌ | "VN" | Country code |
| language | string | ❌ | "vi-VN" | Response language |

---

## 8. Known Issues & Considerations

### 8.1 Edge Cases
- ✅ Address not found in database → fallback to geocoding
- ✅ Geocoding returns no results → error handling needed
- ✅ Routing API returns no route → error handling needed
- ✅ Multiple saved destinations with same address → use first match

### 8.2 Error Scenarios
- Geocoding failure → return error response
- Routing API failure → return error response
- No route found → return error response
- Invalid coordinates → validation error

---

## 9. Next Steps (Phase 2 Execution)

### 9.1 Block Design Phase
1. ✅ **User Review** - Developer approves this analysis
2. Create detailed block descriptions in `prompt/specs/diagrams/blocks/`
3. Wait for user approval on blocks

### 9.2 Code Generation Phase
1. Generate DTOs
2. Generate Use Case
3. Update DI Container
4. Update MCP Server
5. Add to MCP Tool list
6. Test implementation

---

## 10. Summary

| Item | Status | Notes |
|------|--------|-------|
| **Diagram** | ❌ Not required | Already has routing diagram |
| **Blocks** | ⏳ Ready to create | Will follow 14-block pattern |
| **Code** | ⏳ Ready to generate | Follow existing patterns |
| **DTOs** | ⏳ Ready to create | Request/Response defined |
| **Use Case** | ⏳ Ready to generate | Composite pattern |
| **DI Setup** | ⏳ Ready to wire | Simple constructor injection |
| **MCP Tool** | ⏳ Ready to add | Parameters defined |

---

**Recommendation:** ✅ **PROCEED TO PHASE 2 - BLOCK DESIGN**

User should review this analysis and approve before proceeding with block creation.
