# Báo Cáo Phân Tích Tính Năng: Tool get_detailed_route

**Tạo:** 2025-10-17  
**Trạng Thái:** 🔄 SẴN SÀNG CHO GIAI ĐOẠN 2 THỰC HIỆN

---

## 1. Tóm Tắt Điều Hành

Tool `get_detailed_route` đã được dọn dẹp khỏi codebase (tất cả 14 services, use case, DTOs đã bị xóa). Báo cáo này phân tích các yêu cầu và khuyến nghị thực hiện lại theo mô hình Clean Architecture v5.

**Khuyến Nghị:** ✅ **TIẾP TỤC VỚI THÊM MỚI**

---

## 2. Tổng Quan Tính Năng

### 2.1 Trạng Thái Hiện Tại
- **Diagram:** ✅ CÓ SẴN tại `prompt/specs/diagrams/routing mcp server diagram.drawio`
- **Blocks:** ✅ ĐỦ 14 files (tất cả block descriptions đã tạo)
- **Code:** ❌ ĐÃ XÓA (cần generate lại)
- **DTOs:** ❌ ĐÃ XÓA (cần generate lại)
- **Use Case:** ❌ ĐÃ XÓA (cần generate lại)

**14 Block Descriptions Có Sẵn:**
1. ✅ BLK-1-00-ListenMCPRequest.md - Lắng nghe request MCP
2. ✅ BLK-1-01-Valid Input Param.md - Validate tham số input
3. ✅ BLK-1-02-CheckError.md - Kiểm tra lỗi validation
4. ✅ BLK-1-03-MapValidationErrorsToUserMessages.md - Map lỗi sang user messages
5. ✅ BLK-1-04-CheckDestinationExists.md - Kiểm tra destination trong database
6. ✅ BLK-1-05-ClassifyErrorType.md - Phân loại loại lỗi
7. ✅ BLK-1-06-HandleSystemError.md - Xử lý lỗi hệ thống
8. ✅ BLK-1-07-SaveRequestHistory.md - Lưu lịch sử request
9. ✅ BLK-1-08-SaveDestination.md - Lưu destination mới
10. ✅ BLK-1-09-RequestRoutingAPI.md - Gọi API TomTom để tính tuyến
11. ✅ BLK-1-10-CheckAPISuccess.md - Kiểm tra API response thành công
12. ✅ BLK-1-11-ClassifyAndFormatErrorOutput.md - Format error output
13. ✅ BLK-1-12-TransformSuccessDataForAI.md - Transform data cho AI
14. ✅ BLK-1-13-UpdateRequestResult.md - Cập nhật kết quả request

### 2.2 Mục Đích Tool
Tính toán tuyến đường chi tiết giữa hai địa chỉ:
- Chấp nhận hai địa chỉ (điểm xuất phát, điểm đến)
- Sử dụng các địa chỉ đã lưu từ cơ sở dữ liệu nếu có sẵn
- Geocode các địa chỉ nếu không tìm thấy trong cơ sở dữ liệu
- Trả về tuyến đường chi tiết với:
  - Hướng dẫn từng bước (turn-by-turn)
  - Thông tin giao thông cho mỗi đoạn
  - Các tuyến đường thay thế
  - Ước tính thời gian

### 2.3 Loại Kiến Trúc
**Use Case Composite** - Yêu cầu nhiều adapter:
- `GeocodingProvider` (từ geocoding_adapter)
- `RoutingProvider` (từ routing_adapter)
- `DestinationRepository` (từ SQLite repository)

---

## 3. Các Phụ Thuộc & Điểm Tích Hợp

### 3.1 Adapter Cần Thiết
- ✅ **TomTomGeocodingAdapter** - Đã tồn tại tại `infrastructure/tomtom/adapters/geocoding_adapter.py`
- ✅ **TomTomRoutingAdapter** - Đã tồn tại tại `infrastructure/tomtom/adapters/routing_adapter.py`
- ✅ **SQLiteDestinationRepository** - Đã tồn tại tại `infrastructure/persistence/repositories/sqlite_destination_repository.py`

### 3.2 Các Use Case Tương Tự để Tham Khảo
- ✅ **SaveDestinationUseCase** - Composite, sử dụng geocoding_adapter + destination_repository
  - Vị trí: `app/application/use_cases/save_destination.py`
  - Mô hình: Nhiều adapter được inject qua constructor

