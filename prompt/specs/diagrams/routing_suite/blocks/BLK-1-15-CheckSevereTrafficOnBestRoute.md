# BLK-1-15 — Check severe traffic on best route (A → B)

Mô tả một dịch vụ bên ngoài (API provider) được gọi bởi block liền kề để kiểm tra: "tuyến tốt nhất A → B hiện có đoạn nào tắc nặng không" và trả dữ liệu đã được chuẩn hoá cho các block phía sau.

---

## 1) Trigger / Preconditions / Guards
- **Trigger:**
  - Được gọi trực tiếp từ block quyết định/tiền xử lý trước đó sau khi input đã hợp lệ (ví dụ: sau ValidateInput và sau khi xác định cặp A→B).
- **Preconditions (Business):**
  - Có đủ thông tin toạ độ điểm xuất phát (A) và điểm đích (B).
  - Ngôn ngữ hiển thị đã chọn (mặc định: vi-VN).
- **Preconditions (Technical):**
  - Kết nối mạng sẵn sàng; DNS và TLS hoạt động.
- **Guards / Idempotency:**
  - Có thể áp dụng idempotency theo cặp `(origin, destination, options)` để tránh gọi lặp.

---

## 2) Input / Output / Ràng buộc

### 2.1 Input (endpoint & tham số)
Endpoint thực tế:
```
https://api.tomtom.com/routing/1/calculateRoute
```

Ví dụ request (tham khảo):
```
https://api.tomtom.com/routing/1/calculateRoute/{{A_LAT}},{{A_LON}}:{{B_LAT}},{{B_LON}}/json?traffic=true&sectionType=traffic&instructionsType=text&language=vi-VN&travelMode=motorcycle
```

Mapping tham số:
- Path points (bắt buộc A,B; có thể có các điểm trung gian C, D, ...):
  - Điểm xuất phát: `{{A_LAT}},{{A_LON}}`
  - Điểm đến: `{{B_LAT}},{{B_LON}}`
  - Điểm trung gian (tuỳ chọn, có thể nhiều điểm): giữ định dạng cặp `lat,lon` phân tách bằng dấu `:` và luôn có `A` ở đầu, `B` ở cuối. Mẫu tổng quát:
    `{{A_LAT}},{{A_LON}}[:{{VIA1_LAT}},{{VIA1_LON}}[:{{VIA2_LAT}},{{VIA2_LON}}[:...]]]:{{B_LAT}},{{B_LON}}`
- Query params (cũng là input của block):
  - `traffic` (boolean, mặc định: true) — yêu cầu thông tin giao thông
  - `sectionType` (string | lặp nhiều lần, mặc định: `traffic`) — dùng để chỉ định loại các đoạn đường (section) đặc biệt mà bạn muốn nhận thông tin chi tiết trong response
  - `instructionsType` (string, mặc định: `text`) — loại thông báo hướng dẫn
  - `language` (string, mặc định: `en-US`) — ngôn ngữ kết quả
  - `travelMode` (string, mặc định: `car`) — phương thức di chuyển. Giá trị hợp lệ:
    - `car` (mặc định)
    - `truck`
    - `taxi`
    - `bus`
    - `van`
    - `motorcycle`
    - `bicycle`
    - `pedestrian`

