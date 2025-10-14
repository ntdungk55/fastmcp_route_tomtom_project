# BLK-1-07 — Save Request History

Mục tiêu: Lưu lại lịch sử request vào database để audit, analytics, và debugging. Block này chạy song song (async) với main processing flow.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi song song (async/background task) ngay sau BLK-1-00 (nhận request)
  - [x] Có thể trigger từ nhiều điểm trong flow để update status
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Có request_id và basic request metadata
  - Database connection sẵn sàng
  - Request logging enabled (feature flag)

- **Điều kiện dừng/không chạy (Guards):**
  - Request logging disabled (config/feature flag) → skip
  - Database unavailable → log warning, skip (don't block main flow)
  - Anonymous/health check requests → có thể skip tùy policy

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```python
{
  "request_id": str,
  "tool_name": str,
  "arguments": dict,  # Sanitized input arguments
  "request_context": {
    "user_id": str | None,
    "session_id": str,
    "client_id": str,  # MCP client identifier
    "timestamp": str,  # ISO8601
    "ip_address": str | None  # If available
  },
  "status": "RECEIVED" | "PROCESSING" | "SUCCESS" | "ERROR",
  "metadata": dict  # Additional tracking info
}
```

- **Bắt buộc:**
  - `request_id` (unique, indexed)
  - `tool_name`
  - `timestamp`
  - `status`

- **Nguồn:** 
  - Initial call: từ BLK-1-00 (ListenMCPRequest)
  - Updates: từ BLK-1-12 (UpdateRequestResult) khi có kết quả

- **Bảo mật:**
  - **Sanitize arguments:** Remove sensitive data (API keys, full addresses nếu là PII)
  - **Hash user_id** nếu có privacy policy requirement
  - **Không lưu** raw coordinates nếu là sensitive location data
  - Tuân thủ GDPR/data retention policies

### 2.2 Output
- **Kết quả trả về:**
  - Database record ID (UUID)
  - Success/failure status (cho logging)

- **Side-effects:**
  - **INSERT** vào bảng `request_history`:
    ```sql
    CREATE TABLE request_history (
      id UUID PRIMARY KEY,
      request_id TEXT UNIQUE NOT NULL,
      tool_name TEXT NOT NULL,
      arguments JSONB,
      user_id TEXT,
      session_id TEXT,
      client_id TEXT,
      status TEXT NOT NULL,
      created_at TIMESTAMP NOT NULL,
      updated_at TIMESTAMP,
      completed_at TIMESTAMP,
      duration_ms INTEGER,
      error_code TEXT,
      metadata JSONB
    );
    ```
  
  - **Indexes:**
    - `request_id` (unique)
    - `user_id, created_at` (for user history queries)
    - `tool_name, status` (for analytics)
    - `created_at` (for time-based queries)

- **Đảm bảo (Guarantees):**
  - Best-effort persistence (async, không block main flow)
  - At-least-once semantics (có thể retry nếu fail)
  - No data loss nếu DB available

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 500ms (DB insert)
- **Retry & Backoff:** 
  - 2 retries, exponential backoff (100ms, 200ms)
  - Sau đó log error và skip (don't block response)
- **Idempotency:** 
  - `request_id` UNIQUE constraint → duplicate inserts fail silently
  - Updates by `request_id` (idempotent)
- **Circuit Breaker:** 
  - Mở sau 10 DB errors liên tiếp trong 30s
  - Auto-close sau 60s recovery period
- **Rate limit/Quota:** Không áp dụng (internal operation)
- **Bảo mật & Quyền:**
  - Write-only access cho application
  - Read access restricted to analytics/ops

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-07 |
| **Tên Block** | SaveRequestHistory |
| **Trigger** | Async sau BLK-1-00, hoặc từ BLK-1-12 (update) |
| **Preconditions** | DB available, logging enabled |
| **Input (schema)** | `{ request_id, tool_name, arguments, status, context }` |
| **Output** | DB record ID |
| **Side-effects** | INSERT/UPDATE request_history table |
| **Timeout/Retry** | 500ms, 2 retries với backoff |
| **Idempotency** | Yes (request_id unique constraint) |
| **AuthZ/Scope** | Write-only for app, read for analytics |

---

## 4) Ví dụ cụ thể

### Case 1: Initial request save
**Input (từ BLK-1-00):**
```python
{
  "request_id": "req-123",
  "tool_name": "calculate_route",
  "arguments": {
    "origin": "Hanoi",  # Sanitized (removed full address if PII)
    "destination": "Ho Chi Minh City",
    "travelMode": "car"
  },
  "request_context": {
    "user_id": "user-456",
    "session_id": "session-789",
    "client_id": "claude-desktop",
    "timestamp": "2025-10-14T10:30:00Z"
  },
  "status": "RECEIVED",
  "metadata": {}
}
```

**DB Operation:**
```sql
INSERT INTO request_history (
  id, request_id, tool_name, arguments, user_id, session_id, 
  client_id, status, created_at, metadata
) VALUES (
  'uuid-abc', 'req-123', 'calculate_route', 
  '{"origin": "Hanoi", "destination": "Ho Chi Minh City", "travelMode": "car"}',
  'user-456', 'session-789', 'claude-desktop', 
  'RECEIVED', '2025-10-14T10:30:00Z', '{}'
);
```

**Output:**
```python
{
  "record_id": "uuid-abc",
  "status": "saved"
}
```

### Case 2: Update request status (từ BLK-1-12)
**Input:**
```python
{
  "request_id": "req-123",
  "status": "SUCCESS",
  "completed_at": "2025-10-14T10:30:15Z",
  "duration_ms": 15000,
  "metadata": {
    "route_distance_km": 1730,
    "route_duration_min": 1200
  }
}
```

**DB Operation:**
```sql
UPDATE request_history 
SET status = 'SUCCESS',
    completed_at = '2025-10-14T10:30:15Z',
    updated_at = '2025-10-14T10:30:15Z',
    duration_ms = 15000,
    metadata = '{"route_distance_km": 1730, "route_duration_min": 1200}'
WHERE request_id = 'req-123';
```

### Case 3: Error case save
**Input:**
```python
{
  "request_id": "req-456",
  "status": "ERROR",
  "error_code": "EXTERNAL_API_TIMEOUT",
  "completed_at": "2025-10-14T10:35:00Z",
  "duration_ms": 30000
}
```

**DB Operation:**
```sql
UPDATE request_history 
SET status = 'ERROR',
    error_code = 'EXTERNAL_API_TIMEOUT',
    completed_at = '2025-10-14T10:35:00Z',
    duration_ms = 30000
WHERE request_id = 'req-456';
```

---

## 5) Analytics & Retention

### Use Cases
1. **User analytics:** Most used tools per user
2. **Performance monitoring:** Average duration by tool
3. **Error tracking:** Error rate trends
4. **Usage patterns:** Peak hours, popular routes
5. **Audit trail:** Request history for compliance

### Common Queries
```sql
-- Error rate by tool (last 24h)
SELECT tool_name, 
       COUNT(*) as total,
       COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
       ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'ERROR') / COUNT(*), 2) as error_rate_pct
FROM request_history
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY tool_name
ORDER BY error_rate_pct DESC;

-- Average duration by tool
SELECT tool_name,
       AVG(duration_ms) as avg_duration_ms,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms
FROM request_history
WHERE status = 'SUCCESS' AND created_at > NOW() - INTERVAL '7 days'
GROUP BY tool_name;

-- User request history
SELECT request_id, tool_name, status, created_at, duration_ms
FROM request_history
WHERE user_id = 'user-456'
ORDER BY created_at DESC
LIMIT 50;
```

### Data Retention Policy
- **Hot storage:** Last 30 days (full access)
- **Warm storage:** 31-90 days (compressed, slower access)
- **Cold storage/archive:** 91-365 days (if compliance requires)
- **Deletion:** After 365 days (or per GDPR data subject request)

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Database icon "lưu lịch sử request"
- **Related Blocks:**
  - ← BLK-1-00-ListenMCPRequest (initial save)
  - ← BLK-1-12-UpdateRequestResult (status updates)
- **Related Code:**
  - `app/infrastructure/persistence/sqlite_destination_repository.py` (extend for request_history)
  - `destinations.db` - Current database (add request_history table)

---

## 7) Error cases
- **DB insert fails:** → Retry 2 lần, log error, continue (don't block)
- **Duplicate request_id:** → Ignore (idempotent), log warning
- **DB connection timeout:** → Open circuit breaker, skip logging temporarily
- **Invalid data schema:** → Log error with sanitized data, skip insert

---

## 8) Privacy & Compliance

### PII Handling
- **Hash user_id** if required (or use pseudonymous IDs)
- **Sanitize addresses:** Keep only city/country if full address is PII
- **Don't store:** Exact GPS coordinates for user locations (if sensitive)
- **Encrypt at rest:** Database encryption if storing any sensitive metadata

### GDPR Compliance
- **Right to erasure:** Implement soft-delete or hard-delete by user_id
- **Data export:** Support query by user_id for data export
- **Consent tracking:** Store consent_version in metadata if applicable

---

## 9) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-07-SaveRequestHistory.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với INSERT và UPDATE cases
- [x] DB schema và indexes
- [x] Ràng buộc runtime (timeout, retry, circuit breaker)
- [x] Analytics use cases và example queries
- [x] Data retention policy
- [x] Privacy & compliance considerations
- [x] Error handling (best-effort, không block main flow)

---

> **Lưu ý:** Block này chạy async/background để không impact latency của main request flow. DB failures không được block response trả về user.

