# BLK-2-01 — Validate Input Param

Mục tiêu: Kiểm tra và validate các tham số đầu vào cho weather check request.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-00 (Listen MCP Request)

- **Điều kiện tiền đề (Preconditions):**
  - Request đã được nhận từ MCP client

- **Điều kiện dừng/không chạy (Guards):**
  - Location rỗng hoặc null → Error `INVALID_LOCATION`

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "location": "<string>",
  "units": "metric" | "imperial" | "kelvin",
  "language": "<string>"
}
```

- **Bắt buộc:**
  - `location`: Không rỗng, có thể là địa chỉ hoặc "lat,lon"

- **Validation Rules:**
  - Location không rỗng
  - Units nếu có phải thuộc ["metric", "imperial", "kelvin"]
  - Language nếu có phải là string hợp lệ

### 2.2 Output
- **Kết quả trả về (success):**
  - Validated request object

- **Kết quả trả về (error):**
```json
{
  "valid": false,
  "errors": [
    {
      "code": "INVALID_LOCATION" | "INVALID_UNITS" | "INVALID_LANGUAGE",
      "message": "<string>"
    }
  ]
}
```

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** < 100ms
- **Retry:** N/A (validation logic)
- **Idempotency:** Yes

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-01 |
| **Tên Block** | ValidateInputParam |
| **Trigger** | After BLK-2-00 |
| **Preconditions** | Request received |
| **Input (schema)** | `{ location, units?, language? }` |
| **Output** | `{ valid: bool, data?, errors? }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 100ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: Valid Input
**Input:**
```json
{
  "location": "Hanoi, Vietnam",
  "units": "metric"
}
```

**Output:**
```json
{
  "valid": true,
  "data": {
    "location": "Hanoi, Vietnam",
    "units": "metric",
    "language": "vi"
  }
}
```

### Case 2: Invalid - Empty Location
**Input:**
```json
{
  "location": "",
  "units": "metric"
}
```

**Output:**
```json
{
  "valid": false,
  "errors": [
    {
      "code": "INVALID_LOCATION",
      "message": "Location cannot be empty"
    }
  ]
}
```

### Case 3: Invalid Units
**Input:**
```json
{
  "location": "Hanoi",
  "units": "fahrenheit"  // Invalid
}
```

**Output:**
```json
{
  "valid": false,
  "errors": [
    {
      "code": "INVALID_UNITS",
      "message": "Units must be one of: metric, imperial, kelvin"
    }
  ]
}
```

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-00-ListenMCPRequest
  - → BLK-2-02-CheckError (check validation result)
- **Related Code:**
  - `app/application/services/validation_service.py` - Validation service


