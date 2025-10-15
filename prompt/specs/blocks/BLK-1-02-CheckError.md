# BLK-1-02 — Check Error

Mục tiêu: Kiểm tra xem có lỗi validation xảy ra sau BLK-1-01 hay không, để phân nhánh xử lý (lỗi → BLK-1-03, thành công → tiếp tục).

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi trực tiếp từ BLK-1-01 (ValidateInput) hoàn thành
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - BLK-1-01 đã thực thi xong (có hoặc không có lỗi)
  - Có kết quả validation (errors list hoặc validated data)

- **Điều kiện dừng/không chạy (Guards):**
  - Không có (luôn chạy sau BLK-1-01)

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```python
{
  "validation_result": {
    "is_valid": bool,
    "errors": List[ValidationError] | None,
    "validated_data": dict | None
  }
}
```

- **Bắt buộc:**
  - `is_valid`: boolean flag
  - `errors`: danh sách lỗi nếu có (hoặc None/empty)
  - `validated_data`: dữ liệu đã validate nếu thành công

- **Nguồn:** Output từ BLK-1-01-ValidateInput

- **Bảo mật:** Không áp dụng (chỉ kiểm tra cấu trúc)

### 2.2 Output
- **Kết quả trả về:**
  - **Case 1 (has errors):** Forward errors → BLK-1-03 (MapValidationErrorsToUserMessages)
  - **Case 2 (no errors):** Forward validated_data → BLK-1-04 hoặc BLK-1-07 (tùy flow)

- **Side-effects:** 
  - Ghi log decision: `"Validation failed with N errors"` hoặc `"Validation passed"`

- **Đảm bảo (Guarantees):**
  - Chỉ một trong hai nhánh được thực thi
  - Không modify dữ liệu, chỉ routing logic

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** < 1ms (pure decision logic)
- **Retry & Backoff:** Không áp dụng
- **Idempotency:** N/A (deterministic)
- **Circuit Breaker:** Không áp dụng
- **Rate limit/Quota:** Không áp dụng
- **Bảo mật & Quyền:** Không yêu cầu

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-02 |
| **Tên Block** | CheckError |
| **Trigger** | From BLK-1-01 (ValidateInput) completed |
| **Preconditions** | Có validation_result từ BLK-1-01 |
| **Input (schema)** | `{ is_valid: bool, errors: List, validated_data: dict }` |
| **Output** | Branch: errors → BLK-1-03, success → BLK-1-04/BLK-1-07 |
| **Side-effects** | Log decision |
| **Timeout/Retry** | < 1ms, no retry |
| **Idempotency** | N/A |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ cụ thể

### Case 1: Có lỗi validation
**Input:**
```python
{
  "validation_result": {
    "is_valid": False,
    "errors": [
      {"code": "INVALID_LOCATIONS_COUNT", "field": "routePlanningLocations", "reason": ">= 2 required"}
    ],
    "validated_data": None
  }
}
```

**Output:**
- Branch: `has_errors = True` → Forward to **BLK-1-03**
- Log: `WARNING: Validation failed with 1 error(s): INVALID_LOCATIONS_COUNT`

### Case 2: Validation thành công
**Input:**
```python
{
  "validation_result": {
    "is_valid": True,
    "errors": None,
    "validated_data": {
      "origin": {"lat": 21.0285, "lon": 105.8542},
      "destination": {"lat": 10.8231, "lon": 106.6297},
      "travelMode": "car"
    }
  }
}
```

**Output:**
- Branch: `has_errors = False` → Forward to **BLK-1-04** (hoặc BLK-1-07 tùy context)
- Log: `INFO: Validation passed, proceeding to next step`

---

## 5) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Decision node "Lỗi?"
- **Related Blocks:** 
  - ← BLK-1-01-ValidateInput (input source)
  - → BLK-1-03-MapValidationErrorsToUserMessages (error path)
  - → BLK-1-04-CheckDestinationExists (success path)
  - → BLK-1-07-SaveRequestHistory (parallel/async)
- **Related Code:**
  - `app/application/services/validation_service.py` - Validation logic
  - `app/interfaces/mcp/server.py` - Request handler routing

---

