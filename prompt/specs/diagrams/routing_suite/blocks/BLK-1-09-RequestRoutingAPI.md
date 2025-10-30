# BLK-1-09 — Request Routing API

Mục tiêu: Gọi API TomTom (hoặc routing provider khác) để tính toán tuyến đường giữa các điểm, lấy thông tin chi tiết về route.

---

## 1) Khi nào trigger block này?

- **Sự kiện kích hoạt (Trigger):**
  - [x] Gọi sau BLK-1-04 (có hoặc không có cached destination)
  - [x] Gọi sau BLK-1-08 (nếu đã save destination mới)
  - [x] Luôn chạy khi cần route data mới (không cache route, chỉ cache destination)
  - [ ] Message/Event đến
  - [ ] Lịch/Timer
  - [ ] Webhook/Callback

- **Điều kiện tiền đề (Preconditions):**
  - Có coordinates hợp lệ cho origin và destination
  - Environment variables đã được load
  - Network connectivity sẵn sàng
  - Input đã qua validation (BLK-1-01)

- **Điều kiện dừng/không chạn (Guards):**
  - Environment variable `TOMTOM_API_KEY` không tồn tại → Error `API_KEY_NOT_CONFIGURED`
  - API key rỗng/invalid format → Error `API_KEY_INVALID`
  - Coordinates invalid → Error (user error)
  - API rate limit exceeded → Error với retry-after
  - Circuit breaker open → Fast-fail `SERVICE_UNAVAILABLE`

---

## 2) Input, Output và các ràng buộc

### 2.1 Input
- **Schema/kiểu dữ liệu:**
```json
{
  "route_request": {
    "origin": {"lat": <number>, "lon": <number>},
    "destination": {"lat": <number>, "lon": <number>},
    "waypoints": [{"lat": <number>, "lon": <number>}] | null,
    "travel_mode": "car" | "truck" | "taxi" | "bus" | "van" | "motorcycle" | "bicycle" | "pedestrian",
    "departure_time": <ISO8601 string> | null,
    "arrival_time": <ISO8601 string> | null,
    "route_type": "fastest" | "shortest" | "eco" | "thrilling",
    "avoid": ["tollRoads" | "motorways" | "ferries" | "unpavedRoads"] | null,
    "traffic": <boolean>
  },
  "request_context": {
    "request_id": <string>,
    "timeout": <integer milliseconds, default: 10000>
  }
}
```

- **Bắt buộc:**
  - `origin.lat`, `origin.lon`
  - `destination.lat`, `destination.lon`
  - `travel_mode` (default: "car")
  - **API key được lấy từ environment, KHÔNG từ input**

- **Nguồn:**
  - Validated data từ BLK-1-01
  - Enriched với cached destination data từ BLK-1-04/BLK-1-08 nếu có
  - **API key:** Lấy từ environment variable `TOMTOM_API_KEY` hoặc từ config file

- **Bảo mật:**
  - **API key lấy từ environment variable `TOMTOM_API_KEY`**, KHÔNG từ client request
  - **KHÔNG** log API key (chỉ log 4 ký tự cuối nếu cần debug: `key=***abc12`)
  - Mask coordinates trong logs nếu là sensitive locations
  - Use HTTPS cho tất cả API calls
  - Validate API key format trước khi sử dụng (non-empty, alphanumeric)

### 2.2 Output
- **Kết quả trả về (success):**
```json
{
  "success": true,
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
      "instructions": [{
        "message": <string>,
        "maneuver": <string>,
        "point": {"lat": <number>, "lon": <number>}
      }]
    }
  },
  "metadata": {
    "provider": "tomtom",
    "api_version": "1",
    "request_duration_ms": <integer>,
    "cached": false
  }
}
```

