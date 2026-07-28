# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trịnh Bá Khánh Trình
- **Student ID**: 2A202601531
- **Date**: 28/07/2026
    
## I. Technical Contribution (15 Points)

Với vai trò Role 5, tôi phụ trách **quan sát và đánh giá** toàn bộ hệ thống (Chatbot Baseline + ReAct Agent) do 4 role còn lại xây dựng. Đây không phải role viết code chính, mà là *"con mắt kiểm định"* — đảm bảo mỗi cấp độ AI được đánh giá công bằng và có bằng chứng.

- **Modules Implementated**:
  - `docs/trace_eval.md` — báo cáo trung tâm gồm 4 mục:
    1. **Scoring Matrix** (Mốc 1): chấm 4 tiêu chí Agentic Fit (Multi-step Reasoning, Tool Interaction, Dynamic Decision, Long Horizon) → tổng **19/20 điểm** cho bài toán tuyển dụng.
    2. **So sánh phản hồi Test Case #3** (Mốc 1): đối chiếu Chatbot vs ReAct trên câu multi-step.
    3. **Nhật ký Chatbot Baseline** (Mốc 2): quan sát cả 5 test case, phát hiện **1/5 ảo giác nghiêm trọng** ở edge case.
    4. **Trace log ReAct Agent** (Mốc 3): trích chuỗi `Thought → Action → Observation` từ `docs/agent_raw_log.md` do Role 4 sinh.

- **Code Highlights**:
  - **Scoring Matrix** — chấm điểm dựa trên phân tích quy trình HR:
    ```markdown
    | 🧠 Multi-step Reasoning | 5/5 | Đọc CV → trích kỹ năng → đối chiếu JD → chấm điểm → xếp lịch |
    | 🛠️ Tool Interaction    | 5/5 | Phải gọi extract_cv, score_candidate, schedule_interview... |
    | 🔀 Dynamic Decision     | 5/5 | Chỉ ứng viên đạt ngưỡng mới được xếp lịch (case #4)     |
    | ⏳ Long Horizon         | 4/5 | Quy trình 5-7 bước liên tiếp                             |
    ```
  - **Bảng quan sát Baseline** — phân loại 3 trạng thái output:
    ```
    ✅ Trả lời chính xác:     2/5 (case #1, #2 - kiến thức chung)
    ⚠️ Từ chối do thiếu tool: 2/5 (case #3, #4 - safe fallback)
    🚨 Ảo giác / bịa dữ liệu: 1/5 (case #5 - bịa CV không tồn tại, chấp nhận ngày sai)
    ```

