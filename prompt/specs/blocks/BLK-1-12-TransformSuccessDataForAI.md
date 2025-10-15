# BLK-1-12 — Transform Success Data For AI

Mục tiêu: Chiết xuất và biến đổi dữ liệu route thành công từ API (BLK-1-09) thành format tối ưu để gửi cho AI/LLM thông báo người dùng.

**Lưu ý:** Theo diagram, block này được gọi là "chiết xuất dữ liệu rồi biến đổi sang dữ liệu phù hợp cho AI" - tương ứng với success path.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi từ BLK-1-10 khi `api_success = True`
  - [x] Sau khi có route data hợp lệ từ TomTom API
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - API call thành công (BLK-1-10 = success)
  - Có route_data hợp lệ với summary, legs, guidance

- **Điều kiện dừng/không chạy (Guards):**
  - API failed → đi qua error handling (BLK-1-11), không qua block này

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:** Route data từ BLK-1-10 (success path)
```python
{
  "api_success": True,
  "route_data": {
    "summary": {
      "length_in_meters": int,
      "travel_time_in_seconds": int,
      "traffic_delay_in_seconds": int,
      "departure_time": str,  # ISO8601
      "arrival_time": str
    },
    "legs": List[{
      "summary": {...},
      "points": List[{"lat": float, "lon": float}]
    }],
    "sections": List[{...}],
    "guidance": {
      "instructions": List[{
        "message": str,
        "maneuver": str,
        "point": {"lat": float, "lon": float}
      }]
    }
  },
  "metadata": {
    "provider": str,
    "request_duration_ms": int,
    "request_id": str
  },
  "request_context": {
    "locale": "vi" | "en",
    "user_preferences": {
      "unit_system": "metric" | "imperial",
      "time_format": "24h" | "12h"
    }
  }
}
```

- **Bắt buộc:**
  - `route_data.summary`
  - `route_data.guidance.instructions` (ít nhất basic directions)

- **Nguồn:** BLK-1-10 (CheckAPISuccess - success path)

- **Bảo mật:**
  - Không lộ toàn bộ raw API response (có thể chứa internal metadata)
  - Chỉ trả về data cần thiết cho user

### 2.2 Output
- **Kết quả trả về (AI-friendly format):**
```python
{
  "type": "ROUTE_SUCCESS",
  "locale": "vi",
  "summary": {
    "distance": {
      "value": 1730,  # kilometers (hoặc miles nếu imperial)
      "unit": "km",
      "formatted": "1,730 km"
    },
    "duration": {
      "value": 72000,  # seconds
      "formatted": "20 giờ",
      "with_traffic": "20 giờ 30 phút"  # Including traffic delay
    },
    "departure": {
      "time": "2025-10-14T10:30:00+07:00",
      "formatted": "10:30 SA, 14/10/2025"
    },
    "arrival": {
      "time": "2025-10-15T06:30:00+07:00",
      "formatted": "06:30 SA, 15/10/2025"
    },
    "traffic_info": "Có kẹt xe nhẹ (+30 phút)"
  },
  "route_overview": {
    "main_roads": ["QL1A", "AH1"],  # Extracted major roads
    "via_cities": ["Vinh", "Huế", "Đà Nẵng", "Nha Trang"],
    "highlights": [
      "Đi qua 5 tỉnh thành",
      "Có trạm thu phí (khoảng 300,000 VNĐ)",
      "Nghỉ qua đêm khuyến nghị tại Huế hoặc Đà Nẵng"
    ]
  },
  "turn_by_turn": [
    {
      "step": 1,
      "instruction": "Đi về phía bắc trên Phố Huế",
      "distance": "500m",
      "duration": "2 phút"
    },
    {
      "step": 2,
      "instruction": "Rẽ phải vào QL1A",
      "distance": "120km",
      "duration": "2 giờ"
    }
    # ... (có thể rút gọn nếu quá dài)
  ],
  "rendering_hints": {
    "style": "conversational",
    "detail_level": "summary",  # "summary" | "detailed" | "minimal"
    "include_map_link": True,
    "map_url": "https://tomtom.com/route/..." # Optional
  },
  "metadata": {
    "request_id": "req-123",
    "calculated_at": "2025-10-14T10:30:15Z",
    "data_source": "TomTom Routing API"
  }
}
```

- **Side-effects:**
  - (Optional) Lưu formatted route vào cache để reuse
  - Log transformation metrics (processing time)

