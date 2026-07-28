# 🧠 LOG TRACE — REACT AGENT (Mốc 3)

> File này do `python src/app.py --agent --save` sinh tự động lúc 2026-07-28 15:55.
> Provider: `GeminiProvider` — model: `gemini-flash-latest` — MAX_ITERATIONS: `6`.
> 👉 Role 5 copy trace cần dùng sang `docs/trace_eval.md` rồi chấm điểm.

| # | Loại câu hỏi | Steps | LLM calls | Tool calls | Tool đã gọi | Dừng bởi |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | 🟢 Đơn giản (Chỉ cần LLM) | 1 | 1 | 0 | — | final_answer |
| 2 | 🟢 Đơn giản (Chỉ cần LLM) | 1 | 1 | 0 | — | final_answer |
| 3 | 🟡 Multi-step (Cần Tool) | 3 | 3 | 2 | extract_cv_information | final_answer |
| 4 | 🟡 Multi-step (Cần gọi 2 Tools) | 3 | 3 | 2 | extract_cv_information | provider_error |
| 5 | 🔴 Edge Case (Bẫy Guardrail / Lỗi Tool) | 1 | 1 | 0 | — | provider_error |

## Test case #1 — 🟢 Đơn giản (Chỉ cần LLM)

**Câu hỏi**: Quy trình phỏng vấn chuẩn cho vị trí lập trình viên thường gồm mấy bước?

**Kỳ vọng (Role 1)**: Chatbot trả lời trực tiếp dựa trên kiến thức chung (không cần gọi tool).

**Trace đầy đủ**:

```text
Question: Quy trình phỏng vấn chuẩn cho vị trí lập trình viên thường gồm mấy bước?

Thought: Câu hỏi của người dùng là một câu hỏi tổng quan về quy trình tuyển dụng chuẩn cho vị trí lập trình viên, không yêu cầu trích xuất CV, phân tích JD cụ thể hay chấm điểm/lên lịch cho ứng viên. Do đó, tôi không cần gọi công cụ nào và có thể trả lời trực tiếp.
Final Answer: Quy trình phỏng vấn chuẩn cho vị trí lập trình viên (Software Developer/Engineer) thường bao gồm **5 đến 6 bước** chính như sau:

1. **Lọc hồ sơ (CV Screening):** HR xem xét CV của ứng viên để đánh giá mức độ phù hợp ban đầu về kỹ năng, kinh nghiệm và dự án đã làm.
2. **Phỏng vấn sơ loại (HR Screening Call):** Cuộc trao đổi ngắn (15–30 phút) qua điện thoại/online để tìm hiểu về định hướng nghề nghiệp, mức lương mong muốn, thời gian có thể nhận việc và văn hóa làm việc.
3. **Bài kiểm tra kỹ thuật (Technical Test/Coding Challenge):** Ứng viên thực hiện bài test lập trình trực tuyến (qua LeetCode, HackerRank,...) hoặc bài tập thực tế (Take-home assignment) để đánh giá tư duy logic và kỹ năng viết code.
4. **Phỏng vấn kỹ thuật chuyên sâu (Technical Interview):** Trao đổi trực tiếp với Tech Lead/Senior Developer về kiến thức chuyên môn, cấu trúc dữ liệu & giải thuật, kiến trúc hệ thống (System Design), và giải quyết các bài toán thực tế.
5. **Phỏng vấn Văn hóa & Quản lý (Culture Fit & Management Interview):** Trao đổi với Engineering Manager/CTO/HR Manager để đánh giá kỹ năng mềm, khả năng làm việc nhóm, thái độ làm việc và sự phù hợp với văn hóa công ty.
6. **Thỏa thuận & Mời nhận việc (Offer Stage):** Trao đổi về chế độ đãi ngộ, phúc lợi và gửi thư mời nhận việc chính thức (Job Offer). 

*Lưu ý: Tùy vào quy mô công ty (Startup, SME hay Big Tech), quy trình có thể rút gọn hoặc bổ sung thêm các vòng phỏng vấn chuyên sâu.*

```

**Thống kê**: `steps = 1` · `llm_calls = 1` · `tool_calls = 0` · tool đã gọi: — · dừng bởi `final_answer` · 7.82s

---

## Test case #2 — 🟢 Đơn giản (Chỉ cần LLM)

**Câu hỏi**: Làm thế nào để chuẩn bị một CV đẹp và thu hút nhà tuyển dụng?

**Kỳ vọng (Role 1)**: Chatbot trả lời trực tiếp dựa trên kiến thức chung (không cần gọi tool).

**Trace đầy đủ**:

