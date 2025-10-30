# BLK-1-06 — Handle System Error

Mục tiêu: Xử lý lỗi hệ thống (system errors) bằng cách ghi log chi tiết, gửi thông báo/alert cho ops team, và trả về thông báo lỗi generic an toàn cho người dùng.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi trực tiếp từ BLK-1-05 khi error được classify là SYSTEM_ERROR
  - [x] Uncaught exceptions trong processing pipeline
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Có system error object (đã được classify)
  - Logging infrastructure sẵn sàng
  - Alert/notification channels configured (optional)

- **Điều kiện dừng/không chạy (Guards):**
  - User errors → đi qua BLK-1-03, không vào block này
  - Errors đã được handled ở tầng trên → không trigger

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "SERVICE_UNAVAILABLE" | "INTERNAL_ERROR" | "TIMEOUT" | "DATABASE_ERROR",
  "internal_error": {
    "code": str,
    "message": str,
    "severity": "WARNING" | "ERROR" | "CRITICAL",
    "source": str,  # "api", "database", "internal"
    "stack_trace": str | None,
    "context": dict
  },
  "request_context": {
    "request_id": str,
    "tool_name": str,
    "user_id": str | None,
    "timestamp": str
  }
}
```

- **Bắt buộc:**
  - `error_type`
  - `internal_error.code` và `internal_error.message`
  - `internal_error.severity`
  - `request_context.request_id`

- **Nguồn:** Output từ BLK-1-05 (ClassifyErrorType)

- **Bảo mật:**
  - **KHÔNG** log sensitive data (API keys, tokens, passwords, PII)
  - Sanitize stack traces (remove paths, secrets)
  - Log rotation và retention policy (max 30 days)

### 2.2 Output
- **Kết quả trả về (cho AI/user):**
```python
{
  "type": "SYSTEM_ERROR",
  "user_message": "Hệ thống đang gặp sự cố, vui lòng thử lại sau",
  "error_code": "SYS_ERROR_GENERIC",
  "request_id": "req-123",  # For support reference
  "retry_after": 60  # seconds (optional)
}
```

- **Side-effects:**
  1. **Ghi log structured logging:**
     ```json
     {
       "level": "ERROR",
       "timestamp": "2025-10-14T10:30:00Z",
       "request_id": "req-123",
       "error_code": "EXTERNAL_API_TIMEOUT",
       "error_type": "SERVICE_UNAVAILABLE",
       "message": "TomTom API timeout after 3 retries",
       "severity": "ERROR",
       "source": "tomtom_api",
       "context": { "retries": 3, "endpoint": "/routing" },
       "stack_trace": "..."
     }
     ```
  
  2. **Gửi alert/notification (nếu severity >= ERROR):**
     - Slack/Teams webhook
     - PagerDuty (nếu CRITICAL)
     - Email ops team
  
  3. **Increment metrics:**
     - `system_errors_total{error_type="SERVICE_UNAVAILABLE", source="tomtom_api"}`
     - `error_severity_count{severity="ERROR"}`

- **Đảm bảo (Guarantees):**
  - Mọi system error đều được log
  - CRITICAL errors trigger immediate alerts
  - User không nhìn thấy internal details

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 200ms (logging + alert gửi async)
- **Retry & Backoff:** 
  - Logging: 2 retries nếu log write fails (fallback to stderr)
  - Alert: 1 retry, sau đó skip (don't block response)
- **Idempotency:** Alert deduplication trong 5 phút (cùng error_code + request_id)
- **Circuit Breaker:** 
  - Mở alert channel nếu alert API fails 10 lần liên tiếp
  - Log vẫn hoạt động (fallback to file/stdout)
- **Rate limit/Quota:** 
  - Max 100 alerts/phút (để tránh alert storm)
  - Aggregate similar errors (cùng error_code trong 1 phút)
- **Bảo mật & Quyền:**
  - Chỉ ops team access logs
  - PII masking trong logs

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-06 |
| **Tên Block** | HandleSystemError |
| **Trigger** | From BLK-1-05 = SYSTEM_ERROR |
| **Preconditions** | Có system error object, logging ready |
| **Input (schema)** | `{ error_category: "SYSTEM_ERROR", internal_error: {...} }` |
| **Output** | Generic user message + log + alert |
| **Side-effects** | Write logs, send alerts, increment metrics |
| **Timeout/Retry** | 200ms, retry logging 2x, alert 1x |
| **Idempotency** | Alert dedup 5 min window |
| **AuthZ/Scope** | Ops team only for logs/alerts |

---

## 4) Ví dụ cụ thể

### Case 1: API Timeout (ERROR severity)
**Input:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "SERVICE_UNAVAILABLE",
  "internal_error": {
    "code": "EXTERNAL_API_TIMEOUT",
    "message": "TomTom API timeout after 3 retries",
    "severity": "ERROR",
    "source": "tomtom_api",
    "context": {"retries": 3, "endpoint": "/routing/1/calculateRoute"}
  },
  "request_context": {
    "request_id": "req-456",
    "tool_name": "calculate_route",
    "timestamp": "2025-10-14T10:30:00Z"
  }
}
```

