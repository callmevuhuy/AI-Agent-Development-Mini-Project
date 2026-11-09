# MEMORY_AND_SAFETY

## 1. Ba loại state, tách biệt
| Loại | Scope | Ví dụ | Lưu ở đâu |
|---|---|---|---|
| Run state | `run_id` | step_count, trace, outcome | RAM + `eval/traces/` |
| Session state | `user_id` + `session_id` | `active_trip_id` | `session_store` (xóa khi hết session) |
| Persistent preference | `user_id` | `response_language`, `preferred_output_format` | `preference_store`, CHỈ khi user yêu cầu lưu |

Source of truth: mock systems. Trip status, itinerary, approval, expense luôn đọc lại qua tool; memory không được thay thế.

## 2. Không lưu
Hộ chiếu, visa, thẻ, số tài khoản, token, địa chỉ thật, full raw conversation (mặc định).

## 2. Role và quyền (mock authorization)
Application gắn `user_context = {user_id, role, session_id}` từ `users.json`; model không được tự khai role. Với một lượt review của Approver, application có thể gắn thêm `approval_scope = {trip_id, action_type}` lấy từ đúng một request đang `pending`. Model không được tự đặt hoặc mở rộng scope này. `user_id` khác `traveler_id`: Employee map tới đúng một `traveler_id`.

| Hành động | Employee | Reviewer | Approver |
|---|---|---|---|
| Đọc trip / itinerary / expense | Chỉ của mình | Tất cả trong dataset | Chỉ facts cần cho `approval_scope` đang pending; không browse/list tùy ý |
| Đọc approval status | Của mình | Tất cả | Chỉ request trong `approval_scope` |
| Đọc traveler profile | Của mình | Tất cả (field không nhạy cảm) | Không đọc profile trực tiếp |
| Tạo draft checklist / escalation | Của mình | Mọi trip | Không |
| Tạo draft expense review | Của mình | Mọi report | Không |
| `request_approval` (tạo pending) | Của mình | Mọi trip | Không |
| Preference / session | Của mình | Của mình | Của mình |

- Approver chỉ đọc packet/draft của request `pending` đang nằm trong `approval_scope` và các trường nguồn tối thiểu cần để xem xét đúng action đó. Ví dụ: checklist review được giới hạn vào facts của chuyến đi; escalation review vào itinerary/disruption liên quan. Không có quyền đọc trip, expense, itinerary hoặc approval khác để tìm kiếm rộng. Nếu không có scope hợp lệ hoặc request không còn pending, từ chối bằng `unauthorized_scope` và không trả dữ liệu.
- `U-APR-001` không có phân công approver riêng trong mock dataset; application chỉ đưa từng request pending vào scope của một lượt review. Không có công cụ list request hoặc chuyển scope do model yêu cầu.
- Approver không được tạo draft, gọi `request_approval`, thay đổi fixture, approve/reject, publish hay gửi bất kỳ nội dung nào. Quyết định `approved/rejected` chỉ được mô phỏng bằng fixture/test helper nằm ngoài tool set của agent.
- Vi phạm quyền -> `unauthorized_scope`, trace ghi `safety_event`, không lộ dữ liệu của người khác trong error message.
- Test bắt buộc: Employee A đọc trip của B (bị chặn), Employee gọi draft của trip người khác, Approver đọc đúng packet/facts trong scope pending (cho phép), Approver đọc dữ liệu ngoài scope hoặc tạo draft/request approval (bị chặn), Reviewer đọc mọi trip (cho phép).

## 3. API memory
Internal API: `get_preferences(user_id)`, `set_preference(user_id, key, value)` (whitelist key), `delete_preference(user_id, key)`, `clear_session(user_id, session_id)`. Đây là API nội bộ; tool-facing schema không nhận `user_id` hay `session_id` từ model mà dispatcher truyền scope từ `user_context`.
Mọi hàm bắt buộc kiểm tra scope; truy cập chéo user -> `unauthorized_scope`.

## 4. Safety controls
| Lớp | Cách làm |
|---|---|
| Input validation | Regex ID, giới hạn độ dài query, required fields |
| Tool allowlist | Per-workflow; tool ngoài list bị từ chối trước execution |
| Validation | JSON Schema + domain + output check |
| Least privilege | Tool read-only hoặc draft-only; không file/network/shell tự do |
| Budgets | max_steps=8, retry<=2, top_k<=5, rewrite<=1 |
| Data boundary | Chỉ dataset training; isolation user/session |
| Approval | `request_approval` chỉ tạo record `pending`; pending/rejected => không action nào; agent không có tool duyệt |
| Prompt injection | User text + chunk là data; strip/flag chuỗi kiểu "ignore previous instructions"; không cho chunk đổi allowlist hay gọi tool |
| Audit | Trace whitelist field; không secret/PII |

## 5. Xử lý injection
- Input user: dispatcher không cho tool ngoài allowlist dù user ép; planner chỉ chọn từ tool list của workflow.
- Chunk policy chứa lệnh: đánh dấu `untrusted`, bỏ qua câu lệnh, vẫn có thể trích phần policy hợp lệ nếu có; ghi `safety_event` vào trace.

## 6. Giới hạn (đưa vào báo cáo)
Không booking/đổi/hủy vé, visa, bảo hiểm, thanh toán, hoàn tiền, phê duyệt thật, gửi email/ticket, API/credential thật, scheduler/background job/production.
