# BLK-1-14 — Normalize Output For LLM

Mục tiêu: Chuẩn hóa format output cuối cùng (success hoặc error) theo MCP protocol, với **xương sống là chi tiết đường đi từng bước (turn-by-turn directions)**.

**Lưu ý:** Block này là bước cuối cùng trước khi trả response về LLM, được gọi từ OR gate sau success path (BLK-1-13) hoặc error path (BLK-1-03, BLK-1-06, BLK-1-11).

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi từ OR gate sau BLK-1-13 (success) hoặc các error blocks
  - [x] Trước khi trả response về MCP Client/LLM

- **Điều kiện tiền đề (Preconditions):**
  - Đã có kết quả cuối cùng (success data hoặc error) từ các block trước

---

## 2) Input, Output và các ràng buộc

### 2.1 Input

**Success result:**
```json
{
  "request_id": "string",
  "status": "SUCCESS",
  "result": {
    "type": "ROUTE_SUCCESS",
    "summary": {...},
    "route_overview": {...},
    "turn_by_turn": [...]  // QUAN TRỌNG: Chi tiết đường đi từng bước
  },
  "request_context": {
    "tool_name": "calculate_route"
  }
}
```

**Error result:**
```json
{
  "request_id": "string",
  "status": "ERROR",
  "error": {
    "error_category": "USER_ERROR" | "SYSTEM_ERROR",
    "user_facing_error": {
      "code": "string",
      "message": "string",
      "hint": "string"
    }
  },
  "request_context": {
    "tool_name": "calculate_route"
  }
}
```

### 2.2 Output

**MCP Protocol Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "...formatted message với turn-by-turn directions..."
    },
    {
      "type": "resource",
      "resource": {
        "uri": "route://{request_id}",
        "mimeType": "application/json",
        "text": "{full_route_data_with_complete_turn_by_turn}"
      }
    }
  ],
  "isError": false,
  "metadata": {
    "request_id": "string",
    "tool_name": "calculate_route",
    "status": "SUCCESS",
    "timestamp": "ISO8601"
  }
}
```

### 2.3 Ràng buộc thực thi
- **Timeout:** 50ms
- **Idempotency:** Yes
- **Resource Content:** LUÔN include full `turn_by_turn` array (không rút gọn)

---

## 3) Bảng tóm tắt
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-14 |
| **Tên Block** | NormalizeOutputForLLM |
| **Trigger** | From OR gate after BLK-1-13 or error blocks |
| **Input** | `{ request_id, status, result?, error?, request_context }` |
| **Output** | MCP protocol compliant response với turn-by-turn |
| **Timeout** | 50ms |

---

## 4) Turn-by-Turn Directions Formatting (XƯƠNG SỐNG)

**Mục tiêu:** Format chi tiết hướng dẫn đường đi từng bước một cách rõ ràng, dễ đọc cho người dùng khi lái xe.

### 4.1 Input Structure

```json
{
  "turn_by_turn": [
    {
      "step": 1,
      "instruction": "Đi về phía bắc trên Phố Huế",
      "distance": "500m",
      "duration": "2 phút",
      "maneuver": "DEPART" | "CONTINUE" | "TURN_LEFT" | "TURN_RIGHT" | "UTURN" | "ROUNDABOUT" | "ENTER_HIGHWAY" | "EXIT_HIGHWAY" | "ARRIVE",
      "road_name": "Phố Huế",
      "coordinates": {"lat": 21.0285, "lng": 105.8542}
    }
  ]
}
```

### 4.2 Formatting Rules theo Route Length

#### Route ngắn (< 50km, ≤ 30 steps)
**Hiển thị TẤT CẢ các bước chi tiết:**

```
📋 Hướng dẫn chi tiết từng bước:

1. 🚗 Khởi hành từ {origin}
   • Đi thẳng trên {road_name}
   • Khoảng cách: {distance}
   • Thời gian: {duration}

2. ➡️ {instruction}
   • {maneuver_description}
   • Khoảng cách: {distance}
   • Thời gian: {duration}
   • Tên đường: {road_name}

