# BLK-1-05 — Classify Error Type

Mục tiêu: Phân loại lỗi thành **lỗi hệ thống** (system error) hoặc **lỗi do người dùng** (user error) để định tuyến xử lý phù hợp.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi từ các block xử lý khi phát hiện lỗi (không phải từ BLK-1-02 - validation errors đã được xử lý riêng)
  - [x] Exception/Error được throw trong quá trình xử lý (API call fail, DB error, etc.)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Có error object/exception được catch
  - Error chưa được classify (raw error từ downstream services)

- **Điều kiện dừng/không chạy (Guards):**
  - Validation errors → đã được xử lý ở BLK-1-03, không đi qua block này
  - Không có error → skip

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```python
{
  "error": {
    "type": str,  # Exception class name
    "message": str,
    "code": str | None,  # Error code nếu có
    "status_code": int | None,  # HTTP status nếu từ API
    "source": str,  # "api", "database", "internal", etc.
    "stack_trace": str | None,  # For logging only
    "context": dict  # Additional metadata
  },
  "request_context": {
    "request_id": str,
    "tool_name": str,
    "user_id": str | None
  }
}
```

- **Bắt buộc:**
  - `error.type` hoặc `error.message`
  - `error.source` để biết nguồn gốc lỗi

- **Nguồn:** 
  - Exception handlers trong use cases
  - API error responses (TomTom, geocoding)
  - Database errors

- **Bảo mật:**
  - Không log stack_trace với sensitive data
  - Sanitize error messages trước khi trả về user

### 2.2 Output
- **Kết quả trả về:**
  - **Case 1 (User Error):**
    ```python
    {
      "error_category": "USER_ERROR",
      "error_type": "INVALID_INPUT" | "RESOURCE_NOT_FOUND" | "PERMISSION_DENIED",
      "user_facing_error": {
        "code": "...",
        "message": "...",
        "hint": "..."
      }
    }
    ```
    → Forward to **BLK-1-03** (Map to user message)
  
  - **Case 2 (System Error):**
    ```python
    {
      "error_category": "SYSTEM_ERROR",
      "error_type": "SERVICE_UNAVAILABLE" | "INTERNAL_ERROR" | "TIMEOUT",
      "internal_error": {
        "code": "...",
        "message": "...",
        "severity": "ERROR" | "CRITICAL"
      }
    }
    ```
    → Forward to **BLK-1-06** (Handle system error - log & notify)

- **Side-effects:**
  - Log classification decision
  - Increment error metrics (user_errors_count, system_errors_count)

- **Đảm bảo (Guarantees):**
  - Mọi error đều được classify vào một trong hai categories
  - Không lộ internal details trong user-facing errors

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** < 5ms (pure logic)
- **Retry & Backoff:** Không áp dụng
- **Idempotency:** Yes (deterministic classification)
- **Circuit Breaker:** Không áp dụng
- **Rate limit/Quota:** Không áp dụng
- **Bảo mật & Quyền:**
  - Không trả về stack traces cho user errors
  - Mask sensitive info trong error messages

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-05 |
| **Tên Block** | ClassifyErrorType |
| **Trigger** | Exception/Error caught trong processing pipeline |
| **Preconditions** | Có error object chưa được classify |
| **Input (schema)** | `{ error: { type, message, code, source, ... }, context }` |
| **Output** | `{ error_category: "USER_ERROR" | "SYSTEM_ERROR", ... }` |
| **Side-effects** | Log classification, increment metrics |
| **Timeout/Retry** | < 5ms, no retry |
| **Idempotency** | Yes |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

### Case 1: User Error (API returned 400/404)
**Input:**
```python
{
  "error": {
    "type": "TomTomAPIError",
    "message": "Invalid coordinates format",
    "code": "MALFORMED_REQUEST",
    "status_code": 400,
    "source": "tomtom_api",
    "context": {"endpoint": "/routing/1/calculateRoute"}
  },
  "request_context": {
    "request_id": "req-123",
    "tool_name": "calculate_route"
  }
}
```

**Classification Logic:**
- `status_code = 400` → Client error → **USER_ERROR**
- `code = MALFORMED_REQUEST` → Invalid input