```text
Question: Làm thế nào để chuẩn bị một CV đẹp và thu hút nhà tuyển dụng?

Thought: Đây là câu hỏi tư vấn chung về cách chuẩn bị CV đẹp và thu hút nhà tuyển dụng, không cần sử dụng các công cụ xử lý dữ liệu ứng viên hay JD cụ thể. Tôi đã có đủ thông tin để trả lời người dùng.
Final Answer: Để chuẩn bị một CV đẹp, chuyên nghiệp và thu hút nhà tuyển dụng, bạn nên tuân thủ các nguyên tắc cốt lõi sau:

### 1. Bố cục & Hình thức trình bày (Visual & Layout)
* **Độ dài tối ưu:** Nằm trong khoảng 1 - 2 trang.
* **Font chữ & Kích thước:** Sử dụng các font chữ chuẩn, dễ đọc (như Arial, Helvetica, Calibri, Times New Roman) với cỡ chữ từ 10 - 12pt cho nội dung và 12 - 14pt cho tiêu đề.
* **Phối màu & Thiết kế:** Sử dụng 2 - 3 màu chủ đạo, ưu tiên phong cách tối giản, hiện đại và tạo khoảng trắng hợp lý giữa các phần.
* **Định dạng lưu file:** Luôn xuất file dưới dạng **PDF** (đặt tên file chuyên nghiệp: `CV_[Họ và tên]_[Vị trí ứng tuyển].pdf`) để không bị lỗi font hoặc vỡ khung khi mở trên thiết bị khác.

---

### 2. Nội dung trọng tâm (Core Content)

#### a. Thông tin cá nhân (Contact Information)
* Họ và tên (viết nổi bật).
* Số điện thoại, Email chuyên nghiệp (ví dụ: `nguyenvana@gmail.com`).
* Địa chỉ/Khu vực sinh sống, đường link LinkedIn hoặc Portfolio sản phẩm (nếu có).
* *Lưu ý:* Không cần bao gồm thông tin quá riêng tư như CMND/CCCD, tình trạng hôn nhân, tôn giáo.

#### b. Tóm tắt bản thân / Mục tiêu nghề nghiệp (Professional Summary)
* Viết cô đọng trong 2 - 3 câu nêu bật tổng số năm kinh nghiệm, thế mạnh lớn nhất và giá trị bạn có thể mang lại cho công ty.

#### c. Kinh nghiệm làm việc (Work Experience)
* **Thứ tự:** Sắp xếp theo thứ tự thời gian đảo ngược (công việc gần nhất đặt lên đầu).
* **Cấu trúc:** Tên công ty – Vị trí công tác – Thời gian làm việc.
* **Công thức tả hành động:** Sử dụng các động từ hành động mạnh mẽ và tập trung vào **kết quả có thể định lượng** (con số, %, số lượng dự án, doanh số) thay vì chỉ liệt kê nhiệm vụ.
  * *Ví dụ tốt:* "Quản lý chiến dịch tiếp thị digital, giúp tăng 35% lưu lượng truy cập website trong 6 tháng."

#### d. Kỹ năng (Skills)
* **Kỹ năng chuyên môn (Hard Skills):** Công cụ, phần mềm, ngôn ngữ lập trình, ngoại ngữ...
* **Kỹ năng mềm (Soft Skills):** Giao tiếp, làm việc nhóm, giải quyết vấn đề, quản lý thời gian...

#### e. Học vấn & Chứng chỉ (Education & Certifications)
* Tên trường đại học/cao đẳng, ngành học, năm tốt nghiệp.
* Liệt kê các chứng chỉ chuyên môn có giá trị và liên quan trực tiếp đến vị trí ứng tuyển.

---

### 3. Bí quyết giúp CV nổi bật hơn các ứng viên khác
1. **Tùy chỉnh CV theo Job Description (JD):** Đọc kỹ mô tả công việc và lồng ghép khéo léo các từ khóa (Keywords) trong JD vào CV để vượt qua hệ thống lọc CV tự động (ATS) cũng như tạo sự chú ý với HR.
2. **Kiểm tra kỹ lỗi:** Rà soát chính tả, ngữ pháp, các liên kết (link) trước khi gửi.
3. **Trung thực:** Chỉ đưa các thông tin đúng thực tế, vì nhà tuyển dụng sẽ dễ dàng kiểm tra qua phỏng vấn hoặc Reference Check.

```

**Thống kê**: `steps = 1` · `llm_calls = 1` · `tool_calls = 0` · tool đã gọi: — · dừng bởi `final_answer` · 10.4s

---

## Test case #3 — 🟡 Multi-step (Cần Tool)

**Câu hỏi**: Hãy trích xuất thông tin từ CV có nội dung sau:
Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.

**Kỳ vọng (Role 1)**: Agent gọi tool extract_cv_information với nội dung CV được cung cấp.

