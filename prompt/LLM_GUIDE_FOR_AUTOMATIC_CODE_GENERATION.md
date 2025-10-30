# 🤖 LLM Guide for Automatic Code Generation (Hướng Dẫn LLM Tự Động Tạo Code)

## 📋 Mục Đích Của File Này

File hướng dẫn này cung cấp cho **Large Language Models (LLM)** quy trình để **tự động tạo code** cho các tính năng mới dựa trên yêu cầu từ Developer.

**Hai bước chính:**
1. **Phase 1: ANALYSIS & REPORT** (LLM phân tích, Developer quyết định)
2. **Phase 2: EXECUTION** (LLM thực hiện theo quyết định)

**Kết hợp tài nguyên từ thư mục `prompt/`:**
- **🏗️ Project Architecture Backbone** - Quy tắc & patterns viết code
- **📋 Block Specifications** - Mô tả chi tiết tính năng
- **📖 Block Creation Guidelines** - Template tạo specs
- **🔍 Reports & Feedback** - Lưu trong `prompt/review/`

---

## 📁 Bố Cục Thư Mục `prompt/`

```
prompt/
├── project architecture/              # 🏗️ Architecture Backbone
│   ├── *.txt, *.md files             # LLM đọc toàn bộ
│
├── specs/                             # 📋 Feature Specifications
│   ├── block_creation_instruction.txt # Template
│   └── diagrams/
│       └── <feature>/                 # One folder per feature
│           ├── diagram.drawio         # Diagram for this feature
│           └── blocks/                # Block specs for this feature
│           ├── BLK-<id>-BlockName.md  # Block specs
│           └── ...
│
└── review/                            # 📊 Reports & Feedback
    ├── llm/                           # 🤖 LLM gen reports
    │   └── [feature]_analysis.md      # LLM analysis reports
    └── developer/                     # 👤 Developer feedback
        └── feedback.md                # Developer lessons ONLY
```

---

## 📖 Giải Thích Các Tài Nguyên

### 1️⃣ Project Architecture Backbone
**Mục đích:** Follow chuẩn khi gen blocks/code

### 2️⃣ Block Creation Guidelines  
**Mục đích:** Template để gen blocks đúng format

### 3️⃣ Reports & Feedback (trong `prompt/review/`)
- **[feature]_analysis.md:** LLM gen reports (Phase 1) → `prompt/review/llm/`
- **feedback.md:** Developer feedback ONLY → `prompt/review/developer/`

---

## 🔄 Workflow Tổng Quát

```
Developer: "Tôi muốn tạo/sửa feature"
   ↓
Phase 1: LLM ANALYSIS & REPORT
   → Đọc file diagram và các file mô tả trong thư mục `prompt/specs/diagrams/<feature>/` xem có thiếu gì không?
   → Scan codebase dựa trên các file trong thư mục project prompt/architecture/ xem có vấn đề gì không?
   → Dựa vào file specs phân tích sự khác biệt giữa code và logic
   → Gen report → lưu: prompt/review/llm/[feature]_analysis.md
   ↓
Developer quyết định (dựa trên report)
   → ADD / MODIFY / DELETE / SKIP
   ↓
Phase 2: LLM EXECUTE
   → Check feedback.md (from prompt/review/developer/feedback.md) ngăn lỗi trong quá trình gen code
   → Gen code
   → Tự kiểm tra lại xem đã tuân thủ prompt/architecture/ và đúng logic chuẩn các file prompt/specs/ 
```

---

## 🔍 Phase 1: ANALYSIS & REPORT

### Scan Codebase
```
1. Check diagram: specs/diagrams/<feature>/diagram.drawio
2. Check blocks: specs/diagrams/<feature>/blocks/BLK-*-*.md
3. Check code: use_cases, ports, adapters, DTOs
4. Find dependencies
```

### Generate REPORT
**Save to:** `prompt/review/llm/[feature_name]_analysis.md`

