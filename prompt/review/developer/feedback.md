# ⏺️ FEEDBACK & LESSONS LEARNED

**⚠️ CRITICAL: Developer điền nội dung file này**  
**LLM chỉ đọc để hiểu bài học, KHÔNG được ghi vào file này**

---

## Format Feedback Item

```
ID: BUG-YYYYMMDD-XXX
MODULE: <file path hoặc class name>
ISSUE: <mô tả lỗi ngắn gọn>
CAUSE: <nguyên nhân gốc>
FIX: <cách sửa>
BÀI HỌC: <LLM nên tránh bằng cách nào>
SEVERITY: Blocker|Critical|Major|Minor|Trivial
TAGS: <tag1, tag2, ...>
```

---

## Developer Feedback Items

### Ví dụ (hãy xóa khi có feedback thật):

```
ID: BUG-20251017-001
MODULE: app/application/use_cases/update_destination.py
ISSUE: Entity mutation - modify properties trực tiếp
CAUSE: LLM gen code: updated_destination.name = new_name (direct mutation)
FIX: Tạo Destination object mới thay vì mutation
BÀI HỌC: Entity KHÔNG mutation! Phải immutable
SEVERITY: Major
TAGS: ddd-violation, entity-immutability
```

---

**Hướng dẫn cho Developer:**
1. Sau khi review code LLM gen
2. Ghi lỗi/pattern tìm thấy vào file này
3. LLM sẽ đọc những "BÀI HỌC" này ở lần gen tiếp theo
4. Code gen quality sẽ cải thiện qua iterations
