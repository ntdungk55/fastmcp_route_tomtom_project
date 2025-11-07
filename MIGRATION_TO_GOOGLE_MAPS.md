# Hướng dẫn Migration từ TomTom Map API sang Google Maps API

## 📋 Tổng quan

Để chuyển đổi từ TomTom Map API sang Google Maps API, bạn cần thay thế các components sau:

---

## 🔧 1. Infrastructure Layer - Adapters (Thay thế hoàn toàn)

### 1.1. Thay thế thư mục `app/infrastructure/tomtom/` → `app/infrastructure/google_maps/`

**Các adapter cần tạo mới:**
- ✅ `app/infrastructure/google_maps/adapters/routing_adapter.py`
  - Thay thế: `TomTomRoutingAdapter` → `GoogleMapsRoutingAdapter`
  - API: Google Directions API
  - Endpoint: `https://maps.googleapis.com/maps/api/directions/json`

- ✅ `app/infrastructure/google_maps/adapters/geocoding_adapter.py`
  - Thay thế: `TomTomGeocodingAdapter` → `GoogleMapsGeocodingAdapter`
  - API: Google Geocoding API
  - Endpoint: `https://maps.googleapis.com/maps/api/geocode/json`

- ✅ `app/infrastructure/google_maps/adapters/reverse_geocode_adapter.py`
  - Thay thế: `TomTomReverseGeocodeAdapter` → `GoogleMapsReverseGeocodeAdapter`
  - API: Google Reverse Geocoding API
  - Endpoint: `https://maps.googleapis.com/maps/api/geocode/json`

- ✅ `app/infrastructure/google_maps/adapters/traffic_adapter.py`
  - Thay thế: `TomTomTrafficAdapter` → `GoogleMapsTrafficAdapter`
  - API: Google Directions API với `traffic_model` và `departure_time`
  - Note: Google Maps không có Traffic API riêng, dùng Directions API với traffic info

**ACL Mappers cần tạo mới:**
- ✅ `app/infrastructure/google_maps/acl/mappers.py`
  - Thay thế: `TomTomMapper` → `GoogleMapsMapper`
  - Chuyển đổi response từ Google Directions API format sang domain RoutePlan

- ✅ `app/infrastructure/google_maps/acl/geocoding_mapper.py`
  - Thay thế: `TomTomGeocodingMapper` → `GoogleMapsGeocodingMapper`
  - Chuyển đổi response từ Google Geocoding API format sang domain DTOs

- ✅ `app/infrastructure/google_maps/acl/traffic_mapper.py`
  - Thay thế: `TomTomTrafficMapper` → `GoogleMapsTrafficMapper`
  - Chuyển đổi traffic data từ Google Directions API

**Constants & Endpoints:**
- ✅ `app/infrastructure/google_maps/endpoint.py`
  - Thay thế: TomTom endpoints → Google Maps endpoints
  - Định nghĩa các path patterns cho Google Maps API

- ✅ `app/infrastructure/google_maps/errors.py`
  - Thay thế: TomTom-specific errors → Google Maps API errors
  - Xử lý Google Maps API error codes

- ✅ `app/infrastructure/constants/google_maps_constants.py`
  - Thay thế: `app/infrastructure/constants/tomtom_constants.py`
  - Định nghĩa Google Maps API constants, endpoints, defaults

---

## ⚙️ 2. Configuration Layer

### 2.1. Settings (`app/infrastructure/config/settings.py`)

**Thay đổi:**
```python
# Thay đổi từ:
tomtom_base_url: str = Field(default_factory=lambda: os.getenv("TOMTOM_BASE_URL", "https://api.tomtom.com"))
tomtom_api_key: str = Field(default_factory=lambda: os.getenv("TOMTOM_API_KEY", ""))

# Thành:
google_maps_base_url: str = Field(default_factory=lambda: os.getenv("GOOGLE_MAPS_BASE_URL", "https://maps.googleapis.com/maps/api"))
google_maps_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_MAPS_API_KEY", ""))
```

**Validator cần cập nhật:**
- Đổi `validate_tomtom_api_key` → `validate_google_maps_api_key`
- Cập nhật error messages

