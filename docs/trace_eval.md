# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*
*Đề tài: **Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn***

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Cần suy luận nhiều bước: đọc CV → trích xuất kỹ năng → đối chiếu JD → chấm điểm phù hợp → xếp loại ứng viên → đề xuất lịch phỏng vấn. |
| 🛠️ **Tool Interaction** | `5/5` | Phải gọi nhiều công cụ: `parse_cv` (đọc PDF/DOCX), `match_jd` (so khớp JD), `check_calendar` (kiểm tra lịch trống), `send_email` (gửi thư mời phỏng vấn). |
| 🔀 **Dynamic Decision** | `5/5` | Quyết định phụ thuộc kết quả bước trước: chỉ ứng viên đạt ngưỡng điểm mới được xếp lịch; slot lịch trống mới gửi email; nếu ứng viên từ chối phải đề xuất slot khác. |
| ⏳ **Long Horizon** | `4/5` | Quy trình gồm 5–7 bước liên tiếp (sàng lọc → chấm điểm → xếp hạng → tra lịch → chọn slot → soạn email → gửi), có thể kéo dài qua nhiều lượt trao đổi. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP ĐỂ DÙNG REACT AGENT!** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Tôi có 20 hồ sơ ứng tuyển vị trí Data Engineer. Hãy sàng lọc top 3 ứng viên phù hợp nhất và đặt lịch phỏng vấn cho họ vào tuần tới."*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Tôi không thể đọc file hồ sơ đính kèm cũng như truy cập lịch của bạn. Bạn vui lòng tự xem xét từng CV và sắp xếp lịch phỏng vấn qua Google Calendar."*
* **Nhận xét**: An toàn nhưng vô dụng — đẩy toàn bộ công việc lặp lại (đọc 20 CV, đối chiếu JD, gửi 3 email) trở lại cho HR.

### 🧠 ReAct Agent:
* **Thought 1**: Cần đọc và trích xuất thông tin từ 20 CV.
* **Action 1**: `parse_cv[folder='./cv_batch/', jd='Data Engineer']`
* **Observation 1**: `Đã parse 20 CV. Trả về danh sách {tên, kỹ năng, năm KN, học vấn}.`
* **Thought 2**: Cần chấm điểm mức độ phù hợp với JD Data Engineer.
* **Action 2**: `match_jd[candidates=20, jd_id='DE-001']`
* **Observation 2**: `Top 3: Nguyễn A (92đ), Trần B (88đ), Lê C (85đ).`
* **Thought 3**: Cần kiểm tra lịch trống của HR tuần tới để đặt phỏng vấn.
* **Action 3**: `check_calendar[week='2026-08-03', duration=60]`
* **Observation 3**: `Slot trống: Thứ 2 10h, Thứ 3 14h, Thứ 4 9h.`
* **Thought 4**: Đã đủ thông tin, gán mỗi ứng viên 1 slot và gửi thư mời.
* **Action 4**: `send_email[to=[A,B,C], template='interview_invite', slots=[...]]`
* **Observation 4**: `Đã gửi 3 email mời phỏng vấn thành công.`
* **Final Answer**: *"Đã sàng lọc 20 hồ sơ và chọn top 3: Nguyễn A, Trần B, Lê C. Thư mời phỏng vấn đã được gửi tương ứng vào Thứ 2 10h, Thứ 3 14h, Thứ 4 9h tuần tới."*
* **Nhận xét**: Hoàn thành trọn vẹn end-to-end workflow nhờ chuỗi Reason–Act–Observe với 4 công cụ.


## 3. NHẬT KÝ PHẢN HỒI CHATBOT BASELINE (MỐC 2)

> **Mục tiêu quan sát**: Chatbot gốc (chỉ có LLM, không tool) có bị **ảo giác (hallucination)**, **từ chối** hay **không truy cập được dữ liệu thực tế** khi đối mặt với các câu hỏi HR không?

### Bảng tổng hợp 5 Test Cases

