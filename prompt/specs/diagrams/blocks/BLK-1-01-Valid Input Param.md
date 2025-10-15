# BLK-1-01 — Validate TomTom Routing Params

---

## 1) Khi nào **trigger** block này?

### Sự kiện kích hoạt (Trigger)
- [x] Gọi trực tiếp từ MCP tool `calculate_route` hoặc `get_detailed_route`
- [ ] Message/Event đến
- [ ] Lịch/Timer
- [ ] Webhook/Callback từ hệ thống ngoài

### Điều kiện tiền đề (Preconditions)
- **Business:** 
  - User cung cấp yêu cầu tính toán tuyến đường
  - Có ít nhất 2 điểm (origin & destination)
- **Kỹ thuật:** 
  - MCP Server đang chạy và nhận được request

### Điều kiện dừng/không chạy (Guards)
- Nếu số lượng điểm < 2 → dừng, trả lỗi `INVALID_LOCATIONS_COUNT`

---

## 2) **Input, Output** và **các ràng buộc**

### 2.1 Input
**Schema/kiểu dữ liệu:**
```json
{
  "routePlanningLocations": <string>,
  "maxAlternatives": <integer, range 0-5, optional>,
  "alternativeType": <string, optional>,
  "routeType": <string, optional: "fastest"|"shortest"|"eco"|"thrilling"|"short">,
  "travelMode": <string, optional: "car"|"truck"|"taxi"|"bus"|"van"|"motorcycle"|"bicycle"|"pedestrian">,
  "avoid": [<string>, optional],
  "traffic": <boolean, optional>,
  "departAt": <RFC3339 datetime string, optional>,
  "arriveAt": <RFC3339 datetime string, optional, XOR với departAt>,
  "computeBestOrder": <boolean, optional>
}
```

**Bắt buộc:**
- `routePlanningLocations`: chuỗi chứa ≥ 2 điểm, định dạng `lat,lon` với:
  - `lat ∈ [-90, 90]` 
  - `lon ∈ [-180, 180]`
  - Hỗ trợ thêm `circle(lat,lon,radiusMeters)` cho waypoint

**Nguồn:**
- Từ MCP Client qua tool parameters (do AI Agent cung cấp)

**Bảo mật:**
- Không nhận API key từ client (API key được quản lý ở server-side)
- Validate input để tránh injection attacks

### 2.2 Output
**Kết quả trả về:**
- **Success:** Validated parameters object ready cho TomTom API call
- **Failure:** ValidationError với code và message cụ thể

**Side-effects:**
- Không có (pure validation logic)

**Đảm bảo:**
- Fail-fast: dừng ngay khi gặp lỗi đầu tiên
- Deterministic: cùng input → cùng output

### 2.3 Ràng buộc thực thi (Runtime Constraints)

**Validation Rules (fail fast):**
1. **Số lượng điểm**  
   - `routePlanningLocations` phải có **≥ 2** điểm hợp lệ ⇒ nếu <2 ⇒ `INVALID_LOCATIONS_COUNT`
   
2. **Định dạng toạ độ**  
   - Mỗi điểm `lat,lon` đúng định dạng số
   - `lat ∈ [-90, 90]`, `lon ∈ [-180, 180]` ⇒ sai ⇒ `INVALID_LOCATION_FORMAT` / `INVALID_COORD_RANGE`
   
3. **Waypoint & giới hạn**  
   - Tôn trọng giới hạn waypoint của TomTom (max 150 waypoints)
   - `circle(...)` **không** kết hợp với `computeBestOrder=true` ⇒ `INVALID_WAYPOINTS_RULES`
   
4. **Thời gian khởi hành/đến nơi**  
   - `departAt` **không dùng cùng** `arriveAt` ⇒ `PARAM_CONFLICT_TIME`
   
5. **Phương án tuyến thay thế**  
   - `maxAlternatives` ∈ **[0..5]** ⇒ ngoài biên ⇒ `INVALID_MAX_ALTERNATIVES`
   - `maxAlternatives>0` **không** đi với `computeBestOrder=true` ⇒ `PARAM_CONFLICT_ALTERNATIVES`
   
6. **Chế độ di chuyển**  
   - `travelMode` phải thuộc tập cho phép ⇒ sai ⇒ `INVALID_TRAVEL_MODE`
   
7. **Ràng buộc POST body**  
   - Không mix tham số per-leg với tham số query xung đột
   - Nếu khai báo `legs`, **số phần tử = số đoạn** (waypoints + 1)
   - Không dùng per-leg với waypoint dạng `circle`
   - Vi phạm ⇒ `INVALID_POST_BODY_COMBINATION`

