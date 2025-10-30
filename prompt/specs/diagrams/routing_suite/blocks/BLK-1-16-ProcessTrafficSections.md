# BLK-1-16 — Process Traffic Sections (Orchestrator)

Mục tiêu: Nhận `route_data` từ BLK-1-09, chuẩn hoá request gửi đến BLK-1-17 (legs[0].points + indices trong sections), chờ kết quả địa chỉ từ BLK-1-17, rồi tổng hợp `summary` + `guidance` (từ BLK-1-09) với `jam_pairs` (từ BLK-1-17) để trả cho BLK-1-13. Nếu lỗi (input/BLK-1-17) → chuyển cho BLK-1-11.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-1-09 thành công (có route_data với legs và sections)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - BLK-1-09 đã trả về success = true
  - route_data có đầy đủ legs và sections
  - sections có ít nhất 1 section với section_type = "TRAFFIC"
  - legs có đủ points để map với start_point_index và end_point_index

- **Điều kiện dừng/không chạy (Guards):**
  - route_data không có sections → Skip (không có traffic data)
  - Tất cả sections đều không phải traffic → Skip
  - legs.points rỗng hoặc không hợp lệ → Error `INVALID_ROUTE_DATA`
  - start_point_index hoặc end_point_index vượt quá bounds của legs.points → Error `INVALID_POINT_INDEX`

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "route_data": {
    "summary": {
      "length_in_meters": <integer>,
      "travel_time_in_seconds": <integer>,
      "traffic_delay_in_seconds": <integer>,
      "departure_time": <ISO8601 string>,
      "arrival_time": <ISO8601 string>
    },
    "legs": [{
      "summary": {...},
      "points": [{"lat": <number>, "lon": <number>}]
    }],
    "sections": [{
      "start_point_index": <integer>,
      "end_point_index": <integer>,
      "section_type": <string>,
      "travel_mode": <string>
    }],
    "guidance": {
      "instructions": [...]
    }
  },
  "request_context": {
    "request_id": <string>
  }
}
```

- **Bắt buộc:**
  - `route_data.legs` (ít nhất 1 leg)
  - `route_data.legs[0].points` (ít nhất 2 points)
  - `route_data.sections` (ít nhất 1 section)
  - `request_context.request_id`

- **Nguồn:**
  - Output từ BLK-1-09 (RequestRoutingAPI)

- **Bảo mật:**
  - Không chứa thông tin nhạy cảm
  - Log coordinates với precision giới hạn (2 decimal places)

### 2.2 Output (aggregate for BLK-1-13)
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
  "route_summary": {
    "total_length_meters": <integer>,
    "total_travel_time_seconds": <integer>,
    "total_traffic_delay_seconds": <integer>,
    "traffic_sections_count": <integer>
  },
  "guidance": {
    "instructions": [...]
  },
  "metadata": {
    "processed_at": <ISO8601 string>,
    "request_id": <string>
  }
}
```

- **Kết quả trả về (error):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_ROUTE_DATA" | "INVALID_POINT_INDEX" | "NO_TRAFFIC_SECTIONS" | "API_KEY_NOT_CONFIGURED" | "API_KEY_UNAUTHORIZED" | "RATE_LIMIT" | "TIMEOUT" | "SERVICE_UNAVAILABLE" | "INVALID_COORDINATES",
    "message": <string>
  }
}
```

- **Side-effects:**
  - Gọi BLK-1-17 (ReverseGeocodeAPI) để reverse geocode theo batch song song
  - Log orchestrator metrics

- **Đảm bảo (Guarantees):**
  - Deterministic processing (same input → same output)
  - No external dependencies
  - Fast processing (< 100ms)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 1s (local processing only)
- **Retry & Backoff:** Không cần (local processing)
- **Idempotency:** Yes (deterministic)
- **Circuit Breaker:** Không áp dụng
- **Rate limit/Quota:** Không áp dụng
- **Bảo mật & Quyền:** Không cần authentication

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-16 |
| **Tên Block** | ProcessTrafficSections |
| **Trigger** | After BLK-1-09 success |
| **Preconditions** | Valid route_data with legs and sections |
| **Input (schema)** | `{ route_data: {...}, request_context }` |
| **Output** | `{ success: bool, traffic_sections?: [...], error?: {...} }` |
| **Side-effects** | Log processing metrics |
| **Timeout/Retry** | 1s timeout, no retry needed |
| **Idempotency** | Yes (deterministic) |
| **AuthZ/Scope** | None required |

---

## 4) Ví dụ cụ thể

## 5) Processing Logic

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing_suite/diagram.drawio` - Block "Process Traffic Sections"
- **Related Blocks:**
  - ← BLK-1-09-RequestRoutingAPI (input source)
  - → BLK-1-17-ReverseGeocodeAPI (call to reverse geocode)
  - → BLK-1-13-UpdateRequestResult (success aggregate)
  - → BLK-1-11-ClassifyAndFormatErrorOutput (error path)
- **Related Code:**
  - `app/application/use_cases/process_traffic_sections.py` - Use case implementation
  - `app/application/dto/traffic_sections_dto.py` - DTO definitions

---

## 7) Error cases

### 7.1 Data Validation Errors
| Error Code | Condition | Classification | Next Action |
|-----------|-----------|----------------|-------------|
| INVALID_ROUTE_DATA | Missing legs, points, or sections | USER_ERROR | Return to user |
| INVALID_POINT_INDEX | Index exceeds points array bounds | USER_ERROR | Return to user |
| NO_TRAFFIC_SECTIONS | All sections are non-traffic | Normal flow | Continue with empty traffic_sections |

