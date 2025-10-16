## Hướng dẫn đọc nội dụng các item trong file
Dưới đây là định nghĩa cho 1 feedback item 
```feedback
ID: BUG-YYYYMMDD-XXX <ID do người dùng đánh theo format >
MODULE: <file/path#symbol hoặc thêm tên class,hoặc một khu vực cụ thể>
ISSUE: <mô tả ngắn điều sai>
ERROR: <log/exception/hành vi sai>
CAUSE: <nguyên nhân gốc ngắn gọn>
FIX: <cách sửa súc tích + điểm chính>
VERIFY: <cách kiểm: lệnh test/expected output>
SEVERITY: <Blocker|Critical|Major|Minor|Trivial>
TAGS: <logic, api, validation, security, performance, db, test, deploy, i18n,...>
OWNER: <ai|you|teammate>
```

## Từ đây là nội dung feedback item

```feedback
ID: BUG-20251710-001 
MODULE: thư mục gốc của class
ISSUE: đặt sai vị trí của các file tự test của AI, database, file instructions
ERROR: None 
CAUSE: trong prompt có thể chưa có hướng dẫn đặt vị trí đúng
FIX: thêm vào prompt yêu cầu vị trí khi tự động tạo
VERIFY: developer review
SEVERITY: Major
TAGS: lỗi thiếu hướng dẫn AI đặt nội dung
OWNER: developer
```

