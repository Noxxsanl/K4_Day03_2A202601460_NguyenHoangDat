# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Hoàng Đạt
- **Student ID**: 2A202601460
- **Date**: 28/07/2026
- **Vai trò trong nhóm**: **Role 4 — Core Developer / Integrator** (phụ trách `src/app.py`, đầu mối `git pull` và lắp ráp code của cả nhóm thành ứng dụng chạy được)
- **Đề tài nhóm**: Đề tài 9 — Trợ lý Sàng lọc Hồ sơ Tuyển dụng & Hẹn Phỏng vấn

---

## I. Technical Contribution (15 Points)

### 1.1 Module đã triển khai

| File | Phần tôi viết | Mốc |
| :--- | :--- | :---: |
| `src/app.py` | Toàn bộ Preflight Check (7 nhóm kiểm tra) | Mốc 1 |
| `src/app.py` | `run_baseline_chatbot()`, `run_baseline_suite()`, `save_baseline_log()` | Mốc 2 |
| `src/app.py` | `run_react_agent()` + parser + executor + guardrails, `run_agent_suite()`, `save_agent_log()`, `run_compare_suite()`, CLI `argparse` | Mốc 3 |
| `src/providers.py` | Sửa model mặc định + cơ chế tự thử lại khi lỗi 429 | Mốc 2, 3 |

### 1.2 Code Highlights

**(a) Preflight Check — biến `app.py` thành bộ chẩn đoán cho cả nhóm** (`src/app.py`, hàm `check_python()` → `check_provider_pipeline()`)

Thay vì chỉ chạy cho có, `python src/app.py` kiểm tra 7 nhóm: Python/venv, thư viện, `.env` + provider + SDK, `test_cases.json` (Role 1), `AVAILABLE_TOOLS` (Role 2), prompts + `MAX_ITERATIONS` (Role 3), smoke test provider. Kết quả hiện tại: **27 ✅ / 0 ⚠️ / 0 ❌**.

Hai phép kiểm tra tôi tự thêm đã bắt được lỗi tích hợp thật:

- **Lint hợp đồng lỗi của tool**: gọi từng tool với tham số rỗng để xem nó *trả về chuỗi lỗi* hay *raise Exception*. Ở Mốc 1 nó phát hiện **5/5 tool đang raise `ValueError`** — vi phạm yêu cầu của CODELAB. Role 2 sau đó đã sửa thành `return f"Lỗi: {exc}"` (commit `Moc3: return result string avoid crash`).
- **Kiểm tra độ khớp Prompt ↔ Tool**: đối chiếu tên tool trong `AVAILABLE_TOOLS` với `REACT_SYSTEM_PROMPT`. Ở Mốc 1 nó báo **0/5 tool được mô tả trong prompt** (prompt còn ghi tool cũ `get_weather`, `search_flights`). Nếu không phát hiện sớm, Agent sẽ gọi tool không tồn tại và fail 100% ở Mốc 3.

**(b) Chatbot Baseline — giữ đúng "1 LLM call, 0 tool"** (`run_baseline_chatbot()`)

```python
# ⬇️ ĐÚNG 1 LẦN GỌI LLM DUY NHẤT — không vòng lặp, không tool
start = time.perf_counter()
answer = provider.generate(user_query, system_prompt=system_prompt)
elapsed = time.perf_counter() - start
result = {
    "tool_calls": 0,      # ⬅️ Bằng chứng baseline: không hề gọi tool
    "llm_calls": 1,
    ...
}
```

App in ra `tool_calls = 0` cho từng case, để việc "baseline công bằng" là **số liệu đo được** chứ không phải lời khẳng định.

**(c) Chặn LLM tự bịa Observation** (`_strip_hallucinated_observation()`)

Đây là nguyên tắc bất biến quan trọng nhất của ReAct: chỉ *application* được chèn Observation, và chỉ chèn kết quả tool thật.

```python
def _strip_hallucinated_observation(text: str):
    match = OBSERVATION_RE.search(text or "")
    if match:
        return text[: match.start()].rstrip(), True   # cắt bỏ + đánh dấu đã bịa
    return (text or "").strip(), False
```