## 6) Error cases
- **Invalid validation_result structure:** → Default to `has_errors = True` và forward đến error handling
- **Null/undefined validation_result:** → Log critical error, return system error

---

## 6) **Nghiệm thu kết quả (Acceptance Criteria)**

### 6.1 Tiêu chí nghiệm thu chung
- [ ] **Functional Requirements:** Block kiểm tra đúng validation result và phân nhánh xử lý
- [ ] **Input Validation:** Xử lý đúng các trường hợp validation_result hợp lệ và không hợp lệ
- [ ] **Output Format:** Chuyển tiếp đúng đến BLK-1-03 (error) hoặc BLK-1-04/BLK-1-07 (success)
- [ ] **Error Handling:** Xử lý đúng các trường hợp validation_result null/undefined
- [ ] **Performance:** Kiểm tra hoàn thành trong thời gian < 10ms (simple boolean check)
- [ ] **Security:** Không expose sensitive data trong routing decision

### 6.2 Test Cases bắt buộc

#### 6.2.1 Happy Path Tests
- [ ] **Valid Success Result:** Test với is_valid=true, errors=null → forward to success path
- [ ] **Valid Error Result:** Test với is_valid=false, errors=[...] → forward to error path

#### 6.2.2 Error Handling Tests  
- [ ] **Null Validation Result:** Test với validation_result=null → default to error path
- [ ] **Invalid Structure:** Test với validation_result thiếu required fields → default to error path
- [ ] **Undefined Result:** Test với validation_result=undefined → log critical error

#### 6.2.3 Edge Cases Tests
- [ ] **Empty Errors Array:** Test với is_valid=false, errors=[] → forward to error path
- [ ] **Mixed State:** Test với is_valid=true nhưng có errors → forward to error path
- [ ] **Malformed Data:** Test với validation_result có cấu trúc sai → default to error path

### 6.3 Ví dụ Test Cases mẫu

**Ví dụ cho block "CheckError":**
```json
// Test Case 1: Success Path
Input: {
  "validation_result": {
    "is_valid": true,
    "errors": null,
    "validated_data": {"routePlanningLocations": "52.50931,13.42936:52.50274,13.43872"}
  }
}
Expected: Forward to BLK-1-04 or BLK-1-07 (success path)

// Test Case 2: Error Path
Input: {
  "validation_result": {
    "is_valid": false,
    "errors": [{"code": "INVALID_LOCATIONS_COUNT", "message": "Cần ít nhất 2 điểm"}],
    "validated_data": null
  }
}
Expected: Forward to BLK-1-03 (error path)

// Test Case 3: Null Input
Input: {
  "validation_result": null
}
Expected: Default to error path, log critical error
```

### 6.4 Checklist nghiệm thu cuối
- [ ] **Code Review:** Code đã được review bởi senior developer
- [ ] **Unit Tests:** Tất cả test cases đã pass (coverage ≥ 90%)
- [ ] **Integration Tests:** Test tích hợp với BLK-1-01, BLK-1-03, BLK-1-04
- [ ] **Documentation:** Code có comment và documentation đầy đủ
- [ ] **Performance Test:** Đáp ứng < 10ms decision time
- [ ] **Security Review:** Đã kiểm tra data handling
- [ ] **Deployment:** Deploy thành công và hoạt động ổn định

---

## 7) Decision Logic (Pseudo-code)
```python
def check_error(validation_result: ValidationResult) -> str:
    """
    Returns: 'error_path' | 'success_path'
    """
    if not validation_result.is_valid or validation_result.errors:
        log.warning(f"Validation failed with {len(validation_result.errors)} error(s)")
        return 'error_path'  # → BLK-1-03
    else:
        log.info("Validation passed")
        return 'success_path'  # → BLK-1-04 or BLK-1-07
```

---

## 8) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-02-CheckError.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với 2 cases (error/success)
- [x] Ràng buộc runtime nêu rõ
- [x] Có bảng tóm tắt
- [x] Có pseudo-code minh họa decision logic
- [x] Liên kết đến blocks upstream/downstream

---

> **Lưu ý:** Đây là decision node đơn giản (diamond trong flowchart). Không thực hiện business logic, chỉ routing dựa trên flag.

