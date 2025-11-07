# BLK-2-08 — Check API Success?

Mục tiêu: Kiểm tra xem API call từ WeatherAPI.com có thành công hay không.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-07 (Request Weather API)

- **Điều kiện tiền đề (Preconditions):**
  - API response đã nhận được từ WeatherAPI.com

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "response": {
    "success": <boolean>,
    "data": <object> | null,
    "error": <object> | null
  }
}
```

### 2.2 Output
- **Kết quả trả về:**
  - `is_success`: boolean (true nếu API success, false nếu có error)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** < 10ms (chỉ check boolean)
- **Retry:** N/A
- **Idempotency:** Yes

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-08 |
| **Tên Block** | CheckAPISuccess |
| **Trigger** | After API call |
| **Preconditions** | API response received |
| **Input (schema)** | `{ response: { success, data?, error? } }` |
| **Output** | `{ is_success: bool }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 10ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: API Success
**Input:**
```json
{
  "response": {
    "success": true,
    "data": {
      "location": {...},
      "current": {...}
    }
  }
}
```

**Output:**
```json
{
  "is_success": true
}
```

**Next:** → BLK-2-10 (Transform Weather Data)

### Case 2: API Error
**Input:**
```json
{
  "response": {
    "success": false,
    "error": {
      "code": 1002,
      "message": "API key is invalid."
    }
  }
}
```

**Output:**
```json
{
  "is_success": false
}
```

**Next:** → BLK-2-09 (Classify Error Output) → BLK-End

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-07-RequestWeatherAPI
  - → BLK-2-09-ClassifyErrorOutput (nếu error)
  - → BLK-2-10-TransformWeatherData (nếu success)
- **Related Code:**
  - `app/infrastructure/adapters/weather_adapter.py` - API error checking




