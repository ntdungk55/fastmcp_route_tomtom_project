# BLK-1-00 — Listen MCP Request

Mục tiêu: Lắng nghe và nhận request từ MCP Client, parse payload ban đầu để chuyển tiếp vào pipeline xử lý.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] MCP Client gửi request đến MCP Server (qua stdio/HTTP transport)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - MCP Server đã khởi động và lắng nghe trên transport (stdio/SSE/HTTP)
  - Connection với MCP Client đã được thiết lập
  - Request payload hợp lệ theo MCP protocol (JSON-RPC 2.0)

- **Điều kiện dừng/không chạy (Guards):**
  - Server chưa khởi động hoặc đang shutdown
  - Connection bị đứt/timeout
  - Payload không phải JSON-RPC hợp lệ → reject ngay ở transport layer

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:** JSON-RPC 2.0 request
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "method": "tools/call",
  "params": {
    "name": "calculate_route",
    "arguments": { ... }
  }
}
```
- **Bắt buộc:**
  - `jsonrpc`: "2.0"
  - `method`: string (tool name hoặc method MCP)
  - `params`: object chứa arguments

- **Nguồn:** MCP Client (Claude Desktop, VSCode, custom client)

- **Bảo mật:**
  - Không log toàn bộ payload nếu chứa API key/token
  - Sanitize sensitive fields trước khi logging

### 2.2 Output
- **Kết quả trả về:**
  - Parsed request object chuyển sang BLK-1-01 (ValidateInput)
  - Request metadata (id, timestamp, client info) cho logging/tracing

- **Side-effects:**
  - Ghi log nhận request (request_id, method, timestamp)
  - Khởi tạo request context (trace_id, span_id nếu có OpenTelemetry)

- **Đảm bảo (Guarantees):**
  - Mỗi request hợp lệ đều được forward đến validation
  - Request không hợp lệ trả lỗi ngay (JSON-RPC error response)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 30s (cho toàn bộ request lifecycle, không riêng block này)
- **Retry & Backoff:** Không áp dụng (client retry nếu cần)
- **Idempotency:** Hỗ trợ `request_id` để track duplicate requests
- **Circuit Breaker:** Không áp dụng ở tầng này
- **Rate limit/Quota:** Có thể áp dụng rate limiting theo client_id/IP
- **Bảo mật & Quyền:** 
  - Validate API key nếu yêu cầu (trong infrastructure config)
  - Check client permissions cho tool access

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-00 |
| **Tên Block** | ListenMCPRequest |
| **Trigger** | MCP Client gửi JSON-RPC request |
| **Preconditions** | Server running, connection established, valid JSON-RPC |
| **Input (schema)** | JSON-RPC 2.0 request { jsonrpc, id, method, params } |
| **Output** | Parsed request object → BLK-1-01 |
| **Side-effects** | Log request, init request context/trace |
| **Timeout/Retry** | 30s total request timeout, no retry |
| **Idempotency** | Track by request_id |
| **AuthZ/Scope** | Validate API key, check tool permissions |

---

## 4) Ví dụ cụ thể

**Input:**
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "method": "tools/call",
  "params": {
    "name": "calculate_route",
    "arguments": {
      "origin": "Hanoi",
      "destination": "Ho Chi Minh City"
    }
  }
}
```

**Output (forward to BLK-1-01):**
```python
{
  "request_id": "req-123",
  "tool_name": "calculate_route",
  "arguments": {
    "origin": "Hanoi",
    "destination": "Ho Chi Minh City"
  },
  "metadata": {
    "timestamp": "2025-10-14T10:30:00Z",
    "trace_id": "trace-abc",
    "client_id": "claude-desktop"
  }
}
```

**Side-effects:**
- Log: `INFO: Received request req-123 for tool calculate_route from claude-desktop`
- Trace context initialized với `trace_id=trace-abc`

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio`
- **Related Blocks:** → BLK-1-01-ValidateInput
- **Related Use Cases:** `app/interfaces/mcp/server.py` - MCP server handlers
- **API Docs:** MCP Protocol Specification (JSON-RPC 2.0)
- **Related Code:**
  - `app/interfaces/mcp/server.py` - FastMCP server setup
  - `app/application/services/request_handler.py` - Request routing

---

## 6) Error cases
- **Invalid JSON-RPC:** → Return JSON-RPC error `-32700` (Parse error)
- **Missing required fields:** → Return JSON-RPC error `-32600` (Invalid Request)
- **Unknown method/tool:** → Return JSON-RPC error `-32601` (Method not found)
- **Server overload:** → Return JSON-RPC error `-32000` (Server error) + retry-after header
- **Authentication failed:** → Return JSON-RPC error `-32001` (Unauthorized)

---

## 7) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-00-ListenMCPRequest.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định, có ví dụ cụ thể
- [x] Ràng buộc runtime nêu rõ (timeout, auth)
- [x] Có bảng tóm tắt
- [x] Error cases được mô tả với JSON-RPC error codes
- [x] Liên kết đến diagram và code liên quan

---

> **Lưu ý:** Block này là entry point của toàn bộ request pipeline. Đảm bảo logging/tracing đầy đủ để troubleshoot issues downstream.
