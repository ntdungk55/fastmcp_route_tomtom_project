# BLK-2-07 — Request Weather API

Mục tiêu: Gọi WeatherAPI.com API để lấy thông tin thời tiết hiện tại tại địa điểm đã chỉ định.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-05 khi API key đã được verify

- **Điều kiện tiền đề (Preconditions):**
  - Coordinates đã sẵn sàng
  - API key hợp lệ (từ environment variable `WEATHERAPI_API_KEY`)
  - Network connectivity sẵn sàng

- **Điều kiện dừng/không chạy (Guards):**
  - Environment variable `WEATHERAPI_API_KEY` không tồn tại → Error `API_KEY_NOT_CONFIGURED`
  - API key không hợp lệ → Error (đã check ở BLK-2-05)
  - Coordinates invalid → Error

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "coordinates": {
    "lat": <number>,
    "lon": <number>
  },
  "units": "metric" | "imperial" | "kelvin",
  "language": "<string>",
  "api_key": "<string>"  // Từ BLK-2-05
}
```

- **Bắt buộc:**
  - `coordinates.lat`, `coordinates.lon`
  - `api_key`

### 2.2 Output
- **Kết quả trả về (success):**
```json
{
  "success": true,
  "weather_data": {
    "temperature": <number>,
    "feels_like": <number>,
    "humidity": <number>,
    "pressure": <number>,
    "description": "<string>",
    "wind_speed": <number>,
    "wind_direction": <number>,
    "visibility": <number>,
    "cloudiness": <number>,
    "sunrise": <ISO8601 string>,
    "sunset": <ISO8601 string>,
    "location_name": "<string>",
    "country": "<string>"
  },
  "metadata": {
    "provider": "openweathermap",
    "units": "metric" | "imperial" | "kelvin",
    "request_time": <ISO8601 string>
  }
}
```

- **Kết quả trả về (error):**
```json
{
  "success": false,
  "error": {
    "code": "API_ERROR" | "TIMEOUT" | "RATE_LIMIT" | "INVALID_RESPONSE",
    "message": "<string>",
    "status_code": <integer> | null
  }
}
```

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** 10s cho API call
- **Retry:** 3 lần với exponential backoff (1s, 2s, 4s)
- **Idempotency:** Yes (GET request)
- **Rate limit:** OpenWeatherMap free tier: 60 calls/minute
- **Circuit Breaker:** Mở sau 10 errors liên tiếp trong 60s

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-07 |
| **Tên Block** | RequestWeatherAPI |
| **Trigger** | After API key check success |
| **Preconditions** | Valid coordinates, API key, network |
| **Input (schema)** | `{ coordinates, units, language, api_key }` |
| **Output** | `{ success: bool, weather_data?, error? }` |
| **Side-effects** | HTTP call to OpenWeatherMap, log, metrics |
| **Timeout/Retry** | 10s timeout, 3 retries |
| **Idempotency** | Yes |
| **AuthZ/Scope** | API key from env |

---

## 4) Ví dụ cụ thể

### Case 1: Successful API Call
**Input:**
```json
{
  "coordinates": {
    "lat": 10.8231,
    "lon": 106.6297
  },
  "units": "metric",
  "language": "vi",
  "api_key": "abc123..."
}
```

**API Call:**
```http
GET https://api.weatherapi.com/v1/current.json?key=abc123...&q=10.8231,106.6297&lang=vi
```

**API Response (200 OK):**
```json
{
  "location": {
    "name": "Ho Chi Minh City",
    "region": "Ho Chi Minh",
    "country": "Vietnam",
    "lat": 10.8231,
    "lon": 106.6297,
    "tz_id": "Asia/Ho_Chi_Minh",
    "localtime_epoch": 1697123456,
    "localtime": "2023-10-13 17:30:56"
  },
  "current": {
    "last_updated_epoch": 1697123456,
    "last_updated": "2023-10-13 17:30",
    "temp_c": 32.5,
    "temp_f": 90.5,
    "feelslike_c": 38.2,
    "feelslike_f": 100.8,
    "condition": {
      "text": "Partly cloudy",
      "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
      "code": 1003
    },
    "wind_mph": 11.6,
    "wind_kph": 18.7,
    "wind_degree": 180,
    "wind_dir": "S",
    "pressure_mb": 1010.0,
    "pressure_in": 29.83,
    "precip_mm": 0.0,
    "precip_in": 0.0,
    "humidity": 75,
    "cloud": 20,
    "feelslike_c": 38.2,
    "vis_km": 10.0,
    "uv": 6.0
  }
}
```

**Output:**
```json
{
  "success": true,
  "weather_data": {
    "temperature": 32.5,
    "feels_like": 38.2,
    "humidity": 75,
    "pressure": 1010,
    "description": "mây thưa",
    "wind_speed": 5.2,
    "wind_direction": 180,
    "visibility": 10000,
    "cloudiness": 20,
    "sunrise": "2023-10-13T05:06:40+07:00",
    "sunset": "2023-10-13T17:20:00+07:00",
    "location_name": "Ho Chi Minh City",
    "country": "VN"
  },
  "metadata": {
    "provider": "openweathermap",
    "units": "metric",
    "request_time": "2023-10-13T10:30:56Z"
  }
}
```

**Next:** → BLK-2-08 (Check API Success) → BLK-2-10 (Transform Weather Data)

### Case 2: API Key Unauthorized (401)
**API Response:**
```json
{
  "cod": 401,
  "message": "Invalid API key. Please see http://openweathermap.org/faq#error401 for more info."
}
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_UNAUTHORIZED",
    "message": "WeatherAPI.com API key is not authorized",
    "status_code": 401
  }
}
```

**Next:** → BLK-2-09 (Classify Error) → BLK-2-06 (Handle System Error)

### Case 3: Location Not Found (404)
**API Response:**
```json
{
  "cod": "404",
  "message": "city not found"
}
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "LOCATION_NOT_FOUND",
    "message": "Weather data not found for this location",
    "status_code": 404
  }
}
```

**Next:** → BLK-2-09 (Classify Error) → BLK-2-03 (Map Validation Errors - USER_ERROR)

### Case 4: Rate Limit (429)
**API Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT",
    "message": "API rate limit exceeded, please try again later",
    "status_code": 429,
    "retry_after": 60
  }
}
```

**Handling:** Retry after 60s (1 lần), nếu vẫn fail → return error

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-05-CheckAPIKeyConfigured
  - → BLK-2-08-CheckAPISuccess
- **Related Code:**
  - `app/infrastructure/adapters/weather_adapter.py` - Weather API adapter
  - `app/application/ports/weather_provider.py` - Weather provider interface
  - `app/infrastructure/http/client.py` - HTTP client với retry
- **API Docs:**
  - WeatherAPI.com Current Weather API: https://www.weatherapi.com/docs/
  - Get API Key: https://www.weatherapi.com/signup.aspx