Số lần LLM bịa bị chặn được đếm và in ra (`faked_observations`) để Role 5 đưa vào báo cáo.

**(d) Parser chịu được tham số chứa dấu phẩy** (`_split_action_args()`)

```python
quoted = re.findall(r'"([^"]*)"|\'([^\']*)\'', raw, re.DOTALL)
if quoted:
    return [(a or b).strip() for a, b in quoted]      # ưu tiên chuỗi trong dấu nháy
return [part.strip() for part in raw.split(",") if part.strip()]
```

Lý do: tham số của đề tài này (nội dung CV, mô tả công việc) **bản thân nó chứa dấu phẩy**, tách bừa theo dấu phẩy sẽ sai — xem phần II.

**(e) Executor có 4 lớp bắt lỗi** (`execute_tool_call()`)

Ánh xạ tham số theo vị trí sang tên tham số bằng `inspect.signature()`, rồi dispatch qua `call_tool()` của Role 2. Bắt được: tool không tồn tại (trả kèm danh sách tool hợp lệ), sai số lượng tham số (trả kèm cú pháp đúng), sai cú pháp `Action:`, và lặp lại y hệt một Action đã gọi.

**(f) Guardrail + Safe Fallback** (`run_react_agent()`)

Chạm `MAX_ITERATIONS` mà chưa có Final Answer → **không bịa câu trả lời**, mà trả về thông báo lịch sự có nêu nguyên nhân gần nhất và đề nghị chuyển cho HR phụ trách.

### 1.3 Code của tôi tương tác với vòng lặp ReAct như thế nào

```
Question ──► [scratchpad] ──► provider.generate(prompt, REACT_SYSTEM_PROMPT)   ← Role 3
                 ▲                          │
                 │                          ▼
                 │              _strip_hallucinated_observation()   (chặn bịa)
                 │                          ▼
                 │                    parse_llm_step()              (Thought/Action/Final)
                 │                          ▼
                 │                  execute_tool_call() ──► call_tool() ──► AVAILABLE_TOOLS  ← Role 2
                 │                          ▼
                 └──── "Observation: <kết quả tool thật>" ◄─┘
                                            │
                       chạm MAX_ITERATIONS ─┴─► Safe Fallback   ← Role 3 cấu hình
```

Điểm mấu chốt: `src/app.py` **không import cứng tên tool nào**. Mọi tool được nạp động qua `AVAILABLE_TOOLS`, nên Role 2 đổi tool bao nhiêu lần app cũng không vỡ — bài học rút ra từ đúng sự cố ở phần II.1.

---

## II. Debugging Case Study (10 Points)

### II.1 Sự cố mở màn: `ImportError` khi Role 2 đổi domain

- **Problem**: Ở Mốc 1, `python src/app.py` chết ngay dòng import: `ImportError: cannot import name 'get_weather' from 'tools'`.
- **Diagnosis**: `app.py` import cứng `from tools import AVAILABLE_TOOLS, get_weather, search_flights`. Khi Role 2 đổi `tools.py` sang domain tuyển dụng, hai tên đó biến mất. Nguyên nhân gốc là **coupling sai tầng**: file điều phối không được phụ thuộc vào *từng tool cụ thể*.
- **Solution**: Bỏ toàn bộ import cứng, chuyển sang nạp động qua `safe_import()` + đọc registry `AVAILABLE_TOOLS`. Sau đó app sống sót qua 4 lần Role 2 sửa `tools.py` mà không cần chỉnh dòng nào.

### II.2 Case study chính: Agent truyền 5 tham số cho tool chỉ nhận 1

- **Problem Description**: Test case #3 yêu cầu trích xuất thông tin từ CV. Agent gọi tool với **5 tham số** trong khi `extract_cv_information` chỉ nhận **1**.

- **Log Source**: `docs/agent_raw_log.md`, Test case #3 (sinh bằng `python src/app.py --agent --save --max-steps 6`)

