# Phân tích Yêu cầu: Tra cứu Tuyến đường với Waypoints/Via Points

## 📋 Tổng quan Yêu cầu

**Yêu cầu:** Tra cứu tuyến đường đi qua **một hoặc nhiều** điểm trung gian cụ thể.

**Ví dụ:**
- A → B (không có điểm trung gian)
- A → C → B (1 điểm trung gian)
- A → C → D → E → B (nhiều điểm trung gian)

---

## 🔍 Phân tích Hiện trạng

### 1. **DTO Support** ✅ (Đã có)

#### `CalculateRouteCommand` đã có field waypoints:
```python
# app/application/dto/calculate_route_dto.py
@dataclass(frozen=True)
class CalculateRouteCommand:
    origin: LatLon
    destination: LatLon
    travel_mode: TravelMode = TravelMode.CAR
    waypoints: list[LatLon] | None = None  # ✅ Đã có
```

**Nhưng:**
- ❌ Không được sử dụng trong routing adapter
- ❌ Không được validate
- ❌ Không có trong DetailedRouteRequest

#### `ViaRouteCommandDTO` - Chỉ support 1 via point:
```python
# app/application/dto/traffic_dto.py
@dataclass
class ViaRouteCommandDTO:
    origin: LatLon
    via_point: LatLon  # ❌ Chỉ 1 điểm
    destination: LatLon
    travel_mode: str = "car"
    language: str = "vi-VN"
```

**Hạn chế:**
- ❌ Chỉ support 1 via point
- ❌ Không support multiple waypoints
- ❌ Không được sử dụng trong use case

### 2. **Routing Adapter** ❌ (Chưa implement)

#### `TomTomRoutingAdapter.calculate_route()`:
```python
async def calculate_route(self, cmd: CalculateRouteCommand) -> RoutePlan:
    origin = f"{cmd.origin.lat},{cmd.origin.lon}"
    dest = f"{cmd.destination.lat},{cmd.destination.lon}"
    path = CALCULATE_ROUTE_PATH.format(origin=origin, destination=dest)
    # ❌ Không xử lý cmd.waypoints
```

**Vấn đề:**
- ❌ Không build path với waypoints
- ❌ Endpoint format không hỗ trợ waypoints

#### `TomTomRoutingAdapter.calculate_route_with_guidance()`:
- ❌ Tương tự, không xử lý waypoints

### 3. **Endpoint Format** ❌ (Chưa support)

#### Hiện tại:
```python
# app/infrastructure/tomtom/endpoint.py
CALCULATE_ROUTE_PATH = "/routing/1/calculateRoute/{origin}:{destination}/json"
```

**TomTom API Format cho waypoints:**
```
/routing/1/calculateRoute/{origin}:{via1}:{via2}:...:{destination}/json
```

**Ví dụ:**
- 1 waypoint: `/calculateRoute/10.8231,106.6297:21.0285,105.8542:20.9987,105.8622/json`
- 2 waypoints: `/calculateRoute/10.8231,106.6297:21.0285,105.8542:20.9987,105.8622:19.0759,72.8777/json`

### 4. **Use Case** ❌ (Chưa support)

#### `GetDetailedRouteUseCase.execute()`:
```python
route_cmd = CalculateRouteCommand(
    origin=origin_coords,
    destination=dest_coords,
    travel_mode=travel_mode_enum
    # ❌ Không có waypoints
)
```

**Vấn đề:**
- ❌ `DetailedRouteRequest` không có field `waypoints`
- ❌ Use case không geocode waypoints
- ❌ Không pass waypoints vào command

---

## 🎯 Yêu cầu Chi tiết

### Business Requirements

1. **Input:**
   - Origin address/coordinates
   - Destination address/coordinates
   - Waypoints: List of addresses/coordinates (0..N)
   - Travel mode (car, bicycle, foot)
   - Optional: country_set, language

