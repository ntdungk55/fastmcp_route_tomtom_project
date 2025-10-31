# BLK-2-11 — Normalize Output

Mục tiêu: Chuẩn hóa output cuối cùng trước khi trả về cho MCP client, đảm bảo format nhất quán.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-10 (Transform Weather Data)

- **Điều kiện tiền đề (Preconditions):**
  - Weather data đã được transform từ API response

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "weather_data": {
    "temperature": <number>,
    "feels_like": <number>,
    "humidity": <number>,
    "pressure": <number>,
    "description": "<string>",
    "wind_speed": <number>,
    "wind_direction": <number> | null,
    "visibility": <number> | null,
    "cloudiness": <number> | null,
    "sunrise": "<ISO8601 string>" | null,
    "sunset": "<ISO8601 string>" | null,
    "location_name": "<string>" | null,
    "country": "<string>" | null,
    "icon_code": "<string>" | null,
    "units": "<string>"
  },
  "location": "<string>",
  "coordinates": {
    "lat": <number>,
    "lon": <number>
  }
}
```

### 2.2 Output
- **Kết quả trả về:**
```json
{
  "success": true,
  "weather_data": {
    // Normalized weather data
  },
  "location": "<string>",
  "coordinates": {
    "lat": <number>,
    "lon": <number>
  }
}
```

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** < 50ms
- **Retry:** N/A
- **Idempotency:** Yes

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-11 |
| **Tên Block** | NormalizeOutput |
| **Trigger** | After data transformation |
| **Preconditions** | Transformed weather data available |
| **Input (schema)** | `{ weather_data, location, coordinates }` |
| **Output** | `{ success: true, weather_data, location, coordinates }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 50ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

**Input:**
```json
{
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
    "sunrise": null,
    "sunset": null,
    "location_name": "Ho Chi Minh City",
    "country": "Vietnam",
    "icon_code": "116",
    "units": "metric"
  },
  "location": "Ho Chi Minh City, Vietnam",
  "coordinates": {
    "lat": 10.8231,
    "lon": 106.6297
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
    "sunrise": null,
    "sunset": null,
    "location_name": "Ho Chi Minh City",
    "country": "Vietnam",
    "icon_code": "116",
    "units": "metric"
  },
  "location": "Ho Chi Minh City, Vietnam",
  "coordinates": {
    "lat": 10.8231,
    "lon": 106.6297
  }
}
```

**Normalization Rules:**
- Đảm bảo tất cả fields có type đúng
- Rounding numbers nếu cần (temperature, wind_speed)
- Format dates theo ISO8601 nếu có
- Đảm bảo null values được handle đúng
- Validate units value (metric/imperial/kelvin)

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-10-TransformWeatherData
  - → BLK-End (return final response to MCP client)
- **Related Code:**
  - `app/application/use_cases/get_weather.py` - Response building
  - `app/application/dto/weather_dto.py` - WeatherResponse DTO