```text
Question: Hãy trích xuất thông tin từ CV có nội dung sau:
Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.

Thought: Tôi cần trích xuất thông tin ứng viên từ nội dung CV được cung cấp.
Action: extract_cv_information['Nguyen Van A', '3 nam kinh nghiem Python', 'Django', 'PostgreSQL', 'tieng Anh giao tiep.']
Observation: Lỗi: Tool 'extract_cv_information' cần 1 tham số (cv_content), nhưng bạn truyền 5.
             Cú pháp đúng: Action: extract_cv_information["<cv_content>"]

Thought: Do lần gọi trước bị lỗi cú pháp vì nội dung có dấu phẩy khiến công cụ hiểu nhầm là
         nhiều tham số, tôi sẽ bọc toàn bộ nội dung CV vào trong dấu ngoặc kép.
Action: extract_cv_information['Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.']
Observation: Da trich xuat thong tin ung vien tu CV (1 dong). Dong dau tien: 'Nguyen Van A, 3 nam...'.

Thought: Tôi đã có đủ thông tin để trả lời người dùng.
Final Answer: - Họ và tên: Nguyen Van A  - Kinh nghiệm: 3 năm
              - Kỹ năng: Python, Django, PostgreSQL  - Ngoại ngữ: Tiếng Anh giao tiếp
```

- **Diagnosis**: Không phải lỗi model, mà là **xung đột giữa tool spec và cú pháp Action**. `Action: tool[a, b]` dùng dấu phẩy làm ký tự phân tách tham số, nhưng dữ liệu nghiệp vụ của đề tài này (nội dung CV, danh sách skill) **bản thân nó đầy dấu phẩy**. Ở lần parser đầu tiên tôi tách tham số bằng `raw.split(",")`, nên 1 chuỗi CV bị xé thành 5 tham số. Đây là lỗi thiết kế parser, LLM chỉ là nạn nhân.

- **Solution** (2 lớp):
  1. **Sửa parser** — `_split_action_args()` ưu tiên bóc các chuỗi trong dấu nháy trước, chỉ khi không có dấu nháy mới tách theo dấu phẩy. Nhờ vậy `tool["a, b", "c"]` được hiểu đúng là 2 tham số.
  2. **Biến lỗi thành dữ liệu để Agent tự sửa** — executor không chỉ báo "sai", mà trả về **số tham số cần, tên tham số, và cú pháp đúng** ngay trong Observation.

- **Kết quả đo được**: Agent **tự phục hồi ở bước 2** mà không cần người can thiệp — dòng `Thought` bước 2 cho thấy nó đọc hiểu Observation lỗi và tự suy ra cách bọc dấu ngoặc kép. Case #3 kết thúc `dừng bởi: final_answer` với 3 steps / 2 tool calls / 10.37s.

### II.3 Sự cố thứ ba: `MAX_ITERATIONS = 3` quá chật (kèm bằng chứng)

Test case #4 cần tối thiểu 5 bước (`extract_cv_information` → `analyze_job_description` → `score_candidate` → `schedule_interview` → Final Answer). Với `MAX_ITERATIONS = 3`, Guardrail ngắt khi Agent mới đi được nửa đường:

```text
Step 1/3  Action: extract_cv_information[...5 tham số...]  ➔ Observation: Lỗi tham số
Step 2/3  Action: extract_cv_information['...1 chuỗi...']  ➔ Observation: OK
Step 3/3  Action: analyze_job_description['Python, SQL, Django'] ➔ Observation: OK
🛡️ GUARDRAIL KÍCH HOẠT: chạm giới hạn 3 bước ➔ ngắt lặp an toàn  (dừng bởi: guardrail_max_iterations)
```

Chạy lại với `--max-steps 6` thì Agent đi tiếp được tới `score_candidate` và nhận `Ung vien dat 100/100 diem va phu hop de phong van. (Nguong pass: 60)`.

**Bài học**: `MAX_ITERATIONS` không phải con số chọn bừa — nó phải **lớn hơn độ sâu tool path dài nhất trong bộ test case, cộng thêm 1–2 bước dự phòng cho việc tự sửa lỗi**. Tôi đã thêm cờ `--max-steps` để thử nghiệm phanh mà không cần sửa file của Role 3, và gửi bằng chứng này để đề nghị nâng lên 6.