```markdown
# Feature Analysis Report: [feature_name]

## Current Status
- Diagram: [✅/❌]
- Blocks: [count] files
- Code: [✅/❌]

## Feature Status
- Status: [NEW / PARTIALLY_IMPLEMENTED / FULLY_IMPLEMENTED]
- Dependencies: [list]

## Recommendation
- Action: ADD / MODIFY / DELETE / SKIP
- Đưa ra 1 Approval Gates bao gồm các options để Developer sẽ đánh dấu và lưa chọn (đưa ra quy định đánh dấu cụ thể). Approval Gates hoàn thành tất cả thì LLM mới được gen code. không thì sẽ thông báo điểm dừng.
```

### Developer Decision
```
Developer review report & chọn action
LLM chờ decision → thực hiện Phase 2
```

---

## ⚙️ Phase 2: EXECUTE

**⚠️ LLM có rất ít quyền!**

### ADD / MODIFY Workflow

```
Step 1: Gen Block Descriptions
   → Follow: block_creation_instruction.txt
   → Create: BLK-*.md files
   → Template-based ONLY, NO creativity
   
Step 2: STOP & WAIT for Developer Review
   → User review & approve blocks
   
Step 3: Gen Code (after approval)

   → Read feedback: prompt/review/developer/feedback.md
   → Generate code files
   → Follow backbone & guidelines
   → Apply feedback lessons
```

### DELETE Workflow
```
1. Verify dependencies
2. Delete blocks & code
```

---

## 📊 REPORTS & FEEDBACK

### LLM Generated Reports
**Location:** `prompt/review/llm/[feature_name]_analysis.md`
- LLM tạo sau Phase 1 analysis
- Giúp Developer quyết định
- Developer có thể xóa/modify sau dùng

### Developer Feedback
**Location:** `prompt/review/developer/feedback.md`
- **ONLY Developer điền** ⏺️
- **LLM chỉ ĐỌC để học**
- LLM KHÔNG được ghi vào file này

**Format:**
```
ID: BUG-YYYYMMDD-XXX
MODULE: <file path>
ISSUE: <lỗi>
BÀI HỌC: <LLM tránh như thế nào>
SEVERITY: Major/Minor
TAGS: tag1, tag2
```

**Accumulation:**
```
Iteration 1 → LLM gen → Developer review → ghi feedback
Iteration 2 → LLM đọc feedback → code better
Iteration 3 → LLM đọc feedback → code even better
```

---

## 🎯 LLM Permission & Limitations

### Phase 1 (Analysis):
- ✅ Scan codebase
- ✅ Gen REPORT → lưu prompt/review/llm/
- ✅ Recommend action
- ❌ KHÔNG execute

### Phase 2 (Execution):
- ✅ Check feedback.md (đọc từ prompt/review/developer/)
- ✅ Gen block descriptions (template-based)
- ⏸️ **MUST WAIT for user review**
- ✅ Gen code (from approved blocks)
- ✅ Apply feedback lessons
- ❌ KHÔNG tự quyết định

### ⏺️ Critical Rules:
- ❌ Gen code trước block approval
- ❌ Tạo/thay đổi diagram
- ❌ **Ghi vào feedback.md** (User ONLY)
- ❌ Review blocks (User làm)
- ❌ Xóa/modify developer feedback

---

## ✅ Best Practices

✅ Gen report → lưu prompt/review/llm/  
✅ Wait for user review (blocks & decision)  
✅ Check feedback.md → read-only (prompt/review/developer/)  
✅ Apply lessons từ feedback  
✅ Follow template & backbone  

❌ Do NOT gen code before block approval  
❌ Do NOT write to feedback.md  
❌ Do NOT create/modify diagram  
❌ Do NOT review blocks  

---

**Version**: 3.1 (All paths consistent: llm/ & developer/)  
**Status**: ✅ Ready