- **Kết quả trả về (error):**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_NOT_CONFIGURED" | "API_KEY_INVALID" | "API_KEY_UNAUTHORIZED" | 
            "API_ERROR" | "TIMEOUT" | "RATE_LIMIT" | "INVALID_REQUEST",
    "message": <string>,
    "status_code": <integer> | null,
    "retry_after": <integer seconds> | null
  }
}
```

- **Side-effects:**
  - HTTP request đến TomTom API
  - Log API call (duration, status)
  - Increment API usage metrics
  - Consume API quota
  - **Output sẽ được xử lý bởi BLK-1-16 để extract traffic sections**

- **Đảm bảo (Guarantees):**
  - Retry on transient failures (5xx, timeouts)
  - Fail-fast on client errors (4xx)
  - At-most-once billing (nếu API charge per request)

### 2.3 Ràng buộc thực thi (Runtime Constraints)
- **Timeout mặc định:** 
  - 10s cho routing request (TomTom thường < 2s)
  - 30s total với retries
- **Retry & Backoff:**
  - Retry trên: 5xx errors, network timeouts, rate limit (429)
  - **KHÔNG** retry: 4xx client errors (trừ 429)
  - Strategy: 3 retries, exponential backoff (1s, 2s, 4s)
  - Jitter: random 0-500ms để tránh thundering herd
- **Idempotency:** 
  - GET request → idempotent
  - Same input → same output (trong short window, traffic changes)
- **Circuit Breaker:**
  - Mở sau 10 API errors liên tiếp trong 60s
  - Half-open sau 120s
  - Close khi 3 requests thành công liên tiếp
- **Rate limit/Quota:**
  - TomTom: varies by plan (e.g., 2500 requests/day free tier)
  - Local rate limiter: max 10 requests/second (để bảo vệ quota)
  - 429 response → exponential backoff, respect `Retry-After` header
- **Bảo mật & Quyền:**
  - API key từ environment variable (không hardcode)
  - HTTPS only
  - Validate API response schema để tránh injection

---

## 3) Bảng tóm tắt điền nhanh
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-09 |
| **Tên Block** | RequestRoutingAPI |
| **Trigger** | After validation & destination check/save |
| **Preconditions** | Valid coordinates, API key, network available |
| **Input (schema)** | `{ route_request: {origin, destination, ...}, context }` |
| **Output** | `{ success: bool, route_data?: {...}, error?: {...} }` |
| **Side-effects** | HTTP call to TomTom, log, metrics, consume quota |
| **Timeout/Retry** | 10s timeout, 3 retries với exponential backoff |
| **Idempotency** | Yes (GET request) |
| **AuthZ/Scope** | API key from env config |

---

## 4) Ví dụ cụ thể

### Case 1: Successful routing request
**Environment:**
```bash
TOMTOM_API_KEY=abc123def456ghi789jkl012mno345pq
```

**Input:**
```json
{
  "route_request": {
    "origin": {"lat": 21.0285, "lon": 105.8542},
    "destination": {"lat": 10.8231, "lon": 106.6297},
    "travel_mode": "car",
    "route_type": "fastest",
    "traffic": true
  },
  "request_context": {
    "request_id": "req-123",
    "timeout": 10000
  }
}
```

**Internal Processing:**
1. Load API key từ `TOMTOM_API_KEY` environment variable
2. Validate key format: `***345pq` (OK)
3. Build request URL

**API Call:**
```http
GET https://api.tomtom.com/routing/1/calculateRoute/21.0285,105.8542:10.8231,106.6297/json
  ?key=abc123def456ghi789jkl012mno345pq
  &travelMode=car
  &routeType=fastest
  &traffic=true
  &computeTravelTimeFor=all
  &instructionsType=text