2. **Output:**
   - Route từ origin → waypoint1 → waypoint2 → ... → destination
   - Summary: total distance, total duration
   - Turn-by-turn instructions cho toàn bộ route
   - Traffic information cho từng segment
   - Route legs (origin→waypoint1, waypoint1→waypoint2, ..., waypointN→destination)

3. **Constraints:**
   - TomTom API limit: Max 150 waypoints
   - Waypoints phải được geocode nếu là addresses
   - Thứ tự waypoints: theo thứ tự user cung cấp (không optimize)

### Technical Requirements

1. **Validation:**
   - Validate waypoints list không vượt quá 150
   - Validate waypoints không trùng với origin/destination
   - Validate format (coordinates hoặc addresses)

2. **Geocoding:**
   - Geocode waypoint addresses nếu cần
   - Handle geocoding failures gracefully

3. **Route Calculation:**
   - Build TomTom API path với waypoints format
   - Calculate route qua tất cả waypoints
   - Map response về domain RoutePlan

4. **Response Structure:**
   - Total route summary
   - Route legs (mỗi leg = origin→waypoint hoặc waypoint→waypoint hoặc waypoint→destination)
   - Instructions cho toàn bộ route
   - Traffic info cho từng leg

---

## 🏗️ Đề xuất Implementation

### 1. Update DTOs

#### `DetailedRouteRequest` - Thêm waypoints:
```python
@dataclass
class DetailedRouteRequest:
    origin_address: str
    destination_address: str
    waypoint_addresses: List[str] = field(default_factory=list)  # ✅ Thêm mới
    travel_mode: str = "car"
    country_set: str = "VN"
    language: str = "vi-VN"
```

#### `CalculateRouteCommand` - Đã có, chỉ cần sử dụng:
```python
# ✅ Đã có waypoints field, không cần sửa
waypoints: list[LatLon] | None = None
```

### 2. Update Routing Adapter

#### Build path với waypoints:
```python
async def calculate_route(self, cmd: CalculateRouteCommand) -> RoutePlan:
    # Build path với waypoints
    path_coords = [f"{cmd.origin.lat},{cmd.origin.lon}"]
    
    # Add waypoints nếu có
    if cmd.waypoints:
        for wp in cmd.waypoints:
            path_coords.append(f"{wp.lat},{wp.lon}")
    
    # Add destination
    path_coords.append(f"{cmd.destination.lat},{cmd.destination.lon}")
    
    # Build path: origin:via1:via2:...:destination
    route_path = ":".join(path_coords)
    path = f"/routing/1/calculateRoute/{route_path}/json"
    
    # ... rest of implementation
```

### 3. Update Use Case

#### Geocode waypoints và build command:
```python
async def execute(self, request: DetailedRouteRequest) -> DetailedRouteResponse:
    # Step 1: Geocode origin
    origin_coords, origin_name = await self._get_coordinates(...)
    
    # Step 2: Geocode waypoints (mới)
    waypoint_coords = []
    waypoint_names = []
    for waypoint_addr in request.waypoint_addresses:
        coords, name = await self._get_coordinates(waypoint_addr, ...)
        waypoint_coords.append(coords)
        waypoint_names.append(name)
    
    # Step 3: Geocode destination
    dest_coords, dest_name = await self._get_coordinates(...)
    
    # Step 4: Build route command với waypoints
    route_cmd = CalculateRouteCommand(
        origin=origin_coords,
        destination=dest_coords,
        waypoints=waypoint_coords if waypoint_coords else None,  # ✅ Pass waypoints
        travel_mode=travel_mode_enum
    )
    
    # ... rest of implementation
```

### 4. Update Endpoint Constant

#### Thêm helper method:
```python
# app/infrastructure/tomtom/endpoint.py

def build_route_path(origin: LatLon, destination: LatLon, waypoints: List[LatLon] | None = None) -> str:
    """Build TomTom routing API path với waypoints."""
    path_coords = [f"{origin.lat},{origin.lon}"]
    
    if waypoints:
        for wp in waypoints:
            path_coords.append(f"{wp.lat},{wp.lon}")
    
    path_coords.append(f"{destination.lat},{destination.lon}")
    route_path = ":".join(path_coords)
    
    return f"/routing/1/calculateRoute/{route_path}/json"
```

