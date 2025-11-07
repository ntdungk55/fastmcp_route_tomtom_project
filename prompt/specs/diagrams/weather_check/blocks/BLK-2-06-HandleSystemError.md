# BLK-2-06 — Handle System Error

Mục tiêu: Xử lý các lỗi hệ thống (API key không cấu hình, network errors, etc.) và trả về error response phù hợp.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-05 khi API key không được cấu hình
  - [x] Gọi từ các blocks khác khi có system error

- **Điều kiện tiền đề (Preconditions):**
  - Có system error (API key missing, network error, etc.)

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "error": {
    "code": "API_KEY_NOT_CONFIGURED" | "API_KEY_INVALID" | "NETWORK_ERROR" | "SYSTEM_ERROR",
    "message": "<string>"
  }
}
```

### 2.2 Output
- **Kết quả trả về:**
```json
{
  "success": false,
  "error_message": "<string>",
  "error_code": "<string>"
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
| **ID Block** | BLK-2-06 |
| **Tên Block** | HandleSystemError |
| **Trigger** | System errors (API key, network, etc.) |
| **Preconditions** | System error detected |
| **Input (schema)** | `{ error: { code, message } }` |
| **Output** | `{ success: false, error_message, error_code }` |
| **Side-effects** | Log error for monitoring |
| **Timeout/Retry** | < 50ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: API Key Not Configured
**Input:**
```json
{
  "error": {
    "code": "API_KEY_NOT_CONFIGURED",
    "message": "WeatherAPI.com API key not found in environment variable WEATHERAPI_API_KEY"
  }
}
```

**Output:**
```json
{
  "success": false,
  "error_message": "WeatherAPI.com API key not found in environment variable WEATHERAPI_API_KEY",
  "error_code": "API_KEY_NOT_CONFIGURED"
}
```

**Action:** Log CRITICAL level để alert ops team

### Case 2: Network Error
**Input:**
```json
{
  "error": {
    "code": "NETWORK_ERROR",
    "message": "Failed to connect to WeatherAPI.com"
  }
}
```

**Output:**
```json
{
  "success": false,
  "error_message": "Failed to connect to WeatherAPI.com. Please try again later.",
  "error_code": "NETWORK_ERROR"
}
```

**Action:** Log ERROR level, có thể retry sau

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-05-CheckAPIKeyConfigured
  - → BLK-End (return error to client)
- **Related Code:**
  - `app/application/use_cases/get_weather.py` - Error handling
  - `app/infrastructure/adapters/weather_adapter.py` - API error handling