**Error Mapping:**
| Code                         | HTTP gợi ý | Mô tả ngắn |
|-----------------------------|-----------:|------------|
| INVALID_LOCATIONS_COUNT     |        400 | Cần ≥ 2 locations |
| INVALID_LOCATION_FORMAT     |        422 | Sai định dạng `lat,lon`/`circle(...)` |
| INVALID_COORD_RANGE         |        422 | Lat/Lon ngoài biên WGS84 |
| INVALID_WAYPOINTS_RULES     |        422 | Vượt giới hạn/combination không hợp lệ |
| PARAM_CONFLICT_TIME         |        409 | `departAt` xung đột `arriveAt` |
| INVALID_MAX_ALTERNATIVES    |        422 | `maxAlternatives` ngoài [0..5] |
| PARAM_CONFLICT_ALTERNATIVES |        409 | `maxAlternatives>0` + `computeBestOrder=true` |
| INVALID_TRAVEL_MODE         |        422 | `travelMode` không hợp lệ |
| INVALID_POST_BODY_COMBINATION|       409 | Conflict per-leg vs query / legs count / circle vs per-leg |

**Timeout/Retry:**
- Không áp dụng (validation đồng bộ, không gọi external service)

**Idempotency:**
- Pure function, idempotent by nature

**AuthZ/Scope:**
- Không áp dụng (validation layer không cần auth)

---

## 3) **Bảng tóm tắt điền nhanh**
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-01 |
| **Tên Block** | ValidateInputParams |
| **Trigger** | Từ MCP tool `calculate_route` hoặc `get_detailed_route` |
| **Preconditions** | Có ≥ 2 điểm từ client |
| **Input (schema)** | routePlanningLocations, query params (không bao gồm API key) |
| **Output** | Validated params hoặc ValidationError |
| **Side-effects** | Không có |
| **Timeout/Retry** | N/A (synchronous validation) |
| **Idempotency** | Yes (pure function) |
| **AuthZ/Scope** | N/A |

---

## 4) **Ví dụ điền mẫu**

### Ví dụ 1: Validation thành công
**Input:**
```json
{
  "routePlanningLocations": "52.50931,13.42936:52.50274,13.43872",
  "travelMode": "car",
  "traffic": true
}
```

**Output:**
```json
{
  "status": "valid",
  "validated_data": {
    "routePlanningLocations": "52.50931,13.42936:52.50274,13.43872",
    "travelMode": "car",
    "traffic": true
  }
}
```

### Ví dụ 2: Xung đột thời gian
**Input:**
```json
{
  "routePlanningLocations": "52.50931,13.42936:52.50274,13.43872",
  "departAt": "2024-01-01T10:00:00Z",
  "arriveAt": "2024-01-01T12:00:00Z"
}
```

**Output:**
```json
{
  "status": "error",
  "code": "PARAM_CONFLICT_TIME",
  "message": "`departAt` và `arriveAt` không thể dùng cùng nhau. Hãy chọn một trong hai."
}
```

### Ví dụ 3: Số lượng điểm không đủ
**Input:**
```json
{
  "routePlanningLocations": "52.50931,13.42936"
}
```
**Comment:** Chỉ có 1 điểm

**Output:**
```json
{
  "status": "error",
  "code": "INVALID_LOCATIONS_COUNT",
  "message": "Cần ít nhất 2 điểm (xuất phát và đích) để tính tuyến đường."
}
```

---

## Liên kết
- **TomTom Routing API Explorer**: https://developer.tomtom.com/routing-api/api-explorer
- **Related Use Cases**: calculate_route, get_detailed_route
- **Validation Service**: validation_service module

---

## 6) **Nghiệm thu kết quả (Acceptance Criteria)**

### 6.1 Tiêu chí nghiệm thu chung
- [ ] **Functional Requirements:** Block validate đúng tất cả TomTom routing parameters theo business rules
- [ ] **Input Validation:** Xử lý đúng các trường hợp input hợp lệ và không hợp lệ
- [ ] **Output Format:** Trả về validated params hoặc ValidationError với format chuẩn
- [ ] **Error Handling:** Trả đúng error codes và messages theo mapping table
- [ ] **Performance:** Validation hoàn thành trong thời gian < 50ms (synchronous)
- [ ] **Security:** Validate input để tránh injection attacks, không expose sensitive data

### 6.2 Test Cases bắt buộc