---

## 8) **Nghiệm thu kết quả (Acceptance Criteria)**

### 8.1 Tiêu chí nghiệm thu chung
- [ ] **Functional Requirements:** Block xử lý đúng legs và sections để extract traffic coordinates
- [ ] **Input Validation:** Xử lý đúng tất cả các trường hợp input hợp lệ và không hợp lệ
- [ ] **Output Format:** Kết quả trả về đúng format và schema đã định nghĩa
- [ ] **Error Handling:** Xử lý lỗi đúng theo error codes và messages đã quy định
- [ ] **Performance:** Đáp ứng được timeout và performance requirements (< 100ms)
- [ ] **Security:** Không có vấn đề bảo mật (local processing only)

### 8.2 Test Cases bắt buộc

#### 8.2.1 Happy Path Tests
- [ ] **Valid Input with Traffic Sections:** Test với input có traffic sections, kiểm tra output đúng
- [ ] **Valid Input without Traffic Sections:** Test với input không có traffic sections, kiểm tra empty array
- [ ] **Multiple Traffic Sections:** Test với nhiều traffic sections

#### 8.2.2 Error Handling Tests  
- [ ] **Invalid Route Data:** Test với missing legs, points, sections
- [ ] **Invalid Point Index:** Test với index vượt quá bounds
- [ ] **Empty Input:** Test với input rỗng

#### 8.2.3 Edge Cases Tests
- [ ] **Single Point:** Test với legs chỉ có 1 point
- [ ] **Boundary Indices:** Test với start_point_index = 0, end_point_index = last
- [ ] **Mixed Section Types:** Test với mix traffic và non-traffic sections

### 8.3 Ví dụ Test Cases mẫu

**Ví dụ cho block "BLK-1-16 ProcessTrafficSections":**
```json
// Test Case 1: Valid Input with Traffic Sections
Input: { "route_data": { "legs": [...], "sections": [...] } }
Expected: { "success": true, "traffic_sections": [...] }

// Test Case 2: Invalid Point Index
Input: { "route_data": { "legs": [{"points": [...]}], "sections": [{"start_point_index": 0, "end_point_index": 10}] } }
Expected: { "success": false, "error": {"code": "INVALID_POINT_INDEX"} }

// Test Case 3: No Traffic Sections
Input: { "route_data": { "legs": [...], "sections": [{"section_type": "CAR"}] } }
Expected: { "success": true, "traffic_sections": [] }
```

### 8.4 Checklist nghiệm thu cuối
- [ ] **Code Review:** Code đã được review bởi senior developer
- [ ] **Unit Tests:** Tất cả test cases đã pass (coverage ≥ 90%)
- [ ] **Integration Tests:** Test tích hợp với BLK-1-09 và BLK-1-17
- [ ] **Documentation:** Code có comment và documentation đầy đủ
- [ ] **Performance Test:** Đáp ứng performance requirements (< 100ms)
- [ ] **Security Review:** Không có vấn đề bảo mật
- [ ] **Deployment:** Deploy thành công và hoạt động ổn định

---

## 9) **Definition of Done (DoD)**

### 9.1 Spec Documentation
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-16-ProcessTrafficSections.md` và **ID khớp** với diagram  
- [x] **CHỈ MÔ TẢ NGHIỆP VỤ** - không chứa code/framework/công nghệ cụ thể
- [x] Phần **Trigger** có đầy đủ: sự kiện kích hoạt, preconditions, guards  
- [x] Phần **Input** có schema rõ ràng, ghi rõ required fields và validation rules  
- [x] Phần **Output** có kết quả trả về, side-effects, và guarantees  
- [x] Phần **Runtime Constraints** có timeout, retry, idempotency (nếu cần)  
- [x] Có **bảng tóm tắt** đầy đủ các mục quan trọng  
- [x] Có **ví dụ cụ thể** với input/output thực tế (ít nhất 2-3 ví dụ)  
- [x] Có **liên kết** đến diagram, API docs, use cases liên quan  
- [x] **Error cases** được mô tả rõ ràng (error codes, messages)  
- [x] Người đọc có thể hiểu và triển khai **không cần hỏi thêm**

### 9.2 Acceptance Criteria
- [x] **Tiêu chí nghiệm thu chung** đã được định nghĩa rõ ràng
- [x] **Test Cases bắt buộc** đã được liệt kê đầy đủ (Happy Path, Error Handling, Edge Cases)
- [x] **Ví dụ Test Cases** cụ thể với input/output thực tế
- [x] **Checklist nghiệm thu cuối** đã được xác định
- [x] Các tiêu chí nghiệm thu phù hợp với độ phức tạp của block

### 9.3 Implementation Ready
- [x] Spec đã được review và approve bởi BA/Product Owner
- [x] Dev team đã hiểu rõ requirements và có thể bắt đầu implement
- [x] Test team đã có đủ thông tin để viết test cases
- [x] Không còn câu hỏi mở hoặc ambiguity trong spec

---

> **Lưu ý:** 
> - Block này chỉ xử lý local data, không có external API calls
> - Focus vào việc extract và validate traffic sections từ route data
> - Output sẽ được sử dụng bởi BLK-1-17 để reverse geocode coordinates thành addresses
