# BLK-2-03 — Map Validation Errors

Mục tiêu: Chuyển đổi validation errors thành user-friendly messages để trả về cho client.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-02 khi `has_error = true`

- **Điều kiện tiền đề (Preconditions):**
  - Có validation errors từ BLK-2-01

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "errors": [{
    "code": "<string>",
    "message": "<string>"
  }]
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
| **ID Block** | BLK-2-03 |
| **Tên Block** | MapValidationErrors |
| **Trigger** | After error check (has_error=true) |
| **Preconditions** | Validation errors available |
| **Input (schema)** | `{ errors: [...] }` |
| **Output** | `{ success: false, error_message, error_code }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 50ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: Invalid Location
**Input:**
```json
{
  "errors": [
    {
      "code": "INVALID_LOCATION",
      "message": "Location cannot be empty"
    }
  ]
}
```

**Output:**
```json
{
  "success": false,
  "error_message": "Location cannot be empty",
  "error_code": "INVALID_LOCATION"
}
```

### Case 2: Invalid Units
**Input:**
```json
{
  "errors": [
    {
      "code": "INVALID_UNITS",
      "message": "Units must be one of: metric, imperial, kelvin"
    }
  ]
}
```

**Output:**
```json
{
  "success": false,
  "error_message": "Units must be one of: metric, imperial, kelvin",
  "error_code": "INVALID_UNITS"
}
```

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-02-CheckError
  - → BLK-End (return error to client)
- **Related Code:**
  - `app/application/use_cases/get_weather.py` - Error handling




