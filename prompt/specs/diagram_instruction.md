# Hướng dẫn tạo thư mục tính năng (diagrams)

Mục tiêu: Mỗi tính năng có một thư mục riêng trong `prompt/specs/diagrams/<feature>/` chứa 1 sơ đồ chính và các mô tả block.

## Cấu trúc chuẩn của một tính năng
```
prompt/specs/diagrams/
└── <feature>/
    ├── diagram.drawio          # Sơ đồ tổng thể cho tính năng
    └── blocks/                 # Mô tả từng block trong sơ đồ
        ├── BLK-<idx>-<Tên-Block-1>.md
        ├── BLK-<idx>-<Tên-Block-2>.md
        └── ...
```

Ví dụ đã có (làm mẫu):
- `prompt/specs/diagrams/routing_suite/diagram.drawio`
- `prompt/specs/diagrams/routing_suite/blocks/BLK-1-00-ListenMCPRequest.md` (và các block khác)

## Quy tắc đặt tên
- `<feature>`: tên ngắn gọn theo snake_case, phản ánh tính năng (ví dụ: `routing_suite`, `favorite_destination`).
- Block file: `BLK-<group>-<index>-<Tên-Block>.md` (ví dụ: `BLK-1-09-RequestRoutingAPI.md`).

## Các bước tạo thư mục tính năng mới
1) Tạo thư mục: `prompt/specs/diagrams/<feature>/`
2) Thêm sơ đồ chính: tạo `diagram.drawio` (có thể copy từ mẫu rồi chỉnh sửa nội dung) 
   - Mẫu tham khảo: `prompt/specs/diagrams/routing_suite/diagram.drawio`
3) Tạo thư mục blocks: `prompt/specs/diagrams/<feature>/blocks/`
4) Cho mỗi block trong sơ đồ, tạo một file `.md` mô tả theo format block (xem mẫu trong `routing_suite/blocks/`):
   - Mục tiêu (Purpose)
   - Input/Output
   - Logic chính
   - Liên kết (References) trỏ về `.../<feature>/diagram.drawio` và các block liên quan
5) Cập nhật các tài liệu liên quan để trỏ đến đường dẫn mới theo cấu trúc per-feature:
   - Trong hướng dẫn hoặc báo cáo, dùng đường dẫn dạng: `prompt/specs/diagrams/<feature>/diagram.drawio`
   - Và blocks: `prompt/specs/diagrams/<feature>/blocks/*.md`

## Tạo file diagram_flow.txt (Text Diagram)

Sau khi có `diagram.drawio`, tạo file `diagram_flow.txt` để mô tả flow dạng text, dễ đọc hơn cho LLM và developer.

### Các bước tạo diagram_flow.txt:

1. **Đọc file diagram.drawio**: Phân tích các block IDs và connections trong file XML
   - Tìm các node có `value="BLK-<id>"` để xác định các block
   - Tìm các edge với `source=` và `target=` để xác định luồng kết nối

2. **Phân tích flow**:
   - Xác định block bắt đầu (BLK-Start)
   - Xác định block kết thúc (BLK-End)
   - Vẽ sơ đồ luồng: các block nối tiếp nhau
   - Xác định các điều kiện rẽ nhánh (decision nodes)
   - Xác định các external services

3. **Viết text diagram**:
   - Dùng format: `BLK-<id> (Mô tả ngắn)`
   - Dùng `->` hoặc `v` để thể hiện luồng chính
   - Dùng `+--[condition]-->` để thể hiện điều kiện rẽ nhánh
   - Dùng `|` và indent để thể hiện cấu trúc phân cấp
   - External services liệt kê riêng ở cuối với `->` chỉ block nhận

4. **Ví dụ format**:
```
BLK-Start
  |
  v
BLK-1-00 (Listen MCP Request)
  |
  v
BLK-1-01 (Validate Input)
  |
  v
BLK-1-02 (Check Error?)
  |
  +--[true]--> BLK-1-03 (Handle Error) --> BLK-End
  |
  +--[false]--> BLK-1-04 (Process)
                  |
                  v
                  BLK-End

External Services:
- BLK-1-15 (TomTom API) -> BLK-1-09
```

5. **Lưu file**: `prompt/specs/diagrams/<feature>/diagram_flow.txt`

### Lưu ý:
- File này nên được cập nhật mỗi khi `diagram.drawio` thay đổi
- Format text giúp LLM dễ đọc và hiểu flow hơn file XML của draw.io
- Có thể tham khảo mẫu: `prompt/specs/diagrams/routing_suite/diagram_flow.txt`

## Checklist nhanh
- [ ] Thư mục `prompt/specs/diagrams/<feature>/` tồn tại
- [ ] Có file `diagram.drawio`
- [ ] Có thư mục `blocks/` kèm các file `BLK-*.md`
- [ ] Có file `diagram_flow.txt` mô tả flow dạng text
- [ ] Tất cả "References" trong blocks trỏ đúng về `.../<feature>/diagram.drawio`
- [ ] Tài liệu nhắc đến diagrams đã cập nhật theo cấu trúc per-feature