#### 6.2.1 Happy Path Tests
- [ ] **Valid Basic Route:** Test với 2 điểm hợp lệ, travelMode="car" → success
- [ ] **Valid Complex Route:** Test với waypoints, traffic=true, departAt → success
- [ ] **Valid Alternative Routes:** Test với maxAlternatives=3 → success

#### 6.2.2 Error Handling Tests  
- [ ] **Invalid Locations Count:** Test với < 2 điểm → INVALID_LOCATIONS_COUNT
- [ ] **Invalid Coordinate Format:** Test với lat,lon sai format → INVALID_LOCATION_FORMAT
- [ ] **Invalid Coordinate Range:** Test với lat/lon ngoài WGS84 → INVALID_COORD_RANGE
- [ ] **Time Conflict:** Test với departAt + arriveAt → PARAM_CONFLICT_TIME
- [ ] **Invalid Max Alternatives:** Test với maxAlternatives > 5 → INVALID_MAX_ALTERNATIVES
- [ ] **Invalid Travel Mode:** Test với travelMode không hợp lệ → INVALID_TRAVEL_MODE

#### 6.2.3 Edge Cases Tests
- [ ] **Boundary Coordinates:** Test với lat=90, lon=180 (boundary values)
- [ ] **Empty Locations:** Test với routePlanningLocations="" → INVALID_LOCATIONS_COUNT
- [ ] **Circle Waypoints:** Test với circle() format và computeBestOrder conflict
- [ ] **Max Waypoints:** Test với 150 waypoints (TomTom limit)

### 6.3 Ví dụ Test Cases mẫu

**Ví dụ cho block "ValidateInputParams":**
```json
// Test Case 1: Valid Input
Input: {
  "routePlanningLocations": "52.50931,13.42936:52.50274,13.43872",
  "travelMode": "car",
  "traffic": true
}
Expected: {
  "status": "valid",
  "validated_data": { /* same as input */ }
}

// Test Case 2: Invalid - Single Location
Input: {
  "routePlanningLocations": "52.50931,13.42936"
}
Expected: {
  "status": "error",
  "code": "INVALID_LOCATIONS_COUNT",
  "message": "Cần ít nhất 2 điểm (xuất phát và đích) để tính tuyến đường."
}

// Test Case 3: Time Conflict
Input: {
  "routePlanningLocations": "52.50931,13.42936:52.50274,13.43872",
  "departAt": "2024-01-01T10:00:00Z",
  "arriveAt": "2024-01-01T12:00:00Z"
}
Expected: {
  "status": "error",
  "code": "PARAM_CONFLICT_TIME",
  "message": "`departAt` và `arriveAt` không thể dùng cùng nhau. Hãy chọn một trong hai."
}
```

### 6.4 Checklist nghiệm thu cuối
- [ ] **Code Review:** Code đã được review bởi senior developer
- [ ] **Unit Tests:** Tất cả test cases đã pass (coverage ≥ 95%)
- [ ] **Integration Tests:** Test tích hợp với BLK-1-00 và BLK-1-02
- [ ] **Documentation:** Code có comment và documentation đầy đủ
- [ ] **Performance Test:** Đáp ứng < 50ms validation time
- [ ] **Security Review:** Đã kiểm tra input sanitization
- [ ] **Deployment:** Deploy thành công và hoạt động ổn định

---

## 7) **Definition of Done (DoD)**

### 7.1 Spec Documentation
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-01-ValidateInputParam.md`
- [x] **CHỈ MÔ TẢ NGHIỆP VỤ** - không chứa code/framework/công nghệ cụ thể
- [x] Phần **Trigger** có đầy đủ: sự kiện kích hoạt, preconditions, guards
- [x] Phần **Input** có schema rõ ràng, ghi rõ required fields và validation rules
- [x] Phần **Output** có kết quả trả về, side-effects, và guarantees
- [x] Phần **Runtime Constraints** có timeout, retry, idempotency (nếu cần)
- [x] Có **bảng tóm tắt** đầy đủ các mục quan trọng
- [x] Có **ví dụ cụ thể** với input/output thực tế (ít nhất 2-3 ví dụ)
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

---

> **Lưu ý:** 
> - Block này làm **một việc duy nhất** (Single Responsibility) - validation client input params.
> - **API key KHÔNG được gửi từ client**, nó được quản lý an toàn ở server-side và sẽ được validate ở BLK-1-09.
> - Chỉ validate business logic và format của routing parameters, không validate credentials.
> - **Technology-agnostic**: Spec này có thể implement bằng bất kỳ ngôn ngữ nào (Python, Node.js, Go, Java, etc.)