**Output:**
```python
{
  "error_category": "USER_ERROR",
  "error_type": "INVALID_INPUT",
  "user_facing_error": {
    "code": "INVALID_COORDINATES",
    "message": "Định dạng toạ độ không hợp lệ",
    "hint": "Vui lòng kiểm tra lại toạ độ (lat, lon)"
  }
}
```
**Next:** → BLK-1-03 (Map to user message)

### Case 2: System Error (API timeout)
**Input:**
```python
{
  "error": {
    "type": "RequestTimeout",
    "message": "TomTom API request timeout after 30s",
    "code": "TIMEOUT",
    "status_code": 504,
    "source": "tomtom_api",
    "context": {"retry_count": 3}
  },
  "request_context": {
    "request_id": "req-456"
  }
}
```

**Classification Logic:**
- `type = RequestTimeout` → Infrastructure issue → **SYSTEM_ERROR**
- `status_code = 504` → Gateway timeout

**Output:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "SERVICE_UNAVAILABLE",
  "internal_error": {
    "code": "EXTERNAL_API_TIMEOUT",
    "message": "TomTom API timeout after 3 retries",
    "severity": "ERROR",
    "context": {"service": "tomtom", "retries": 3}
  }
}
```
**Next:** → BLK-1-06 (Log, notify, return generic error to user)

### Case 3: System Error (Database error)
**Input:**
```python
{
  "error": {
    "type": "DatabaseConnectionError",
    "message": "Connection pool exhausted",
    "code": None,
    "status_code": None,
    "source": "database",
    "context": {"pool_size": 10, "active": 10}
  },
  "request_context": {
    "request_id": "req-789"
  }
}
```

**Output:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "INTERNAL_ERROR",
  "internal_error": {
    "code": "DB_CONNECTION_POOL_EXHAUSTED",
    "message": "Database connection pool exhausted",
    "severity": "CRITICAL"
  }
}
```
**Next:** → BLK-1-06 (Critical alert to ops team)

---

## 5) Classification Rules

### User Errors (forward to BLK-1-03)
- HTTP 4xx status codes (400, 404, 403, 422)
- Validation errors (already handled, but listed for completeness)
- `MALFORMED_REQUEST`, `INVALID_PARAMETER`, `RESOURCE_NOT_FOUND`
- Business rule violations (e.g., "route too long")
- Rate limit exceeded (429) - debatable, could be system

### System Errors (forward to BLK-1-06)
- HTTP 5xx status codes (500, 502, 503, 504)
- Timeouts, connection errors
- Database errors (connection, query failures)
- Internal exceptions (KeyError, AttributeError, etc.)
- Third-party service unavailable
- `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`, `TIMEOUT`

### Edge Cases
- **429 Rate Limit:** Classify as SYSTEM_ERROR nếu từ external API (TomTom quota), USER_ERROR nếu từ internal rate limit per user
- **Unknown errors:** Default to SYSTEM_ERROR để an toàn (không lộ internal info)

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Decision "Lỗi hệ thống hoặc do người dùng?"
- **Related Blocks:**
  - → BLK-1-03-MapValidationErrorsToUserMessages (user error path)
  - → BLK-1-06-HandleSystemError (system error path)
- **Related Code:**
  - `app/application/errors.py` - Error classes
  - `app/domain/errors.py` - Domain exceptions
  - `app/infrastructure/http/exceptions.py` - HTTP error handling

---

## 7) Error cases của chính block này
- **Null/undefined error object:** → Default to SYSTEM_ERROR với code "UNKNOWN_ERROR"
- **Classification logic fails:** → SYSTEM_ERROR (fail-safe)

---

## 8) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-05-ClassifyErrorType.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với 2 categories
- [x] Có classification rules chi tiết
- [x] Có ví dụ cụ thể cho cả user error và system error
- [x] Error handling cho edge cases
- [x] Liên kết đến downstream blocks và error code

---

> **Lưu ý:** Classification chính xác rất quan trọng để user experience tốt (user errors → actionable messages) và ops visibility (system errors → alerts).

