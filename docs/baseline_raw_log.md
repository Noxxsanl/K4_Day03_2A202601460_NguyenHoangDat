# 📝 LOG THÔ — CHATBOT BASELINE (Mốc 2)

> File này do `python src/app.py --baseline --save` sinh tự động lúc 2026-07-28 15:33.
> Provider: `GeminiProvider` — model: `gemini-flash-latest`.
> 👉 Role 5 copy nội dung cần dùng sang `docs/trace_eval.md` rồi chấm điểm.

| # | Loại câu hỏi | LLM calls | Tool calls | Thời gian | Gợi ý phân loại |
| :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | 🟢 Đơn giản (Chỉ cần LLM) | 1 | 0 | 11.22s | ⚪ cần Role 5 chấm tay (correct / hallucinated?) |
| 2 | 🟢 Đơn giản (Chỉ cần LLM) | 1 | 0 | 10.33s | ⚪ cần Role 5 chấm tay (correct / hallucinated?) |
| 3 | 🟡 Multi-step (Cần Tool) | 1 | 0 | 7.46s | 🟡 safe fallback (bot tự nhận không có dữ liệu) |
| 4 | 🟡 Multi-step (Cần gọi 2 Tools) | 1 | 0 | 8.25s | 🟡 safe fallback (bot tự nhận không có dữ liệu) |
| 5 | 🔴 Edge Case (Bẫy Guardrail / Lỗi Tool) | 1 | 0 | 9.07s | 🟡 safe fallback (bot tự nhận không có dữ liệu) |

## Test case #1 — 🟢 Đơn giản (Chỉ cần LLM)

**Câu hỏi**: Quy trình phỏng vấn chuẩn cho vị trí lập trình viên thường gồm mấy bước?

**Kỳ vọng (Role 1)**: Chatbot trả lời trực tiếp dựa trên kiến thức chung (không cần gọi tool).

**Chatbot baseline trả lời**:

```text
Xin chào! Tôi là **TuyenDungBot** — trợ lý tư vấn tuyển dụng của bạn.

Một quy trình phỏng vấn chuẩn cho vị trí Lập trình viên (Developer) trong các công ty công nghệ thường bao gồm **4 đến 5 bước** chính sau:

1. **Sàng lọc hồ sơ & Phỏng vấn sơ loại (HR Screening)**
   - **Mục đích:** Đánh giá mức độ phù hợp cơ bản về tổng quan kinh nghiệm, mức lương kỳ vọng, trình độ ngoại ngữ và định hướng sự nghiệp.
   - **Thời lượng:** 15 – 30 phút (Qua điện thoại hoặc Online).

2. **Kiểm tra Kỹ thuật (Technical Test / Coding Assessment)**
   - **Mục đích:** Đánh giá tư duy logic, thuật toán, cấu trúc dữ liệu hoặc kỹ năng viết code thực tế.
   - **Hình thức:** Làm bài test online (HackerRank, LeetCode) hoặc làm bài tập nhỏ về nhà (Take-home assignment).

3. **Phỏng vấn Kỹ thuật chuyên sâu (Technical Interview)**
   - **Mục đích:** Đánh giá sâu về kiến thức chuyên môn, kiến trúc hệ thống (System Design), cách giải quyết vấn đề thực tế và đào sâu vào các dự án ứng viên đã làm.
   - **Người thực hiện:** Technical Lead / Senior Developer.

4. **Phỏng vấn Văn hóa & Quản lý (Culture Fit & Management Interview)**
   - **Mục đích:** Đánh giá kỹ năng mềm (làm việc nhóm, giao tiếp, xử lý xung đột), thái độ làm việc và mức độ phù hợp với văn hóa công ty.
   - **Người thực hiện:** Engineering Manager / CTO / HR Director.

5. **Gửi Thư mời nhận việc (Offer Letter) & Onboarding**
   - **Mục đích:** Thương lượng mức lương, phúc lợi, thời gian bắt đầu công việc và chính thức gửi **Offer Letter**.

---
Bạn có muốn tôi gợi ý bộ câu hỏi phỏng vấn kỹ thuật hoặc câu hỏi đánh giá văn hóa phù hợp cho vị trí lập trình viên này không?
```

**Thống kê**: `llm_calls = 1` · `tool_calls = 0` · `11.22s` · gợi ý phân loại: ⚪ cần Role 5 chấm tay (correct / hallucinated?)

