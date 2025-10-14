# BLK-1-04 — Check Destination Exists

Mục tiêu: Kiểm tra xem destination (điểm đến) đã được lưu trong database hay chưa để tránh lưu trùng hoặc tái sử dụng thông tin đã có.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi trực tiếp từ BLK-1-02 khi validation thành công (no errors)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Input đã qua validation thành công (BLK-1-01 passed)
  - Database connection sẵn sàng
  - Có thông tin destination để tra cứu (address hoặc coordinates)

- **Điều kiện dừng/không chạy (Guards):**
  - Database không khả dụng → skip (hoặc throw error tùy policy)
  - Request không yêu cầu lưu destination → skip block này

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```python
{
  "validated_data": {
    "destination": {
      "address": str | None,
      "coordinates": {"lat": float, "lon": float} | None
    },
    "origin": { ... },  # optional check for origin too
    # ... other validated fields
  },
  "request_context": {
    "user_id": str | None,
    "session_id": str
  }
}
```

- **Bắt buộc:**
  - `destination.address` hoặc `destination.coordinates` (ít nhất một)
  - `request_context` để scope tra cứu

- **Nguồn:** Output từ BLK-1-02 (validated_data)

- **Bảo mật:**
  - Chỉ tra cứu trong scope của user (nếu có multi-tenancy)
  - Không trả về toàn bộ database records

### 2.2 Output
- **Kết quả trả về:**
  - **Case 1 (exists):** 
    ```python
    {
      "destination_exists": True,
      "destination_id": "uuid-123",
      "destination_data": { ... }  # cached data
    }
    ```
    → Forward to **BLK-1-09** (Request API với cached info nếu có)
  
  - **Case 2 (not exists):**
    ```python
    {
      "destination_exists": False,
      "destination_data": None
    }
    ```
    → Forward to **BLK-1-08** (Save destination) hoặc **BLK-1-09** (Request API)

- **Side-effects:**
  - Query database (SELECT)
  - Log cache hit/miss

- **Đảm bảo (Guarantees):**
  - Readonly operation (không modify DB)
  - Kết quả deterministic với cùng input trong TTL window

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 100ms (DB query)
- **Retry & Backoff:** 2 lần, 50ms backoff nếu DB timeout
- **Idempotency:** Yes (readonly query)
- **Circuit Breaker:** Mở sau 5 DB errors liên tiếp trong 10s
- **Rate limit/Quota:** Không áp dụng (internal operation)
- **Bảo mật & Quyền:**
  - Query chỉ trong scope user/session nếu có isolation
  - Index trên `address` hoặc `coordinates` (geospatial) để tối ưu

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-04 |
| **Tên Block** | CheckDestinationExists |
| **Trigger** | From BLK-1-02 = success (validated data) |
| **Preconditions** | DB available, có destination info |
| **Input (schema)** | `{ validated_data: { destination: {...} }, request_context }` |
| **Output** | `{ destination_exists: bool, destination_id?, destination_data? }` |
| **Side-effects** | DB SELECT query, log cache hit/miss |
| **Timeout/Retry** | 100ms, 2 retries với 50ms backoff |
| **Idempotency** | Yes (readonly) |
| **AuthZ/Scope** | User/session scoped query |

---

## 4) Ví dụ cụ thể

### Case 1: Destination đã tồn tại
**Input:**
```python
{
  "validated_data": {
    "destination": {
      "address": "Landmark 81, Ho Chi Minh City",
      "coordinates": {"lat": 10.7946, "lon": 106.7218}
    }
  },
  "request_context": {
    "user_id": "user-456",
    "session_id": "session-789"
  }
}
```

**DB Query:**
```sql
SELECT id, address, coordinates, geocoded_data 
FROM destinations 
WHERE address = 'Landmark 81, Ho Chi Minh City' 
  AND user_id = 'user-456'
LIMIT 1;
```

**Output:**
```python
{
  "destination_exists": True,
  "destination_id": "dest-uuid-123",
  "destination_data": {
    "address": "Landmark 81, Ho Chi Minh City",
    "coordinates": {"lat": 10.7946, "lon": 106.7218},
    "geocoded_at": "2025-10-10T08:00:00Z"
  }
}
```
**Next:** → BLK-1-09 (có thể dùng cached geocoded data)

### Case 2: Destination chưa tồn tại
**Input:** (tương tự trên)

**DB Query:** (không tìm thấy)

**Output:**
```python
{
  "destination_exists": False,
  "destination_data": None
}
```
**Next:** → BLK-1-08 (Save destination sau khi geocode) hoặc BLK-1-09 trực tiếp

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Decision "kiểm tra input destination xem đã lưu hay chưa?"
- **Related Blocks:**
  - ← BLK-1-02-CheckError (success path)
  - → BLK-1-08-SaveDestination (if not exists)
  - → BLK-1-09-RequestRoutingAPI (next step)
- **Related Code:**
  - `app/infrastructure/persistence/sqlite_destination_repository.py` - DB queries
  - `app/domain/entities/destination.py` - Destination entity
  - `app/application/ports/destination_repository.py` - Repository interface

---

## 6) Query Optimization
- **Index strategy:**
  - Primary index: `address` (TEXT index)
  - Secondary index: `coordinates` (geospatial index nếu DB hỗ trợ)
  - Composite index: `(user_id, address)` nếu có multi-tenancy
  
- **Cache strategy:**
  - In-memory cache (Redis/dict) cho frequently accessed destinations
  - TTL: 1 hour
  - Invalidate on destination update/delete

- **Matching logic:**
  - Exact match trên `address` (case-insensitive)
  - Fuzzy match (optional): Levenshtein distance < 3 cho typos
  - Geospatial match: distance < 100m cho coordinates

---

## 7) Error cases
- **DB connection timeout:** → Retry 2 lần, sau đó skip cache check và proceed to API
- **DB query error:** → Log error, return `destination_exists = False` (fail-open)
- **Multiple matches found:** → Return first match (hoặc most recently used)
- **Invalid coordinates format:** → Fallback to address-only lookup

---

## 8) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-04-CheckDestinationExists.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với 2 cases (exists/not exists)
- [x] Ràng buộc runtime nêu rõ (timeout, retry, circuit breaker)
- [x] Có bảng tóm tắt
- [x] Có SQL query examples và optimization notes
- [x] Error handling strategy rõ ràng
- [x] Liên kết đến repository code và diagram

---

> **Lưu ý:** Block này là optimization để tránh duplicate geocoding calls. Nếu destination đã có, có thể skip một số bước API downstream hoặc dùng cached route data.

