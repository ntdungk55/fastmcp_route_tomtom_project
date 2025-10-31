# BLK-2-02 — Check Error?

Mục tiêu: Kiểm tra xem có lỗi validation từ BLK-2-01 hay không.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-01 (Validate Input Param)

- **Điều kiện tiền đề (Preconditions):**
  - Validation result đã có từ BLK-2-01

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "valid": <boolean>,
  "errors": [{
    "code": "<string>",
    "message": "<string>"
  }] | null
}
```

### 2.2 Output
- **Kết quả trả về:**
  - `has_error`: boolean (true nếu có lỗi, false nếu không)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** < 10ms (chỉ check boolean)
- **Retry:** N/A
- **Idempotency:** Yes

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-02 |
| **Tên Block** | CheckError |
| **Trigger** | After validation |
| **Preconditions** | Validation result available |
| **Input (schema)** | `{ valid: bool, errors?: [...] }` |
| **Output** | `{ has_error: bool }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 10ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: No Error
**Input:**
```json
{
  "valid": true,
  "errors": null
}
```

**Output:**
```json
{
  "has_error": false
}
```

**Next:** → BLK-2-04 (Get Coordinates From Address)

### Case 2: Has Error
**Input:**
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

**Output:**
```json
{
  "has_error": true
}
```

**Next:** → BLK-2-03 (Map Validation Errors) → BLK-End

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-01-ValidateInputParam
  - → BLK-2-03-MapValidationErrors (nếu có lỗi)
  - → BLK-2-04-GetCoordinatesFromAddress (nếu không có lỗi)