**Trace đầy đủ**:

```text
Question: Hãy trích xuất thông tin từ CV có nội dung sau:
Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.

Thought: Tôi cần trích xuất thông tin ứng viên từ nội dung CV được cung cấp.
Action: extract_cv_information['Nguyen Van A', '3 nam kinh nghiem Python', 'Django', 'PostgreSQL', 'tieng Anh giao tiep.']
Observation: Lỗi: Tool 'extract_cv_information' cần 1 tham số (cv_content), nhưng bạn truyền 5. Cú pháp đúng: Action: extract_cv_information["<cv_content>"]

Thought: Do lần gọi trước bị lỗi cú pháp vì nội dung có dấu phẩy khiến công cụ hiểu nhầm là nhiều tham số, tôi sẽ bọc toàn bộ nội dung CV vào trong dấu ngoặc kép.
Action: extract_cv_information['Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.']
Observation: Da trich xuat thong tin ung vien tu CV (1 dong). Dong dau tien: 'Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.'.

Thought: Tôi đã có đủ thông tin để trả lời người dùng.
Final Answer: Kết quả trích xuất thông tin từ CV của ứng viên như sau:

- **Họ và tên:** Nguyen Van A
- **Kinh nghiệm làm việc:** 3 năm
- **Kỹ năng chuyên môn:** Python, Django, PostgreSQL
- **Ngoại ngữ:** Tiếng Anh giao tiếp

```

**Thống kê**: `steps = 3` · `llm_calls = 3` · `tool_calls = 2` · tool đã gọi: extract_cv_information · dừng bởi `final_answer` · 10.37s

---

## Test case #4 — 🟡 Multi-step (Cần gọi 2 Tools)

**Câu hỏi**: Hãy chấm điểm ứng viên có thông tin 'Nguyen Van A, Python, SQL, Django' với yêu cầu tuyển dụng là 'Python, SQL, Django'. Nếu ứng viên đạt tiêu chuẩn, hãy đặt lịch phỏng vấn cho 'Nguyen Van A' vào ngày 2026-08-15 lúc 14:00.

**Kỳ vọng (Role 1)**: Agent gọi tool score_candidate trước để chấm điểm. Vì điểm đạt ngưỡng pass (>= 60), Agent tiếp tục gọi tool schedule_interview để xếp lịch hẹn vào ngày 2026-08-15 lúc 14:00.

**Trace đầy đủ**:

```text
Question: Hãy chấm điểm ứng viên có thông tin 'Nguyen Van A, Python, SQL, Django' với yêu cầu tuyển dụng là 'Python, SQL, Django'. Nếu ứng viên đạt tiêu chuẩn, hãy đặt lịch phỏng vấn cho 'Nguyen Van A' vào ngày 2026-08-15 lúc 14:00.

Thought: Cần trích xuất thông tin ứng viên từ nội dung CV được cung cấp.
Action: extract_cv_information['Nguyen Van A', 'Python', 'SQL', 'Django']
Observation: Lỗi: Tool 'extract_cv_information' cần 1 tham số (cv_content), nhưng bạn truyền 4. Cú pháp đúng: Action: extract_cv_information["<cv_content>"]

Thought: Tôi cần trích xuất thông tin ứng viên từ nội dung CV, sử dụng dấu ngoặc kép để bao quanh tham số nhằm tránh lỗi phân tách tham số bởi dấu phẩy.
Action: extract_cv_information['Nguyen Van A, Python, SQL, Django']
Observation: Da trich xuat thong tin ung vien tu CV (1 dong). Dong dau tien: 'Nguyen Van A, Python, SQL, Django'.

```

**Thống kê**: `steps = 3` · `llm_calls = 3` · `tool_calls = 2` · tool đã gọi: extract_cv_information · dừng bởi `provider_error` · 72.42s

---

## Test case #5 — 🔴 Edge Case (Bẫy Guardrail / Lỗi Tool)

**Câu hỏi**: Hãy lên lịch phỏng vấn cho ứng viên 'Nguyen Van A' vào ngày 2020-01-01 lúc 25:00.

**Kỳ vọng (Role 1)**: Tool schedule_interview sẽ báo lỗi do ngày trong quá khứ hoặc giờ sai định dạng. Agent nhận thông báo lỗi từ tool, ngắt lặp an toàn và phản hồi lịch sự.

**Trace đầy đủ**:

```text
Question: Hãy lên lịch phỏng vấn cho ứng viên 'Nguyen Van A' vào ngày 2020-01-01 lúc 25:00.

```

**Thống kê**: `steps = 1` · `llm_calls = 1` · `tool_calls = 0` · tool đã gọi: — · dừng bởi `provider_error` · 62.17s

---