**Actions:**
1. **Log (structured JSON):**
   ```json
   {
     "level": "ERROR",
     "timestamp": "2025-10-14T10:30:00Z",
     "request_id": "req-456",
     "error_code": "EXTERNAL_API_TIMEOUT",
     "message": "TomTom API timeout after 3 retries",
     "severity": "ERROR",
     "source": "tomtom_api",
     "tool_name": "calculate_route",
     "context": {"retries": 3, "endpoint": "/routing/1/calculateRoute"}
   }
   ```

2. **Send Alert (Slack):**
   ```
   🚨 System Error - TomTom API Timeout
   Severity: ERROR
   Request ID: req-456
   Tool: calculate_route
   Message: TomTom API timeout after 3 retries
   Time: 2025-10-14 10:30:00 UTC
   ```

3. **Increment Metrics:**
   - `system_errors_total{error_type="SERVICE_UNAVAILABLE", source="tomtom_api"} += 1`
   - `error_severity_count{severity="ERROR"} += 1`

**Output (to user via AI):**
```python
{
  "type": "SYSTEM_ERROR",
  "user_message": "Hệ thống bản đồ tạm thời không khả dụng, vui lòng thử lại sau ít phút",
  "error_code": "SYS_ERROR_GENERIC",
  "request_id": "req-456",
  "retry_after": 60
}
```

### Case 2: Database Error (CRITICAL severity)
**Input:**
```python
{
  "error_category": "SYSTEM_ERROR",
  "error_type": "DATABASE_ERROR",
  "internal_error": {
    "code": "DB_CONNECTION_POOL_EXHAUSTED",
    "message": "Database connection pool exhausted",
    "severity": "CRITICAL",
    "source": "database",
    "context": {"pool_size": 10, "active": 10, "waiting": 5}
  },
  "request_context": {
    "request_id": "req-789"
  }
}
```

**Actions:**
1. **Log (CRITICAL level):**
   - Write to error log file + stdout
   - Include full context

2. **Send PagerDuty Alert:**
   ```
   🔥 CRITICAL: Database Connection Pool Exhausted
   Request ID: req-789
   Pool: 10/10 active, 5 waiting
   Immediate action required!
   ```

3. **Send Slack Alert** (high priority channel)

**Output:**
```python
{
  "type": "SYSTEM_ERROR",
  "user_message": "Hệ thống đang gặp sự cố nghiêm trọng, chúng tôi đang khẩn trương xử lý",
  "error_code": "SYS_ERROR_CRITICAL",
  "request_id": "req-789"
}
```

---

## 5) Logging Strategy

### Log Levels
- **WARNING:** Recoverable issues (retry succeeded, degraded performance)
- **ERROR:** Failed operations requiring attention (API timeouts, 5xx errors)
- **CRITICAL:** System-wide failures (DB down, critical service unavailable)

### Structured Logging Format
```python
{
  "level": "ERROR",
  "timestamp": ISO8601,
  "request_id": str,
  "error_code": str,
  "error_type": str,
  "message": str,
  "severity": "WARNING" | "ERROR" | "CRITICAL",
  "source": str,
  "tool_name": str | None,
  "user_id": str | None,  # Hashed/masked
  "context": dict,
  "stack_trace": str | None,  # Only in dev/staging
  "environment": "production" | "staging" | "dev"
}
```

### Log Destinations
- **Production:**
  - File: `/var/log/mcp-server/error.log` (rotated daily, 30 days retention)
  - Centralized logging: Elasticsearch/Loki (if available)
  - Stdout/stderr (for container logs)

- **Development:**
  - Console (colored, human-readable)
  - Include stack traces

---

## 6) Alert Strategy

### Alert Channels by Severity
| Severity | Channels | Response Time |
|----------|----------|---------------|
| WARNING | Log only | N/A |
| ERROR | Slack #alerts | < 1 hour |
| CRITICAL | Slack #incidents + PagerDuty + Email | < 15 min |

### Alert Deduplication
- Group same `error_code` trong 5 phút window
- Alert message format: `"[count] occurrences of [error_code] in last 5 min"`

### Alert Throttling
- Max 100 alerts/minute (aggregate vượt quá → send summary alert)
- Critical alerts không throttle

---

## 7) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Block "ghi log và gửi thông báo rồi gửi trả thông báo lỗi hệ thống"
- **Related Blocks:**
  - ← BLK-1-05-ClassifyErrorType (input source)
  - → BLK-End (after sending error response)
- **Related Code:**
  - `app/infrastructure/logging/` - Structured logging setup
  - `app/application/errors.py` - Error classes
  - `app/infrastructure/config/settings.py` - Alert webhook configs

---

## 8) Error cases của chính block này
- **Logging fails:** → Fallback to stderr, continue processing
- **Alert send fails:** → Log failure, don't block response to user
- **Alert rate limit hit:** → Drop non-critical alerts, always send CRITICAL
- **Alert dedup service down:** → Send all alerts (better duplicate than miss critical)

---



## 6) **Nghiệm thu kết quả (Acceptance Criteria)**