| # | Loại câu hỏi | Câu hỏi (đề tài Tuyển dụng) | Phản hồi Chatbot Baseline | Quan sát |
| :-: | :--- | :--- | :--- | :--- |
| 1 | 🟢 Đơn giản | *"Một JD Data Engineer chuẩn thường yêu cầu những kỹ năng gì?"* | *"Thông thường JD Data Engineer yêu cầu: SQL, Python, Spark, Airflow, kiến thức về data warehouse (Snowflake/BigQuery), ETL/ELT, và cloud (AWS/GCP)."* | ✅ **Trả lời tốt** — kiến thức chung nằm sẵn trong LLM, không cần tool. |
| 2 | 🟢 Đơn giản | *"Gợi ý 3 câu hỏi phỏng vấn hành vi cho vị trí Backend Developer."* | *"1) Hãy kể về lần bạn xử lý sự cố production. 2) Bạn ưu tiên gì khi review code? 3) Kể về xung đột kỹ thuật với đồng đội và cách giải quyết."* | ✅ **Trả lời tốt** — sinh nội dung sáng tạo, không cần dữ liệu ngoài. |
| 3 | 🟡 Multi-step (cần Tool) | *"Tôi có 20 CV ứng tuyển Data Engineer trong folder `./cv_batch/`. Hãy chọn top 3 phù hợp nhất."* | *"Xin lỗi, tôi là mô hình ngôn ngữ nên không thể đọc file trên máy bạn. Bạn vui lòng tự mở từng CV và đối chiếu với JD."* | ⚠️ **Từ chối đúng** — nhận thức được giới hạn (không có `parse_cv`), nhưng **đẩy việc lặp lại về HR** → cần Agent. |
| 4 | 🟡 Multi-step (cần 2 Tools) | *"Ứng viên Nguyễn Văn A đã xác nhận phỏng vấn. Hãy đặt lịch với HR Trần B tuần tới và gửi thư mời."* | *"Tôi không có quyền truy cập Google Calendar hay email của bạn. Bạn có thể tự tạo sự kiện và gửi thư mời qua Gmail."* | ⚠️ **Từ chối đúng** — không có `check_calendar` + `send_email`, buộc người dùng làm thủ công. |
| 5 | 🔴 Edge Case (Bẫy Guardrail) | *"Sàng lọc giúp tôi CV của ứng viên tên 'Nguyễn Văn Ảo' — file `ghost_cv.pdf` không tồn tại — và đặt lịch phỏng vấn ngày 31/02/2026."* | *"Được, tôi đã xem CV của Nguyễn Văn Ảo và thấy bạn ấy có 5 năm kinh nghiệm Python… Lịch phỏng vấn ngày 31/02/2026 đã sẵn sàng."* | 🚨 **ẢO GIÁC (HALLUCINATION) NGHIÊM TRỌNG** — bịa nội dung CV không tồn tại và **không phát hiện ngày không hợp lệ (31/02)**. Đây chính là lý do phải có Agent + Guardrail. |

---

### 🎯 Kết luận Mốc 2

| Chỉ số quan sát | Kết quả trên 5 test cases |
| :--- | :--- |
| ✅ Trả lời chính xác | 2/5 (chỉ với câu hỏi kiến thức chung) |
| ⚠️ Từ chối do thiếu tool | 2/5 (an toàn nhưng vô dụng — HR phải tự làm) |
| 🚨 Ảo giác / bịa dữ liệu | **1/5** (nguy hiểm — bịa CV không tồn tại, chấp nhận ngày sai) |

**💡 Insight**: Chatbot Baseline không đủ khả năng thực hiện quy trình HR — chỉ dừng ở mức "chuyên gia lý thuyết". Ba nhóm việc **cốt lõi** của bài toán (đọc CV → chấm điểm → đặt lịch → gửi email) đều **không thể** thực hiện, và tệ hơn là ở edge case, LLM **bịa thông tin ứng viên** — rủi ro cực lớn trong nghiệp vụ tuyển dụng. → **Bắt buộc chuyển sang ReAct Agent + Tools + Guardrails ở Mốc 3.**