- ✅ **CheckAddressTraffic** - Composite, sử dụng geocoding_adapter + traffic_adapter
  - Vị trí: `app/application/use_cases/check_address_traffic.py`
  - Mô hình: Nhiều adapter + orchestration

### 3.3 Các Port Hiện Tại để Mở Rộng
- Port `DestinationRepository` đã tồn tại
- Port `GeocodingProvider` đã tồn tại  
- Port `RoutingProvider` đã tồn tại

---

## 4. Kế Hoạch Thực Hiện

### 4.1 Cấu Trúc Theo Từng Tầng

#### **Tầng 1: Domain (Không Cần Thay Đổi)**
- ✅ Sử dụng value object `LatLon` hiện tại
- ✅ Sử dụng enum `TravelMode` hiện tại
- ✅ Không cần entity domain mới

#### **Tầng 2: Application**
**Các File Cần Tạo:**

1. **Tầng DTO:**
   - `app/application/dto/detailed_route_dto.py`
     - Request: `DetailedRouteRequest` với origin_address, dest_address, travel_mode, vv.
     - Response: `DetailedRouteResponse` với origin, destination, main_route, alternative_routes, vv.
     - Các loại hỗ trợ: `RoutePoint`, `RouteInstruction`, `RouteLeg`, `TrafficSection`, `GuidanceInfo`

2. **Tầng Use Case:**
   - `app/application/use_cases/get_detailed_route.py`
     - Class: `GetDetailedRouteUseCase`
     - Constructor: inject DestinationRepository, GeocodingProvider, RoutingProvider
     - Method: `execute(request: DetailedRouteRequest) → DetailedRouteResponse`
     - Logic:
       1. Kiểm tra nếu origin_address tồn tại trong cơ sở dữ liệu
       2. Nếu không, geocode origin_address
       3. Kiểm tra nếu destination_address tồn tại trong cơ sở dữ liệu
       4. Nếu không, geocode destination_address
       5. Tính toán tuyến đường sử dụng routing_provider
       6. Lấy guidance/instructions từ routing_provider
       7. Xây dựng DetailedRouteResponse
       8. Trả về response

#### **Tầng 3: Infrastructure**
- ✅ Đã có tất cả adapter cần thiết
- ✅ Không cần file infrastructure mới

#### **Tầng 4: Interfaces (MCP)**
**File Cần Cập Nhật:**

1. **`app/interfaces/mcp/server.py`**
   - Thêm: function `get_detailed_route_tool`
   - Decorator: `@mcp.tool(name=MCPToolNames.GET_DETAILED_ROUTE)`
   - Parameters: origin_address, destination_address, travel_mode, country_set, language
   - Gọi: `await _container.get_detailed_route.execute(request)`
   - Trả về: DetailedRouteResponse dưới dạng dict

#### **Tầng 5: DI Container**
**Cập Nhật: `app/di/container.py`**

1. Import: `from app.application.use_cases.get_detailed_route import GetDetailedRouteUseCase`
2. Trong method `_init_use_cases()`:
   ```python
   # Detailed Route Use Case (composite use case)
   self.get_detailed_route = GetDetailedRouteUseCase(
       destination_repository=self.destination_repository,
       geocoding_provider=self.geocoding_adapter,
       routing_provider=self.routing_adapter
   )
   ```

---

## 5. Mô Hình Tham Khảo Thực Hiện

### 5.1 Ví Dụ: CheckAddressTraffic (Composite Use Case)
Vị trí: `app/application/use_cases/check_address_traffic.py`

```python
class CheckAddressTraffic:
    def __init__(self, geocoding: GeocodingProvider, traffic: TrafficProvider):
        self._geocoding = geocoding
        self._traffic = traffic
    
    async def handle(self, cmd: AddressTrafficCommandDTO) -> TrafficAnalysisResponse:
        # Geocode địa chỉ xuất phát
        origin_geocode = await self._geocoding.geocode_address(...)
        # Lấy thông tin giao thông cho điểm xuất phát
        traffic_data = await self._traffic.get_traffic(...)
        # Trả về response kết hợp
        return TrafficAnalysisResponse(...)
```

