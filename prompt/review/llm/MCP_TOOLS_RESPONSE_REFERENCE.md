# MCP Tools - Input/Output Reference

**Based on:** `app/interfaces/mcp/server.py` - Analysis of all 14 tools  
**Date:** 2025-10-17

---

## Summary: 14 MCP Tools Available

| Tool | Category | Parameters | Returns |
|------|----------|-----------|---------|
| `calculate_route` | Routing | origin_lat, origin_lon, dest_lat, dest_lon, travel_mode | Route with summary |
| `geocode_address` | Geocoding | address, country_set, limit, language | Coordinates + address info |
| `get_intersection_position` | Geocoding | street_name, cross_street, municipality, country_code | Intersection coordinates |
| `get_street_center_position` | Geocoding | street_name, country_set, language | Street center coordinates |
| `get_traffic_condition` | Traffic | latitude, longitude, zoom | Traffic flow data |
| `get_route_with_traffic` | Traffic | origin_lat, origin_lon, dest_lat, dest_lon, travel_mode | Route + traffic info |
| `get_via_route` | Traffic | origin_lat, origin_lon, via_lat, via_lon, dest_lat, dest_lon | Route via point |
| `analyze_route_traffic` | Traffic | origin_lat, origin_lon, dest_lat, dest_lon | Traffic analysis |
| `check_traffic_between_addresses` | Traffic | origin_address, destination_address | Traffic between addresses |
| `get_detailed_route` | Composite | origin_address, destination_address, travel_mode | Detailed route info |
| `save_destination` | Destination | name, address | Saved destination with ID |
| `list_destinations` | Destination | (none) | All saved destinations |
| `delete_destination` | Destination | name OR address | Success/error |
| `update_destination` | Destination | destination_id, name, address | Updated destination |

---

## Tool Details

### 1. CALCULATE_ROUTE
**Purpose:** Calculate route between two coordinates

**Input:**
```python
{
    "origin_lat": float,        # Origin latitude
    "origin_lon": float,        # Origin longitude
    "dest_lat": float,          # Destination latitude
    "dest_lon": float,          # Destination longitude
    "travel_mode": str          # "car" | "bicycle" | "foot"
}
```

**Output (Success):**
```json
{
    "jsonrpc": "2.0",
    "id": "req-xxxxx",
    "result": {
        "type": "route_calculated",
        "summary": {
            "distance": {
                "formatted": "1730 km"
            },
            "duration": {
                "formatted": "20h 30m"
            },
            "traffic_info": "moderate"
        },
        "route_overview": {
            "main_roads": ["Highway 1", "Highway 5"],
            "via_cities": ["City A", "City B"]
        }
    }
}
```

**Output (Error):**
```json
{
    "error": "Invalid coordinates or calculation failed"
}
```

---

### 2. GEOCODE_ADDRESS
**Purpose:** Convert address to coordinates

**Input:**
```python
{
    "address": str,             # Address to geocode
    "country_set": str,         # Country code (default: "VN")
    "limit": int,               # Max results (1-100)
    "language": str             # "en" or "vi"
}
```

**Output (Success):**
```json
{
    "results": [
        {
            "position": {
                "lat": 21.0285,
                "lon": 105.8542
            },
            "address": {
                "formatted_address": "123 Main St, Hanoi, VN",
                "country": "Vietnam"
            },
            "confidence": 0.95
        }
    ],
    "summary": {
        "query": "123 Main St",
        "query_type": "address"
    }
}
```

---

### 3. GET_DETAILED_ROUTE
**Purpose:** Get comprehensive route information with traffic data

**Input:**
```python
{
    "origin_address": str,      # Origin address
    "destination_address": str, # Destination address
    "travel_mode": str,         # "car" | "bicycle" | "foot"
    "country_set": str,         # Country code
    "language": str             # "en" or "vi"
}
```