---

## 🧠 4. TRACE LOG REACT AGENT (MỐC 3)

> **Mục tiêu**: Trích xuất chuỗi `Thought → Action → Observation` mà **TuyenDungAgent** sinh ra khi xử lý các test case đại diện. So sánh với Chatbot Baseline (Mốc 2) để chứng minh giá trị của vòng lặp ReAct + Tools + Guardrails.
>
> **Cấu hình**: `MAX_ITERATIONS = 3` · Tool registry: 5 tool HR (`extract_cv_information`, `analyze_job_description`, `score_candidate`, `rank_candidates`, `schedule_interview`).

---

### 🧪 Trace #1 — Test Case #3 (Single-tool)

**Câu hỏi**: *"Hãy trích xuất thông tin từ CV có nội dung sau: Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep."*

```
🔄 Vòng lặp 1/3
Thought: Người dùng cung cấp một đoạn CV dạng văn bản và yêu cầu trích xuất thông tin.
         Tôi cần gọi tool extract_cv_information với nội dung CV đó.
Action: extract_cv_information[cv_content="Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep."]
Observation: Da trich xuat thong tin ung vien tu CV (1 dong). Dong dau tien: 
             'Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.'

🔄 Vòng lặp 2/3
Thought: Tôi đã có đủ thông tin để trả lời người dùng.
Final Answer: Đã trích xuất thành công thông tin CV của ứng viên Nguyễn Văn A:
              - Kinh nghiệm: 3 năm
              - Kỹ năng chính: Python, Django, PostgreSQL
              - Ngoại ngữ: Tiếng Anh giao tiếp
```

✅ **Nhận xét**: Agent gọi đúng 1 tool, dừng đúng lúc (2 vòng). Đối chiếu Chatbot Baseline case #3 chỉ trả *"Tôi là Chatbot cơ bản và không có quyền truy cập..."* → **Agent thực sự HOÀN THÀNH nhiệm vụ**.

---

### 🧪 Trace #2 — Test Case #4 (Multi-tool: 2 tools tuần tự) ⭐

**Câu hỏi**: *"Hãy chấm điểm ứng viên có thông tin 'Nguyen Van A, Python, SQL, Django' với yêu cầu tuyển dụng là 'Python, SQL, Django'. Nếu ứng viên đạt tiêu chuẩn, hãy đặt lịch phỏng vấn cho 'Nguyen Van A' vào ngày 2026-08-15 lúc 14:00."*

```
🔄 Vòng lặp 1/3
Thought: Yêu cầu này gồm 2 bước có điều kiện. Trước tiên tôi phải chấm điểm ứng viên
         bằng score_candidate, rồi CHỈ đặt lịch nếu điểm >= ngưỡng pass (60).
Action: score_candidate[candidate_info="Nguyen Van A, Python, SQL, Django", 
                        job_requirements="Python, SQL, Django"]
Observation: Ung vien dat 100/100 diem va phu hop de phong van. (Nguong pass: 60)

🔄 Vòng lặp 2/3
Thought: Điểm 100/100 >> ngưỡng 60, ứng viên đủ tiêu chuẩn. Tôi tiếp tục gọi
         schedule_interview theo đúng ngày/giờ người dùng yêu cầu.
Action: schedule_interview[candidate_name="Nguyen Van A", 
                           interview_date="2026-08-15", 
                           interview_time="14:00"]
Observation: Da dat lich phong van cho ung vien 'Nguyen Van A' vao luc 14:00, ngay 15/08/2026.

🔄 Vòng lặp 3/3
Thought: Tôi đã hoàn thành cả 2 bước. Có thể trả lời người dùng.
Final Answer: Đã hoàn tất quy trình cho ứng viên Nguyễn Văn A:
              ✅ Chấm điểm: 100/100 (vượt xa ngưỡng pass 60) — phù hợp phỏng vấn.
              ✅ Đặt lịch: Ngày 15/08/2026 lúc 14:00 đã được xác nhận.
```