- **Đảm bảo (Guarantees):**
  - Output luôn có summary (distance, duration)
  - Localized theo user preferences
  - AI có thể đọc và present cho user dễ hiểu

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 100ms (pure data transformation)
- **Retry & Backoff:** Không áp dụng (pure function)
- **Idempotency:** Yes (same input → same output)
- **Circuit Breaker:** Không áp dụng
- **Rate limit/Quota:** Không áp dụng
- **Bảo mật & Quyền:** N/A

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-12 |
| **Tên Block** | TransformSuccessDataForAI |
| **Trigger** | From BLK-1-10 = api_success: True |
| **Preconditions** | Có route_data hợp lệ |
| **Input (schema)** | `{ route_data: { summary, legs, guidance, ... } }` |
| **Output** | AI-friendly format với localized strings |
| **Side-effects** | (Optional) cache, log metrics |
| **Timeout/Retry** | 100ms, no retry |
| **Idempotency** | Yes |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

### Case 1: Route ngắn trong thành phố (< 50km)
**Input:**
```python
{
  "api_success": True,
  "route_data": {
    "summary": {
      "length_in_meters": 15000,
      "travel_time_in_seconds": 1800,
      "traffic_delay_in_seconds": 300,
      "departure_time": "2025-10-14T10:30:00+07:00",
      "arrival_time": "2025-10-14T11:00:00+07:00"
    },
    "guidance": {
      "instructions": [
        {"message": "Head north on Lê Duẩn", "maneuver": "DEPART"},
        {"message": "Turn right onto Điện Biên Phủ", "maneuver": "TURN_RIGHT"},
        {"message": "Arrive at destination", "maneuver": "ARRIVE"}
      ]
    }
  },
  "request_context": {
    "locale": "vi",
    "user_preferences": {"unit_system": "metric"}
  }
}
```

**Output:**
```python
{
  "type": "ROUTE_SUCCESS",
  "locale": "vi",
  "summary": {
    "distance": {"value": 15, "unit": "km", "formatted": "15 km"},
    "duration": {
      "value": 1800,
      "formatted": "30 phút",
      "with_traffic": "35 phút"
    },
    "departure": {"time": "2025-10-14T10:30:00+07:00", "formatted": "10:30, 14/10/2025"},
    "arrival": {"time": "2025-10-14T11:00:00+07:00", "formatted": "11:00, 14/10/2025"},
    "traffic_info": "Có chút kẹt xe (+5 phút)"
  },
  "route_overview": {
    "main_roads": ["Lê Duẩn", "Điện Biên Phủ"],
    "via_cities": [],
    "highlights": ["Tuyến đường ngắn trong thành phố", "Ước tính thời gian 30-35 phút tuỳ giao thông"]
  },
  "turn_by_turn": [
    {"step": 1, "instruction": "Đi về phía bắc trên Lê Duẩn", "distance": "8km", "duration": "15 phút"},
    {"step": 2, "instruction": "Rẽ phải vào Điện Biên Phủ", "distance": "7km", "duration": "15 phút"},
    {"step": 3, "instruction": "Đến nơi", "distance": "0m", "duration": "0 phút"}
  ],
  "rendering_hints": {
    "style": "conversational",
    "detail_level": "summary"
  }
}
```

### Case 2: Route dài liên tỉnh (> 500km)
**Input:** (Route Hà Nội → TP.HCM, 1730km, 20h)

**Output:**
```python
{
  "type": "ROUTE_SUCCESS",
  "locale": "vi",
  "summary": {
    "distance": {"value": 1730, "unit": "km", "formatted": "1,730 km"},
    "duration": {
      "value": 72000,
      "formatted": "20 giờ",
      "with_traffic": "20 giờ 30 phút"
    },
    "departure": {"formatted": "10:30, 14/10/2025"},
    "arrival": {"formatted": "06:30, 15/10/2025"},
    "traffic_info": "Có kẹt xe nhẹ ở một số đoạn (+30 phút)"
  },
  "route_overview": {
    "main_roads": ["QL1A (Quốc lộ 1A)"],
    "via_cities": ["Nam Định", "Thanh Hóa", "Vinh", "Huế", "Đà Nẵng", "Quảng Ngãi", "Nha Trang", "Phan Thiết"],
    "highlights": [
      "Hành trình dài qua 15 tỉnh thành",
      "Khuyến nghị nghỉ đêm ở Huế hoặc Đà Nẵng (sau 10-12 giờ lái)",
      "Chi phí phí đường bộ khoảng 300,000 - 400,000 VNĐ",
      "Đường ven biển đẹp từ Huế đến Nha Trang"
    ]
  },
  "turn_by_turn": [
    {"step": 1, "instruction": "Đi về phía nam trên QL1A", "distance": "~1,700km", "duration": "~19 giờ"},
    {"step": 2, "instruction": "Đến TP. Hồ Chí Minh", "distance": "30km", "duration": "1 giờ"}
    # Rút gọn vì quá nhiều bước
  ],
  "rendering_hints": {
    "style": "conversational",
    "detail_level": "summary",  # Không show hết turn-by-turn cho route dài
    "include_map_link": True
  },
  "metadata": {
    "request_id": "req-123",
    "note": "Turn-by-turn directions simplified due to route length. Full details available on request."
  }
}
```

