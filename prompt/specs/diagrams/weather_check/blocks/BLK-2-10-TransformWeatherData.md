# BLK-2-10 — Transform Weather Data

Mục tiêu: Chuyển đổi response từ OpenWeatherMap API thành format chuẩn của domain model, chuẩn hóa units và format dữ liệu.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-08 khi API call thành công

- **Điều kiện tiền đề (Preconditions):**
  - Weather API response thành công
  - Response có đầy đủ các trường cần thiết

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "api_response": {
    // OpenWeatherMap API response format
  },
  "request_units": "metric" | "imperial" | "kelvin",
  "language": "<string>"
}
```

### 2.2 Output
- **Kết quả trả về:**
```json
{
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
  "country": "<string>",
  "units": "<string>",
  "icon_code": "<string>"
}
```

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** < 50ms (chỉ transform data)
- **Retry:** N/A
- **Idempotency:** Yes

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-10 |
| **Tên Block** | TransformWeatherData |
| **Trigger** | After API success |
| **Preconditions** | Valid API response |
| **Input (schema)** | OpenWeatherMap API response |
| **Output** | Normalized weather data |
| **Side-effects** | None |
| **Timeout/Retry** | < 50ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

**Input (API Response):**
```json
{
  "main": {
    "temp": 32.5,
    "feels_like": 38.2,
    "pressure": 1010,
    "humidity": 75
  },
  "weather": [{
    "description": "mây thưa",
    "icon": "02d"
  }],
  "wind": {
    "speed": 5.2,
    "deg": 180
  },
  "visibility": 10000,
  "clouds": {"all": 20},
  "sys": {
    "country": "VN",
    "sunrise": 1697080000,
    "sunset": 1697124000
  },
  "name": "Ho Chi Minh City"
}
```

**Output:**
```json
{
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
  "country": "VN",
  "units": "metric",
  "icon_code": "02d"
}
```

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-08-CheckAPISuccess
  - → BLK-2-11-NormalizeOutput
- **Related Code:**
  - `app/infrastructure/adapters/weather_adapter.py` - Weather data transformation
  - `app/application/dto/weather_dto.py` - Weather DTOs