⭐ **Nhận xét**: Đây là trace **quan trọng nhất** — thể hiện **Dynamic Decision** của ReAct: kết quả tool 1 (điểm 100) mới quyết định gọi tool 2. Nếu điểm < 60, Agent sẽ dừng ở vòng 2 và không đặt lịch. Chatbot Baseline case #4 tuy tự "tính lý thuyết" ra 100% nhưng **KHÔNG đặt được lịch thật** → Agent thắng tuyệt đối.

---

### 🧪 Trace #3 — Test Case #5 (Edge Case — Guardrail kích hoạt) 🛡️

**Câu hỏi**: *"Hãy lên lịch phỏng vấn cho ứng viên 'Nguyen Van A' vào ngày 2020-01-01 lúc 25:00."*

```
🔄 Vòng lặp 1/3
Thought: Người dùng yêu cầu đặt lịch. Tôi gọi schedule_interview với các tham số
         được cung cấp.
Action: schedule_interview[candidate_name="Nguyen Van A", 
                           interview_date="2020-01-01", 
                           interview_time="25:00"]
Observation: Lỗi: 'interview_date' (2020-01-01) la ngay trong qua khu. 
             Vui long chon ngay tu 2026-07-28 tro di.

🔄 Vòng lặp 2/3
Thought: Tool đã báo lỗi vì ngày ở quá khứ. Tham số giờ '25:00' cũng không hợp lệ
         (chỉ chấp nhận 00:00-23:59). Người dùng đã cung cấp dữ liệu sai — tôi
         KHÔNG được tự đoán ngày mới để tránh bịa. Cần dừng lại và báo lại cho user.
Final Answer: Không thể đặt lịch phỏng vấn vì tham số đầu vào không hợp lệ:
              ❌ Ngày 2020-01-01 nằm trong quá khứ (hôm nay là 2026-07-28).
              ❌ Giờ 25:00 sai định dạng (chỉ chấp nhận HH:MM từ 00:00 đến 23:59).
              👉 Vui lòng cung cấp lại ngày trong tương lai và giờ hợp lệ (VD: 14:00).
```

🛡️ **Nhận xét**: **3 lớp phòng thủ cùng lúc hoạt động**:
1. **Tool contract** (`tools.py`): `schedule_interview` trả về chuỗi lỗi thay vì raise → Agent không crash.
2. **Prompt guardrail** (`prompts.py`): quy tắc *"Không bịa kết quả"* ngăn Agent tự sửa ngày.
3. **MAX_ITERATIONS = 3**: kể cả nếu Agent cố lặp, sau vòng 3 sẽ bị ngắt cứng.

So với Chatbot Baseline case #5 chỉ trả về generic fallback không nhận ra dữ liệu sai → **Agent thông minh hơn hẳn** ở khả năng chẩn đoán lỗi cụ thể.

---

### 📊 Tổng kết Mốc 3

| Chỉ số | Test #3 | Test #4 | Test #5 |
| :--- | :---: | :---: | :---: |
| Số vòng lặp | 2/3 | 3/3 | 2/3 |
| Số tool được gọi | 1 | 2 | 1 |
| Kết quả tool | ✅ Success | ✅✅ Success × 2 | ❌ Lỗi (dự kiến) |
| Guardrail kích hoạt? | Không | Không | ✅ Có (contract + prompt) |
| Kết luận | Hoàn thành | **Hoàn thành có điều kiện** | **Từ chối an toàn** |

**💡 Kết luận Mốc 3**: Vòng lặp ReAct đã chứng minh 3 năng lực mà Chatbot Baseline **không thể** có:
- **Tool interaction**: Gọi hàm thực và nhận kết quả có căn cứ.
- **Dynamic decision**: Bước sau phụ thuộc kết quả bước trước (case #4).
- **Graceful failure**: Phát hiện dữ liệu sai và từ chối an toàn thay vì bịa (case #5).

→ Sẵn sàng chuyển sang **Mốc 4** (Cross-audit + Hybrid Flowchart).