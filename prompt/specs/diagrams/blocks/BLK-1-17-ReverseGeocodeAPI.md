# BLK-1-17 — Reverse Geocode API

Mục tiêu: Nhận `sections` (có chỉ số `start_point_index`, `end_point_index`) và `legs[0].points` từ BLK-1-16, map indices → toạ độ, gọi TomTom Reverse Geocode để lấy `freeformAddress` cho điểm đầu/cuối. Cắt bỏ các số ở cuối chuỗi địa chỉ để trả về text gọn.

## API Information
- **API:** TomTom Reverse Geocode API
- **Endpoint:** `https://api.tomtom.com/search/2/reverseGeocode/{lat},{lon}.json?key={Your_API_Key}&radius=100`
- **Documentation:** https://developer.tomtom.com/search-api/documentation/search/reverse-geocoding
- **Authentication:** API key from environment variable `TOMTOM_API_KEY`
- **Rate Limit:** Respect `Retry-After` header, max concurrency to avoid quota limits
- **Response Format:** JSON with `addresses[0].address.freeformAddress` field

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-1-16 thành công (có traffic_sections với coordinates)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - BLK-1-16 đã trả về success = true
  - Có `legs` với `legs[0].points` ≥ 2
  - Có `sections` với `start_point_index`, `end_point_index`
  - Có `TOMTOM_API_KEY` trong environment

- **Điều kiện dừng/không chạy (Guards):**
  - `sections` rỗng → trả kết quả rỗng
  - `legs[0].points` rỗng → Error `INVALID_ROUTE_DATA`
  - Index vượt bounds của `legs[0].points` → Error `INVALID_POINT_INDEX`
  - Thiếu `TOMTOM_API_KEY` → Error `API_KEY_NOT_CONFIGURED`

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "sections": [{
    "section_index": <integer>,
    "start_point_index": <integer>,
    "end_point_index": <integer>,
    "section_type": <string>
  }],
  "legs": [{
    "points": [{"lat": <number>, "lon": <number>}]
  }],
  "request_context": {
    "request_id": <string>,
    "timeout": <integer milliseconds, default: 5000>
  }
}
```

- **Bắt buộc:**
  - `sections` (ít nhất 1 section)
  - `sections[].start_point_index`, `sections[].end_point_index`
  - `legs[0].points` (ít nhất 2 toạ độ)
  - `request_context.request_id`
  - `TOMTOM_API_KEY` (environment)

- **Nguồn:**
  - Output từ BLK-1-16 (ProcessTrafficSections)

- **Bảo mật:**
  - Mask coordinates trong logs nếu là sensitive locations

### 2.2 Output
- **Kết quả trả về (success):**
```json
{
  "success": true,
"jam_pairs": [{
  "section_index": <integer>,
  "start": {"lat": <number>, "lon": <number>},
  "end": {"lat": <number>, "lon": <number>},
  "start_address": <string>,
  "end_address": <string>
}],
  "metadata": {
    "request_id": <string>,
    "processed_at": <ISO8601 string>,
    "sections_count": <integer>
  }
}
```

- **Kết quả trả về (error):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_COORDINATES" | "INVALID_REQUEST",
    "message": <string>,
    "status_code": <integer> | null
  }
}
```

- **Side-effects:**
  - Log processing metrics (local)

- **Đảm bảo (Guarantees):**
  - Deterministic processing (same input → same output)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 5s cho mỗi reverse geocode call; tổng thời gian giảm nhờ chạy song song
- **Retry & Backoff:** 1-2 lần (exponential backoff) cho TIMEOUT/5xx/429
- **Idempotency:** GET requests → idempotent
- **Circuit Breaker:** Mở khi lỗi liên tiếp trong 60s (tuỳ cấu hình)
- **Rate limit/Quota:** Tôn trọng `Retry-After`; giới hạn concurrency để tránh vượt quota
- **Bảo mật & Quyền:** `TOMTOM_API_KEY` từ environment; HTTPS only

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-17 |
| **Tên Block** | ReverseGeocodeAPI |
| **Trigger** | After BLK-1-16 success with traffic sections |
| **Preconditions** | Valid sections + legs, API key, network available |
| **Input (schema)** | `{ sections: [...], legs: [...], context }` |
| **Output** | `{ success: bool, jam_pairs?: [...], error?: {...} }` |
| **Side-effects** | HTTP calls to TomTom Reverse Geocode, log/metrics |
| **Timeout/Retry** | 5s timeout per call, retry theo policy |
| **Idempotency** | Yes (GET requests) |
| **AuthZ/Scope** | API key from env |