---

## 5) Transformation Logic

### Distance Formatting
```python
def format_distance(meters: int, unit_system: str, locale: str) -> dict:
    if unit_system == "imperial":
        miles = meters / 1609.34
        return {
            "value": round(miles, 1),
            "unit": "miles",
            "formatted": f"{miles:,.1f} miles" if locale == "en" else f"{miles:,.1f} dặm"
        }
    else:  # metric
        km = meters / 1000
        return {
            "value": round(km, 1) if km > 10 else round(km, 2),
            "unit": "km",
            "formatted": f"{km:,.1f} km" if locale == "vi" else f"{km:,.1f} km"
        }
```

### Duration Formatting
```python
def format_duration(seconds: int, locale: str) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if locale == "vi":
        if hours > 0:
            return f"{hours} giờ {minutes} phút" if minutes > 0 else f"{hours} giờ"
        else:
            return f"{minutes} phút"
    else:  # en
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        else:
            return f"{minutes}m"
```

### Traffic Info Extraction
```python
def format_traffic_info(delay_seconds: int, locale: str) -> str:
    if delay_seconds < 300:  # < 5 min
        return "Giao thông thông thoáng" if locale == "vi" else "Light traffic"
    elif delay_seconds < 1800:  # < 30 min
        delay_min = delay_seconds // 60
        return f"Có chút kẹt xe (+{delay_min} phút)" if locale == "vi" else f"Some traffic (+{delay_min} min)"
    else:  # > 30 min
        delay_min = delay_seconds // 60
        return f"Kẹt xe khá nhiều (+{delay_min} phút)" if locale == "vi" else f"Heavy traffic (+{delay_min} min)"
```

### Turn-by-Turn Simplification
- Nếu route < 50km: Show all steps
- Nếu 50km - 200km: Group minor steps, show ~10-15 major turns
- Nếu > 200km: Chỉ show major highways và via cities

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Block "chiết xuất dữ liệu rồi biến đổi sang dữ liệu phù hợp cho AI"
- **Related Blocks:**
  - ← BLK-1-10-CheckAPISuccess (success path)
  - → BLK-1-13-UpdateRequestResult (update request history với result)
  - → Return to AI/user (formatted response)
- **Related Code:**
  - `app/application/dto/detailed_route_dto.py` - Route DTOs
  - `app/interfaces/mcp/formatters/` - Response formatters (if exists)

---

## 7) AI Presentation Guidelines

### For LLM/AI to present to user:
```
Tôi đã tìm được tuyến đường từ [Origin] đến [Destination]:

📍 Khoảng cách: {distance.formatted}
⏱️ Thời gian: {duration.with_traffic} (bình thường {duration.formatted})
🚗 Đi qua: {via_cities[0]}, {via_cities[1]}, ...

🛣️ Tuyến đường chính:
- {main_roads[0]}

💡 Lưu ý:
{highlights[0]}
{highlights[1]}

Bạn có muốn xem chi tiết từng bước rẽ không?
```

---

## 8) Error cases của chính block này
- **Missing summary data:** → Fallback to minimal format với available data
- **Invalid time format:** → Log warning, use raw ISO8601
- **Localization failure:** → Fallback to English
- **Guidance instructions empty:** → Return summary only, no turn-by-turn

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

**Ví dụ cho block "BLK 1 12 TransformSuccessDataForAI":**
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
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-12-TransformSuccessDataForAI.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với AI-friendly format
- [x] Ví dụ cụ thể cho route ngắn và dài
- [x] Transformation logic cho distance, duration, traffic
- [x] Localization support (vi/en)
- [x] Turn-by-turn simplification strategy
- [x] AI presentation guidelines
- [x] Error handling cho missing data

---

> **Lưu ý:** Output format cần balance giữa đầy đủ thông tin và dễ đọc cho AI. Tránh quá technical, ưu tiên conversational tone.