Schema input (JSON Schema):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "BLK-1-15-input.schema.json",
  "title": "BLK-1-15 CheckSevereTrafficOnBestRoute Input",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "pathPoints": {
      "type": "array",
      "description": "Danh sách điểm theo thứ tự: A (start), các điểm trung gian (C, D, ...), B (end)",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "lat": { "type": "number", "minimum": -90, "maximum": 90 },
          "lon": { "type": "number", "minimum": -180, "maximum": 180 }
        },
        "required": ["lat", "lon"]
      }
    },
    "params": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "traffic": { "type": "boolean", "default": true },
        "sectionType": { "type": "string", "default": "traffic" },
        "instructionsType": { "type": "string", "default": "text" },
        "language": { "type": "string", "default": "en-US" },
        "travelMode": {
          "type": "string",
          "enum": [
            "car",
            "truck",
            "taxi",
            "bus",
            "van",
            "motorcycle",
            "bicycle",
            "pedestrian"
          ],
          "default": "car"
        }
      }
    }
  },
  "required": ["pathPoints"]
}
```

### 2.2 Output (bám calculateRoute, bao gồm `legs`)
```json
{
  "formatVersion": "string",
  "routes": [
    {
      "summary": {
        "lengthInMeters": number,
        "travelTimeInSeconds": number,
        "trafficDelayInSeconds": number,
        "trafficLengthInMeters": number,
        "departureTime": "ISO-8601",
        "arrivalTime": "ISO-8601"
      },
      "legs": [
        {
          "summary": {
            "lengthInMeters": number,
            "travelTimeInSeconds": number,
            "trafficDelayInSeconds": number,
            "trafficLengthInMeters": number,
            "departureTime": "ISO-8601",
            "arrivalTime": "ISO-8601"
          },
          "points": [ { "latitude": number, "longitude": number } ]
        }
      ],
      "sections": [
        {
          "sectionType": "TRAFFIC",
          "startPointIndex": number,
          "endPointIndex": number,
          "simpleCategory": "JAM",
          "effectiveSpeedInKmh": number,
          "delayInSeconds": number,
          "magnitudeOfDelay": number,
          "tec": { "causes": [ { "mainCauseCode": number } ], "effectCode": number },
          "eventId": "string"
        }
      ],
      "guidance": {
        "instructions": [
          {
            "routeOffsetInMeters": number,
            "travelTimeInSeconds": number,
            "point": { "latitude": number, "longitude": number },
            "pointIndex": number,
            "instructionType": "LOCATION_DEPARTURE|TURN|LOCATION_ARRIVAL|...",
            "street": "string",
            "countryCode": "string",
            "maneuver": "DEPART|KEEP_LEFT|TURN_RIGHT|ARRIVE_RIGHT|...",
            "message": "string",
            "combinedMessage": "string?"
          }
        ]
      }
    }
  ]
}
```

Error response (khi 4xx/5xx):
```json
{
  "formatVersion": "string",
  "detailedError": {
    "code": "string",
    "message": "string"
  }
}
```

Các mã lỗi có thể gặp (detailedError.code):
- MAP_MATCHING_FAILURE — Không thể map điểm xuất phát/đích/waypoint lên bản đồ.
- NO_ROUTE_FOUND — Không tìm thấy lộ trình hợp lệ.
- NO_RANGE_FOUND — Không tìm thấy phạm vi di chuyển hợp lệ.
- CANNOT_RESTORE_BASEROUTE — Lỗi khi tái tạo lộ trình từ supportingPoints.
- BAD_INPUT — Tham số đầu vào không hợp lệ.
- COMPUTE_TIME_LIMIT_EXCEEDED — Quá thời gian xử lý nội bộ.
- HTTP: 400, 403, 404, 405, 408, 414, 415, 429, 500, 502, 503, 504, 596.

### 2.3 Runtime Constraints
- **Timeout (mặc định):** 5s đối với gọi dịch vụ ngoài.
- **Retry & Backoff:** Tối đa 2 lần, backoff luỹ thừa + jitter; chỉ retry với lỗi mạng/5xx/timeouts.
- **Idempotency:** `idempotencyKey = hash(origin,destination,options)`, TTL ngắn (vài phút) nếu caching.
- **Rate limit/Quota:** Tuân thủ quota của nhà cung cấp; khi đạt ngưỡng, trả lỗi chuẩn `PROVIDER_RATE_LIMIT`.
- **Bảo mật:** Không log thô API key hoặc toạ độ nếu gắn với dữ liệu nhạy cảm; mask/redact.

---

## 3) Bảng tóm tắt
| Mục | Giá trị |
|---|---|
| **ID Block** | BLK-1-15 |
| **Tên Block** | CheckSevereTrafficOnBestRoute |
| **Trigger** | Từ block quyết định trước đó (Validate/Preprocess) |
| **Preconditions** | Có toạ độ A,B |
| **Input (schema)** | Xem mục 2.1 |
| **Output** | `formatVersion`, `routes[].summary`, `routes[].legs`, `routes[].sections`, `routes[].guidance` |
| **Side-effects** | Không bắt buộc; có thể ghi cache lịch sử request (tuỳ flow) |
| **Timeout/Retry** | 5s; retry tối đa 2 lần với backoff |
| **Idempotency** | Key = origin+destination+options |
| **AuthZ/Scope** | N/A |

---

## 4) Ví dụ

### 4.1 Ví dụ Input
```
GET https://api.tomtom.com/routing/1/calculateRoute/10.762622,106.660172:10.775000,106.690000:10.782222,106.700000/json?traffic=true&sectionType=traffic&instructionsType=text&language=vi-VN&travelMode=motorcycle
```

Ví dụ body theo schema (nếu cần chuẩn hoá trước khi map sang path+query):
```json
{
  "pathPoints": [
    { "lat": 10.762622, "lon": 106.660172 },
    { "lat": 10.775000, "lon": 106.690000 },
    { "lat": 10.782222, "lon": 106.700000 }
  ],
  "params": {
    "traffic": true,
    "sectionType": "traffic",
    "instructionsType": "text",
    "language": "vi-VN",
    "travelMode": "motorcycle"
  }
}
```


### 4.3 Error cases
- `INVALID_COORDINATES`: Thiếu/không hợp lệ lat/lon của A hoặc B.
- `MAP_MATCHING_FAILURE`: Không thể map điểm xuất phát/đích/waypoint lên bản đồ.
- `NO_ROUTE_FOUND`: Không tìm thấy lộ trình hợp lệ.
- `NO_RANGE_FOUND`: Không tìm thấy phạm vi di chuyển hợp lệ.
- `CANNOT_RESTORE_BASEROUTE`: Lỗi khi tái tạo lộ trình từ supportingPoints.
- `BAD_INPUT`: Tham số đầu vào không hợp lệ.
- `COMPUTE_TIME_LIMIT_EXCEEDED`: Quá thời gian xử lý nội bộ.
- `PROVIDER_RATE_LIMIT`: Quá hạn mức; yêu cầu giảm tần suất hoặc chờ.
- `PROVIDER_TIMEOUT`: Quá thời gian chờ; có thể retry theo chính sách.
- `PROVIDER_UNAVAILABLE`: Lỗi 5xx hoặc mạng; xem xét fallback.
- HTTP: 400, 403, 404, 405, 408, 414, 415, 429, 500, 502, 503, 504, 596.

---

## 5) Liên kết (References)
- **Diagram:** Block `BLK-1-15` trong file `prompt/specs/diagrams/routing mcp server diagram.drawio` (đám mây "dịch vụ tomtom API- calculateRoute").
- **API Definition (Postman item):** `resources/Tomtom.postman_collection.json` → item "tuyến tốt nhất A → B hiện có đoạn nào tắc nặng không".
- **Related Blocks:**
  - `BLK-1-09` Request routing info from external API (nếu có trong flow).
  - `BLK-1-10` Decision success? (điều hướng sau khi gọi).
  - `BLK-1-14` Chuẩn hoá output trả về cho LLM.

---

## 6) Acceptance Criteria
- Functional: Trả về cấu trúc calculateRoute chuẩn, bao gồm `legs` với `summary` và `points`.
- Validation: Từ chối input sai định dạng; thông báo lỗi chuẩn hoá theo danh mục lỗi.
- Output: Bao gồm `formatVersion`, `routes[].summary`, `routes[].legs`, `routes[].sections`, `routes[].guidance`.
- Error Handling: Mapping lỗi nhà cung cấp sang mã lỗi chuẩn; có phân biệt 4xx/5xx/timeout.
- Performance: 95p requests hoàn tất < 5s; retry không vượt chính sách.
- Security: Không log dữ liệu nhạy cảm; áp dụng mask/redact khi cần.