---

## Test case #2 — 🟢 Đơn giản (Chỉ cần LLM)

**Câu hỏi**: Làm thế nào để chuẩn bị một CV đẹp và thu hút nhà tuyển dụng?

**Kỳ vọng (Role 1)**: Chatbot trả lời trực tiếp dựa trên kiến thức chung (không cần gọi tool).

**Chatbot baseline trả lời**:

```text
Xin chào! Tôi là **TuyenDungBot** — trợ lý tư vấn tuyển dụng của bạn. Rất vui được hỗ trợ bạn!

Để chuẩn bị một chiếc CV vừa đẹp mắt, vừa "chinh phục" được nhà tuyển dụng (đặc biệt là trong ngành Công nghệ), bạn nên lưu ý các yếu tố cốt lõi sau:

---

### 1. **Hình thức thiết kế (Visual)**
* **Độ dài tối ưu:** Từ **1 - 2 trang**. Nhà tuyển dụng chỉ dành khoảng 6–10 giây để đọc lướt một CV.
* **Font chữ & Bố cục:** Dùng font hiện đại, dễ đọc (**Arial, Roboto, Calibri**), cỡ chữ 10-12pt. Khoảng cách giữa các phần rõ ràng.
* **Định dạng file:** Luôn lưu và gửi CV dưới dạng file **PDF** để tránh lỗi font hoặc vỡ khung giao diện.

### 2. **Nội dung trọng tâm & Nổi bật**
* **Thông tin liên hệ:** Đầy đủ Họ tên, Số điện thoại, Email chuyên nghiệp. Với ngành công nghệ, bắt buộc/nên có link **LinkedIn** và **GitHub/Portfolio**.
* **Tóm tắt bản thân (Summary):** 2–3 câu ngắn gọn nêu bật **thế mạnh cốt lõi** và **mục tiêu nghề nghiệp** phù hợp với vị trí ứng tuyển.
* **Kinh nghiệm làm việc (Quan trọng nhất):**
  * Sắp xếp theo thứ tự **thời gian ngược** (mới nhất ở trên).
  * Tập trung vào **kết quả định lượng** bằng số liệu cụ thể thay vì chỉ liệt kê đầu việc. *(Ví dụ: "Tối ưu hệ thống giúp giảm 20% thời gian tải trang" tốt hơn "Viết code cho website").*
* **Kỹ năng (Skills):** Chia rõ **Kỹ năng chuyên môn** (Ngôn ngữ lập trình, Frameworks, Tools) và **Kỹ năng mềm** (Làm việc nhóm, Giải quyết vấn đề).
* **Dự án nổi bật (Projects):** Đưa vào 2–3 dự án thực tế, nêu rõ **Công nghệ sử dụng** và **Vai trò của bạn** trong dự án đó.

### 3. **Tối ưu theo Mô tả công việc (JD)**
* **Khớp từ khóa (Keywords):** Đọc kỹ JD và đưa các từ khóa quan trọng trong JD vào CV để dễ dàng vượt qua các hệ thống lọc CV tự động (ATS).
* **Tính tùy chỉnh:** Hãy chỉnh sửa CV một chút cho từng công ty để thể hiện sự phù hợp cao nhất, tránh dùng 1 bản CV chung chung cho tất cả.

### 4. **Những lỗi cần tránh tuyệt đối**
* Sai **lỗi chính tả** và lỗi định dạng.
* Dùng email cá nhân thiếu chuyên nghiệp (ví dụ: *boypro9x@...*).
* Trung thực về mức độ thành thạo kỹ năng (không nâng khống trình độ).

---

Bạn đang muốn chuẩn bị CV cho **vị trí cụ thể nào** (như *Frontend Developer, Data Engineer, Tester...*)? Hãy chia sẻ để tôi gợi ý chi tiết hơn nhé!
```

**Thống kê**: `llm_calls = 1` · `tool_calls = 0` · `10.33s` · gợi ý phân loại: ⚪ cần Role 5 chấm tay (correct / hallucinated?)

---

## Test case #3 — 🟡 Multi-step (Cần Tool)

**Câu hỏi**: Hãy trích xuất thông tin từ CV có nội dung sau:
Nguyen Van A, 3 nam kinh nghiem Python, Django, PostgreSQL, tieng Anh giao tiep.

