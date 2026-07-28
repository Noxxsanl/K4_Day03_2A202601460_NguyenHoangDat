# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Văn Phúc
- **Student ID**: 2A202601350
- **Date**: 28/07/2026

---


## I. Technical Contribution (15 Points)

### Modules Implemented: `src/guardrails/` (Hệ thống Phanh An Toàn 3 Lớp)

Tôi xây dựng toàn bộ package `src/guardrails/` gồm 3 module độc lập, hoạt động như lớp bảo vệ bao quanh vòng lặp ReAct Agent.

| File | Lớp | Chức năng |
|---|---|---|
| [`input_guard.py`](../src/guardrails/input_guard.py) | Lớp 1 — Input | Chặn Prompt Injection, Sanitize CV, Topic Restriction |
| [`execution_guard.py`](../src/guardrails/execution_guard.py) | Lớp 2 — Execution | Pydantic validation, Error Feedback Loop, Human-in-the-loop |
| [`output_guard.py`](../src/guardrails/output_guard.py) | Lớp 3 — Output | Anti-hallucination heuristic, JSON schema enforcement |

### Code Highlights

**Lớp 1 — `run_input_guard()`: Gác cổng đầu vào trước khi vào ReAct loop**

```python
# input_guard.py — L166-223
def run_input_guard(user_input: str) -> dict:
    # Bước 1: Phát hiện Prompt Injection bằng 14 regex pattern (EN + VI)
    is_injected, matched = detect_prompt_injection(user_input)
    if is_injected:
        return {"status": "blocked", "reason": f"Prompt Injection: '{matched}'", ...}

    # Bước 2: Sanitize (xóa HTML/script tags, null bytes, shell injection)
    clean = sanitize_input(user_input)

    # Bước 3: Topic Restriction — chỉ cho phép domain HR
    is_allowed, _ = restrict_topic(clean)
    if not is_allowed:
        return {"status": "blocked", "response": _OFF_TOPIC_RESPONSE, ...}

    return {"status": "ok", "clean_text": clean, ...}
```

**Lớp 2 — `execute_with_guard()`: Kiểm soát TRƯỚC khi tool chạy**

```python
# execution_guard.py — L230-295
def execute_with_guard(tool_name, params, tools_mod, require_confirm=None) -> dict:
    # Bước 1: Pydantic validate — ScheduleInterviewParams kiểm tra ngày tương lai + regex giờ
    is_valid, err_msg = _validate_params(tool_name, params)
    if not is_valid:
        return {"status": "validation_error", "error_context": f"[VALIDATION_ERROR]..."}

    # Bước 2: Human-in-the-loop cho HIGH_RISK_TOOLS = {"schedule_interview"}
    if tool_name in HIGH_RISK_TOOLS:
        confirmed = request_human_confirmation(tool_name, params)
        if not confirmed:
            return {"status": "rejected", "error_context": "[HUMAN_REJECTED]..."}

    # Bước 3: Gọi tool thật và bắt mọi exception
    result = tools_mod.call_tool(tool_name, **params)
    return {"status": "ok", "result": result}
```

**Lớp 3 — `validate_output()`: Phát hiện LLM bịa số liệu**

```python
# output_guard.py — L52-107: Heuristic chống hallucination
suspicious_numbers = {
    n for n in output_numbers
    if n not in facts_numbers          # Số không có trong tool observations
    and float(n.replace(",", ".")) > 9 # Bỏ qua số 0-9 quá phổ biến
}
if suspicious_numbers:
    warnings.append(f"⚠️ [HALLUCINATION-RISK] Output chứa số {suspicious_numbers}...")
```

### Documentation — Cách Guardrails tích hợp với ReAct Loop

```
User Input
    │
    ▼
[Lớp 1] run_input_guard()          ← Chặn injection/off-topic TRƯỚC khi vào loop
    │  status="ok" → tiếp tục
    ▼
ReAct Loop (Thought → Action parsing)
    │
    ▼
[Lớp 2] execute_with_guard()       ← Validate params + confirm TRƯỚC khi gọi tool
    │  status="ok" → Observation = result
    │  status="error" → Observation = error_context (LLM tự sửa)
    ▼
scratchpad += Observation → LLM step kế tiếp
    │
    ▼
Final Answer
    │
    ▼
[Lớp 3] validate_output()          ← Đối chiếu output với tool facts, cảnh báo hallucination
```

---

## II. Debugging Case Study (10 Points)

### Problem: `execute_with_guard` — Pydantic chặn nhầm `candidate_info` hợp lệ

**Mô tả lỗi:** Khi test `score_candidate` với input `"Nguyen Van A, Python, SQL"`, lớp `ScoreCandidateParams` báo lỗi validation mặc dù data hoàn toàn hợp lệ.

**Log thực tế:**
```
WARNING guardrails.execution - _validate_params - tool 'score_candidate'
params không hợp lệ: Value error, Tham số không được chỉ chứa khoảng trắng.
```

