# BLK-1-10 — Check API Success

Mục tiêu: Kiểm tra xem API response từ BLK-1-09 có thành công hay không, để định tuyến sang xử lý success data hoặc error handling.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi trực tiếp sau BLK-1-09 (RequestRoutingAPI) hoàn thành
  - [x] Luôn chạy bất kể API success hay fail
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Có API response từ BLK-1-09 (success hoặc error object)
  - Response đã được parse thành structured format

- **Điều kiện dừng/không chạy (Guards):**
  - Không có (luôn chạy sau API call)

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:** Output từ BLK-1-09
```python
{
  "success": bool,
  "route_data": dict | None,  # Nếu success = True
  "error": {  # Nếu success = False
    "code": str,
    "message": str,
    "status_code": int,
    "retry_after": int | None
  } | None,
  "metadata": {
    "provider": str,
    "request_duration_ms": int,
    "request_id": str
  }
}
```

- **Bắt buộc:**
  - `success`: boolean flag
  - `metadata.request_id` cho tracing

- **Nguồn:** BLK-1-09 (RequestRoutingAPI)

- **Bảo mật:** Không áp dụng (chỉ routing logic)

### 2.2 Output
- **Kết quả trả về:**
  - **Case 1 (success = True):**
    ```python
    {
      "api_success": True,
      "route_data": {...},  # Forward to BLK-1-12
      "next_action": "TRANSFORM_SUCCESS_DATA"
    }
    ```
    → Forward to **BLK-1-12** (TransformSuccessDataForAI)
  
  - **Case 2 (success = False):**
    ```python
    {
      "api_success": False,
      "error": {...},  # Forward to BLK-1-11 or BLK-1-05
      "next_action": "HANDLE_ERROR"
    }
    ```
    → Forward to **BLK-1-11** (ClassifyAndFormatErrorOutput) hoặc **BLK-1-05** (ClassifyErrorType)

- **Side-effects:**
  - Log decision: `"API call success"` hoặc `"API call failed: {error_code}"`
  - Increment metrics:
    - `api_success_count` hoặc `api_error_count`

- **Đảm bảo (Guarantees):**
  - Chỉ một trong hai nhánh được thực thi
  - Không modify dữ liệu, chỉ routing

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** < 1ms (pure decision logic)
- **Retry & Backoff:** Không áp dụng
- **Idempotency:** Yes (deterministic)
- **Circuit Breaker:** Không áp dụng
- **Rate limit/Quota:** Không áp dụng
- **Bảo mật & Quyền:** Không yêu cầu

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-10 |
| **Tên Block** | CheckAPISuccess |
| **Trigger** | From BLK-1-09 (RequestRoutingAPI) completed |
| **Preconditions** | Có API response (success hoặc error) |
| **Input (schema)** | `{ success: bool, route_data?, error?, metadata }` |
| **Output** | Branch: success → BLK-1-12, fail → BLK-1-11/BLK-1-05 |
| **Side-effects** | Log decision, increment metrics |
| **Timeout/Retry** | < 1ms, no retry |
| **Idempotency** | Yes |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

### Case 1: API call thành công
**Input:**
```python
{
  "success": True,
  "route_data": {
    "summary": {
      "length_in_meters": 1730000,
      "travel_time_in_seconds": 72000,
      "traffic_delay_in_seconds": 1800
    },
    "legs": [...],
    "guidance": {
      "instructions": [...]
    }
  },
  "error": None,
  "metadata": {
    "provider": "tomtom",
    "request_duration_ms": 1850,
    "request_id": "req-123"
  }
}
```

**Decision:**
- `success = True` → **SUCCESS path**

**Output:**
```python
{
  "api_success": True,
  "route_data": {
    "summary": {...},
    "legs": [...],
    "guidance": {...}
  },
  "next_action": "TRANSFORM_SUCCESS_DATA"
}
```

**Log:**
```
INFO: API call success for request req-123 (duration: 1850ms, provider: tomtom)
```

**Metrics:**
```
api_success_count{provider="tomtom"} += 1
```

**Next:** → **BLK-1-12** (TransformSuccessDataForAI)

---

### Case 2: API call thất bại (client error - 400)
**Input:**
```python
{
  "success": False,
  "route_data": None,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid coordinates format",
    "status_code": 400,
    "retry_after": None
  },
  "metadata": {
    "provider": "tomtom",
    "request_duration_ms": 250,
    "request_id": "req-456"
  }
}
```

**Decision:**
- `success = False` → **ERROR path**
- `status_code = 400` → Client error (likely user error)