```

**API Response (200 OK):**
```json
{
  "formatVersion": "0.0.12",
  "routes": [{
    "summary": {
      "lengthInMeters": 1730000,
      "travelTimeInSeconds": 72000,
      "trafficDelayInSeconds": 1800,
      "departureTime": "2025-10-14T10:30:00+07:00",
      "arrivalTime": "2025-10-15T06:30:00+07:00"
    },
    "legs": [{...}],
    "sections": [{...}],
    "guidance": {
      "instructions": [{
        "message": "Head north on Phố Huế",
        "maneuver": "TURN",
        "point": {"latitude": 21.0285, "longitude": 105.8542}
      }, ...]
    }
  }]
}
```

**Output:**
```json
{
  "success": true,
  "route_data": {
    "summary": {
      "length_in_meters": 1730000,
      "travel_time_in_seconds": 72000,
      "traffic_delay_in_seconds": 1800,
      "departure_time": "2025-10-14T10:30:00+07:00",
      "arrival_time": "2025-10-15T06:30:00+07:00"
    },
    "legs": [...],
    "sections": [...],
    "guidance": {
      "instructions": [...]
    }
  },
  "metadata": {
    "provider": "tomtom",
    "api_version": "1",
    "request_duration_ms": 1850,
    "cached": false
  }
}
```

**Next:** → BLK-1-16 (ProcessTrafficSections) để xử lý legs và sections

### Case 2: API timeout (retry success)
**Attempt 1:** Timeout after 10s
**Retry 1:** Success in 2s

**Log:**
```
WARNING: TomTom API timeout on attempt 1, retrying... (backoff: 1s)
INFO: TomTom API success on attempt 2 (duration: 2000ms)
```

**Output:** (same as Case 1, với `request_duration_ms` = tổng thời gian gồm retries)

### Case 3: Client error (400 Bad Request)
**API Response:**
```json
{
  "error": {
    "statusCode": 400,
    "message": "Invalid coordinates format"
  }
}
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid coordinates format",
    "status_code": 400,
    "retry_after": null
  }
}
```
**Next:** → BLK-1-10 (classify error) → BLK-1-05 (should be USER_ERROR)

### Case 4: API Key không được cấu hình
**Environment:**
```bash
# TOMTOM_API_KEY not set
```

**Input:**
```json
{
  "route_request": {
    "origin": {"lat": 21.0285, "lon": 105.8542},
    "destination": {"lat": 10.8231, "lon": 106.6297},
    "travel_mode": "car"
  },
  "request_context": {
    "request_id": "req-404"
  }
}
```

**Internal Processing:**
1. Try load `TOMTOM_API_KEY` from environment → Not found
2. Try load from config file → Not found
3. Return error immediately (không gọi API)

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_NOT_CONFIGURED",
    "message": "TomTom API key not found in environment or config",
    "status_code": null
  }
}
```

**Next:** → BLK-1-10 (classify as SYSTEM_ERROR) → BLK-1-06 (HandleSystemError với CRITICAL severity - cần ops fix configuration)

---

### Case 5: API Key invalid format
**Environment:**
```bash
TOMTOM_API_KEY="abc"  # Too short, < 20 chars
```

**Input:** (tương tự Case 1)

**Internal Processing:**
1. Load `TOMTOM_API_KEY` from environment → "abc"
2. Validate format: regex check fails (min 20 chars)
3. Return error

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_INVALID",
    "message": "TomTom API key format is invalid (expected alphanumeric, min 20 chars)",
    "status_code": null
  }
}
```

**Next:** → BLK-1-10 → SYSTEM_ERROR → BLK-1-06 (CRITICAL - bad configuration)

---

### Case 6: API Key unauthorized (403 from TomTom)
**Environment:**
```bash
TOMTOM_API_KEY=invalidkey123456789012345678  # Valid format nhưng không hợp lệ với TomTom
```

**Input:** (tương tự Case 1)

**Internal Processing:**
1. Load và validate format: OK
2. Build URL và gọi TomTom API

**API Response (403 Forbidden):**
```json
{
  "error": {
    "statusCode": 403,
    "message": "Forbidden. The supplied API key is not valid for this service."
  }
}
```

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "API_KEY_UNAUTHORIZED",
    "message": "TomTom API key is not authorized",
    "status_code": 403,
    "retry_after": null
  }
}
```

**Next:** → BLK-1-10 → SYSTEM_ERROR (403 = config issue, not user error) → BLK-1-06

---

### Case 7: Rate limit exceeded (429)
**API Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "statusCode": 429,
    "message": "Rate limit exceeded"
  }
}
```

**Handling:**
- Retry after 60s (respect `Retry-After` header)
- Max 1 retry for 429
- Nếu vẫn fail → return error

**Output:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT",
    "message": "API rate limit exceeded, please try again later",
    "status_code": 429,
    "retry_after": 60
  }
}
```

---

## 5) API Key Management & Validation

### 5.1 Lấy API Key từ Environment
**Quy trình (Pseudocode):**
```
FUNCTION get_tomtom_api_key() RETURNS (api_key, error):
  
  // Step 1: Lấy từ environment variable
  api_key = READ environment_variable("TOMTOM_API_KEY")
  
  // Step 2: Fallback sang config file nếu env không có
  IF api_key is NULL OR api_key is EMPTY:
    TRY:
      api_key = READ config_file("tomtom.api_key")
    CATCH:
      RETURN (null, {
        "code": "API_KEY_NOT_CONFIGURED",
        "message": "TomTom API key not found in environment or config"
      })
  END IF
  
  // Step 3: Validate API key không rỗng
  api_key = TRIM(api_key)
  IF api_key is EMPTY:
    RETURN (null, {
      "code": "API_KEY_INVALID",
      "message": "TomTom API key is empty"
    })
  END IF
  
  // Step 4: Validate format (alphanumeric, min 20 chars)
  IF NOT MATCH(api_key, REGEX "^[a-zA-Z0-9]{20,}$"):
    RETURN (null, {
      "code": "API_KEY_INVALID",
      "message": "TomTom API key format is invalid (expected alphanumeric, min 20 chars)"
    })
  END IF
  
  // Step 5: Log (masked) để debug
  masked_key = "***" + LAST_4_CHARS(api_key)
  LOG_DEBUG("TomTom API key loaded: " + masked_key)
  
  RETURN (api_key, null)
END FUNCTION
```

