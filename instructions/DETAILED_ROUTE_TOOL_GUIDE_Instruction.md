# 🛣️ Tool: get_detailed_route

## 📋 Mô tả

Tool `get_detailed_route` tính toán tuyến đường chi tiết giữa hai địa chỉ, sử dụng dữ liệu địa chỉ đã lưu nếu có sẵn, nếu không thì sử dụng geocoding request.

## 🎯 Tính năng chính

- ✅ **Sử dụng dữ liệu đã lưu**: Tự động tìm kiếm trong database các địa chỉ đã lưu trước đó
- ✅ **Geocoding thông minh**: Chỉ geocoding khi không tìm thấy địa chỉ đã lưu
- ✅ **Tuyến đường chi tiết**: Trả về thông tin chi tiết về tuyến đường
- ✅ **Hướng dẫn từng bước**: Turn-by-turn instructions
- ✅ **Thông tin giao thông**: Traffic sections và delays
- ✅ **Tối ưu hiệu suất**: Giảm API calls bằng cách sử dụng dữ liệu đã lưu

## 🔧 Parameters

| Parameter | Type | Required | Default | Mô tả |
|-----------|------|----------|---------|-------|
| `origin_address` | string | ✅ | - | Địa chỉ điểm xuất phát |
| `destination_address` | string | ✅ | - | Địa chỉ điểm đến |
| `travel_mode` | string | ❌ | "car" | Phương tiện di chuyển ("car", "bicycle", "foot") |
| `country_set` | string | ❌ | "VN" | Mã quốc gia |
| `language` | string | ❌ | "vi-VN" | Ngôn ngữ trả về |

## 📤 Response Format

```json
{
  "summary": {
    "distance_m": 1677357,
    "duration_s": 96406,
    "traffic_delay_s": 0,
    "fuel_consumption_l": null
  },
  "instructions": [
    {
      "instruction": "Bắt đầu từ điểm xuất phát",
      "distance_m": 0,
      "duration_s": 0,
      "point": {
        "lat": 21.032026,
        "lon": 105.853163,
        "address": "Phố Hồ Hoàn Kiếm, Hàng Bạc, Hoàn Kiếm, Hà Nội"
      },
      "maneuver": "DEPART",
      "road_name": "Phố Hồ Hoàn Kiếm"
    }
  ],
  "waypoints": [
    {
      "lat": 21.032026,
      "lon": 105.853163,
      "address": "Phố Hồ Hoàn Kiếm, Hàng Bạc, Hoàn Kiếm, Hà Nội"
    },
    {
      "lat": 10.770046,
      "lon": 106.691385,
      "address": "Bến Thành, Quận 1 Hồ Chí Minh"
    }
  ],
  "origin": {
    "lat": 21.032026,
    "lon": 105.853163,
    "address": "Phố Hồ Hoàn Kiếm, Hàng Bạc, Hoàn Kiếm, Hà Nội"
  },
  "destination": {
    "lat": 10.770046,
    "lon": 106.691385,
    "address": "Bến Thành, Quận 1 Hồ Chí Minh"
  },
  "traffic_sections": [
    {
      "kind": "traffic:FLOWING",
      "start_index": 0,
      "end_index": 10,
      "description": "Giao thông thông suốt"
    }
  ],
  "guidance": {
    "instructions": [
      {
        "instruction": "Bắt đầu từ điểm xuất phát",
        "distance_m": 0,
        "duration_s": 0,
        "point": {
          "lat": 21.032026,
          "lon": 105.853163,
          "address": "Phố Hồ Hoàn Kiếm, Hàng Bạc, Hoàn Kiếm, Hà Nội"
        },
        "maneuver": "DEPART",
        "road_name": "Phố Hồ Hoàn Kiếm"
      },
      {
        "instruction": "Rẽ phải gấp",
        "distance_m": 46,
        "duration_s": 15,
        "point": {
          "lat": 21.0325,
          "lon": 105.8532
        },
        "maneuver": "SHARP_RIGHT",
        "road_name": "Phố Hàng Bạc"
      }
    ]
  },
  "legs": [
    {
      "start_point": {
        "lat": 21.032026,
        "lon": 105.853163,
        "address": "Phố Hồ Hoàn Kiếm, Hàng Bạc, Hoàn Kiếm, Hà Nội"
      },
      "end_point": {
        "lat": 10.770046,
        "lon": 106.691385,
        "address": "Bến Thành, Quận 1 Hồ Chí Minh"
      },
      "distance_m": 1677357,
      "duration_s": 96406
    }
  ],
  "route_geometry": null
}
```

