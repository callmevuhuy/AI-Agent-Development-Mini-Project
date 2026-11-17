# Công việc và trạng thái dự án

## Đã hoàn thành trong phạm vi nguyên mẫu

- [x] Dữ liệu giả lập, 19 tool, JSON Schema, registry, allowlist và phân quyền tại dispatcher.
- [x] Ba quy trình trước/trong/sau chuyến đi, bản nháp có ID ổn định, trạng thái dừng trung thực và trích dẫn policy.
- [x] `request_approval` chỉ tạo pending, chỉ dành cho Employee sở hữu chuyến đi, không tạo trùng theo `(trip_id, action_type)`.
- [x] Định tuyến bốn luồng, lookup theo ID/ngày/điểm đến, câu hỏi kết hợp nghiệp vụ và chính sách, kiểm tra ngày bay thực tế.
- [x] Session có TTL; preferences có yêu cầu đồng ý; cách ly user/session.
- [x] CSV UTF-8 BOM có che mẫu token/số thẻ; audit kỹ thuật không chứa nguyên văn tin nhắn.
- [x] Web demo và CLI; Admin xem audit, tải CSV, reset runtime; API các tab lọc dữ liệu theo quyền.
- [x] RAG áp dụng ACL trước xếp hạng, kiểm tra căn cứ, xung đột và loại chỉ thị injection.
- [x] Rà lại happy case và ca không thành công của bốn Employee, Reviewer, Approver, Admin.
- [x] Sửa danh sách chuyến của Employee, preferences của Approver, pending request qua chat và từ chối quyết định phê duyệt qua chat.
- [x] Lỗi scope dùng thông báo chung; lỗi thao tác theo role có thông báo riêng; giữ mã kỹ thuật và không lộ hồ sơ ngoài quyền.
- [x] Bỏ câu nhắc thừa về các hành động chưa thực hiện trong phản hồi.
- [x] Chuyển Markdown sang tiếng Việt và sửa bộ sinh báo cáo để lần chạy sau vẫn tạo tài liệu tiếng Việt.

## Xác minh

Lần kiểm tra ngày 2026-11-17: **96/96 test pytest đạt**, bao gồm test HTTP thật; **31/31 ca evaluation đạt**, không có hồi quy trên tập ca đã lưu. `compileall` và kiểm tra diff không phát hiện lỗi.

Chạy các lệnh trong `README.md`; xem kết quả mới nhất ở `eval/reports/after.md` và `eval/reports/regression.md`. Số lượng test được xác định bởi pytest lúc chạy. Mốc 2026-11-16 có 53 test; mốc trước đợt rà soát này có 69 test. Các số lịch sử không thay thế kết quả kiểm tra hiện tại.

Evaluator có 31 ca xác định. Baseline là lần đo đầu tiên sau khi triển khai, không phải số đo trước khi dự án tồn tại; không suy diễn thành mức cải thiện lịch sử.

## Chỉ cần khi mở rộng dự án

- [ ] Thêm kiểm tra căn cứ ngữ nghĩa để hỗ trợ diễn đạt lại và quy định phức tạp.
- [ ] Thay tài khoản demo bằng đăng nhập và phân công phê duyệt thật.
- [ ] Dùng cơ sở dữ liệu, kiểm soát ghi đồng thời, mã hóa và chính sách lưu/xóa log phù hợp vận hành.
- [ ] Bổ sung tổng budget cho toàn bộ tin nhắn, timeout cưỡng chế và đo hiệu quả trên nhiều dữ liệu hơn.
- [ ] Tích hợp LLM hoặc dịch vụ bên ngoài chỉ khi có yêu cầu mở rộng phạm vi rõ ràng.

Đặt vé, thanh toán, hoàn tiền, gửi email, chạy lịch nền và dùng dữ liệu cá nhân thật vẫn nằm ngoài phạm vi mini-project.