N. ✅ Đến nơi tại {destination}
```

#### Route trung bình (50-200km, 31-100 steps)
**Hiển thị bước quan trọng + tóm tắt:**

```
📋 Hướng dẫn chi tiết từng bước:

[Bước khởi đầu - 10-15 steps]
1. 🚗 Khởi hành từ {origin}
2. ➡️ {instruction}
...

[Tóm tắt đoạn giữa]
📌 Đi tiếp qua {main_roads} trong khoảng {total_distance} ({total_duration})
   • Qua {via_cities}
   • {number_of_missed_steps} bước được bỏ qua (chủ yếu đi thẳng)

[Bước cuối - 10-15 steps]
...

N. ✅ Đến nơi tại {destination}
```

#### Route dài (> 200km, > 100 steps)
**Hiển thị điểm mốc quan trọng:**

```
📋 Hướng dẫn tuyến đường (rút gọn):

1. 🚗 Khởi hành từ {origin}

2. ➡️ Đi qua {major_city}
   • Tổng khoảng cách: {cumulative_distance}
   • Thời gian: {cumulative_duration}

...

📌 Tóm tắt hành trình:
   • Đi qua: {via_cities.join(" → ")}
   • Đường chính: {main_roads.join(", ")}
   • Tổng cộng: {total_steps} bước (chi tiết đầy đủ có trong resource JSON)