**Output:**
```python
{
  "api_success": False,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid coordinates format",
    "status_code": 400
  },
  "next_action": "HANDLE_ERROR"
}
```

**Log:**
```
WARNING: API call failed for request req-456: INVALID_REQUEST (status: 400)
```

**Metrics:**
```
api_error_count{provider="tomtom", error_code="INVALID_REQUEST", status="400"} += 1
```

**Next:** → **BLK-1-05** (ClassifyErrorType) → Sẽ classify là USER_ERROR

---

### Case 3: API call thất bại (server error - 503)
**Input:**
```python
{
  "success": False,
  "route_data": None,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "TomTom routing service temporarily unavailable",
    "status_code": 503,
    "retry_after": 60
  },
  "metadata": {
    "provider": "tomtom",
    "request_duration_ms": 10000,
    "request_id": "req-789"
  }
}
```

**Decision:**
- `success = False` → **ERROR path**
- `status_code = 503` → Server error (system error)

**Output:**
```python
{
  "api_success": False,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "TomTom routing service temporarily unavailable",
    "status_code": 503,
    "retry_after": 60
  },
  "next_action": "HANDLE_ERROR"
}
```

**Log:**
```
ERROR: API call failed for request req-789: SERVICE_UNAVAILABLE (status: 503, retry_after: 60s)
```

**Metrics:**
```
api_error_count{provider="tomtom", error_code="SERVICE_UNAVAILABLE", status="503"} += 1
```

**Next:** → **BLK-1-05** (ClassifyErrorType) → Sẽ classify là SYSTEM_ERROR → **BLK-1-06** (HandleSystemError)

---

## 5) Decision Logic (Pseudo-code)

```python
def check_api_success(api_response: APIResponse) -> DecisionResult:
    """
    Returns: 'success_path' | 'error_path'
    """
    request_id = api_response.metadata.request_id
    
    if api_response.success:
        log.info(f"API call success for request {request_id}")
        metrics.increment("api_success_count", {"provider": api_response.metadata.provider})
        
        return DecisionResult(
            api_success=True,
            route_data=api_response.route_data,
            next_action="TRANSFORM_SUCCESS_DATA"
        )
    else:
        error = api_response.error
        log.warning(
            f"API call failed for request {request_id}: {error.code} "
            f"(status: {error.status_code})"
        )
        metrics.increment("api_error_count", {
            "provider": api_response.metadata.provider,
            "error_code": error.code,
            "status": str(error.status_code)
        })
        
        return DecisionResult(
            api_success=False,
            error=error,
            next_action="HANDLE_ERROR"
        )
```

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Decision node "success?"
- **Related Blocks:**
  - ← BLK-1-09-RequestRoutingAPI (input source)
  - → BLK-1-12-TransformSuccessDataForAI (success path)
  - → BLK-1-11-ClassifyAndFormatErrorOutput (error path - nếu từ API response)
  - → BLK-1-05-ClassifyErrorType (error path - general classification)
- **Related Code:**
  - `app/interfaces/mcp/server.py` - Request handler routing logic
  - `app/application/use_cases/calculate_route.py` - Use case orchestration

---

## 7) Metrics & Monitoring

### Success Metrics
```
api_success_count{provider="tomtom"} 
api_success_rate{provider="tomtom"} = success_count / (success_count + error_count)
```

### Error Metrics (by category)
```
api_error_count{provider="tomtom", error_code="INVALID_REQUEST", status="400"}
api_error_count{provider="tomtom", error_code="SERVICE_UNAVAILABLE", status="503"}
api_error_count{provider="tomtom", error_code="TIMEOUT", status="0"}
```

### Alerting Rules
- **Alert:** API success rate < 95% over 5 min → WARNING
- **Alert:** API success rate < 80% over 5 min → CRITICAL
- **Alert:** 5xx errors > 10 in 1 min → Ops notification

---

## 8) Error cases của chính block này
- **Null/undefined API response:** → Default to `api_success = False`, forward to error handling
- **Invalid response structure:** → Log critical error, treat as SYSTEM_ERROR

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

**Ví dụ cho block "BLK 1 10 CheckAPISuccess":**
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
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-10-CheckAPISuccess.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với 2 cases (success/error)
- [x] Ví dụ cụ thể cho cả success, client error, server error
- [x] Pseudo-code cho decision logic
- [x] Metrics tracking cho success/error rates
- [x] Liên kết đến downstream blocks (BLK-1-12 và BLK-1-05/BLK-1-11)

---

> **Lưu ý:** Đây là decision node quan trọng để phân luồng success vs error từ external API. Logging và metrics tại đây giúp monitor API health và debug issues.