### 5. Update MCP Tool

#### Thêm waypoints parameter:
```python
@mcp.tool(name=MCPToolNames.GET_DETAILED_ROUTE)
async def get_detailed_route_tool(
    origin_address: str,
    destination_address: str,
    waypoint_addresses: List[str] = [],  # ✅ Thêm mới
    travel_mode: TravelModeLiteral = TravelModeConstants.CAR,
    country_set: str = CountryConstants.DEFAULT,
    language: str = LanguageConstants.DEFAULT
) -> dict:
    """Calculate detailed route with optional waypoints."""
    request = DetailedRouteRequest(
        origin_address=origin_address,
        destination_address=destination_address,
        waypoint_addresses=waypoint_addresses,  # ✅ Pass waypoints
        travel_mode=travel_mode,
        country_set=country_set,
        language=language
    )
    # ... rest
```

### 6. Validation Service

#### Thêm validation cho waypoints với skip logic:
```python
# app/application/services/validation_service.py

def validate_waypoints(waypoints: List[str] | None) -> None:
    """Validate waypoints list."""
    if waypoints is None:
        return
    
    # Max 150 waypoints (TomTom limit)
    if len(waypoints) > 150:
        raise ValidationError("Maximum 150 waypoints allowed")
```

#### Geocode waypoints với skip logic:
```python
# app/application/use_cases/get_detailed_route.py

async def _geocode_waypoints(
    self, 
    waypoint_addresses: List[str], 
    country_set: str, 
    language: str
) -> List[LatLon]:
    """Geocode waypoint addresses, skip những cái không geocode được."""
    waypoint_coords = []
    
    for waypoint_addr in waypoint_addresses:
        try:
            geocode_cmd = GeocodeAddressCommandDTO(
                address=waypoint_addr,
                country_set=country_set,
                limit=1,
                language=language
            )
            
            geocode_result = await self._geocoding_provider.geocode_address(geocode_cmd)
            
            if geocode_result.results and len(geocode_result.results) > 0:
                coords = geocode_result.results[0].position
                waypoint_coords.append(coords)
                logger.info(f"✅ Geocoded waypoint '{waypoint_addr}' to {coords.lat},{coords.lon}")
            else:
                logger.warning(f"⚠️ Skipping waypoint '{waypoint_addr}': geocoding failed")
                # Skip waypoint không geocode được
                continue
                
        except Exception as e:
            logger.warning(f"⚠️ Skipping waypoint '{waypoint_addr}': {str(e)}")
            # Skip waypoint với lỗi
            continue
    
    if waypoint_coords:
        logger.info(f"✅ Successfully geocoded {len(waypoint_coords)}/{len(waypoint_addresses)} waypoints")
    else:
        logger.warning(f"⚠️ No waypoints could be geocoded from {len(waypoint_addresses)} addresses")
    
    return waypoint_coords
```

---

## 📊 Route Response Structure với Waypoints

### Response Structure:
```python
{
    "origin": {
        "address": "...",
        "lat": ...,
        "lon": ...
    },
    "destination": {
        "address": "...",
        "lat": ...,
        "lon": ...
    },
    "waypoints": [
        {"address": "waypoint1", "lat": ..., "lon": ...},
        {"address": "waypoint2", "lat": ..., "lon": ...},
        # Chỉ include waypoints đã geocode thành công
    ],
    "main_route": {
        "summary": {
            "total_distance_meters": ...,  # Tổng distance qua tất cả waypoints
            "total_duration_seconds": ...   # Tổng duration qua tất cả waypoints
        },
        "instructions": [
            # Turn-by-turn instructions cho toàn bộ route
            {"step": 1, "instruction": "...", ...},
            ...
        ],
        "sections": [
            # Traffic sections cho toàn bộ route
            {...},
            ...
        ]
    },
    "skipped_waypoints": [
        # Optional: List waypoints bị skip do geocoding failed
        {"address": "...", "reason": "Geocoding failed"}
    ]
}
```