### II.4 Hai sự cố hạ tầng

- **404 NOT_FOUND**: `gemini-2.5-flash` bị Google khóa với API key mới tạo (*"no longer available to new users"*). Sửa mặc định trong `src/providers.py` sang alias `gemini-flash-latest`.
- **429 RESOURCE_EXHAUSTED**: ReAct gọi LLM 3–6 lần/case nên đốt quota free tier nhanh gấp nhiều lần Chatbot, và cạn quota ngay giữa một trace. Đã thêm cơ chế **tự chờ + thử lại** (0s → 20s → 40s), chỉ retry với lỗi `429/503`, còn `404`/sai key thì dừng ngay để không chờ vô ích.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — khối `Thought` giúp được gì

Trước khi làm bài này tôi nghĩ `Thought` chỉ để "cho đẹp log". Thực tế nó là **nơi Agent tự sửa mình**. Ở case #3, đúng dòng `Thought` bước 2 mới là chỗ Agent chuyển từ thất bại sang thành công:

> *"Do lần gọi trước bị lỗi cú pháp vì nội dung có dấu phẩy khiến công cụ hiểu nhầm là nhiều tham số, tôi sẽ bọc toàn bộ nội dung CV vào trong dấu ngoặc kép."*

Chatbot không có bước trung gian này: nó chỉ có một lượt sinh text duy nhất, đúng thì đúng, sai thì sai, **không có cơ hội thứ hai**. Khác biệt lớn nhất giữa Cấp 2 và Cấp 3 vì vậy không phải là "gọi được tool", mà là **có vòng phản hồi để sửa sai**.

### 2. Reliability — khi nào Agent *tệ hơn* Chatbot

Đây là phần tôi thấy đáng ghi nhận nhất, vì kết quả đo được ngược với kỳ vọng ban đầu của tôi:

