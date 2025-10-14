# BLK-1-11 — Classify And Format Error Output

Mục tiêu: Phân loại lỗi từ API response (BLK-1-10 failed path) và format thành output phù hợp để gửi cho AI thông báo người dùng.

**Lưu ý:** Block này tương tự BLK-1-05 (ClassifyErrorType) nhưng specialized cho API errors. Trong thực tế có thể merge vào BLK-1-05 hoặc giữ riêng tuỳ design.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi từ BLK-1-10 khi `api_success = False`
  - [x] Chuyên xử lý errors từ external API (TomTom routing)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Có API error object từ BLK-1-10
  - Error chưa được format cho user

- **Điều kiện dừng/không chạy (Guards):**
  - API success → không chạy block này
  - Validation errors (đã qua BLK-1-03) → không qua đây

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:** Error object từ BLK-1-10
```python
{
  "api_success": False,
  "error": {
    "code": str,  # API error code
    "message": str,  # Raw API error message
    "status_code": int,  # HTTP status
    "retry_after": int | None
  },
  "metadata": {
    "provider": str,  # "tomtom"
    "request_id": str,
    "request_duration_ms": int
  }
}
```

- **Bắt buộc:**
  - `error.code` hoặc `error.status_code`
  - `error.message`

- **Nguồn:** BLK-1-10 (CheckAPISuccess - failed path)

- **Bảo mật:**
  - Không lộ internal API details (keys, endpoints)
  - Sanitize error messages

### 2.2 Output
- **Kết quả trả về:**

**Case 1: User Error (4xx):**
```python
{
  "error_category": "USER_ERROR",
  "error_type": "INVALID_INPUT" | "RESOURCE_NOT_FOUND",
  "user_facing_error": {
    "type": "API_CLIENT_ERROR",
    "code": "INVALID_ROUTE_PARAMS",
    "message": "Không thể tính toán tuyến đường với thông tin đã cung cấp",
    "hint": "Vui lòng kiểm tra lại điểm xuất phát và điểm đến",
    "details": {
      "original_error": "Invalid coordinates format"  # Optional, sanitized
    }
  }
}
```

**Case 2: System Error (5xx, timeouts):**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "SERVICE_UNAVAILABLE" | "TIMEOUT",
  "internal_error": {
    "code": "EXTERNAL_API_ERROR",
    "message": "TomTom routing API unavailable",
    "severity": "ERROR",
    "retry_after": 60,
    "context": {
      "provider": "tomtom",
      "status_code": 503
    }
  },
  "user_facing_error": {
    "type": "SYSTEM_ERROR",
    "code": "SERVICE_TEMPORARILY_UNAVAILABLE",
    "message": "Dịch vụ bản đồ tạm thời không khả dụng",
    "hint": "Vui lòng thử lại sau ít phút",
    "retry_after": 60
  }
}
```

- **Side-effects:**
  - Log classification
  - Increment error category metrics

- **Đảm bảo (Guarantees):**
  - Mọi API error đều được classify
  - User-facing messages không lộ internal details

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** < 5ms (pure logic)
- **Retry & Backoff:** Không áp dụng
- **Idempotency:** Yes (deterministic mapping)
- **Circuit Breaker:** Không áp dụng
- **Rate limit/Quota:** Không áp dụng
- **Bảo mật & Quyền:** N/A

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-11 |
| **Tên Block** | ClassifyAndFormatErrorOutput |
| **Trigger** | From BLK-1-10 = api_success: False |
| **Preconditions** | Có API error object |
| **Input (schema)** | `{ error: { code, message, status_code, ... } }` |
| **Output** | `{ error_category, user_facing_error, internal_error? }` |
| **Side-effects** | Log classification, metrics |
| **Timeout/Retry** | < 5ms, no retry |
| **Idempotency** | Yes |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

### Case 1: Client Error (400 - Invalid coordinates)
**Input:**
```python
{
  "api_success": False,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid coordinates format",
    "status_code": 400,
    "retry_after": None
  },
  "metadata": {
    "provider": "tomtom",
    "request_id": "req-456"
  }
}
```

**Classification:**
- `status_code = 400` → Client error → **USER_ERROR**

**Output:**
```python
{
  "error_category": "USER_ERROR",
  "error_type": "INVALID_INPUT",
  "user_facing_error": {
    "type": "API_CLIENT_ERROR",
    "code": "INVALID_ROUTE_PARAMS",
    "message": "Định dạng toạ độ không hợp lệ",
    "hint": "Vui lòng kiểm tra lại toạ độ điểm xuất phát và điểm đến (định dạng: lat, lon)",
    "details": {}
  }
}
```

**Next:** → Return to user via AI (formatted message)

---

### Case 2: Not Found (404 - No route found)
**Input:**
```python
{
  "api_success": False,
  "error": {
    "code": "NO_ROUTE_FOUND",
    "message": "No route could be found between the origin and destination",
    "status_code": 404,
    "retry_after": None
  },
  "metadata": {
    "provider": "tomtom",
    "request_id": "req-789"
  }
}
```

**Output:**
```python
{
  "error_category": "USER_ERROR",
  "error_type": "RESOURCE_NOT_FOUND",
  "user_facing_error": {
    "type": "NO_ROUTE_AVAILABLE",
    "code": "NO_ROUTE_FOUND",
    "message": "Không tìm thấy tuyến đường giữa hai điểm này",
    "hint": "Hai điểm có thể không kết nối được bằng đường bộ. Hãy thử điểm đến khác hoặc phương tiện di chuyển khác.",
    "details": {}
  }
}
```

---

### Case 3: Server Error (503 - Service Unavailable)
**Input:**
```python
{
  "api_success": False,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "The routing service is temporarily unavailable",
    "status_code": 503,
    "retry_after": 60
  },
  "metadata": {
    "provider": "tomtom",
    "request_id": "req-101"
  }
}
```

**Classification:**
- `status_code = 503` → Server error → **SYSTEM_ERROR**

**Output:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "SERVICE_UNAVAILABLE",
  "internal_error": {
    "code": "EXTERNAL_API_UNAVAILABLE",
    "message": "TomTom routing service unavailable (503)",
    "severity": "ERROR",
    "context": {
      "provider": "tomtom",
      "status_code": 503,
      "retry_after": 60
    }
  },
  "user_facing_error": {
    "type": "SYSTEM_ERROR",
    "code": "SERVICE_TEMPORARILY_UNAVAILABLE",
    "message": "Dịch vụ tính toán tuyến đường tạm thời không khả dụng",
    "hint": "Vui lòng thử lại sau 1 phút",
    "retry_after": 60
  }
}
```

