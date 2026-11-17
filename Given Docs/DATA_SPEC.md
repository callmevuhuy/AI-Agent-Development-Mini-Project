# Đặc tả dữ liệu giả lập

Toàn bộ dữ liệu được tạo cho học tập, không chứa PII thật. ID chuẩn: `TRIP-YYYY-NNN`, `EXP-YYYY-NNN`, `EMP-NNN`. Định danh trường giữ nguyên để đối chiếu JSON.

## Tài khoản: users.json

| user_id | role | traveler_id |
|---|---|---|
| U-EMP-001 | Employee | EMP-001 |
| U-EMP-002 | Employee | EMP-002 |
| U-EMP-003 | Employee | EMP-003 |
| U-EMP-004 | Employee | EMP-004 |
| U-REV-001 | Reviewer | null |
| U-APR-001 | Approver | null |
| U-ADM-001 | Admin | null |

CLI `--user` nhận `user_id`; application tra role và nhân viên tương ứng. `traveler_id` không phải tài khoản đăng nhập. Dùng bảng này để kiểm tra quyền và cách ly người dùng.

## Chuyến đi: trips.json

Mọi chuyến bay đi trong dữ liệu giả lập xuất phát từ `Hanoi, Viet Nam` (HAN).

| trip_id | Nhân viên | Điểm đến | travel_status | Tình huống |
|---|---|---|---|---|
| TRIP-2026-001 | EMP-001 | Singapore | submitted | Chờ duyệt, quy trình A |
| TRIP-2026-002 | EMP-002 | Tokyo | confirmed | Đã duyệt; có hoãn chuyến bay, quy trình B |
| TRIP-2026-003 | EMP-003 | Berlin | draft | Thiếu purpose |
| TRIP-2026-004 | EMP-001 | London | submitted | Phê duyệt bị từ chối |
| TRIP-2026-005 | EMP-004 | Bangkok | cancelled | Chuyến đã hủy |
| TRIP-2026-006 | EMP-002 | Sydney | confirmed | Hợp lệ, có yêu cầu visa |

Các trường: `trip_id, traveler_id, origin, destination, start_date, end_date, purpose, travel_status`. Trạng thái chuyến khác trạng thái phê duyệt; approval lấy từ nguồn riêng.

## Nhân viên: travelers.json

Có ít nhất bốn hồ sơ ở hai bộ phận: EMP-001/EMP-003 thuộc Sales, EMP-002/EMP-004 thuộc Engineering. Các trường gồm `traveler_id`, `display_name`, `department`, `preferences`. Tên, sở thích ghế/bữa ăn đều giả lập; không có hộ chiếu, visa hoặc thẻ thật.

## Hành trình: itineraries.json

Có ít nhất bốn hành trình với chuyến bay, khách sạn và sự kiện giả lập. Chuyến TRIP-2026-002 có `flight_delay`, `delay_minutes=240`; TRIP-2026-005 có `flight_cancelled`. Các trường giờ đi/đến là nguồn để xác minh ngày bay, không suy từ toàn bộ khoảng ngày công tác.

## Phê duyệt: approvals.json và approval_requests.json

`approvals.json` giữ trạng thái duyệt chuyến: 001 pending, 002 approved, 004 rejected, 006 approved. Đây là nguồn nghiệp vụ về duyệt chuyến, tool agent không sửa dữ liệu này.

`approval_requests.json` giữ yêu cầu review theo `(trip_id, action_type)`. `request_approval` chỉ tạo pending và trả bản cũ khi gọi lại cùng cặp. Seed có `TRIP-2026-001/checklist_review` và `TRIP-2026-002/escalation`. Scope Approver phải khớp một yêu cầu hiện còn pending; không thay thế trạng thái duyệt chuyến.

`audit_events.json` ghi sự kiện workflow, tạo yêu cầu và quyết định mô phỏng. Tool Admin chỉ đọc; dữ liệu là JSON cục bộ, không phải audit bất biến production. Endpoint reset demo có thể xóa sự kiện runtime, giữ seed. Audit kỹ thuật không chứa nguyên văn hội thoại.

## Memory khi chạy

`data/memory/` chứa session theo user/phiên và preferences theo user; không commit dữ liệu phát sinh. Chỉ application xác nhận yêu cầu rõ ràng mới cho ghi/xóa preference. Memory không thay thế mock source.

## Chi phí: expenses.json

| report_id | Chuyến | Chủ báo cáo | Tình huống |
|---|---|---|---|
| EXP-2026-001 | TRIP-2026-002 | EMP-002 | Hợp lệ |
| EXP-2026-002 | TRIP-2026-006 | EMP-002 | Thiếu chứng từ/trường |
| EXP-2026-003 | TRIP-2026-001 | EMP-001 | Hạn mức ăn uống có xung đột chính sách |

Báo cáo có `currency`; dòng chi phí gồm `item_id, category, amount, date, receipt_attached`. Tổng, tỷ lệ, cờ ngưỡng và thông tin thiếu do code tính.

## Kho chính sách: policy_chunks.json

Trường bắt buộc: `chunk_id, doc_id, source, section, version, category, text`; bổ sung `allowed_roles`, `classification`, `page`, `effective_date`, `status`. `page` có thể null; không bịa số trang. Danh mục: `travel`, `expense`, `visa`, `insurance`, `approval`.

Chunk hạn mức có thể chứa `rule={category, measure, cap, currency}` để tính toán xác định. Nhiều bản active mâu thuẫn phải báo conflict. Chỉ ưu tiên bản mới khi bản cũ superseded và ngày hiệu lực mới hợp lệ; nêu lựa chọn trong draft.

Tập dữ liệu có chính sách phê duyệt, visa Singapore/Australia, bảo hiểm, chứng từ, hạn mức phòng ở, hạn mức ăn uống và hỗ trợ sự cố. Có cặp chính sách ăn uống v1/v2 cùng active để kiểm tra needs_human, và chunk chứa câu injection giả để kiểm tra loại khỏi evidence. ACL được lọc trước ranking/conflict/citation; Approver còn bị giới hạn danh mục theo action, Admin không có quyền kho.

## Luật kiểm tra: requirements.json

- Trường bắt buộc: `trip_id, traveler_id, destination, start_date, end_date, purpose`; thiếu → `needs_input`.
- Chuyến cancelled hoặc approval rejected → `needs_human`.
- Approval pending → `awaiting_approval`; chỉ nguồn approved mới được coi là đã duyệt.
- Singapore yêu cầu `approval, travel, insurance`; Sydney thêm `visa`.
- Mỗi danh mục bắt buộc cần evidence phù hợp; claim phải được căn cứ hỗ trợ. Thiếu evidence → cần người xem xét, không tạo citation giả.

## Bản nháp: drafts/

Draft JSON có ID ổn định theo `(workflow, source_id)`, ghi nguyên tử; chạy lại cập nhật cùng bản. Nội dung chỉ là dữ liệu giả lập đã lấy qua tool, không chứa chỉ thị thực thi. `delivery_status` giữ `not_sent` hoặc `not_published`.
