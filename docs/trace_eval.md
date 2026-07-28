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