**Output (Success):**
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
            "instructions": [
                {
                    "step": 1,
                    "instruction": "Head north on Phố Huế",
                    "distance_meters": 250,
                    "duration_seconds": 30,
                    "traffic_condition": {
                        "description": "Light traffic"
                    }
                }
            ]
        },
        "alternative_routes": [
            {
                "summary": "Alternative Route 1",
                "total_distance_meters": 1800000,
                "total_duration_seconds": 75600,
                "traffic_condition": {
                    "description": "Heavy traffic",
                    "delay_minutes": 45
                }
            }
        ]
    }
}
```

---

### 4. GET_TRAFFIC_CONDITION
**Purpose:** Get traffic flow data at a location

**Input:**
```python
{
    "latitude": float,          # Latitude
    "longitude": float,         # Longitude
    "zoom": int                 # Zoom level (0-22)
}
```

**Output (Success):**
```json
{
    "location": {
        "lat": 21.0285,
        "lon": 105.8542
    },
    "flow_data": {
        "freeFlowSpeed": 50,
        "currentSpeed": 30,
        "currentTravelTime": 120,
        "freeFlowTravelTime": 60,
        "confidence": 0.95,
        "roadClosure": false
    },
    "road_closure": false
}
```

---

### 5. SAVE_DESTINATION
**Purpose:** Save a destination to database

**Input:**
```python
{
    "name": str,                # Destination name
    "address": str              # Destination address
}
```

**Output (Success):**
```json
{
    "success": true,
    "destination_id": "dest-uuid-123",
    "message": "Destination saved successfully",
    "destination": {
        "id": "dest-uuid-123",
        "name": "My Office",
        "address": "123 Business Ave",
        "latitude": 21.0350,
        "longitude": 105.8600,
        "created_at": "2025-10-17T15:13:34Z"
    }
}
```

**Output (Error):**
```json
{
    "success": false,
    "error": "Address already exists"
}
```

---

### 6. LIST_DESTINATIONS
**Purpose:** Get all saved destinations

**Input:**
```python
{}  # No parameters
```

**Output (Success):**
```json
{
    "success": true,
    "destinations": [
        {
            "id": "dest-uuid-1",
            "name": "Home",
            "address": "123 Home St",
            "latitude": 21.0285,
            "longitude": 105.8542,
            "created_at": "2025-10-17T10:00:00Z",
            "updated_at": "2025-10-17T10:00:00Z"
        },
        {
            "id": "dest-uuid-2",
            "name": "Office",
            "address": "456 Work Ave",
            "latitude": 21.0350,
            "longitude": 105.8600,
            "created_at": "2025-10-17T11:00:00Z",
            "updated_at": "2025-10-17T11:00:00Z"
        }
    ],
    "total": 2
}
```

---

### 7. DELETE_DESTINATION
**Purpose:** Delete a destination by name or address

**Input:**
```python
{
    "name": str | None,         # Destination name
    "address": str | None       # Destination address
}
```

**Output (Success):**
```json
{
    "success": true,
    "message": "Destination deleted successfully",
    "deleted": "Home"
}
```

**Output (Error):**
```json
{
    "success": false,
    "message": "No destinations found matching the criteria",
    "error": "Destination not found"
}
```

---

### 8. UPDATE_DESTINATION
**Purpose:** Update destination details

**Input:**
```python
{
    "destination_id": str,      # Destination UUID
    "name": str | None,         # New name (optional)
    "address": str | None       # New address (optional)
}
```

**Output (Success):**
```json
{
    "success": true,
    "destination_id": "dest-uuid-123",
    "message": "Destination updated successfully",
    "destination": {
        "id": "dest-uuid-123",
        "name": "Updated Office",
        "address": "456 New Business Ave",
        "updated_at": "2025-10-17T15:20:00Z"
    }
}
```

---

### 9. GET_TRAFFIC_CONDITION (Other tools follow similar patterns)

Additional tools like:
- `get_intersection_position` - Returns: `{results: [...], summary: {...}}`
- `get_street_center_position` - Returns: `{results: [...], summary: {...}}`
- `get_route_with_traffic` - Returns: `{summary: {...}, sections: [...]}`
- `get_via_route` - Returns: `{summary: {...}, sections: [...]}`
- `analyze_route_traffic` - Returns: `{analysis: {...}, recommendations: [...]}`
- `check_traffic_between_addresses` - Returns: `{traffic_data: {...}}`

---

## Error Handling

### Standard Error Response
```json
{
    "error": "Error message describing what went wrong"
}
```

### JSON-RPC Error Response (for routing tools)
```json
{
    "jsonrpc": "2.0",
    "id": "req-xxxxx",
    "error": {
        "code": -32602,
        "message": "Invalid parameters",
        "data": {
            "validation_errors": [
                {
                    "code": "INVALID_COORD_RANGE",
                    "field": "origin_lat",
                    "message": "Latitude must be between -90 and 90"
                }
            ]
        }
    }
}
```

---

## Key Features Across All Tools

✅ **Async/Await Pattern** - All tools are async for non-blocking I/O  
✅ **Error Handling** - Comprehensive error messages and codes  
✅ **Type Safety** - Full type hints for parameters and returns  
✅ **Logging** - Debug logging for monitoring  
✅ **Validation** - Input validation before processing  
✅ **Retry Logic** - Automatic retry on transient failures  
✅ **Timeout Handling** - Proper timeout management  
✅ **Clean Architecture** - Uses Use Cases and Ports/Adapters  
✅ **DI Container** - All dependencies injected via Container  

---

## Usage Examples for LLM

### Example 1: Calculate Route
```
Request: Calculate route from Hanoi to HCMC by car
Tool: calculate_route(21.0285, 105.8542, 10.8231, 106.6297, "car")
Response: Route info with distance, duration, traffic
```

### Example 2: Save Destination
```
Request: Save "My Home" at "123 Nguyen Hue, Hanoi"
Tool: save_destination("My Home", "123 Nguyen Hue, Hanoi")
Response: Destination saved with UUID and coordinates
```

### Example 3: Get Detailed Route
```
Request: Get detailed route from "Hanoi" to "Ho Chi Minh City"
Tool: get_detailed_route("Hanoi", "Ho Chi Minh City", "car")
Response: Complete route with instructions, traffic, alternatives
```

---

**Total Tools:** 14  
**Categories:** Routing (2), Geocoding (3), Traffic (5), Composite (1), Destination (3)  
**All Implemented:** ✅ Yes  
**Ready for Production:** ✅ Yes
