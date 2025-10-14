# BLK-1-03 — Map Validation Errors To User Messages

Mục tiêu: Chuẩn hoá output lỗi từ `BLK-1-01-ValidateInput` thành payload thân thiện người dùng để gửi cho AI (LLM) thông báo lỗi cho người dùng cuối (không phải lỗi kỹ thuật cho developer).

---

## 1) Khi nào trigger block này?
> Xử lý ngay khi bước `BLK-1-01-ValidateInput` phát hiện lỗi validation.

- Sự kiện kích hoạt (Trigger):
  - [x] Gọi trực tiếp từ block trước sau khi `ValidateInput` thất bại
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback
- Điều kiện tiền đề (Preconditions):
  - Có payload lỗi hợp lệ từ `BLK-1-01-ValidateInput` (danh sách lỗi kèm `code`/`field`/`reason` tối thiểu)
  - Context yêu cầu (locale, feature flags) sẵn sàng nếu có
- Điều kiện dừng/không chạy (Guards):
  - Không có lỗi nào (errors.length = 0) → bỏ qua block này
  - Payload lỗi thiếu trường tối thiểu (`code`) → dùng thông báo lỗi mặc định

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- Schema/kiểu dữ liệu: JSON từ `BLK-1-01-ValidateInput`
- Tối thiểu:
  - `errors`: Array<{ `code`: string, `field`?: string, `reason`?: string, `context`?: object }>
  - `locale`?: 'vi' | 'en' | string (mặc định 'vi')
- Bắt buộc:
  - `errors` phải có ít nhất 1 phần tử
  - Mỗi lỗi phải có `code`
- Nguồn: `app/application/services/validation_service.py` và/hoặc các use case validate input
- Bảo mật:
  - Không log thô giá trị nhạy cảm (API key, token, địa chỉ đầy đủ, toạ độ raw nếu là PII theo chính sách)
  - Chỉ truyền `field` ở mức nhãn hiển thị (ví dụ: "Điểm xuất phát", "Điểm đến") thay vì giá trị người dùng nhập

### 2.2 Output
- Kết quả trả về (payload gửi AI):
```json
{
  "type": "USER_VALIDATION_ERROR",
  "locale": "vi",
  "summary": "Dữ liệu chưa hợp lệ, vui lòng kiểm tra và thử lại.",
  "errors": [
    {
      "code": "INVALID_LOCATIONS_COUNT",
      "field": "routePlanningLocations",
      "userMessage": "Cần ít nhất 2 điểm để lập lộ trình.",
      "hint": "Hãy thêm cả điểm xuất phát và điểm đến."
    }
  ],
  "renderingHints": {
    "tone": "helpful",
    "style": "concise",
    "maxChars": 480
  }
}
```
- Side-effects: Không ghi DB, không gọi API ngoài. Chỉ chuẩn hoá payload cho AI/LLM tầng trên.
- Đảm bảo (Guarantees):
  - Không lộ thông tin kỹ thuật nội bộ (stack trace, tên lớp, đường dẫn file)
  - Không lộ secrets/token/PII
  - Thông điệp tập trung "cách người dùng sửa"

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- Timeout mặc định: 10ms (chuyển đổi nội bộ, không I/O)
- Retry & Backoff: Không áp dụng
- Idempotency: Không cần (pure mapping)
- Circuit Breaker: Không áp dụng
- Rate limit/Quota: Không áp dụng
- Bảo mật & Quyền: Không yêu cầu AuthZ riêng (dùng context có sẵn nếu hệ thống yêu cầu)

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-03 |
| **Tên Block** | MapValidationErrorsToUserMessages |
| **Trigger** | From `BLK-1-01-ValidateInput` = Fail |
| **Preconditions** | Có danh sách lỗi validation hợp lệ |
| **Input (schema)** | `{ errors: [{ code, field?, reason?, context? }], locale? }` |
| **Output** | Payload user-facing cho AI (type, summary, errors[], hints) |
| **Side-effects** | Không |
| **Timeout/Retry** | 10ms, no-retry |
| **Idempotency** | N/A |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

- Trigger: từ `BLK-1-01-ValidateInput` trả lỗi `INVALID_LOCATIONS_COUNT`
- Input:
```json
{
  "locale": "vi",
  "errors": [
    { "code": "INVALID_LOCATIONS_COUNT", "field": "routePlanningLocations", "reason": ">= 2 required" },
    { "code": "PARAM_CONFLICT_TIME", "field": "timeOptions", "reason": "departAt & arriveAt cannot coexist" }
  ]
}
```
- Output:
```json
{
  "type": "USER_VALIDATION_ERROR",
  "locale": "vi",
  "summary": "Dữ liệu chưa hợp lệ, vui lòng kiểm tra và thử lại.",
  "errors": [
    {
      "code": "INVALID_LOCATIONS_COUNT",
      "field": "routePlanningLocations",
      "userMessage": "Cần ít nhất 2 điểm (xuất phát và điểm đến) để lập lộ trình.",
      "hint": "Hãy thêm điểm còn thiếu rồi thử lại."
    },
    {
      "code": "PARAM_CONFLICT_TIME",
      "field": "timeOptions",
      "userMessage": "Bạn chỉ nên chọn một trong hai: thời gian xuất phát hoặc thời gian đến.",
      "hint": "Xoá một lựa chọn (departAt hoặc arriveAt) để tiếp tục."
    }
  ],
  "renderingHints": { "tone": "helpful", "style": "concise" }
}
```

---

## 5) Liên kết (References)
- Related Blocks: `BLK-1-01-ValidateInput`
- Related Use Cases: `app/application/services/validation_service.py`
- API Docs (nếu hiển thị qua MCP/REST): xem `app/interfaces/mcp/server.py`

---

## 6) Quy tắc mapping mã lỗi → thông điệp người dùng
- Nguyên tắc chung:
  - Tập trung mô tả vấn đề và cách sửa, tránh thuật ngữ kỹ thuật
  - Câu ngắn gọn, văn phong hỗ trợ, không đổ lỗi cho người dùng
  - Ưu tiên tiếng Việt nếu `locale = 'vi'`, fallback tiếng Anh nếu không có bản địa hoá
- Gợi ý mapping phổ biến:
  - `INVALID_LOCATIONS_COUNT` → "Cần ít nhất 2 điểm để lập lộ trình."
  - `PARAM_CONFLICT_TIME` → "Chỉ chọn một trong hai: thời gian xuất phát hoặc thời gian đến."
  - `INVALID_COORDINATE_FORMAT` → "Định dạng toạ độ chưa đúng (lat, lon). Vui lòng kiểm tra lại."
  - `MISSING_REQUIRED_FIELD:<field>` → "Thiếu thông tin bắt buộc: <Nhãn hiển thị>."
  - Lỗi khác/không biết: thông điệp chung + giữ `code` để AI có thể diễn giải thêm

---

## 7) Error cases (của chính block này)
- Input thiếu `errors` hoặc `errors` rỗng → bỏ qua (không tạo payload)
- Lỗi không có `code` → gán `code = "UNKNOWN_VALIDATION_ERROR"` và dùng thông điệp chung
- `locale` không hỗ trợ → fallback 'vi' hoặc 'en' theo cấu hình toàn hệ thống

---

## 8) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-03-MapValidationErrorsToUserMessages.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định, có ví dụ cụ thể
- [x] Ràng buộc runtime nêu rõ (timeout, retry)
- [x] Có bảng tóm tắt
- [x] Có quy tắc mapping và fallback an toàn không lộ thông tin kỹ thuật