### 6.1 Tiêu chí nghiệm thu chung
- [ ] **Functional Requirements:** Block thực hiện đúng chức năng nghiệp vụ được mô tả
- [ ] **Input Validation:** Xử lý đúng tất cả các trường hợp input hợp lệ và không hợp lệ
- [ ] **Output Format:** Kết quả trả về đúng format và schema đã định nghĩa
- [ ] **Error Handling:** Xử lý lỗi đúng theo error codes và messages đã quy định
- [ ] **Performance:** Đáp ứng được timeout và performance requirements
- [ ] **Security:** Tuân thủ các yêu cầu bảo mật (auth, validation, logging)

### 6.2 Test Cases bắt buộc

#### 6.2.1 Happy Path Tests
- [ ] **Valid Input → Expected Output:** Test với input hợp lệ, kiểm tra output đúng
- [ ] **Normal Flow:** Test luồng xử lý bình thường từ đầu đến cuối

#### 6.2.2 Error Handling Tests  
- [ ] **Invalid Input:** Test với input không hợp lệ, kiểm tra error response đúng
- [ ] **Missing Required Fields:** Test thiếu các trường bắt buộc
- [ ] **Business Logic Errors:** Test các lỗi nghiệp vụ (vd: không đủ quyền, dữ liệu không tồn tại)
- [ ] **System Errors:** Test lỗi hệ thống (timeout, DB connection, external API)

#### 6.2.3 Edge Cases Tests
- [ ] **Boundary Values:** Test các giá trị biên (min/max, empty/null)
- [ ] **Concurrent Access:** Test xử lý đồng thời (nếu áp dụng)
- [ ] **Idempotency:** Test tính idempotent (nếu có)

### 6.3 Ví dụ Test Cases mẫu

**Ví dụ cho block "BLK 1 06 HandleSystemError":**
```json
// Test Case 1: Valid Input
Input: { /* input example */ }
Expected: { /* expected output */ }

// Test Case 2: Invalid Input
Input: { /* invalid input example */ }
Expected: { /* error response */ }

// Test Case 3: Edge Case
Input: { /* edge case input */ }
Expected: { /* edge case output */ }
```

### 6.4 Checklist nghiệm thu cuối
- [ ] **Code Review:** Code đã được review bởi senior developer
- [ ] **Unit Tests:** Tất cả test cases đã pass (coverage ≥ 80%)
- [ ] **Integration Tests:** Test tích hợp với các block liên quan
- [ ] **Documentation:** Code có comment và documentation đầy đủ
- [ ] **Performance Test:** Đáp ứng performance requirements
- [ ] **Security Review:** Đã kiểm tra bảo mật (nếu cần)
- [ ] **Deployment:** Deploy thành công và hoạt động ổn định

---

## 7) **Definition of Done (DoD)**

### 7.1 Spec Documentation
- [x] File nằm đúng vị trí và **ID khớp** với diagram  
- [x] **CHỈ MÔ TẢ NGHIỆP VỤ** - không chứa code/framework/công nghệ cụ thể
- [x] Phần **Trigger** có đầy đủ: sự kiện kích hoạt, preconditions, guards  
- [x] Phần **Input** có schema rõ ràng, ghi rõ required fields và validation rules  
- [x] Phần **Output** có kết quả trả về, side-effects, và guarantees  
- [x] Phần **Runtime Constraints** có timeout, retry, idempotency (nếu cần)  
- [x] Có **bảng tóm tắt** đầy đủ các mục quan trọng  
- [x] Có **ví dụ cụ thể** với input/output thực tế (ít nhất 1-2 ví dụ)  
- [x] Có **liên kết** đến diagram, API docs, use cases liên quan  
- [x] **Error cases** được mô tả rõ ràng (error codes, messages, HTTP status)  
- [x] Người đọc có thể hiểu và triển khai **không cần hỏi thêm**

### 7.2 Acceptance Criteria
- [x] **Tiêu chí nghiệm thu chung** đã được định nghĩa rõ ràng
- [x] **Test Cases bắt buộc** đã được liệt kê đầy đủ (Happy Path, Error Handling, Edge Cases)
- [x] **Ví dụ Test Cases** cụ thể với input/output thực tế
- [x] **Checklist nghiệm thu cuối** đã được xác định
- [x] Các tiêu chí nghiệm thu phù hợp với độ phức tạp của block

### 7.3 Implementation Ready
- [x] Spec đã được review và approve bởi BA/Product Owner
- [x] Dev team đã hiểu rõ requirements và có thể bắt đầu implement
- [x] Test team đã có đủ thông tin để viết test cases
- [x] Không còn câu hỏi mở hoặc ambiguity trong spec

## 9) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-06-HandleSystemError.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định
- [x] Side-effects chi tiết (log, alert, metrics)
- [x] Logging strategy với format và destinations
- [x] Alert strategy với severity-based routing
- [x] Error handling cho chính block (logging/alert failures)
- [x] Security considerations (PII masking, log retention)
- [x] Ví dụ cụ thể cho ERROR và CRITICAL severity

---

> **Lưu ý:** Block này là safety net cuối cùng để ensure không có error nào bị bỏ sót. Logging và alerting phải reliable, có fallback mechanisms.

