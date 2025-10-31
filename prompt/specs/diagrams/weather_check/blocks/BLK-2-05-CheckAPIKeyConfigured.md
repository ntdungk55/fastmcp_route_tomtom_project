# BLK-2-05 — Check API Key Configured

Mục tiêu: Kiểm tra xem WeatherAPI.com API key đã được cấu hình trong environment hay chưa.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-2-04 khi đã có coordinates

- **Điều kiện tiền đề (Preconditions):**
  - Coordinates đã sẵn sàng
  - Server đã load environment variables

- **Điều kiện dừng/không chạy (Guards):**
  - Environment variable `WEATHERAPI_API_KEY` không tồn tại → Error `API_KEY_NOT_CONFIGURED`

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
  - Không có input từ block trước (đọc từ environment)
  - Context: Có coordinates sẵn sàng

### 2.2 Output
- **Kết quả trả về (success):**
  - API key hợp lệ (được lưu trong context để dùng cho BLK-2-07)

- **Kết quả trả về (error):**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_NOT_CONFIGURED" | "API_KEY_INVALID",
    "message": "<string>"
  }
}
```

- **API key management:**
  - **Environment variable:** `WEATHERAPI_API_KEY`
  - **Source:** Lấy từ environment variable, KHÔNG từ client request
  - **Security:** KHÔNG log API key (chỉ log 4 ký tự cuối nếu cần debug)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** < 50ms (chỉ đọc env)
- **Retry:** N/A
- **Idempotency:** Yes

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-05 |
| **Tên Block** | CheckAPIKeyConfigured |
| **Trigger** | After BLK-2-04 |
| **Preconditions** | Coordinates ready |
| **Input (schema)** | N/A (read from env) |
| **Output** | `{ success: bool, api_key?, error? }` |
| **Side-effects** | None |
| **Timeout/Retry** | < 50ms, N/A |
| **Idempotency** | Yes |

---

## 4) Ví dụ cụ thể

### Case 1: API Key Configured
**Environment:**
```bash
WEATHERAPI_API_KEY=abc123def456ghi789jkl012
```

**Output:**
```json
{
  "success": true,
  "api_key": "abc123def456ghi789"  // Masked in logs
}
```

**Next:** → BLK-2-07 (Request Weather API)

### Case 2: API Key Not Configured
**Environment:**
```bash
# WEATHERAPI_API_KEY not set
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_NOT_CONFIGURED",
    "message": "WeatherAPI.com API key not found in environment variable WEATHERAPI_API_KEY"
  }
}
```

**Next:** → BLK-2-06 (Handle System Error) → BLK-End

### Case 3: API Key Invalid Format
**Environment:**
```bash
OPENWEATHER_API_KEY="abc"  # Too short
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_INVALID",
    "message": "WeatherAPI.com API key format is invalid"
  }
}
```

**Next:** → BLK-2-06 (Handle System Error)

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - ← BLK-2-04-GetCoordinatesFromAddress
  - → BLK-2-06-HandleSystemError (nếu key không có)
  - → BLK-2-07-RequestWeatherAPI (nếu key có)
- **Related Code:**
  - `app/infrastructure/config/settings.py` - Settings và validation
  - `app/infrastructure/config/api_config.py` - API config service