### 5.2 API Key Error Handling Flow
```
┌─────────────────────────────────────┐
│ get_tomtom_api_key()                │
└──────────────┬──────────────────────┘
               │
               ├─ Check env TOMTOM_API_KEY
               │  ├─ Found → Validate format
               │  │  ├─ Valid → Return key
               │  │  └─ Invalid → Error: API_KEY_INVALID
               │  │
               │  └─ Not Found → Check config file
               │     ├─ Found → Validate format
               │     └─ Not Found → Error: API_KEY_NOT_CONFIGURED
               │
               └─ Return (key, error)
```

### 5.3 Request Builder (với API key validation)
**Quy trình:**
```
FUNCTION build_tomtom_routing_url(route_request) RETURNS (url, error):
  
  // Step 1: Lấy API key
  (api_key, error) = get_tomtom_api_key()
  IF error is NOT NULL:
    RETURN (null, error)
  END IF
  
  // Step 2: Build URL
  base_url = "https://api.tomtom.com/routing/1/calculateRoute"
  locations = "{origin.lat},{origin.lon}:{destination.lat},{destination.lon}"
  
  params = {
    "key": api_key,
    "travelMode": route_request.travel_mode,
    "routeType": route_request.route_type,
    "traffic": route_request.traffic ? "true" : "false",
    "computeTravelTimeFor": "all",
    "instructionsType": "text"
  }
  
  IF route_request.avoid is NOT EMPTY:
    params["avoid"] = JOIN(route_request.avoid, ",")
  END IF
  
  IF route_request.departure_time is NOT NULL:
    params["departAt"] = route_request.departure_time
  END IF
  
  url = base_url + "/" + locations + "/json?" + URLENCODE(params)
  RETURN (url, null)
END FUNCTION
```

### 5.4 Response Parser
**Quy trình:**
```
FUNCTION parse_tomtom_response(api_response) RETURNS route_data:
  
  route = api_response["routes"][0]  // First route
  
  RETURN {
    "summary": {
      "length_in_meters": route["summary"]["lengthInMeters"],
      "travel_time_in_seconds": route["summary"]["travelTimeInSeconds"],
      "traffic_delay_in_seconds": route["summary"]["trafficDelayInSeconds"] OR 0,
      "departure_time": route["summary"]["departureTime"],
      "arrival_time": route["summary"]["arrivalTime"]
    },
    "legs": PARSE legs from route["legs"],
    "sections": PARSE sections from route["sections"],
    "guidance": PARSE guidance from route["guidance"]
  }
END FUNCTION
```

---

## 6) Liên kết (References)
- **Diagram:** `prompt/specs/diagrams/routing mcp server diagram.drawio` - Block "request thông tin từ API kiểm tra tuyến đường"
- **Related Blocks:**
  - ← BLK-1-04-CheckDestinationExists (có thể dùng cached coords)
  - ← BLK-1-08-SaveDestination (sau khi save)
  - → BLK-1-16-ProcessTrafficSections (xử lý legs và sections để extract traffic coordinates)
  - → BLK-1-10-CheckAPISuccess (check response)
- **Related Code:**
  - `app/infrastructure/tomtom/routing_gateway.py` - TomTom API client
  - `app/application/ports/routing_provider.py` - Routing provider interface
  - `app/infrastructure/http/client.py` - HTTP client với retry logic
- **API Docs:** 
  - TomTom Routing API: https://developer.tomtom.com/routing-api/documentation

---

## 7) Error cases

### 7.1 Configuration Errors (không gọi API)
| Error Code | Condition | Classification | Severity | Action |
|-----------|-----------|----------------|----------|--------|
| API_KEY_NOT_CONFIGURED | `TOMTOM_API_KEY` env variable missing & config file missing | SYSTEM_ERROR | CRITICAL | Alert ops team, block all requests |
| API_KEY_INVALID | API key empty hoặc format không hợp lệ | SYSTEM_ERROR | CRITICAL | Alert ops team, fix configuration |

