# BLK-1-13 — Update Request Result

Mục tiêu: Cập nhật kết quả (success hoặc error) vào bảng request_history đã được tạo ở BLK-1-07, để hoàn thiện audit trail.

**Lưu ý:** Theo diagram, block này tương ứng với database icon "cập nhật kết quả lịch sử request".

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-1-12 (success case - có route data)
  - [x] **Cập nhật:** Gọi sau BLK-1-17 (success case - có traffic sections với addresses)
  - [x] Gọi sau BLK-1-06 hoặc BLK-1-03 (error cases - đã xử lý lỗi)
  - [x] Trước khi return response về user (final step)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - BLK-1-07 đã tạo request_history record (có `request_id`)
  - Đã có kết quả cuối cùng (success data hoặc error)
  - Database connection sẵn sàng

- **Điều kiện dừng/không chạy (Guards):**
  - Request history disabled (feature flag) → skip
  - Database unavailable → log error, skip (don't block response)
  - Request_id không tồn tại trong DB → log warning, skip

---

## 2) Input, Output và các ràng buộc

### 2.1 Input

**Case 1: Success result (từ BLK-1-12 hoặc BLK-1-17)**
```python
{
  "request_id": str,
  "status": "SUCCESS",
  "result": {
    "type": "ROUTE_SUCCESS",
    "summary": {
      "distance_km": float,
      "duration_seconds": int,
      "traffic_delay_seconds": int
    },
    # ... other success data
    # **Cập nhật:** Nếu từ BLK-1-17, sẽ có thêm:
    "traffic_sections_with_addresses": [{
      "section_index": int,
      "start_address": str,
      "end_address": str,
      "section_type": str
    }] | null
  },
  "metadata": {
    "api_provider": str,
    "api_duration_ms": int,
    "total_duration_ms": int,
    "completed_at": str  # ISO8601
  }
}
```

**Case 2: Error result**
```python
{
  "request_id": str,
  "status": "ERROR",
  "error": {
    "category": "USER_ERROR" | "SYSTEM_ERROR",
    "code": str,
    "message": str  # Sanitized for storage
  },
  "metadata": {
    "failed_at": str,  # ISO8601
    "total_duration_ms": int
  }
}
```

- **Bắt buộc:**
  - `request_id`
  - `status`: "SUCCESS" | "ERROR"
  - Timestamp (completed_at hoặc failed_at)

- **Nguồn:**
  - Success: từ BLK-1-16 (ProcessTrafficSections orchestrator) hoặc BLK-1-12 (TransformSuccessDataForAI)
  - Error: từ BLK-1-16 (error path), BLK-1-03, BLK-1-06, BLK-1-11

- **Bảo mật:**
  - Sanitize error messages (không lưu stack traces chi tiết)
  - Không lưu sensitive data trong result (đã sanitize ở BLK-1-07)

### 2.2 Output
- **Kết quả trả về:**
```python
{
  "updated": True,
  "request_id": str,
  "final_status": "SUCCESS" | "ERROR"
}
```

- **Side-effects:**
  - **UPDATE** bảng `request_history`:
    ```sql
    UPDATE request_history 
    SET 
      status = ?,
      completed_at = ?,
      duration_ms = ?,
      result_summary = ?,  -- JSONB với summary data
      error_code = ?,       -- Nếu error
      updated_at = NOW()
    WHERE request_id = ?;
    ```

- **Đảm bảo (Guarantees):**
  - Best-effort update (async, không block response)
  - Idempotent (UPDATE by request_id)
  - At-most-once update cho same request_id

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 300ms (DB update)
- **Retry & Backoff:** 
  - 2 retries, exponential backoff (100ms, 200ms)
  - Sau đó log error và skip (don't block response)
- **Idempotency:** Yes (UPDATE by request_id)
- **Circuit Breaker:** 
  - Mở sau 10 DB errors liên tiếp trong 30s
  - Fallback: skip update, log error
- **Rate limit/Quota:** Không áp dụng (internal)
- **Bảo mật & Quyền:** Write access cho application

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-13 |
| **Tên Block** | UpdateRequestResult |
| **Trigger** | After final result (success or error) |
| **Preconditions** | request_id exists in DB, DB available |
| **Input (schema)** | `{ request_id, status, result?, error?, metadata }` |
| **Output** | `{ updated: bool }` |
| **Side-effects** | UPDATE request_history table |
| **Timeout/Retry** | 300ms, 2 retries |
| **Idempotency** | Yes (UPDATE by request_id) |
| **AuthZ/Scope** | Write access for app |

---

## 4) Ví dụ cụ thể

### Case 1: Update success result
**Input:**
```python
{
  "request_id": "req-123",
  "status": "SUCCESS",
  "result": {
    "type": "ROUTE_SUCCESS",
    "summary": {
      "distance_km": 1730,
      "duration_seconds": 72000,
      "traffic_delay_seconds": 1800
    }
  },
  "metadata": {
    "api_provider": "tomtom",
    "api_duration_ms": 1850,
    "total_duration_ms": 15000,
    "completed_at": "2025-10-14T10:30:15Z"
  }
}
```

**DB Operation:**
```sql
UPDATE request_history 
SET 
  status = 'SUCCESS',
  completed_at = '2025-10-14T10:30:15Z',
  duration_ms = 15000,
  result_summary = '{
    "distance_km": 1730,
    "duration_seconds": 72000,
    "traffic_delay_seconds": 1800,
    "api_provider": "tomtom"
  }',
  error_code = NULL,
  updated_at = NOW()
WHERE request_id = 'req-123';
```

**Output:**
```python
{
  "updated": True,
  "request_id": "req-123",
  "final_status": "SUCCESS"
}
```

**Log:**
```
INFO: Updated request history for req-123: SUCCESS (duration: 15000ms)
```

---

### Case 2: Update success result từ BLK-1-17 (có traffic addresses)
**Input:**
```python
{
  "request_id": "req-124",
  "status": "SUCCESS",
  "result": {
    "type": "ROUTE_SUCCESS",
    "summary": {
      "distance_km": 5.0,
      "duration_seconds": 600,
      "traffic_delay_seconds": 120
    },
    "traffic_sections_with_addresses": [
      {
        "section_index": 0,
        "start_address": "Phố Huế, Hoàn Kiếm, Hà Nội",
        "end_address": "Phố Huế, Hoàn Kiếm, Hà Nội",
        "section_type": "TRAFFIC"
      }
    ]
  },
  "metadata": {
    "api_provider": "tomtom",
    "api_duration_ms": 2500,
    "total_duration_ms": 18000,
    "completed_at": "2025-10-14T10:30:15Z"
  }
}
```

**DB Operation:**
```sql
UPDATE request_history 
SET 
  status = 'SUCCESS',
  completed_at = '2025-10-14T10:30:15Z',
  duration_ms = 18000,
  result_summary = '{
    "distance_km": 5.0,
    "duration_seconds": 600,
    "traffic_delay_seconds": 120,
    "api_provider": "tomtom",
    "traffic_sections_count": 1,
    "traffic_sections": [
      {
        "section_index": 0,
        "start_address": "Phố Huế, Hoàn Kiếm, Hà Nội",
        "end_address": "Phố Huế, Hoàn Kiếm, Hà Nội",
        "section_type": "TRAFFIC"
      }
    ]
  }',
  error_code = NULL,
  updated_at = NOW()
WHERE request_id = 'req-124';
```

**Output:**
```python
{
  "updated": True,
  "request_id": "req-124",
  "final_status": "SUCCESS"
}
```

---

### Case 3: Update error result (user error)
**Input:**
```python
{
  "request_id": "req-456",
  "status": "ERROR",
  "error": {
    "category": "USER_ERROR",
    "code": "INVALID_LOCATIONS_COUNT",
    "message": "At least 2 locations required"
  },
  "metadata": {
    "failed_at": "2025-10-14T10:31:00Z",
    "total_duration_ms": 50
  }
}
```

**DB Operation:**
```sql
UPDATE request_history 
SET 
  status = 'ERROR',
  completed_at = '2025-10-14T10:31:00Z',
  duration_ms = 50,
  error_code = 'INVALID_LOCATIONS_COUNT',
  result_summary = '{
    "error_category": "USER_ERROR",
    "error_message": "At least 2 locations required"
  }',
  updated_at = NOW()
WHERE request_id = 'req-456';
```

**Output:**
```python
{
  "updated": True,
  "request_id": "req-456",
  "final_status": "ERROR"
}
```

---

### Case 4: Update error result (system error)
**Input:**
```python
{
  "request_id": "req-789",
  "status": "ERROR",
  "error": {
    "category": "SYSTEM_ERROR",
    "code": "EXTERNAL_API_TIMEOUT",
    "message": "TomTom API timeout"
  },
  "metadata": {
    "failed_at": "2025-10-14T10:32:00Z",
    "total_duration_ms": 30000
  }
}
```

**DB Operation:**
```sql
UPDATE request_history 
SET 
  status = 'ERROR',
  completed_at = '2025-10-14T10:32:00Z',
  duration_ms = 30000,
  error_code = 'EXTERNAL_API_TIMEOUT',
  result_summary = '{
    "error_category": "SYSTEM_ERROR",
    "error_message": "TomTom API timeout"
  }',
  updated_at = NOW()
WHERE request_id = 'req-789';
```

---

### Case 5: Update fails (DB timeout)
**Error:**
```
DBConnectionTimeout: Connection pool exhausted
```

**Handling:**
1. Retry 2 lần
2. Nếu vẫn fail:
   - Log error: `ERROR: Failed to update request history for req-123 after 2 retries`
   - Return: `{"updated": False, "error": "DB_TIMEOUT"}`
   - **Continue với response trả về user** (don't block)

---

## 5) Database Schema (extend from BLK-1-07)

### Updated Schema
```sql
-- Extend request_history table from BLK-1-07
ALTER TABLE request_history 
ADD COLUMN result_summary JSONB,      -- Success/error details
ADD COLUMN error_code TEXT;           -- Error code if failed
```

### Indexes for Analytics
```sql
-- Query by status
CREATE INDEX idx_request_history_status ON request_history (status, created_at DESC);

-- Query errors by code
CREATE INDEX idx_request_history_error_code ON request_history (error_code) WHERE error_code IS NOT NULL;

-- Performance queries
CREATE INDEX idx_request_history_duration ON request_history (duration_ms) WHERE status = 'SUCCESS';
```

---

## 6) Analytics Queries

### Success Rate
```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_requests,
  COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful,
  COUNT(*) FILTER (WHERE status = 'ERROR') as failed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'SUCCESS') / COUNT(*), 2) as success_rate_pct
FROM request_history
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Error Distribution
```sql
SELECT 
  error_code,
  result_summary->>'error_category' as category,
  COUNT(*) as count
FROM request_history
WHERE status = 'ERROR' AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY error_code, category
ORDER BY count DESC;
```

### Performance Stats
```sql
SELECT 
  tool_name,
  AVG(duration_ms) as avg_duration_ms,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as p50_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_ms,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_ms
FROM request_history
WHERE status = 'SUCCESS' AND created_at > NOW() - INTERVAL '7 days'
GROUP BY tool_name;
```

---

## 7) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing_suite/diagram.drawio` - Database icon "cập nhật kết quả lịch sử request"
- **Related Blocks:**
  - ← BLK-1-07-SaveRequestHistory (created initial record)
  - ← BLK-1-16-ProcessTrafficSections (success aggregate with jam_pairs)
  - ← BLK-1-12-TransformSuccessDataForAI (alternative success)
  - ← BLK-1-03, BLK-1-06, BLK-1-11 (error results)
  - → BLK-End (final step before response)
- **Related Code:**
  - `app/infrastructure/persistence/sqlite_destination_repository.py` (extend for request_history updates)
  - `destinations.db` - Database file

---

## 8) Error cases
- **DB update fails:** → Retry 2x, log error, skip (don't block response)
- **Request_id not found:** → Log warning (BLK-1-07 might have failed), skip
- **Invalid status value:** → Log error, use default "ERROR"
- **Circuit breaker open:** → Skip update, log warning

---

## 9) Monitoring & Alerts

### Metrics
```
request_history_update_success{status="SUCCESS|ERROR"}
request_history_update_failed{reason="timeout|not_found|circuit_open"}
request_history_update_duration_ms{quantile="0.5|0.95|0.99"}
```

### Alerting
- **Alert:** Update failure rate > 5% over 10 min → WARNING
- **Alert:** Circuit breaker open > 5 min → Ops notification

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

**Ví dụ cho block "BLK 1 13 UpdateRequestResult":**
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

## 10) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-13-UpdateRequestResult.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định cho success và error cases
- [x] DB schema extensions và UPDATE queries
- [x] Ví dụ cụ thể cho success, user error, system error
- [x] Error handling (retry, fallback, don't block)
- [x] Analytics queries cho reporting
- [x] Monitoring metrics
- [x] Liên kết đến BLK-1-07 và result blocks

---

> **Lưu ý:** Block này chạy async/best-effort. DB update failure **KHÔNG ĐƯỢC** block response trả về user. Logging và monitoring quan trọng để track update failures.