### 5.2 Ví Dụ: SaveDestinationUseCase (Multi-Adapter)
Vị trí: `app/application/use_cases/save_destination.py`

```python
class SaveDestinationUseCase:
    def __init__(self, destination_repository: DestinationRepository, 
                 geocoding_provider: GeocodingProvider):
        self._repository = destination_repository
        self._geocoding = geocoding_provider
    
    async def execute(self, request: SaveDestinationRequest) -> SaveDestinationResponse:
        # Geocode địa chỉ
        geocoding_result = await self._geocoding.geocode_address(...)
        # Lưu vào repository
        destination = await self._repository.save(...)
        # Trả về response
        return SaveDestinationResponse(...)
```

---

## 6. Yêu Cầu DTO

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
    "name": "string (từ database nếu đã lưu)",
    "lat": number,
    "lon": number
  },
  "destination": {
    "address": "string",
    "name": "string (từ database nếu đã lưu)",
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

## 7. Định Nghĩa Tool MCP

### 7.1 Chữ Ký Tool
```python
@mcp.tool(name="get_detailed_route")
async def get_detailed_route_tool(
    origin_address: str,
    destination_address: str,
    travel_mode: TravelModeLiteral = "car",
    country_set: str = "VN",
    language: str = "vi-VN"
) -> dict:
    """Tính toán tuyến đường chi tiết giữa hai địa chỉ với thông tin giao thông."""
```

### 7.2 Các Tham Số Tool
| Tham Số | Loại | Bắt Buộc | Mặc Định | Mô Tả |
|---------|------|----------|----------|-------|
| origin_address | string | ✅ | - | Địa chỉ điểm xuất phát |
| destination_address | string | ✅ | - | Địa chỉ điểm đến |
| travel_mode | string | ❌ | "car" | Phương tiện: car, bicycle, foot |
| country_set | string | ❌ | "VN" | Mã quốc gia |
| language | string | ❌ | "vi-VN" | Ngôn ngữ response |

---

## 8. Các Vấn Đề Đã Biết & Cân Nhắc

### 8.1 Trường Hợp Edge
- ✅ Địa chỉ không tìm thấy trong database → fallback sang geocoding
- ✅ Geocoding không trả về kết quả → cần xử lý lỗi
- ✅ Routing API không trả về tuyến đường → cần xử lý lỗi
- ✅ Nhiều địa chỉ lưu với cùng địa chỉ → sử dụng kết quả đầu tiên

### 8.2 Các Kịch Bản Lỗi
- Geocoding thất bại → trả về error response
- Routing API thất bại → trả về error response
- Không tìm thấy tuyến đường → trả về error response
- Tọa độ không hợp lệ → validation error

---

## 9. Các Bước Tiếp Theo (Giai Đoạn 2 Thực Hiện)

### 9.1 Giai Đoạn Thiết Kế Block
1. ✅ **Review của User** - Developer phê duyệt phân tích này
2. Tạo mô tả block chi tiết trong `prompt/specs/diagrams/blocks/`
3. Chờ phê duyệt block của user

### 9.2 Giai Đoạn Tạo Code
1. Tạo DTOs
2. Tạo Use Case
3. Cập nhật DI Container
4. Cập nhật MCP Server
5. Thêm vào danh sách MCP Tool
6. Kiểm thử thực hiện

---

## 10. Tóm Tắt

| Mục | Trạng Thái | Ghi Chú |
|-----|-----------|--------|
| **Diagram** | ✅ Có sẵn | File: routing mcp server diagram.drawio |
| **Blocks** | ✅ Đầy đủ 14 files | Tất cả block descriptions đã tạo |
| **Code** | ❌ Cần generate | DTOs, Use Case, MCP tool |
| **DTOs** | ❌ Cần tạo | detailed_route_dto.py |
| **Use Case** | ❌ Cần tạo | get_detailed_route.py |
| **DI Setup** | ⏳ Cần wire | Container wiring simple |
| **MCP Tool** | ⏳ Cần thêm | Sử dụng blocks hiện tại |

---

**Khuyến Nghị:** ✅ **TIẾP TỤC GIAI ĐOẠN 2 - GENERATE CODE (SKIP BLOCK DESIGN)**

Vì blocks đã sẵn → có thể gen code luôn mà không cần tạo blocks mới.
