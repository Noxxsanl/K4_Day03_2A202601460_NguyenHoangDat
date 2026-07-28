# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vũ Thành Khang
- **Student ID**: 2A202601866
- **Date**: 28/07/2026

---

## I. Technical Contribution (15 Points)


_Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.)._

- **Modules Implemented**: `src/tools.py`
- **Code Highlights**:
    - Cải thiện cơ chế xử lý lỗi trong `src/tools.py` để mọi công cụ trả về chuỗi kết quả hoặc chuỗi thông báo lỗi.
    - Thêm kiểm tra đầu vào chung `_require_non_empty_str()` để phát hiện sớm tham số không hợp lệ.
    - Cập nhật `call_tool()` để kiểm tra `tool_name`, thông báo khi tool không tồn tại, và bắt mọi exception khi gọi tool.
- **Documentation**: `src/tools.py` là module chứa các tool mà ReAct agent gọi qua hàm `call_tool()`. Khi agent chọn hành động, `call_tool()` bảo đảm đầu ra luôn là chuỗi, kể cả khi input sai hoặc tool gặp lỗi. Điều này giữ cho vòng lặp ReAct ổn định và tránh crash do exception nội bộ.

---

## II. Debugging Case Study (10 Points)

_Analyze a specific failure event you encountered during the lab using the logging system._

- **Problem Description**: Dựa trên kiểm tra mã nguồn, các tool và `call_tool()` chưa xử lý lỗi nhất quán. Nếu input validation thất bại hoặc tool chưa tồn tại, agent có thể không nhận được thông báo lỗi dạng chuỗi và có nguy cơ bị gián đoạn.
- **Log Source**: Phân tích dựa trên mã nguồn `src/tools.py`; hiện chưa có log thực tế từ `logs/` nên phần đánh giá lấy từ các dòng `logger.error(...)` và `logger.exception(...)` trong file này.
- **Diagnosis**: Nguyên nhân nằm ở cơ chế xử lý lỗi không đồng nhất. `_require_non_empty_str()` ném exception khi input không hợp lệ, và một số tool trả về lỗi không rõ ràng nếu exception xảy ra sâu bên trong. Ngoài ra, `call_tool()` trước đây chưa kiểm tra kỹ `tool_name` rỗng hoặc không tồn tại trước khi truy cập registry.
- **Solution**: Bổ sung `try/except` cho từng tool để trả về chuỗi lỗi rõ ràng thay vì ném exception. Cập nhật `call_tool()` để validate `tool_name`, trả về thông báo khi tool không tồn tại, và bắt mọi exception chung khi gọi tool.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

_Reflect on the reasoning capability difference._

1.  **Reasoning**: `Thought` giúp agent tách bạch quá trình suy nghĩ và hành động. Thay vì trả lời trực tiếp, agent dùng `Thought` để quyết định xem có cần gọi tool không, rồi dùng tool nếu cần. Điều này phù hợp với ReAct và giúp hành vi rõ ràng hơn so với chatbot trả lời thẳng.
2.  **Reliability**: Agent có thể kém hơn chatbot khi tool spec không đủ rõ hoặc khi agent chọn sai tool. Trong repo này, nếu tool trả về lỗi không rõ ràng, agent dễ bị sa lầy vào “action” không hiệu quả. Nhờ ổn định hoá `src/tools.py`, agent sẽ đáng tin cậy hơn.
3.  **Observation**: Phản hồi môi trường (`observation`) là dữ liệu quan trọng để agent điều chỉnh bước tiếp theo. Khi `call_tool()` luôn trả về chuỗi, agent nhận được thông báo hợp lệ và có thể quyết định lại thay vì bị gián đoạn bởi exception.

---

## IV. Future Improvements (5 Points)

_How would you scale this for a production-level AI agent system?_

- **Scalability**: Dùng hàng đợi bất đồng bộ (async queue) để xử lý tool calls, tách riêng reasoning và execution, đồng thời cho phép nhiều request tool chạy song song.
- **Safety**: Triển khai một lớp giám sát (supervisor) kiểm tra tool calls trước khi thực hiện, lọc các yêu cầu không hợp lệ hoặc nguy hiểm.
- **Performance**: Tách registry thành module metadata, dùng bộ nhớ đệm cho kết quả giống nhau và có thể dùng vector DB cho truy vấn tool khi hệ thống có nhiều tool hơn.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