### 2.2. API Config (`app/infrastructure/config/api_config.py`)

**Thay đổi:**
```python
# Thay đổi từ:
tomtom_api_key: str

# Thành:
google_maps_api_key: str
```

**Cập nhật:**
- `ApiConfig.from_environment()` - đổi environment variable từ `TOMTOM_API_KEY` → `GOOGLE_MAPS_API_KEY`

---

## 🏭 3. Dependency Injection Layer

### 3.1. Infrastructure Provider (`app/di/providers/infrastructure_provider.py`)

**Thay đổi imports:**
```python
# Thay đổi từ:
from app.infrastructure.tomtom.adapters.geocoding_adapter import TomTomGeocodingAdapter
from app.infrastructure.tomtom.adapters.routing_adapter import TomTomRoutingAdapter
from app.infrastructure.tomtom.adapters.traffic_adapter import TomTomTrafficAdapter

# Thành:
from app.infrastructure.google_maps.adapters.geocoding_adapter import GoogleMapsGeocodingAdapter
from app.infrastructure.google_maps.adapters.routing_adapter import GoogleMapsRoutingAdapter
from app.infrastructure.google_maps.adapters.traffic_adapter import GoogleMapsTrafficAdapter
```

**Cập nhật `get_adapters()`:**
```python
# Thay đổi từ:
base_config = {
    "base_url": self._settings.tomtom_base_url,
    "api_key": self._settings.tomtom_api_key,
    ...
}

# Thành:
base_config = {
    "base_url": self._settings.google_maps_base_url,
    "api_key": self._settings.google_maps_api_key,
    ...
}
```

**Cập nhật adapter instances:**
- `TomTomRoutingAdapter(**base_config)` → `GoogleMapsRoutingAdapter(**base_config)`
- `TomTomGeocodingAdapter(**base_config)` → `GoogleMapsGeocodingAdapter(**base_config)`
- `TomTomTrafficAdapter(**base_config)` → `GoogleMapsTrafficAdapter(**base_config)`

### 3.2. Gateway Factory (`app/di/factories/gateway_factory.py`)

**Thay đổi class name:**
```python
# Thay đổi từ:
class TomTomGatewayFactory:
    def create_geocoding_adapter(self, settings: Settings) -> TomTomGeocodingAdapter:
        ...
    def create_routing_adapter(self, settings: Settings) -> TomTomRoutingAdapter:
        ...

# Thành:
class GoogleMapsGatewayFactory:
    def create_geocoding_adapter(self, settings: Settings) -> GoogleMapsGeocodingAdapter:
        ...
    def create_routing_adapter(self, settings: Settings) -> GoogleMapsRoutingAdapter:
        ...
```

**Cập nhật `GatewayFactoryManager`:**
```python
# Thay đổi từ:
self._factory = TomTomGatewayFactory()

# Thành:
self._factory = GoogleMapsGatewayFactory()
```

**Cập nhật settings references:**
- `settings.tomtom_base_url` → `settings.google_maps_base_url`
- `settings.tomtom_api_key` → `settings.google_maps_api_key`

---

## 🔄 4. API Response Format Differences

### 4.1. Routing API

**TomTom:**
- Response format: `routes[0].legs[0].summary`, `routes[0].sections[]`
- Distance unit: meters (trong summary)
- Duration unit: seconds

**Google Maps:**
- Response format: `routes[0].legs[0].distance`, `routes[0].legs[0].duration`
- Distance object: `{value: number, text: string}` (meters và formatted string)
- Duration object: `{value: number, text: string}` (seconds và formatted string)
- Traffic: Có `duration_in_traffic` trong legs

### 4.2. Geocoding API

**TomTom:**
- Response format: `results[].position`, `results[].address`
- Address structure: `freeformAddress`, `streetName`, `municipality`

**Google Maps:**
- Response format: `results[].geometry.location`, `results[].formatted_address`
- Address components: `address_components[]` với `types[]` (street_number, route, locality, etc.)

### 4.3. Traffic Information

**TomTom:**
- Dedicated Traffic API
- Traffic flow và incidents riêng biệt

