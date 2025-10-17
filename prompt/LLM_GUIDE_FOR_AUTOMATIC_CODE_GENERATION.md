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
│       ├── <feature>.drawio           # Diagram
│       └── blocks/
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
   → Scan codebase
   → Gen report → lưu: prompt/review/llm/[feature]_analysis.md
   → Check feedback.md (from prompt/review/developer/feedback.md)
   ↓
Developer quyết định (dựa trên report)
   → ADD / MODIFY / DELETE / SKIP
   ↓
Phase 2: LLM EXECUTE
   → Gen blocks (template-based)
   → WAIT for user review
   → Gen code (approved blocks)
```

---

## 🔍 Phase 1: ANALYSIS & REPORT

### Scan Codebase
```
1. Check diagram: specs/diagrams/<feature>.drawio
2. Check blocks: specs/diagrams/blocks/BLK-*-*.md
3. Check code: use_cases, ports, adapters, DTOs
4. Find dependencies
5. Read feedback: prompt/review/developer/feedback.md
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
- ✅ Check feedback.md (đọc từ prompt/review/developer/)
- ✅ Recommend action
- ❌ KHÔNG execute

### Phase 2 (Execution):
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
