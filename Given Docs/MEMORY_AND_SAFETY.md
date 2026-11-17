# Memory, phân quyền và an toàn

## 1. Ba loại trạng thái

| Loại | Phạm vi | Nội dung | Nơi lưu |
|---|---|---|---|
| Trạng thái lượt | `run_id` | Số bước, trace, kết quả cuối | RAM; evaluator xuất trace mẫu |
| Ngữ cảnh phiên | `user_id` + `session_id` | `active_trip_id`, `active_report_id`, `last_workflow`, `pending_slot` | JSON trong `data/memory/sessions/` |
| Tùy chọn dài hạn | `user_id` | `response_language`, `preferred_output_format` | JSON trong `data/memory/preferences/` |

Session có TTL mặc định 1.800 giây, được gia hạn khi ghi. Khi đọc thấy hết hạn, file bị xóa và trả trạng thái rỗng; chưa có tiến trình nền dọn file. Preferences không tự hết hạn. Đóng trình duyệt không xóa memory trên đĩa.

Chỉ chấp nhận ngôn ngữ `en|vi` và định dạng `concise|detailed`. Ghi/xóa preference cần `memory_write_authorized=true` do application đặt khi người dùng yêu cầu rõ ràng. Model không truyền cờ hoặc user/session qua arguments.

Memory chỉ giữ ID và ngữ cảnh để nối lượt, không phải nguồn sự thật về chuyến đi, hành trình, approval hoặc chi phí. Những dữ kiện đó phải đọc lại từ mock tool. Không có khả năng tìm kiếm toàn bộ lịch sử chat hoặc memory theo vector. Chưa có giới hạn theo token, mã hóa hay kiểm soát ghi đồng thời ở nhiều tiến trình.

## 2. Dữ liệu không được lưu trong memory

Không lưu hộ chiếu, visa, thẻ, số tài khoản, token, địa chỉ thật hoặc nguyên văn hội thoại. Kho chỉ nhận các khóa nằm trong danh sách cho phép. CSV hội thoại là hệ thống log riêng, có che một số mẫu token/số thẻ nhưng không bảo đảm phát hiện mọi PII.

## 3. Danh tính và quyền

Application tra `user_id`, `role`, `traveler_id` từ `users.json`, gắn `session_id`. Scope Approver là `{trip_id, action_type}` do application cấp cho một yêu cầu pending. Tài khoản demo chưa phải đăng nhập production; bộ nhớ nội bộ tin cậy context từ application, dispatcher kiểm tra role khớp hồ sơ trước khi chạy tool.

| Thao tác | Employee | Reviewer | Approver | Admin |
|---|---|---|---|---|
| Đọc chuyến, hành trình, chi phí | Của mình | Tất cả dữ liệu giả lập | Chỉ facts cần cho scope; không đọc chi phí | Tổng quan chuyến |
| Đọc trạng thái duyệt | Của mình | Tất cả | Theo scope | Qua audit |
| Hồ sơ nhân viên | Của mình | Các trường không nhạy cảm | Không | Không |
| Tạo draft nghiệp vụ | Của mình | Mọi hồ sơ được cấp | Không | Không |
| Tạo yêu cầu pending | Của mình | Không | Không | Không |
| Session và preferences | Của mình | Của mình | Của mình | Không |
| Danh sách chuyến | Của mình | Tất cả | Không | Tất cả, chỉ đọc |
| Audit | Không | Không | Không | Có |
| RAG | Chunk được cấp | Chunk được cấp | Theo action và scope pending | Không |

Approver `U-APR-001` chưa có bảng phân công cá nhân; dispatcher kiểm tra lại scope có bản ghi pending trước mỗi tool call. `checklist_review` đọc trip/approval và tra approval/travel/visa/insurance; `escalation` đọc itinerary và tra travel; `publish_request` đọc trip/approval và tra approval. Không có tool list mọi yêu cầu hoặc approve/reject.

## 4. Phản hồi khi bị từ chối

- Dữ liệu hoặc danh mục ngoài scope: dùng cùng câu chung, không tiết lộ người sở hữu hoặc nội dung hồ sơ.
- Role yêu cầu thao tác không được phép: nêu rõ role, thao tác cụ thể và người có thể hỗ trợ. Ví dụ Reviewer xem audit được hướng tới Admin; Admin rà soát chi phí được hướng tới Employee hoặc Reviewer.
- Thiếu scope hoặc scope hết pending: giải thích cần chọn lại yêu cầu đang chờ.
- Giữ `error.code`, `error.message`, `error.retryable`; trace ghi sự kiện từ chối. Không có side effect nghiệp vụ trên nhánh bị từ chối.

## 5. API memory nội bộ

`get_preferences`, `get_preference`, `set_preference`, `delete_preference`, `get_session_state`, `set_session_value`, `delete_session_value`, `clear_session` nhận context do application cung cấp. `session_id` chỉ nhận chữ, số, `_`, `-`, tối đa 80 ký tự; ID người dùng có mẫu cố định để ngăn đường dẫn thoát thư mục.

## 6. Các lớp bảo vệ

| Lớp | Cơ chế |
|---|---|
| Đầu vào | Regex ID, trường bắt buộc, kiểu dữ liệu, giới hạn query |
| Tool | Registry, allowlist theo workflow, JSON Schema không nhận trường thừa |
| Quyền | Role, chủ hồ sơ, scope pending và ACL policy |
| Budget | Mặc định 8 bước một state, trần 12; tối đa 2 retry; top-k tối đa 5; một rewrite mỗi nhánh |
| Kết quả | Kiểm tra cấu trúc, không đưa raw exception vào phản hồi |
| Injection | Nhận diện chỉ thị vượt quy tắc; loại chunk không an toàn khỏi evidence |
| Audit | Trace dùng trường cho phép; JSON audit không chứa raw message; CSV vận hành được lọc mẫu dữ liệu nhạy cảm |

Orchestrator điều phối retry và trace; dispatcher kiểm tra budget và thực thi. Chưa có timeout cưỡng chế cho handler bị treo. Audit là file JSON cục bộ, không phải kho chống sửa production; Admin có endpoint reset runtime riêng ngoài tool set.

## 7. Kiểm thử bắt buộc

Kiểm tra cách ly user/session, hết TTL, không lưu khóa lạ, ghi preference thiếu đồng ý, giả mạo identity trong arguments, Employee đọc/tạo draft cho hồ sơ người khác, Reviewer đọc hợp lệ, Approver trong/ngoài scope và scope hết pending, Admin bị chặn nghiệp vụ. Kết quả cần kiểm tra cả thông báo, dữ liệu không bị lộ và không có side effect bị cấm.

## 8. Ngoài phạm vi

Không có đặt/đổi/hủy vé thật, visa, bảo hiểm, thanh toán, hoàn tiền, quyết định phê duyệt thật, gửi email/ticket ra ngoài, API hoặc credential thật, lập lịch nền và triển khai production.
