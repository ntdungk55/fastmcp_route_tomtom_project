# MCP Tools - Input/Output Reference (Cleaned)

**Based on:** `app/interfaces/mcp/server.py`  
**Date:** 2025-10-17

---

## Documented Tools (5 Tools)

| Tool | Category | Purpose |
|------|----------|---------|
| `get_detailed_route` | Composite | Get comprehensive route with traffic & alternatives |
| `save_destination` | Destination | Save a destination to database |
| `list_destinations` | Destination | Get all saved destinations |
| `delete_destination` | Destination | Delete destination by name/address |
| `update_destination` | Destination | Update destination details |

---

## Tool Details

### 1. GET_DETAILED_ROUTE
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
                    "duration_seconds": 30
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

### 2. SAVE_DESTINATION
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

### 3. LIST_DESTINATIONS
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

### 4. DELETE_DESTINATION
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

### 5. UPDATE_DESTINATION
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

## Error Handling

### Standard Error Response
```json
{
    "success": false,
    "error": "Error message describing what went wrong"
}
```

---

**Total Documented Tools:** 5  
**Categories:** Composite (1), Destination (4)  
**Status:** ✅ Ready for use