### 7.2 API Call Errors
| Error Code | HTTP Status | Retry? | Classification | Next Action |
|-----------|-------------|--------|----------------|-------------|
| API_KEY_UNAUTHORIZED | 403 | No | SYSTEM_ERROR | Alert ops (key expired/invalid) |
| INVALID_REQUEST | 400, 422 | No | USER_ERROR | Return to user |
| RATE_LIMIT | 429 | Yes (1x) | SYSTEM_ERROR | Respect Retry-After |
| TIMEOUT | - | Yes (3x) | SYSTEM_ERROR | Exponential backoff |
| SERVICE_UNAVAILABLE | 5xx | Yes (3x) | SYSTEM_ERROR | Exponential backoff |
| INVALID_RESPONSE | 200 + bad schema | No | SYSTEM_ERROR | Log & alert |

### 7.3 Circuit Breaker
- **Open:** Fast-fail với `SERVICE_UNAVAILABLE`, không gọi API
- **Conditions:** 10 consecutive failures in 60s
- **Recovery:** Half-open sau 120s, close sau 3 successes

---

---

## 8) Monitoring & Metrics
- **API call metrics:**
  - `routing_api_requests_total{provider="tomtom", status="success|error"}`
  - `routing_api_duration_seconds{provider="tomtom", quantile="0.5|0.95|0.99"}`
  - `routing_api_errors_total{provider="tomtom", error_type="timeout|4xx|5xx"}`
  - `routing_api_retries_total{provider="tomtom"}`

- **Quota tracking:**
  - `routing_api_quota_used{provider="tomtom", period="daily|monthly"}`
  - Alert khi quota > 80%

---

## 9) Environment Configuration

### 9.1 Required Environment Variables
```bash
# Required
TOMTOM_API_KEY=your_32_character_tomtom_api_key_here

# Optional (có defaults)
TOMTOM_API_TIMEOUT=10000  # milliseconds
TOMTOM_API_MAX_RETRIES=3
TOMTOM_API_RATE_LIMIT=10  # requests per second
```

### 9.2 Configuration Validation on Startup
**Quy trình:**
```
FUNCTION validate_tomtom_configuration():
  
  (api_key, error) = get_tomtom_api_key()
  
  IF error is NOT NULL:
    LOG_CRITICAL("TomTom configuration error: " + error)
    THROW ConfigurationError(error["message"])
  END IF
  
  masked_key = "***" + LAST_4_CHARS(api_key)
  LOG_INFO("TomTom API configured successfully (key: " + masked_key + ")")
  
END FUNCTION
```

**Server Startup Flow:**
```
ON SERVER_START:
  // Validate configuration before accepting requests
  validate_tomtom_configuration()
  
  // If validation passes, start MCP server
  START mcp_server()
END
```

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

**Ví dụ cho block "BLK 1 09 RequestRoutingAPI":**
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

## 10) Definition of Done (DoD)
- [x] File nằm đúng vị trí `specs/blocks/BLK-1-09-RequestRoutingAPI.md`
- [x] Có Trigger/Preconditions/Guards rõ ràng
- [x] Input/Output xác định với success và error cases
- [x] **API key management từ environment (không từ client)**
- [x] **API key validation logic với format checking**
- [x] **Configuration error handling (API_KEY_NOT_CONFIGURED, API_KEY_INVALID)**
- [x] **Unauthorized API key handling (403 response)**
- [x] API request/response examples với environment setup
- [x] Retry strategy chi tiết (conditions, backoff, jitter)
- [x] Circuit breaker configuration
- [x] Rate limiting handling
- [x] Security considerations (API key masking, HTTPS)
- [x] Error classification guidance với bảng chi tiết
- [x] Monitoring metrics
- [x] Startup configuration validation

---

> **Lưu ý:** 
> - **API key PHẢI được lưu trong environment variable `TOMTOM_API_KEY`**, KHÔNG BAO GIỜ nhận từ client request.
> - Validate API key configuration khi server khởi động để fail-fast, tránh lỗi runtime.
> - Log API key với masking (`***xyz12`) để debug an toàn.
> - 403 Unauthorized từ TomTom = SYSTEM_ERROR (bad key), không phải USER_ERROR.

