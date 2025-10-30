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

## Checklist nhanh
- [ ] Thư mục `prompt/specs/diagrams/<feature>/` tồn tại
- [ ] Có file `diagram.drawio`
- [ ] Có thư mục `blocks/` kèm các file `BLK-*.md`
- [ ] Tất cả “References” trong blocks trỏ đúng về `.../<feature>/diagram.drawio`
- [ ] Tài liệu nhắc đến diagrams đã cập nhật theo cấu trúc per-feature