## 🚀 Ví dụ sử dụng

### Ví dụ 1: Tuyến đường cơ bản

```python
# Từ Hồ Gươm đến Chợ Bến Thành
result = await get_detailed_route(
    origin_address="Hồ Gươm, Hoàn Kiếm, Hà Nội",
    destination_address="Chợ Bến Thành, Quận 1, TP.HCM"
)
```

### Ví dụ 2: Với phương tiện khác

```python
# Đi xe đạp từ Hồ Gươm đến Chợ Bến Thành
result = await get_detailed_route(
    origin_address="Hồ Gươm, Hoàn Kiếm, Hà Nội",
    destination_address="Chợ Bến Thành, Quận 1, TP.HCM",
    travel_mode="bicycle"
)
```

### Ví dụ 3: Với địa chỉ đã lưu

```python
# Sử dụng địa chỉ đã lưu trước đó
result = await get_detailed_route(
    origin_address="Nhà tôi",  # Đã lưu trong database
    destination_address="Công ty",  # Đã lưu trong database
    travel_mode="car"
)
```

## 🔍 Cách hoạt động

1. **Tìm kiếm địa chỉ đã lưu**: Tool sẽ tìm kiếm trong database các địa chỉ đã lưu trước đó
2. **Geocoding nếu cần**: Nếu không tìm thấy địa chỉ đã lưu, sẽ sử dụng geocoding API
3. **Tính toán tuyến đường**: Sử dụng TomTom Routing API để tính toán tuyến đường
4. **Tạo hướng dẫn chi tiết**: Tạo turn-by-turn instructions
5. **Phân tích giao thông**: Phân tích traffic sections và delays

## ⚡ Tối ưu hiệu suất

- **Giảm API calls**: Sử dụng dữ liệu đã lưu thay vì geocoding mỗi lần
- **Fuzzy matching**: Tìm kiếm địa chỉ đã lưu bằng fuzzy matching
- **Caching**: Dữ liệu địa chỉ được cache trong database

## 🛠️ Kiến trúc

Tool này được implement theo Clean Architecture với:

- **Use Case**: `GetDetailedRouteUseCase`
- **DTOs**: `DetailedRouteRequest`, `DetailedRouteResponse`
- **Dependencies**: Destination Repository, Geocoding Provider, Routing Provider
- **MCP Interface**: `get_detailed_route_tool`

## 📊 Kết quả test

```
✅ Test Results:
📏 Distance: 1,677,357 meters
⏱️ Duration: 96,406 seconds
🚦 Traffic delay: 0 seconds
🛣️ Instructions count: 94
📍 Waypoints count: 2
🚧 Traffic sections: 8
🧭 Guidance instructions: 94
🦵 Route legs: 1

📍 Origin: Phố Hồ Hoàn Kiếm, Hàng Bạc, Hoàn Kiếm, Hà Nội, Hà Nội, 11011
📍 Destination: Bến Thành, Quận 1 Hồ Chí Minh, Hồ Chí Minh

🧭 Guidance Instructions:
  1. DEPART - Distance: 0m, Duration: 0s
  2. SHARP_RIGHT - Distance: 46m, Duration: 15s
  3. ROUNDABOUT_LEFT - Distance: 219m, Duration: 47s

🎉 Test completed successfully!
```

## 🔗 Liên quan

- [Destination Management Tools](./DESTINATION_TOOLS.md)
- [Routing Tools](./ROUTING_TOOLS.md)
- [Clean Architecture Guide](./CLEAN_ARCHITECTURE_USAGE.md)
