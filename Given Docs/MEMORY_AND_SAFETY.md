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

| Hành động | Employee | Reviewer | Approver | Admin |
|---|---|---|---|---|
| Đọc trip / itinerary / expense | Chỉ của mình | Tất cả trong dataset | Chỉ facts cần cho `approval_scope` đang pending; không browse/list tùy ý | Chỉ trip overview |
| Đọc approval status | Của mình | Tất cả | Chỉ request trong `approval_scope` | Chỉ lịch sử audit |
| Đọc traveler profile | Của mình | Tất cả (field không nhạy cảm) | Không đọc profile trực tiếp | Không |
| Tạo draft checklist / escalation | Của mình | Mọi trip | Không | Không |
| Tạo draft expense review | Của mình | Mọi report | Không | Không |
| `request_approval` (tạo pending) | Chỉ trip của mình | Không | Không | Không |
| Preference / session | Của mình | Của mình | Của mình | Không |
| Xem toàn bộ trip | Không | Có | Không | Có (read-only) |
| Xem audit history | Không | Không | Không | Có (read-only) |
| Policy RAG | Allowed chunks | Allowed chunks | Category theo action + pending scope | Không |

- Approver chỉ đọc các source facts tối thiểu cần để xem xét request `pending` trong `approval_scope`. Ví dụ: checklist review được giới hạn vào trip facts; escalation review vào itinerary/disruption liên quan. Hiện chưa có tool đọc packet/draft. Không có quyền đọc trip, expense, itinerary hoặc approval khác để tìm kiếm rộng. Nếu scope không hợp lệ hoặc request không còn pending, trả `unauthorized_scope` và không trả dữ liệu.
- `U-APR-001` không có phân công approver riêng; application chỉ đưa một request đang `pending` trong `approval_requests.json` vào scope của lượt review. Dispatcher kiểm tra lại fixture trên từng lần đọc và giới hạn tool theo `action_type`. Không có công cụ list request hoặc chuyển scope do model yêu cầu.
- Fixture mẫu có scope `checklist_review` cho TRIP-2026-001 và `escalation` cho TRIP-2026-002. `request_approval` chỉ tạo `pending`, idempotent theo `(trip_id, action_type)`; quyết định đến từ mock external helper, không nằm trong tool set.
- Approver không được tạo draft, gọi `request_approval`, thay đổi fixture, approve/reject, publish hay gửi bất kỳ nội dung nào. Quyết định `approved/rejected` chỉ được mô phỏng bằng fixture/test helper nằm ngoài tool set của agent.
- Admin (`U-ADM-001`) chỉ được gọi `admin_list_trips` và `admin_get_audit_history`; không thể tạo draft, request approval, approve/reject, sửa dữ liệu hoặc search policy. Audit local mock giữ vô thời hạn trong prototype, không có chức năng sửa/xóa; chỉ lưu workflow outcome, request creation và decision events, không lưu raw message.
- RAG ACL được kiểm tra trước retrieval: Employee/Reviewer chỉ thấy chunks có `allowed_roles`; Approver cần pending `approval_scope` và category phù hợp action; Admin mặc định không có corpus access. Chunk bị lọc không thể tạo citation, version conflict hay trace result.
- Vi phạm quyền -> `unauthorized_scope`, trace ghi `safety_event`, không lộ dữ liệu của người khác trong error message.
- Test bắt buộc: Employee A đọc trip của B (bị chặn), Employee gọi draft của trip người khác, Approver đọc đúng packet/facts trong scope pending (cho phép), Approver đọc dữ liệu ngoài scope hoặc tạo draft/request approval (bị chặn), Reviewer đọc mọi trip (cho phép).

## 3. API memory
Internal API nhận `user_context` từ application: `get_preferences(context)`, `get_preference(context, key)`, `set_preference(context, key, value)`, `delete_preference(context, key)`, `get_session_state(context)`, `set_session_value(context, key, value)`, `clear_session(context)`. Tool schema không nhận `user_id` hay `session_id` từ model.
Preference keys chỉ gồm `response_language` (`en|vi`) và `preferred_output_format` (`concise|detailed`). Ghi/xóa preference cần `memory_write_authorized=true` do application đặt khi user yêu cầu rõ ràng; model không thể tự đặt cờ này trong args. Session chỉ lưu `active_trip_id` và `last_workflow`, scoped theo user + session, không phải nguồn sự thật cho trip. Mọi hàm kiểm tra context; truy cập chéo user/session bị từ chối.

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
| Audit | Trace whitelist field; append-only mock events cho workflow, request và decision; không lưu raw message, secret hay PII thật |

## 5. Xử lý injection
- Input user: dispatcher không cho tool ngoài allowlist dù user ép; planner chỉ chọn từ tool list của workflow.
- Chunk policy chứa lệnh: đánh dấu `untrusted`, bỏ qua câu lệnh, vẫn có thể trích phần policy hợp lệ nếu có; ghi `safety_event` vào trace.

## 6. Giới hạn (đưa vào báo cáo)
Không booking/đổi/hủy vé, visa, bảo hiểm, thanh toán, hoàn tiền, phê duyệt thật, gửi email/ticket, API/credential thật, scheduler/background job/production.
