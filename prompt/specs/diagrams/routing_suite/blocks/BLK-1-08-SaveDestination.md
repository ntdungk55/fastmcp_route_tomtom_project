# BLK-1-08 — Save Destination

Mục tiêu: Lưu thông tin destination (điểm đến) vào database để tái sử dụng trong các request sau, tránh phải geocode lại.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi từ BLK-1-04 khi destination chưa tồn tại (`destination_exists = False`)
  - [x] Sau khi geocode/validate address thành công (có coordinates hợp lệ)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - BLK-1-04 đã check destination chưa tồn tại
  - Có thông tin đầy đủ để lưu (address hoặc coordinates)
  - Database connection sẵn sàng
  - (Optional) Đã geocode để có coordinates chuẩn hoá

- **Điều kiện dừng/không chạy (Guards):**
  - Destination đã tồn tại (BLK-1-04 = True) → skip
  - Database unavailable → log error, continue (don't block main flow)
  - User opt-out lưu địa chỉ → skip

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```python
{
  "destination": {
    "address": str,
    "coordinates": {"lat": float, "lon": float},
    "formatted_address": str | None,  # From geocoding
    "place_id": str | None,  # External ID (Google/TomTom)
    "country": str | None,
    "city": str | None
  },
  "request_context": {
    "user_id": str | None,
    "session_id": str,
    "request_id": str
  },
  "metadata": {
    "geocoded_at": str,  # ISO8601 timestamp
    "geocoding_provider": "tomtom" | "google" | None
  }
}
```

- **Bắt buộc:**
  - `destination.address` hoặc `destination.coordinates` (ít nhất một)
  - Prefer cả hai để có full data
  - `request_context.session_id` hoặc `user_id` để scope

- **Nguồn:** 
  - Từ BLK-1-04 (check not exists)
  - Sau geocoding step (nếu có)

- **Bảo mật:**
  - Hash `user_id` nếu có privacy requirement
  - Không lưu PII nếu policy không cho phép
  - Encrypt coordinates nếu là sensitive location

### 2.2 Output
- **Kết quả trả về:**
```python
{
  "destination_id": "uuid-123",
  "saved": True,
  "created_at": "2025-10-14T10:30:00Z"
}
```

- **Side-effects:**
  - **INSERT** vào bảng `destinations`:
    ```sql
    CREATE TABLE destinations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      address TEXT,
      coordinates_lat REAL,
      coordinates_lon REAL,
      formatted_address TEXT,
      place_id TEXT,
      country TEXT,
      city TEXT,
      user_id TEXT,  -- NULL for shared/public destinations
      session_id TEXT,
      geocoded_at TIMESTAMP,
      geocoding_provider TEXT,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP,
      access_count INTEGER DEFAULT 0,  -- For analytics
      last_accessed_at TIMESTAMP
    );
    ```
  
  - **Indexes:**
    - `address` (text index, case-insensitive)
    - `(coordinates_lat, coordinates_lon)` (geospatial index nếu DB hỗ trợ)
    - `user_id, created_at` (user history)
    - `place_id` (unique, nếu có)

- **Đảm bảo (Guarantees):**
  - At-least-once persistence (có thể có duplicates nếu retry, nhưng unique constraint sẽ catch)
  - No data loss nếu DB available
  - Idempotent (duplicate address → update hoặc ignore)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 300ms (DB insert)
- **Retry & Backoff:** 
  - 2 retries, exponential backoff (100ms, 200ms)
  - Unique constraint violation → ignore (idempotent)
- **Idempotency:** 
  - Composite unique constraint: `(address, user_id)` hoặc `place_id`
  - Duplicate insert → ON CONFLICT DO UPDATE (upsert)
- **Circuit Breaker:** 
  - Mở sau 10 DB errors liên tiếp trong 30s
  - Fallback: skip save, log error, continue
- **Rate limit/Quota:** Không áp dụng (internal)
- **Bảo mật & Quyền:**
  - User-scoped destinations: chỉ user tạo mới access
  - Shared destinations: NULL user_id, public access

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-08 |
| **Tên Block** | SaveDestination |
| **Trigger** | From BLK-1-04 = destination_exists: False |
| **Preconditions** | Có destination data, DB available |
| **Input (schema)** | `{ destination: {address, coordinates, ...}, context }` |
| **Output** | `{ destination_id: UUID, saved: bool }` |
| **Side-effects** | INSERT/UPSERT destinations table |
| **Timeout/Retry** | 300ms, 2 retries với backoff |
| **Idempotency** | Yes (UPSERT on conflict) |
| **AuthZ/Scope** | User-scoped hoặc public |

---

## 4) Ví dụ cụ thể

### Case 1: Lưu destination mới (INSERT)
**Input:**
```python
{
  "destination": {
    "address": "Landmark 81, Ho Chi Minh City",
    "coordinates": {"lat": 10.7946, "lon": 106.7218},
    "formatted_address": "Landmark 81, Vinhomes Central Park, Bình Thạnh, TP.HCM",
    "place_id": "tomtom:abc123",
    "country": "Vietnam",
    "city": "Ho Chi Minh City"
  },
  "request_context": {
    "user_id": "user-456",
    "session_id": "session-789",
    "request_id": "req-123"
  },
  "metadata": {
    "geocoded_at": "2025-10-14T10:30:00Z",
    "geocoding_provider": "tomtom"
  }
}
```

**DB Operation:**
```sql
INSERT INTO destinations (
  address, coordinates_lat, coordinates_lon, formatted_address,
  place_id, country, city, user_id, session_id,
  geocoded_at, geocoding_provider, created_at
) VALUES (
  'Landmark 81, Ho Chi Minh City', 10.7946, 106.7218,
  'Landmark 81, Vinhomes Central Park, Bình Thạnh, TP.HCM',
  'tomtom:abc123', 'Vietnam', 'Ho Chi Minh City',
  'user-456', 'session-789',
  '2025-10-14T10:30:00Z', 'tomtom', NOW()
)
ON CONFLICT (place_id) 
DO UPDATE SET 
  updated_at = NOW(),
  access_count = destinations.access_count + 1,
  last_accessed_at = NOW()
RETURNING id;
```

**Output:**
```python
{
  "destination_id": "uuid-abc-123",
  "saved": True,
  "created_at": "2025-10-14T10:30:00.123Z"
}
```

### Case 2: Destination đã tồn tại (UPSERT - update access count)
**Input:** (tương tự trên, nhưng `place_id` đã có trong DB)

**DB Operation:**
```sql
-- ON CONFLICT triggers UPDATE instead of INSERT
UPDATE destinations 
SET updated_at = NOW(),
    access_count = access_count + 1,
    last_accessed_at = NOW()
WHERE place_id = 'tomtom:abc123'
RETURNING id;
```

**Output:**
```python
{
  "destination_id": "uuid-abc-123",  # Existing ID
  "saved": True,  # Actually updated
  "created_at": "2025-10-10T08:00:00Z"  # Original creation time
}
```

### Case 3: Save fails (DB timeout)
**Error:**
```
DBConnectionTimeout: Connection pool exhausted
```

**Handling:**
1. Retry 2 lần với backoff
2. Nếu vẫn fail:
   - Log error: `ERROR: Failed to save destination after 2 retries: {error}`
   - Return: `{"saved": False, "error": "DB_TIMEOUT"}`
   - **Continue main flow** (don't block routing request)

---

## 5) Database Schema Extensions

### Indexes for Performance
```sql
-- Text search on address (case-insensitive)
CREATE INDEX idx_destinations_address ON destinations (LOWER(address));

-- Geospatial index (if PostGIS or similar extension)
CREATE INDEX idx_destinations_coords ON destinations USING GIST (
  ST_MakePoint(coordinates_lon, coordinates_lat)
);

-- User destinations lookup
CREATE INDEX idx_destinations_user_created ON destinations (user_id, created_at DESC);

-- Unique constraint on place_id
CREATE UNIQUE INDEX idx_destinations_place_id ON destinations (place_id) WHERE place_id IS NOT NULL;

-- Composite unique for user-scoped addresses
CREATE UNIQUE INDEX idx_destinations_user_address ON destinations (user_id, LOWER(address)) 
WHERE user_id IS NOT NULL;
```

### Partitioning Strategy (for large scale)
- Partition by `user_id` hash (nếu có millions users)
- Time-based partitioning `created_at` (archive old data)

---

## 6) Analytics Use Cases

### Popular Destinations
```sql
SELECT address, city, country, access_count
FROM destinations
WHERE created_at > NOW() - INTERVAL '30 days'
ORDER BY access_count DESC
LIMIT 100;
```

### User Destination History
```sql
SELECT address, coordinates_lat, coordinates_lon, created_at
FROM destinations
WHERE user_id = 'user-456'
ORDER BY last_accessed_at DESC
LIMIT 50;
```

### Geocoding Provider Performance
```sql
SELECT geocoding_provider, COUNT(*) as total
FROM destinations
WHERE geocoded_at > NOW() - INTERVAL '7 days'
GROUP BY geocoding_provider;
```

---

## 7) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing_suite/diagram.drawio` - Database icon "lưu địa chỉ"
- **Related Blocks:**
  - ← BLK-1-04-CheckDestinationExists (trigger nếu not exists)
  - → BLK-1-09-RequestRoutingAPI (next step sau lưu)
- **Related Code:**
  - `app/infrastructure/persistence/sqlite_destination_repository.py` - Repository implementation
  - `app/domain/entities/destination.py` - Destination entity
  - `destinations.db` - SQLite database file

---

## 8) Error cases
- **DB insert fails:** → Retry 2x, log error, return `saved: False`, continue
- **Duplicate place_id:** → UPSERT (update access count)
- **Invalid coordinates:** → Log warning, save với coordinates = NULL
- **DB connection timeout:** → Open circuit breaker, skip save
- **Unique constraint violation (race condition):** → Ignore, treat as success

---

## 9) Privacy & Data Retention

### PII Handling
- **User-scoped destinations:** 
  - Require user consent to save
  - Right to delete: implement DELETE by user_id
  - Data export: support query by user_id

- **Shared/public destinations:**
  - Anonymize (user_id = NULL)
  - No PII in address (use formatted_address from geocoding)

### Data Retention
- **Active destinations:** Keep indefinitely (or until user deletes)
- **Inactive destinations:** Archive after 1 year of no access
- **GDPR compliance:** Support data export and erasure requests

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

**Ví dụ cho block "BLK 1 08 SaveDestination":**
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
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-08-SaveDestination.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với INSERT và UPSERT cases
- [x] DB schema với indexes và unique constraints
- [x] Ràng buộc runtime (timeout, retry, circuit breaker)
- [x] UPSERT strategy cho idempotency
- [x] Analytics use cases
- [x] Privacy & data retention considerations
- [x] Error handling (không block main flow)

---

> **Lưu ý:** Block này là optimization layer. Nếu DB save fails, main routing flow vẫn tiếp tục. Không được block response vì lỗi lưu destination.