---

## 🧪 Test Cases

### Test Case 1: Route không có waypoints
- Input: origin, destination, waypoints=[]
- Expected: Route origin→destination (như hiện tại)

### Test Case 2: Route với 1 waypoint
- Input: origin, destination, waypoints=["address1"]
- Expected: Route origin→waypoint1→destination

### Test Case 3: Route với nhiều waypoints
- Input: origin, destination, waypoints=["addr1", "addr2", "addr3"]
- Expected: Route origin→wp1→wp2→wp3→destination

### Test Case 4: Waypoint validation
- Input: 151 waypoints
- Expected: Validation error

### Test Case 5: Waypoint geocoding failure (skip logic)
- Input: Waypoints = ["valid_address", "invalid_address_xyz", "another_valid"]
- Expected: Route chỉ qua "valid_address" và "another_valid", skip "invalid_address_xyz", log warning

### Test Case 6: All waypoints geocoding failure
- Input: Waypoints = ["invalid1", "invalid2"]
- Expected: Route từ origin→destination (như không có waypoints), log warning về skipped waypoints

### Test Case 7: Partial waypoints geocoding success
- Input: 5 waypoints, 2 geocode failed
- Expected: Route qua 3 waypoints thành công, 2 waypoints skipped, return skipped_waypoints list

---

## 📝 Implementation Checklist

- [ ] Update `DetailedRouteRequest` - thêm `waypoint_addresses: List[str]`
- [ ] Update `GetDetailedRouteUseCase` - implement `_geocode_waypoints()` với skip logic
- [ ] Update `GetDetailedRouteUseCase` - skip waypoints không geocode được (không fail)
- [ ] Update `GetDetailedRouteUseCase` - pass only successfully geocoded waypoints vào command
- [ ] Update `TomTomRoutingAdapter` - build path với waypoints format (`origin:via1:via2:destination`)
- [ ] Update `TomTomRoutingAdapter` - handle waypoints trong cả `calculate_route()` và `calculate_route_with_guidance()`
- [ ] Update endpoint helper - `build_route_path()` với waypoints
- [ ] Update MCP tool - thêm `waypoint_addresses` parameter
- [ ] Update validation service - validate max 150 waypoints (không validate geocoding)
- [ ] Update response structure - include waypoints info (chỉ include geocoded thành công)
- [ ] Update response structure - optional `skipped_waypoints` list (nếu có waypoints bị skip)
- [ ] Add tests - test skip logic: 0, 1, multiple, partial success, all failure
- [ ] Update documentation - waypoints usage với skip behavior

---

## 🔄 Migration Path

### Phase 1: Core Implementation
1. Update DTOs
2. Update routing adapter
3. Update use case

### Phase 2: Interface & Validation
1. Update MCP tool
2. Add validation
3. Update documentation

### Phase 3: Testing & Polish
1. Add tests
2. Error handling improvements
3. Performance optimization

---

## ⚠️ Lưu ý

1. **TomTom API Limit:** Max 150 waypoints
2. **Order Preservation:** Waypoints giữ nguyên thứ tự user cung cấp (không optimize)
3. **Geocoding Costs:** Mỗi waypoint address cần geocode → tăng API calls
4. **Response Size:** Multiple waypoints → larger response → consider pagination nếu cần
5. **Legs Mapping:** Route legs phải được map correctly theo waypoints

---

## 📚 Reference

- [TomTom Routing API - Waypoints](https://developer.tomtom.com/routing-api/documentation/product-information/routing/calculate-route)
- TomTom API Format: `/{origin}:{via1}:{via2}:...:{destination}/json`