**Kỳ vọng (Role 1)**: Agent gọi tool extract_cv_information với nội dung CV được cung cấp.

**Chatbot baseline trả lời**:

```text
Tôi là Chatbot cơ bản và không có quyền truy cập vào dữ liệu thực tế. Vui lòng sử dụng hệ thống Agent đầy đủ để thực hiện tác vụ này.
```

**Thống kê**: `llm_calls = 1` · `tool_calls = 0` · `7.46s` · gợi ý phân loại: 🟡 safe fallback (bot tự nhận không có dữ liệu)

---

## Test case #4 — 🟡 Multi-step (Cần gọi 2 Tools)

**Câu hỏi**: Hãy chấm điểm ứng viên có thông tin 'Nguyen Van A, Python, SQL, Django' với yêu cầu tuyển dụng là 'Python, SQL, Django'. Nếu ứng viên đạt tiêu chuẩn, hãy đặt lịch phỏng vấn cho 'Nguyen Van A' vào ngày 2026-08-15 lúc 14:00.

**Kỳ vọng (Role 1)**: Agent gọi tool score_candidate trước để chấm điểm. Vì điểm đạt ngưỡng pass (>= 60), Agent tiếp tục gọi tool schedule_interview để xếp lịch hẹn vào ngày 2026-08-15 lúc 14:00.

**Chatbot baseline trả lời**:

```text
Chào bạn! 

**Tôi là Chatbot cơ bản và không có quyền truy cập vào dữ liệu thực tế. Vui lòng sử dụng hệ thống Agent đầy đủ để thực hiện tác vụ này.**

Tuy nhiên, dựa trên thông tin văn bản bạn vừa cung cấp, tôi có thể đưa ra **mặt phân tích lý thuyết** như sau:

### 1. Phân tích & Đánh giá mức độ phù hợp (Lý thuyết)
* **Yêu cầu tuyển dụng:** Python, SQL, Django.
* **Kỹ năng ứng viên:** Python, SQL, Django.
* **Đánh giá:** Ứng viên **Nguyễn Văn A** khớp **100%** yêu cầu kỹ năng cứng được đưa ra. Đây là một hồ sơ phù hợp để chuyển sang bước tiếp theo.

### 2. Về việc đặt lịch phỏng vấn
* Tôi **không thể tự động đặt lịch phỏng vấn thực tế** hay gửi thư mời tới ứng viên trên hệ thống lịch/ATS của công ty.
* Vui lòng thao tác đặt lịch ngày **2026-08-15 lúc 14:00** trực tiếp trên hệ thống quản lý tuyển dụng của bạn.

---

Nếu bạn cần, tôi có thể giúp bạn **gợi ý bộ câu hỏi phỏng vấn chuyên sâu về Python, SQL và Django** cho buổi phỏng vấn này. Bạn có muốn tham khảo không?
```

**Thống kê**: `llm_calls = 1` · `tool_calls = 0` · `8.25s` · gợi ý phân loại: 🟡 safe fallback (bot tự nhận không có dữ liệu)

---

## Test case #5 — 🔴 Edge Case (Bẫy Guardrail / Lỗi Tool)

**Câu hỏi**: Hãy lên lịch phỏng vấn cho ứng viên 'Nguyen Van A' vào ngày 2020-01-01 lúc 25:00.

**Kỳ vọng (Role 1)**: Tool schedule_interview sẽ báo lỗi do ngày trong quá khứ hoặc giờ sai định dạng. Agent nhận thông báo lỗi từ tool, ngắt lặp an toàn và phản hồi lịch sự.

**Chatbot baseline trả lời**:

```text
Xin chào! **Tôi là Chatbot cơ bản và không có quyền truy cập vào dữ liệu thực tế. Vui lòng sử dụng hệ thống Agent đầy đủ để thực hiện tác vụ này.**

Ngoài ra, nếu bạn cần hỗ trợ về:
- **Mẫu thư mời phỏng vấn** chuyên nghiệp.
- **Quy trình chuẩn bị** trước buổi phỏng vấn.
- **Gợi ý bộ câu hỏi phỏng vấn** theo từng vị trí.

Hãy cho tôi biết để tôi có thể tư vấn giúp bạn nhé!
```

**Thống kê**: `llm_calls = 1` · `tool_calls = 0` · `9.07s` · gợi ý phân loại: 🟡 safe fallback (bot tự nhận không có dữ liệu)

---
