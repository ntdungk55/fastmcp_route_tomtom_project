# BLK-2-09 — Classify Error Output

Mục tiêu: Phân loại lỗi từ WeatherAPI.com và tạo error response phù hợp (user error vs system error).

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-08 khi `is_success = false`

- **Điều kiện tiền đề (Preconditions):**
  - API error response đã có từ BLK-2-07

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "error": {
    "code": <integer>,
    "message": "<string>"
  }
}
```

### 2.2 Output
- **Kết quả trả về:**
```json
{
  "error_type": "USER_ERROR" | "SYSTEM_ERROR",
  "error_code": "<string>",
  "error_message": "<string>",
  "status_code": <integer> | null
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
| **ID Block** | BLK-2-09 |
| **Tên Block** | ClassifyErrorOutput |
| **Trigger** | After API error detected |
| **Preconditions** | API error response available |
| **Input (schema)** | `{ error: { code, message } }` |
| **Output** | `{ error_type, error_code, error_message, status_code? }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 50ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: User Error - Location Not Found
**Input:**
```json
{
  "error": {
    "code": 1006,
    "message": "No matching location found."
  }
}
```

**Output:**
```json
{
  "error_type": "USER_ERROR",
  "error_code": "LOCATION_NOT_FOUND",
  "error_message": "No matching location found.",
  "status_code": 400
}
```

### Case 2: System Error - Invalid API Key
**Input:**
```json
{
  "error": {
    "code": 1002,
    "message": "API key is invalid."
  }
}
```

**Output:**
```json
{
  "error_type": "SYSTEM_ERROR",
  "error_code": "API_KEY_UNAUTHORIZED",
  "error_message": "WeatherAPI.com API key is not authorized",
  "status_code": 401
}
```

**Next:** → BLK-2-06 (Handle System Error)

### Case 3: System Error - Rate Limit
**Input:**
```json
{
  "error": {
    "code": 1005,
    "message": "API key has exceeded calls per month quota."
  }
}
```

**Output:**
```json
{
  "error_type": "SYSTEM_ERROR",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "error_message": "API rate limit exceeded, please try again later",
  "status_code": 429
}
```

---

## 5) Error Classification Rules

| Error Code | WeatherAPI.com | Classification | Action |
|-----------|----------------|----------------|--------|
| 1002 | Invalid API key | SYSTEM_ERROR | Alert ops |
| 1003 | API key not found | SYSTEM_ERROR | Alert ops |
| 1005 | Rate limit exceeded | SYSTEM_ERROR | Retry after delay |
| 1006 | No location found | USER_ERROR | Return to user |
| 2006 | Invalid coordinates | USER_ERROR | Return to user |
| Others | Unknown | SYSTEM_ERROR | Log & alert |

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-08-CheckAPISuccess
  - → BLK-2-06-HandleSystemError (nếu system error)
  - → BLK-End (nếu user error)
- **Related Code:**
  - `app/infrastructure/adapters/weather_adapter.py` - Error handling
  - `app/application/use_cases/get_weather.py` - Error classification