- **Câu hỏi lý thuyết (case #1, #2)**: cả hai đều dùng đúng 1 LLM call và Agent cũng không gọi tool nào (`tool_calls = 0`) — nhưng Agent phải nuốt thêm system prompt ReAct dài 2281 ký tự và **luôn có rủi ro sinh sai định dạng** rồi tiêu thêm một vòng lặp vô ích. Với loại câu này, orchestration của Agent là chi phí thuần, không đổi lấy giá trị nào.
- **Case #4 — Agent thua trắng**: Chatbot trả lời trôi chảy trong 8.25s. Agent tiêu 5 LLM call, 4 tool call, 72s và **kết thúc không có Final Answer** (bị Guardrail ngắt). Xét theo trải nghiệm người dùng, đây là thất bại rõ ràng — dù xét theo tính trung thực thì việc dừng lại còn tốt hơn bịa.
- **Chi phí vận hành**: Agent làm cạn quota Gemini free tier trong một buổi lab; Chatbot chạy cả 5 case vẫn bình thường. Chi phí Agent cao gấp 3–6 lần **mỗi câu hỏi**.

Đổi lại, ở case #4 Chatbot tự tin khẳng định *"Ứng viên Nguyễn Văn A khớp **100%** yêu cầu"* — một con số **không có bất kỳ bằng chứng nào**, vì `tool_calls = 0`. Agent cũng đưa ra 100 điểm, nhưng là `Ung vien dat 100/100 diem (Nguong pass: 60)` **từ tool `score_candidate` thật**. Hai con số giống nhau, độ tin cậy khác nhau hoàn toàn — và người dùng cuối **không thể phân biệt được** nếu không có trace log. Đây chính xác là lý do phải đo `tool_calls`, không phải đánh giá bằng cảm giác "câu trả lời nghe hợp lý".

**Kết luận của tôi**: không có hệ nào thắng tuyệt đối, nên lời giải đúng là **Hybrid** — phân luồng câu hỏi lý thuyết sang Chatbot cho nhanh và rẻ, chỉ đẩy sang ReAct Agent những câu cần dữ liệu thật hoặc cần thực hiện hành động.

### 3. Observation — phản hồi từ môi trường điều khiển bước sau ra sao

Tôi quan sát được 3 kiểu Observation dẫn tới 3 hành vi khác nhau:

| Kiểu Observation | Ảnh hưởng tới bước sau |
| :--- | :--- |
| **Dữ liệu thành công** (`Ung vien dat 100/100 diem... Nguong pass: 60`) | Agent so 100 với ngưỡng 60 rồi mới quyết định đi tiếp sang `schedule_interview` — quyết định *phụ thuộc dữ liệu*, không phải kịch bản cứng |
| **Lỗi có hướng dẫn** (`cần 1 tham số (cv_content)... Cú pháp đúng: ...`) | Agent tự sửa ngay bước sau (case #3) |
| **Lỗi không có hướng dẫn** | Agent lặp lại y hệt hành động cũ → tôi phải thêm cơ chế phát hiện lặp, chèn cảnh báo *"tool cho kết quả cố định nên gọi lại cũng không đổi, hãy đổi tham số hoặc trả Final Answer"* |

Bài học rút ra: **chất lượng Observation quyết định chất lượng Agent**. Một thông báo lỗi tồi (`ValueError` trần) khiến Agent kẹt lặp; cùng lỗi đó nhưng viết rõ "cần gì, cú pháp đúng ra sao" thì Agent tự thoát. Nói cách khác, thông báo lỗi trong hệ Agent **không viết cho người đọc — nó viết cho LLM đọc**, và đây là điều tôi hoàn toàn không lường trước khi bắt đầu bài lab.

---

## IV. Future Improvements (5 Points)

### Scalability
- **Thay parser regex bằng native function calling / JSON schema** của provider. Toàn bộ sự cố ở phần II.2 sinh ra từ việc dùng text `Action: tool[a, b]` — nếu dùng structured tool calling thì tham số được truyền dưới dạng object, dấu phẩy trong dữ liệu không còn là vấn đề.
- **Chạy song song các tool độc lập**: ở case #4, `extract_cv_information` và `analyze_job_description` không phụ thuộc nhau nhưng vẫn bị chạy tuần tự, tốn 2 vòng LLM. Cho Agent khai báo nhiều Action độc lập trong một bước rồi `asyncio.gather` sẽ cắt đáng kể số vòng lặp.
- **Cache kết quả tool deterministic**: `dict seen_actions` tôi viết chỉ là bản thô để chống lặp; nâng lên cache có TTL sẽ tiết kiệm cả tiền lẫn thời gian.

### Safety
- **Nối 3 lớp guardrails vào mọi chế độ chạy**: nhóm đã có `src/guardrails/` (input / execution / output, 13/13 test pass), nhưng hiện chỉ chế độ `--guardrails` dùng tới. Cần đưa Layer 1 (chặn prompt injection) thành mặc định cho mọi đường vào.
- **Human-in-the-loop cho tool có side effect**: `schedule_interview` ghi dữ liệu thật. Ở hệ production, tool loại này phải chờ người xác nhận trước khi thực thi, không để LLM tự quyết.
- **Supervisor LLM audit trace**: dùng một model thứ hai đọc lại toàn bộ trace và trả lời "Final Answer này có được chống lưng bởi Observation nào không?" — tự động hóa đúng việc mà Role 5 đang làm bằng tay.

### Performance
- **Fallback chain giữa các provider**: nhóm đã có adapter đa provider (Gemini / OpenAI / Anthropic / OpenRouter). Khi Gemini trả 429, tự chuyển sang provider dự phòng thay vì chờ 20s–40s rồi bỏ cuộc như hiện tại.
- **Hybrid router phía trước**: dùng một model nhỏ/rẻ phân loại câu hỏi trước, câu lý thuyết → Chatbot 1 call, câu cần dữ liệu → ReAct Agent. Số đo của nhóm cho thấy cách này cắt được 3–6 lần chi phí cho nhóm câu hỏi lý thuyết.
- **Vector DB để truy hồi tool** khi số tool tăng lên hàng chục: hiện 5 tool được nhồi hết vào system prompt (2281 ký tự); với 50 tool thì cách này vừa đắt vừa làm loãng ngữ cảnh, nên chỉ nạp top-k tool liên quan tới câu hỏi.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