**Chẩn đoán:** Tôi dùng `@field_validator("candidate_info", "job_requirements")` nhưng khai báo sai thứ tự decorator. Trong Pydantic v2, `@field_validator` phải đặt **trên** `@classmethod`, không phải ngược lại. Thêm vào đó, `Field(..., min_length=1)` validate trước khi validator custom chạy — khi LLM truyền string có leading space (` "Python, SQL"`), `min_length=1` pass nhưng validator strip + check whitespace fail.

**Giải pháp:** Sửa lại validator để `strip()` trước rồi mới kiểm tra whitespace, và đảm bảo `@field_validator` luôn đặt trên `@classmethod`:

```python
# Trước (sai):
@classmethod
@field_validator("candidate_info", "job_requirements")
def not_whitespace(cls, v):  # → Pydantic v2 không nhận

# Sau (đúng):
@field_validator("candidate_info", "job_requirements")
@classmethod
def not_whitespace(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("...")
    return v.strip()  # Luôn trả về đã strip
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — `Thought` block giúp gì so với Chatbot thuần?

Chatbot trả lời thẳng từ kiến thức nội tại, không biết mình đang thiếu thông tin gì. ReAct Agent với `Thought` block buộc LLM **tự hỏi "tôi cần làm gì tiếp theo?"** trước mỗi bước. Ví dụ với Test Case #4 (chấm điểm + đặt lịch nếu đạt), Chatbot chỉ đưa ra gợi ý chung chung, còn Agent suy luận: *"Tôi cần gọi `score_candidate` trước, nếu điểm ≥ 60 thì mới gọi `schedule_interview`"* — đây là **conditional planning** mà Chatbot thuần không làm được.

### 2. Reliability — Trường hợp Agent tệ hơn Chatbot

- **Câu hỏi đơn giản (Test Case #1, #2):** Agent tốn 2–3 lần gọi LLM để ra Final Answer, trong khi Chatbot trả lời ngay trong 1 call. Latency cao hơn, chi phí API cao hơn, không có lợi ích thêm.
- **Khi LLM không tuân theo ReAct format:** MockProvider test (Test Case #5) cho thấy nếu LLM không trả đúng định dạng `Thought: ... Action: ...`, Agent lặp 3 vòng vô ích trước khi Guardrail kích hoạt — Chatbot sẽ không có vấn đề này.
- **Câu hỏi sáng tạo / tư vấn mở:** Chatbot linh hoạt hơn vì không bị ràng buộc bởi tool schema.

### 3. Observation — Feedback môi trường ảnh hưởng bước kế tiếp

Observation từ tool là **grounding mechanism** quan trọng nhất. Khi `schedule_interview` trả về `"Lỗi: ngày trong quá khứ"`, LLM nhận chuỗi lỗi đó vào scratchpad và (với LLM tốt) tự viết Final Answer xin lỗi người dùng — thay vì tiếp tục gọi tool sai. Điều này chứng minh **Error Feedback Loop** trong `execution_guard.py` hoạt động đúng: biến Exception thành ngữ cảnh (`error_context`) để LLM học từ lỗi trong cùng 1 conversation context, không cần restart.

---

## IV. Future Improvements (5 Points)

### Scalability — Xử lý song song nhiều tool call

Hiện tại ReAct loop gọi tool **tuần tự** (1 Action mỗi bước). Với hệ thống production có nhiều bước độc lập (ví dụ: `extract_cv` và `analyze_job_description` không phụ thuộc nhau), có thể dùng **parallel tool execution** bằng `asyncio.gather()`:

```python
# Tương lai: Multi-Action step
async def execute_parallel_actions(actions: list[Action]) -> list[str]:
    return await asyncio.gather(*[execute_tool_async(a) for a in actions])
```

### Safety — Supervisor LLM kiểm duyệt Action trước khi thực thi

Thêm một **Supervisor LLM** nhẹ (ví dụ: Gemini Flash) chạy song song để đánh giá mỗi Action trước khi `execute_with_guard` chạy. Supervisor hỏi: *"Action này có hợp lý với câu hỏi ban đầu không? Có dấu hiệu prompt injection không?"*. Đây là bổ sung cho Lớp 2 hiện tại — thay vì chỉ validate schema, ta validate **intent**.

### Performance — Vector DB cho Tool Retrieval

Khi hệ thống có 50+ tools, việc liệt kê tất cả trong System Prompt sẽ vượt context window. Giải pháp: dùng **Semantic Tool Retrieval** — embed mô tả từng tool, lưu vào vector DB (ChromaDB/Pinecone), mỗi bước Thought chỉ lấy Top-K tool phù hợp nhất với câu hỏi hiện tại:

```python
relevant_tools = vector_db.search(query=current_thought, top_k=3)
system_prompt = build_prompt(tools=relevant_tools)  # Dynamic prompt
```

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.