N. ✅ Đến nơi tại {destination}
```

### 4.3 Maneuver Icons

```json
{
  "DEPART": "🚗 Khởi hành",
  "CONTINUE": "➡️ Tiếp tục đi thẳng",
  "TURN_LEFT": "⬅️ Rẽ trái",
  "TURN_RIGHT": "➡️ Rẽ phải",
  "UTURN": "↩️ Quay đầu",
  "ROUNDABOUT": "🔄 Vào bùng binh",
  "ENTER_HIGHWAY": "🛣️ Vào cao tốc/quốc lộ",
  "EXIT_HIGHWAY": "🛤️ Rời cao tốc/quốc lộ",
  "ARRIVE": "✅ Đến nơi"
}
```

### 4.4 Important Steps Detection Logic

1. **Luôn hiển thị:**
   - DEPART, ARRIVE
   - TURN_LEFT, TURN_RIGHT, ROUNDABOUT, ENTER_HIGHWAY, EXIT_HIGHWAY

2. **Grouping Rules:**
   - ≥ 5 bước CONTINUE liên tiếp → group thành "Đi thẳng {total_distance}"
   - Đi qua thành phố/tỉnh → luôn hiển thị

3. **Resource Content:**
   - **LUÔN include** full `turn_by_turn` array trong resource JSON (đầy đủ tất cả steps)
   - Text content có thể rút gọn, nhưng resource JSON phải đầy đủ

---

## 5) Ví dụ

### Case 1: Route ngắn (đầy đủ turn-by-turn)

**Input:**
```json
{
  "request_id": "req-789",
  "status": "SUCCESS",
  "result": {
    "turn_by_turn": [
      {"step": 1, "instruction": "Khởi hành từ 123 Phố Huế", "distance": "0m", "duration": "0 phút", "maneuver": "DEPART", "road_name": "Phố Huế"},
      {"step": 2, "instruction": "Đi thẳng trên Phố Huế", "distance": "500m", "duration": "2 phút", "maneuver": "CONTINUE"},
      {"step": 3, "instruction": "Rẽ phải vào Điện Biên Phủ", "distance": "1.2km", "duration": "4 phút", "maneuver": "TURN_RIGHT", "road_name": "Điện Biên Phủ"},
      {"step": 4, "instruction": "Rẽ trái vào Lê Duẩn", "distance": "2.5km", "duration": "8 phút", "maneuver": "TURN_LEFT", "road_name": "Lê Duẩn"},
      {"step": 5, "instruction": "Đến nơi tại 456 Lê Duẩn", "distance": "0m", "duration": "0 phút", "maneuver": "ARRIVE"}
    ]
  }
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Tôi đã tìm được tuyến đường:\n\n📍 Khoảng cách: 15 km\n⏱️ Thời gian: 30 phút\n\n📋 Hướng dẫn chi tiết từng bước:\n\n1. 🚗 Khởi hành từ 123 Phố Huế\n   • Khoảng cách: 500m, Thời gian: 2 phút\n\n2. ➡️ Đi thẳng trên Phố Huế\n   • Tiếp tục đi thẳng\n   • Khoảng cách: 500m, Thời gian: 2 phút\n\n3. ➡️ Rẽ phải vào Điện Biên Phủ\n   • Rẽ phải\n   • Khoảng cách: 1.2km, Thời gian: 4 phút\n   • Tên đường: Điện Biên Phủ\n\n4. ➡️ Rẽ trái vào Lê Duẩn\n   • Rẽ trái\n   • Khoảng cách: 2.5km, Thời gian: 8 phút\n   • Tên đường: Lê Duẩn\n\n5. ✅ Đến nơi tại 456 Lê Duẩn"
    },
    {
      "type": "resource",
      "resource": {
        "uri": "route://req-789",
        "mimeType": "application/json",
        "text": "{\"turn_by_turn\":[{\"step\":1,...},{\"step\":2,...},{\"step\":3,...},{\"step\":4,...},{\"step\":5,...}]}"
      }
    }
  ],
  "isError": false,
  "metadata": {"request_id": "req-789", "tool_name": "calculate_route", "status": "SUCCESS", "timestamp": "ISO8601"}
}
```

### Case 2: Error response

**Input:**
```json
{
  "request_id": "req-456",
  "status": "ERROR",
  "error": {
    "user_facing_error": {
      "code": "INVALID_LOCATIONS_COUNT",
      "message": "Cần ít nhất 2 địa điểm để tính toán tuyến đường",
      "hint": "Vui lòng cung cấp điểm xuất phát và điểm đến"
    }
  }
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "Cần ít nhất 2 địa điểm để tính toán tuyến đường\n\n💡 Gợi ý: Vui lòng cung cấp điểm xuất phát và điểm đến"
  }],
  "isError": true,
  "error": {
    "code": "INVALID_LOCATIONS_COUNT",
    "message": "Cần ít nhất 2 địa điểm để tính toán tuyến đường",
    "category": "USER_ERROR"
  },
  "metadata": {"request_id": "req-456", "tool_name": "calculate_route", "status": "ERROR", "timestamp": "ISO8601"}
}
```

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - BLK-1-14
- **Related Blocks:**
  - ← BLK-1-13-UpdateRequestResult (success)
  - ← BLK-1-03, BLK-1-06, BLK-1-11 (errors)
  - → BLK-End

---

## 7) Nghiệm thu kết quả (Acceptance Criteria)

### 7.1 Functional Requirements
- [ ] Turn-by-turn directions được format đúng theo route length
- [ ] Resource JSON luôn chứa full `turn_by_turn` array
- [ ] Response tuân thủ MCP protocol

### 7.2 Test Cases

**Test Case 1: Route ngắn hiển thị đầy đủ**
- Input: Route < 50km với turn_by_turn đầy đủ
- Expected: Text content hiển thị tất cả steps, resource có full array

**Test Case 2: Route dài hiển thị summary**
- Input: Route > 200km với nhiều steps
- Expected: Text content chỉ hiển thị major waypoints, resource có full array

**Test Case 3: Error response**
- Input: Error object
- Expected: Error response đúng format với message và hint

---

## 8) Definition of Done (DoD)

### 8.1 Spec Documentation
- [x] File nằm đúng vị trí và ID khớp diagram
- [x] CHỈ MÔ TẢ NGHIỆP VỤ - không chứa code/framework
- [x] **Turn-by-turn directions formatting được mô tả chi tiết (xương sống)**
- [x] Input/Output schema rõ ràng
- [x] Ví dụ cụ thể

### 8.2 Acceptance Criteria
- [x] Test Cases được định nghĩa
- [x] Turn-by-turn logic rõ ràng

---

> **Lưu ý quan trọng:** **Xương sống của block này là chi tiết đường đi từng bước (turn-by-turn directions)**. Resource JSON LUÔN phải chứa full `turn_by_turn` array để đảm bảo người dùng có đầy đủ thông tin khi lái xe. Text content có thể rút gọn theo route length, nhưng resource data phải đầy đủ.
