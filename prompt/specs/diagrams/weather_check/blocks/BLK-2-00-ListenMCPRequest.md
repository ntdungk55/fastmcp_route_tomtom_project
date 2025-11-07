# BLK-2-00 — Listen MCP Request

Mục tiêu: Nhận request từ MCP client để kiểm tra thời tiết tại một địa điểm.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] MCP client gọi tool `check_weather` hoặc `get_weather`
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - MCP Server đang chạy
  - Client đã kết nối thành công
  - Tool đã được đăng ký trong server

- **Điều kiện dừng/không chạy (Guards):**
  - Request format không hợp lệ → trả lỗi ngay

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "location": "<string>",  // Địa chỉ hoặc "lat,lon"
  "units": "metric" | "imperial" | "kelvin",  // optional, default: "metric"
  "language": "<string>"  // optional, default: "vi"
}
```

- **Bắt buộc:**
  - `location`: Địa chỉ hoặc tọa độ lat,lon

- **Nguồn:**
  - Từ MCP Client qua tool parameters

### 2.2 Output
- **Kết quả trả về:**
  - Request object được truyền đến BLK-2-01 (Validate Input Param)

- **Side-effects:**
  - Log request để debug

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout:** N/A (chỉ nhận request)
- **Retry:** N/A
- **Idempotency:** N/A

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-2-00 |
| **Tên Block** | ListenMCPRequest |
| **Trigger** | MCP client gọi weather tool |
| **Preconditions** | MCP server running |
| **Input (schema)** | `{ location, units?, language? }` |
| **Output** | Request object |
| **Side-effects** | Log request |
| **Timeout/Retry** | N/A |
| **Idempotency** | N/A |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

**Input từ MCP Client:**
```json
{
  "location": "Ho Chi Minh City, Vietnam",
  "units": "metric",
  "language": "vi"
}
```

**Output:** Request object được chuyển đến BLK-2-01

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/weather_check/diagram_flow.txt`
- **Related Blocks:**
  - → BLK-2-01-ValidateInputParam (validate input)
- **Related Code:**
  - `app/interfaces/mcp/server.py` - MCP server và tool definitions