**Google Maps:**
- Traffic info được embed trong Directions API
- `duration_in_traffic` field trong route legs
- `traffic_model` parameter: `best_guess`, `pessimistic`, `optimistic`
- Cần `departure_time` để có traffic data chính xác

---

## 📝 5. Environment Variables

**Cập nhật `.env` file:**
```env
# Thay đổi từ:
TOMTOM_BASE_URL=https://api.tomtom.com
TOMTOM_API_KEY=your_tomtom_api_key

# Thành:
GOOGLE_MAPS_BASE_URL=https://maps.googleapis.com/maps/api
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

---

## 🧪 6. Tests

### 6.1. Update Test Files

**Thay đổi test imports:**
- `tests/infrastructure/adapters/test_geocoding_adapter.py`
  - Thay `TomTomGeocodingAdapter` → `GoogleMapsGeocodingAdapter`
  - Cập nhật mock responses theo Google Maps format

- `tests/infrastructure/adapters/test_routing_adapter.py` (nếu có)
  - Thay `TomTomRoutingAdapter` → `GoogleMapsRoutingAdapter`
  - Cập nhật mock responses

- `tests/infrastructure/adapters/test_traffic_adapter.py` (nếu có)
  - Thay `TomTomTrafficAdapter` → `GoogleMapsTrafficAdapter`

### 6.2. Test Data

**Cập nhật mock responses:**
- Tất cả test fixtures cần thay đổi từ TomTom response format → Google Maps response format
- Kiểm tra mapper logic với Google Maps response structure

---

## 📚 7. Documentation

### 7.1. README.md
- Cập nhật API provider từ TomTom → Google Maps
- Cập nhật setup instructions với Google Maps API key

### 7.2. Postman Collection
- Thay đổi hoặc thêm Google Maps API collection
- Xóa hoặc archive TomTom collection

---

## 🔍 8. Code Search & Replace

**Các pattern cần tìm và thay thế toàn bộ codebase:**
- `TomTom` → `GoogleMaps`
- `tomtom` → `google_maps`
- `TOMTOM` → `GOOGLE_MAPS`
- `tomtom_api_key` → `google_maps_api_key`
- `tomtom_base_url` → `google_maps_base_url`

---

## ✅ Checklist Migration

- [ ] Tạo thư mục `app/infrastructure/google_maps/`
- [ ] Tạo các adapter mới (routing, geocoding, reverse_geocode, traffic)
- [ ] Tạo các mapper mới (routing, geocoding, traffic)
- [ ] Tạo constants và endpoints mới
- [ ] Cập nhật Settings class
- [ ] Cập nhật API Config
- [ ] Cập nhật Infrastructure Provider
- [ ] Cập nhật Gateway Factory
- [ ] Cập nhật environment variables (.env)
- [ ] Cập nhật tất cả imports
- [ ] Cập nhật test files
- [ ] Cập nhật documentation
- [ ] Test toàn bộ functionality
- [ ] Xóa hoặc archive thư mục `app/infrastructure/tomtom/`

---

## 🚨 Lưu ý quan trọng

1. **API Key Format:**
   - TomTom: API key là string
   - Google Maps: API key là string, nhưng cần enable các APIs cụ thể trong Google Cloud Console

2. **API Quotas:**
   - Google Maps có quotas khác TomTom
   - Cần cấu hình billing trong Google Cloud Console

3. **API Endpoints:**
   - TomTom: RESTful API với versioning
   - Google Maps: RESTful API với service paths (directions, geocode, etc.)

4. **Error Handling:**
   - Google Maps API có error format khác
   - Cần cập nhật error handling logic

5. **Travel Modes:**
   - Google Maps: `driving`, `walking`, `bicycling`, `transit`
   - TomTom: `car`, `pedestrian`, `bicycle`, `motorcycle`
   - Cần mapping giữa domain enum và Google Maps values

---

## 📖 Tham khảo

- [Google Maps Directions API](https://developers.google.com/maps/documentation/directions)
- [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding)
- [Google Maps API Pricing](https://mapsplatform.google.com/pricing/)