**Next:** 
- Internal error → BLK-1-06 (HandleSystemError - log & alert)
- User error → Return to user

---

### Case 4: Timeout (no status code)
**Input:**
```python
{
  "api_success": False,
  "error": {
    "code": "TIMEOUT",
    "message": "Request timeout after 10s",
    "status_code": 0,  # No HTTP response
    "retry_after": None
  },
  "metadata": {
    "provider": "tomtom",
    "request_id": "req-202",
    "request_duration_ms": 10000
  }
}
```

**Output:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "TIMEOUT",
  "internal_error": {
    "code": "EXTERNAL_API_TIMEOUT",
    "message": "TomTom API timeout after 10s",
    "severity": "ERROR",
    "context": {"duration_ms": 10000}
  },
  "user_facing_error": {
    "type": "SYSTEM_ERROR",
    "code": "REQUEST_TIMEOUT",
    "message": "Yêu cầu mất quá nhiều thời gian",
    "hint": "Vui lòng thử lại hoặc chọn tuyến đường ngắn hơn"
  }
}
```

---

## 5) Classification Rules (API Errors)

### User Errors → USER_ERROR
| HTTP Status | API Error Code | User Message | Hint |
|-------------|----------------|--------------|------|
| 400 | INVALID_REQUEST | Thông tin tuyến đường không hợp lệ | Kiểm tra lại toạ độ/địa chỉ |
| 400 | INVALID_COORDINATES | Định dạng toạ độ không đúng | Định dạng: lat, lon |
| 404 | NO_ROUTE_FOUND | Không tìm thấy tuyến đường | Thử điểm khác hoặc phương tiện khác |
| 403 | FORBIDDEN | Không có quyền truy cập | Liên hệ admin |
| 422 | UNPROCESSABLE_ENTITY | Dữ liệu không xử lý được | Kiểm tra lại tham số |

### System Errors → SYSTEM_ERROR
| HTTP Status | API Error Code | Internal Message | User Message |
|-------------|----------------|------------------|--------------|
| 500 | INTERNAL_ERROR | API internal error | Hệ thống gặp sự cố |
| 502 | BAD_GATEWAY | API gateway error | Dịch vụ tạm thời không khả dụng |
| 503 | SERVICE_UNAVAILABLE | API service down | Vui lòng thử lại sau |
| 504 | GATEWAY_TIMEOUT | API gateway timeout | Yêu cầu quá lâu, thử lại |
| 0 | TIMEOUT | Request timeout | Yêu cầu mất quá nhiều thời gian |
| 429 | RATE_LIMIT | API quota exceeded | Dịch vụ tạm thời quá tải |

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Block "phân loại và xử lý output trả dữ liệu phù hợp cho AI"
- **Related Blocks:**
  - ← BLK-1-10-CheckAPISuccess (trigger khi API fail)
  - → BLK-1-06-HandleSystemError (nếu SYSTEM_ERROR)
  - → Return to user (nếu USER_ERROR)
  - (Alternative: merge với BLK-1-05-ClassifyErrorType)
- **Related Code:**
  - `app/application/errors.py` - Error mapping
  - `app/infrastructure/tomtom/error_mapper.py` - TomTom specific error mapping

---

## 7) Error cases của chính block này
- **Unknown API error code:** → Default to SYSTEM_ERROR với generic message
- **Null error object:** → Log critical error, return generic SYSTEM_ERROR

---

## 8) Localization Support
- Hỗ trợ đa ngôn ngữ (vi, en) dựa trên `locale` trong request context
- Error message mapping có thể dùng i18n file:
  ```json
  {
    "vi": {
      "INVALID_COORDINATES": "Định dạng toạ độ không hợp lệ",
      "NO_ROUTE_FOUND": "Không tìm thấy tuyến đường",
      "SERVICE_UNAVAILABLE": "Dịch vụ tạm thời không khả dụng"
    },
    "en": {
      "INVALID_COORDINATES": "Invalid coordinates format",
      "NO_ROUTE_FOUND": "No route found",
      "SERVICE_UNAVAILABLE": "Service temporarily unavailable"
    }
  }
  ```

---

## 9) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-11-ClassifyAndFormatErrorOutput.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định cho USER_ERROR và SYSTEM_ERROR
- [x] Classification rules table (HTTP status → error category)
- [x] Ví dụ cụ thể cho 400, 404, 503, timeout
- [x] User-facing messages không lộ internal details
- [x] Localization support notes
- [x] Liên kết đến error handling blocks

---

> **Lưu ý:** Block này có thể merge vào BLK-1-05 (ClassifyErrorType) nếu muốn centralize error classification. Giữ riêng nếu API errors cần logic mapping phức tạp hơn.

