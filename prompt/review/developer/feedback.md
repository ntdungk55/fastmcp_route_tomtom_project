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

```
ID: BUG-20251017-001
MODULE: giao tiếp với llm
ISSUE: llm chạy server qua terminal báo lỗi sai thư mục
CAUSE:   khi chạy server qua terminal , llm không chuyển về folder chứa file server chạy
FIX: chuyển đến thư mục chứa dư án rồi mới chạy
BÀI HỌC: DI chuyển về đúng thư mục rồi mới chạy server
SEVERITY: Major
TAGS: llm behavior
```
```
ID: BUG-20251017-001
MODULE: giao tiếp với llm
ISSUE: llm chạy server qua terminal báo lỗi không thực hiện băng "python start_server.py"
CAUSE:  dự án sử dụng uv để giao tiếp với thư viện
FIX: chạy lệnh " uv run python xxx.py" với file xxx.py là file chứa mcp tool 
BÀI HỌC: Phải biết môi trường đang sử dụng thư viện nào để chạy lệnh
SEVERITY: Major
TAGS: llm behavior
