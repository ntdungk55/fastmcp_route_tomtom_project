# TomTom MCP Server - Clean Architecture

## 🏗️ Kiến trúc

Server này được refactor theo Clean Architecture với các layers:

```
app/
├── domain/                 # Domain Layer
│   ├── enums/             # Business enums
│   ├── value_objects/     # Value objects (LatLon)
│   └── errors.py          # Domain errors
├── application/           # Application Layer  
│   ├── dto/               # Data Transfer Objects
│   ├── ports/             # Interfaces (Protocols)
│   ├── use_cases/         # Business logic
│   └── errors.py          # Application errors
├── infrastructure/        # Infrastructure Layer
│   ├── http/              # HTTP client
│   ├── tomtom/            # TomTom API integration
│   │   ├── adapters/      # Port implementations
│   │   └── acl/           # Anti-Corruption Layer
│   ├── config/            # Settings
│   └── logging/           # Logger
├── interfaces/            # Interface Layer
│   └── mcp/               # MCP server implementation
└── di/                    # Dependency Injection
    └── container.py       # DI Container
```

## 🚀 Cách sử dụng

### Server (Clean Architecture):
```bash
python start_server.py
```

**Hoặc chạy trực tiếp:**
```bash
python app/interfaces/mcp/server.py
```

## ✅ Lợi ích của Clean Architecture

### 1. **Vendor Independence**
- TomTom API được cô lập hoàn toàn trong Infrastructure layer
- Có thể thay đổi provider (Google Maps, HERE, etc.) mà không ảnh hưởng business logic

### 2. **Testability** 
- Mỗi Use Case có thể test độc lập với mock Ports
- Business logic tách biệt khỏi I/O operations

### 3. **Maintainability**
- Single Responsibility: mỗi class làm 1 việc duy nhất
- Dependency Injection: dễ dàng thay đổi implementations

### 4. **Scalability**
- Dễ dàng thêm Use Cases mới
- Có thể thêm nhiều Adapters cho các providers khác

## 🔧 Use Cases hiện có

| Use Case | Chức năng | Input | Output |
|----------|-----------|-------|--------|
| `CalculateRoute` | Tính tuyến đường cơ bản | `CalculateRouteCommand` | `RoutePlan` |
| `GeocodeAddress` | Chuyển địa chỉ → tọa độ | `GeocodeAddressCommandDTO` | `GeocodeResponseDTO` |
| `GetIntersectionPosition` | Tìm giao lộ | `StructuredGeocodeCommandDTO` | `GeocodeResponseDTO` |
| `GetStreetCenter` | Tìm trung tâm đường | `street_name, country, language` | `GeocodeResponseDTO` |
| `GetTrafficCondition` | Tình trạng giao thông | `TrafficConditionCommandDTO` | `TrafficConditionResultDTO` |
| `AnalyzeRouteTraffic` | Phân tích traffic | `TrafficAnalysisCommandDTO` | `TrafficAnalysisResultDTO` |
| `CheckAddressTraffic` | Traffic giữa 2 địa chỉ | `AddressTrafficCommandDTO` | `AddressTrafficResultDTO` |

## 🔌 Ports & Adapters

### Ports (Interfaces):
- `RoutingProvider` - Interface cho routing operations
- `GeocodingProvider` - Interface cho geocoding operations  
- `TrafficProvider` - Interface cho traffic operations

### Adapters (Implementations):
- `TomTomRoutingAdapter` - TomTom routing implementation
- `TomTomGeocodingAdapter` - TomTom geocoding implementation
- `TomTomTrafficAdapter` - TomTom traffic implementation

## 🔄 Anti-Corruption Layer (ACL)

### Mappers:
- `TomTomMapper` - Map routing responses
- `TomTomGeocodingMapper` - Map geocoding responses
- `TomTomTrafficMapper` - Map traffic responses

Các mapper này đảm bảo:
- Vendor responses được chuyển đổi thành Domain DTOs
- Không có vendor-specific types leak vào Application layer
- Dễ dàng thay đổi vendor mà không ảnh hưởng business logic

## 🧪 Testing Strategy

```python
# Unit Test - Use Case
def test_geocode_address_success():
    # Mock GeocodingProvider
    mock_provider = Mock(spec=GeocodingProvider)
    mock_provider.geocode_address.return_value = expected_result
    
    # Test Use Case
    use_case = GeocodeAddress(mock_provider)
    result = await use_case.handle(command)
    
    assert result == expected_result
    mock_provider.geocode_address.assert_called_once_with(command)

# Integration Test - Adapter
def test_tomtom_geocoding_adapter():
    adapter = TomTomGeocodingAdapter(base_url, api_key, http_client)
    result = await adapter.geocode_address(command)
    # Test với real TomTom API hoặc mock HTTP responses
```

## 📊 So sánh với Implementation cũ

| Aspect | Cũ (start_streamable_http.py) | Mới (Clean Architecture) |
|--------|-------------------------------|--------------------------|
| **Architecture** | Monolithic, tất cả logic trong 1 file | Layered, separation of concerns |
| **Dependencies** | Hard-coded TomTom API calls | Dependency Injection |
| **Testing** | Khó test vì coupling cao | Dễ test với mocked Ports |
| **Maintainability** | Khó maintain, logic lẫn lộn | Dễ maintain, clear responsibilities |
| **Vendor Lock-in** | Bị lock vào TomTom | Vendor independent |
| **Code Reuse** | Logic duplicate | Reusable Use Cases |

## 🔮 Mở rộng trong tương lai

### Thêm Provider mới:
1. Implement các Ports (`GoogleMapsRoutingAdapter`)
2. Tạo ACL Mapper (`GoogleMapsMapper`)
3. Wire trong Container
4. Không cần thay đổi Use Cases!

### Thêm Use Case mới:
1. Tạo DTO trong `application/dto/`
2. Implement Use Case trong `application/use_cases/`
3. Wire trong Container
4. Expose qua MCP tool

### Thêm Interface mới:
1. Tạo REST API trong `interfaces/rest/`
2. Tạo CLI trong `interfaces/cli/`
3. Sử dụng chung các Use Cases đã có