- **Documentation** — Cách báo cáo của tôi tương tác với ReAct loop:
  - **Đầu vào**: Đọc `config/test_cases.json` (Role 1), `src/tools.py` (Role 2), `src/prompts.py` (Role 3), `docs/agent_raw_log.md` (Role 4 sinh khi chạy `python src/app.py --agent --save`).
  - **Xử lý**: Trích từng chuỗi `Thought → Action → Observation` cho các test case đại diện (#3 single-tool, #4 multi-tool, #5 edge case).
  - **Đầu ra**: `docs/trace_eval.md` — tài liệu duy nhất mà giảng viên đọc để chấm điểm cả nhóm.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:
  Ở **Test Case #5** (edge case), Chatbot Baseline trả về phản hồi có vẻ *"an toàn"* nhưng thực chất là **fallback chung chung** — bot **không phát hiện** được cả hai lỗi trong input (`ngày 2020-01-01` là quá khứ, `25:00` là giờ không hợp lệ). Đây là **false negative nguy hiểm** trong nghiệp vụ tuyển dụng: nếu HR tin vào phản hồi này, họ sẽ nghĩ hệ thống *"biết rõ"* mình đang từ chối.

- **Log Source** — trích từ `docs/baseline_raw_log.md` (Test case #5):
  ```text
  Xin chào! **Tôi là Chatbot cơ bản và không có quyền truy cập vào dữ liệu thực tế.
  Vui lòng sử dụng hệ thống Agent đầy đủ để thực hiện tác vụ này.**

  Ngoài ra, nếu bạn cần hỗ trợ về:
  - Mẫu thư mời phỏng vấn chuyên nghiệp.
  - Quy trình chuẩn bị trước buổi phỏng vấn.
  ...
  ```
  → Bot **không hề nhắc** đến "25:00 sai định dạng" hay "2020 là quá khứ". Đây không phải "an toàn" mà là **né tránh**.

- **Diagnosis**:
  - **Không phải lỗi model** — Gemini 2.5 Flash đủ thông minh để nhận ra ngày quá khứ nếu được prompt đúng.
  - **Không phải lỗi tool** — vì Chatbot Baseline **không có tool** để gọi.
  - **Nguyên nhân gốc**: `CHATBOT_BASELINE_PROMPT` (Role 3) đặt nguyên tắc *"Với các yêu cầu cần dữ liệu thực tế, hãy thông báo: Tôi là Chatbot cơ bản..."* — điều này khiến bot **rẽ nhánh sớm** vào template fallback mà không thèm phân tích tham số. Đây là **trade-off có chủ đích** — Baseline được thiết kế yếu để làm nổi bật giá trị của ReAct Agent ở Mốc 3.

- **Solution**:
  Đây chính là **bằng chứng khoa học** cho lý do phải chuyển sang ReAct Agent. Ở Mốc 3, cùng câu hỏi #5, Agent gọi `schedule_interview(...)` và tool **trả về chuỗi lỗi cụ thể** (`"'interview_date' (2020-01-01) la ngay trong qua khu..."`) — Agent đọc Observation này và trả lời chi tiết cả 2 lỗi cho user. Tôi ghi lại insight này vào Mục 4 của `trace_eval.md` với tiêu đề *"3 lớp phòng thủ cùng lúc hoạt động"* (Tool contract + Prompt guardrail + MAX_ITERATIONS).

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   Block `Thought` **buộc LLM "nghĩ trước khi hành động"**. Ở Test Case #4 (multi-tool), Chatbot Baseline tự "tính lý thuyết" ra ứng viên khớp 100% JD nhưng KHÔNG thể đặt lịch. Ngược lại, Agent viết rõ Thought: *"Điểm 100 >> ngưỡng 60, ứng viên đủ tiêu chuẩn. Tôi tiếp tục gọi schedule_interview"* — chuỗi suy luận này giúp cả hệ thống có **kiểm chứng được**: nếu điểm dưới 60, Thought sẽ khác và Agent sẽ dừng ở vòng 2. Chatbot chỉ có "câu trả lời cuối" — không thể audit.

2. **Reliability** — Khi nào Agent *tệ hơn* Chatbot?
   - **Câu hỏi kiến thức chung** (case #1, #2): Baseline trả lời trong 1 LLM call (~10s). Agent nếu áp dụng máy móc vòng ReAct có thể *"cố tìm tool để gọi"* → tốn thêm 1-2 vòng lặp vô ích, tăng độ trễ và chi phí token. **Bài học**: cần **Hybrid Flowchart** (Mốc 4) để phân luồng — câu đơn giản đi Chatbot path, câu phức tạp đi Agent path.
   - **Overhead**: Agent gọi ~3 lần LLM cho 1 câu hỏi phức tạp → gấp 3x chi phí Baseline. Nếu 90% truy vấn HR là câu đơn giản, dùng Agent cho tất cả là lãng phí.

3. **Observation** — Vai trò của Observation trong việc định hướng bước sau:
   Đây là điểm tôi ấn tượng nhất khi soi log. Ở Test Case #5, Observation *"Lỗi: ngày trong quá khứ. Vui lòng chọn ngày từ 2026-07-28 trở đi"* đã **ép Agent thay đổi hoàn toàn kế hoạch**: thay vì bịa một ngày hợp lệ mới (điều Chatbot có thể làm), Agent tôn trọng Observation và **trả về Final Answer báo lỗi** cho user. Cơ chế feedback loop này chính là **cột sống của Reliability**: mọi quyết định của Agent đều có "bằng chứng" (Observation) đứng sau, không phải là *"linh cảm ngôn ngữ"* của LLM.

---

## IV. Future Improvements (5 Points)

- **Scalability**:
  Hiện tại `run_react_agent()` gọi tool tuần tự trong Python thread. Ở quy mô 100 CV/ngày, nên:
  - Đưa các tool nặng (`extract_cv_information`, `analyze_job_description`) vào **async queue** (Celery/RabbitMQ) — Agent chỉ chờ job ID rồi poll kết quả.
  - Cache kết quả `analyze_job_description` (mỗi JD chỉ phân tích 1 lần, không phân tích lại cho từng ứng viên).

- **Safety**:
  - Thêm **Supervisor LLM** đứng ngoài vòng ReAct — sau mỗi Action, Supervisor kiểm tra: *"Hành động này có ảnh hưởng nghiệp vụ nghiêm trọng không? (VD: schedule_interview gửi email thật)"* → nếu có, yêu cầu **HR xác nhận thủ công** trước khi commit.
  - Log toàn bộ trace (Thought/Action/Observation) vào một hệ thống **immutable audit** (VD: ELK Stack) để đáp ứng compliance HR (GDPR — quyền giải thích quyết định tự động).
  - Bổ sung **rate limit per candidate** — tránh trường hợp Agent bị prompt injection từ nội dung CV độc hại.

- **Performance**:
  - Với ~50 tool trong hệ thống thực tế (không chỉ 5 tool demo), việc nhồi hết mô tả tool vào `REACT_SYSTEM_PROMPT` sẽ **tốn token và giảm chất lượng**. Nên dùng **Vector DB** (Chroma/Qdrant) lưu embedding của tool descriptions → mỗi vòng ReAct chỉ retrieve **top-5 tool phù hợp nhất** với Thought hiện tại → nhồi vào prompt động.
  - Fine-tune một **small model** riêng cho ngành HR (dựa trên Llama-3.1-8B) để chạy các bước phân loại đơn giản → dành LLM lớn (Gemini 2.5) cho bước tổng hợp cuối.

---