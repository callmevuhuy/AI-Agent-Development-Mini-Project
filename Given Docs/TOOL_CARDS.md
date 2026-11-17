# Đặc tả các công cụ

## Ngữ cảnh và hợp đồng chung

Application cung cấp `user_context={user_id, role, session_id}` và tùy trường hợp `approval_scope={trip_id, action_type}`. Những trường này không nằm trong arguments của model. Dispatcher đối chiếu ID với role, sở hữu và scope pending trước khi thực thi. Memory tool lấy user/session từ context.

Mọi schema dùng `type: object`, có trường bắt buộc và `additionalProperties: false`. Thành công trả `{ok:true, data, meta:{source, read_only}}`; lỗi trả `{ok:false, error:{code, message, retryable}}`.

Mã lỗi ổn định: `invalid_argument`, `not_found`, `not_allowed`, `unauthorized_scope`, `budget_exceeded`, `timeout`, `unavailable`, `policy_access_required`. Thông báo bằng tiếng Việt, không lộ stack trace hoặc dữ liệu ngoài quyền. Scope sai dùng câu chung; role bị cấm thao tác có lời giải thích riêng cho thao tác đó.

## Danh sách 19 công cụ

| Công cụ | Arguments chính | Chức năng và điều kiện |
|---|---|---|
| get_trip_request | trip_id | Đọc yêu cầu công tác, kiểm tra ID và quyền |
| get_traveler_profile | traveler_id | Đọc trường hồ sơ không nhạy cảm |
| get_itinerary | trip_id | Đọc hành trình và sự cố |
| get_approval_status | trip_id | Đọc nguồn trạng thái phê duyệt |
| request_approval | trip_id, action_type, action_summary | Chỉ Employee chủ chuyến, tạo pending không trùng |
| search_travel_policy | query, category, max_results? | Tra kho policy ngoại tuyến có ACL |
| get_expense_report | report_id | Đọc báo cáo chi phí |
| calculate_expense_summary | report_id | Tính tổng/tỷ lệ, ngưỡng, chứng từ và trường thiếu |
| validate_trip_requirements | trip_facts, evidence_refs | Đánh giá điều kiện từ nguồn và requirements.json |
| create_travel_checklist_draft | trip_id, checklist | Lưu checklist draft có ID ổn định |
| create_escalation_or_support_draft | trip_id, support_draft | Lưu draft hỗ trợ sự cố |
| create_expense_review_draft | report_id, review_preview | Lưu draft rà soát chi phí |
| get_preference | key | Đọc tùy chọn của user hiện tại |
| set_preference | key, value | Lưu tùy chọn khi người dùng yêu cầu rõ ràng |
| delete_preference | key | Xóa tùy chọn khi người dùng yêu cầu rõ ràng |
| admin_list_trips | không có | Admin đọc tổng quan mọi chuyến |
| admin_get_audit_history | trip_id? / report_id? | Admin đọc audit theo bộ lọc |
| list_my_trips | destination?, date? | Employee xem của mình, Reviewer xem toàn bộ |
| list_my_expenses | trip_id? | Employee xem của mình, Reviewer xem toàn bộ |

Allowlist chính xác nằm trong `registry.py`. Workflow A dùng tool chuyến/duyệt/kiểm tra/checklist; B dùng itinerary/hỗ trợ; C dùng báo cáo/tính toán/rà soát; admin chỉ dùng hai tool quản trị. Các tool lookup/profile/memory được cấp theo nhu cầu của workflow, vẫn phải qua authorization.

## Quy tắc đầu vào và tác động

- `trip_id` khớp `^TRIP-\d{4}-\d{3}$`, `report_id` khớp `^EXP-\d{4}-\d{3}$`.
- Policy query dài 3–200 ký tự, `max_results` từ 1 đến 5. Category thuộc travel/expense/visa/insurance/approval.
- Preferences chỉ nhận `response_language=en|vi`, `preferred_output_format=concise|detailed`; ghi/xóa cần cờ đồng ý từ application.
- Tool draft chỉ ghi JSON trong `data/drafts/`, tối đa 32 KiB, nguồn phải tồn tại và thuộc quyền. Nội dung là dữ liệu thụ động. ID ổn định theo workflow/nguồn; retry cập nhật cùng bản.
- Kết quả draft có `draft_id`, `draft_status`, `delivery_status`, `reused`. Workflow dựa vào kết quả này để xác nhận đã lưu.
- Tool đọc không sửa nghiệp vụ; tool tạo pending và draft là những thao tác ghi giả lập được cấp. Agent không có tool approve/reject, email, booking hoặc thanh toán.

## Schema tham khảo cho tra cứu policy

```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string", "minLength": 3, "maxLength": 200},
    "category": {"type": "string", "enum": ["travel", "expense", "visa", "insurance", "approval"]},
    "max_results": {"type": "integer", "minimum": 1, "maximum": 5}
  },
  "required": ["query", "category"],
  "additionalProperties": false
}
```

## Hợp đồng tạo yêu cầu phê duyệt

```json
{
  "type": "object",
  "properties": {
    "trip_id": {"type": "string", "pattern": "^TRIP-\\d{4}-\\d{3}$"},
    "action_type": {"type": "string", "enum": ["checklist_review", "escalation", "publish_request"]},
    "action_summary": {"type": "string", "minLength": 5, "maxLength": 240}
  },
  "required": ["trip_id", "action_type", "action_summary"],
  "additionalProperties": false
}
```

Cặp `(trip_id, action_type)` là khóa không tạo trùng. Nếu yêu cầu cũ pending, trả cùng record và `meta.reused=true`. Nếu đã resolved, từ chối tạo lại. `action_summary` là dữ liệu không đáng tin cậy, chỉ lưu/hiển thị, không diễn giải thành lệnh. Chat tạo bản tóm tắt ngắn theo action/ID, không dùng nguyên câu hỏi làm chỉ thị.

`approved/rejected` của chuyến và quyết định review do nguồn/hệ thống mô phỏng bên ngoài tool set quản lý. Approver chỉ đọc facts theo scope: checklist_review → trip/approval và policy approval/travel/visa/insurance; escalation → itinerary và travel; publish_request → trip/approval và approval. Không có quyền duyệt danh sách rộng hoặc tạo draft.

## Hợp đồng RAG và citation

BM25 chạy ngoại tuyến; lọc ACL trước xếp hạng, loại chunk injection, trả `no_result` rõ ràng, kiểm tra phiên bản và grounding. Điểm truy xuất không chứng minh claim đúng. Mỗi kết quả giữ `source, doc_id, section, page, version, chunk_id`; citation có mẫu `[doc_id §section v<version> · chunk_id]`, chỉ thêm trang khi có dữ liệu.

## Chuỗi kiểm tra dispatcher

Registry → allowlist workflow → schema/định dạng miền → quyền từ application → budget → thực thi → cấu trúc kết quả. Orchestrator thực hiện retry có giới hạn và ghi trace cho các lần thử, kể cả lần bị từ chối.

## Cập nhật workspace và phản hồi

Trips có bốn tác vụ riêng: xem chi tiết, xem hành trình, kiểm tra checklist và yêu cầu hỗ trợ. Admin xem audit liên quan; Approver xem danh sách pending được phân công trong Trips, rồi đọc hồ sơ theo scope qua chat. Chọn tác vụ gửi đúng ý định, không ghép đọc dữ kiện với checklist. Ngữ cảnh phiên giữ tác vụ cần làm rõ và ngôn ngữ khi người dùng trả lời bằng ID.

Draft giữ mã `DR-…` độc lập với Trip/Expense nguồn. Employee chủ hồ sơ và Reviewer được mở đầy đủ dữ kiện nguồn, hành trình, các trường thiếu và nội dung/citation bản nháp. Chỉ ghi chú, mục đích đề xuất và checklist đề xuất được sửa. Các API `/api/draft/detail`, `/api/draft/save`, `/api/draft/recheck` kiểm tra quyền tại server; không cho sửa identity, approval, dữ kiện nguồn hoặc citation. Kiểm tra lại dùng nguồn thật của mock; nội dung đề xuất được giữ qua lần tạo lại, không tự làm nguồn đầy đủ.

Thông báo không có chức năng không tự tạo phiếu. Pending hiển thị riêng với trạng thái chuyến; yêu cầu hỗ trợ có trạng thái riêng trên Trips. Thẻ prompt dùng nhãn kết quả mong đợi và mã CASE. Các nhánh an toàn kiểm tra nguyên câu tiếng Việt trước lookup/clarification.

Evaluator bổ sung 31 thẻ web vào 31 ca nền; tỷ lệ chọn tool và arguments đo trên các thẻ, số bước/retry lấy từ trace. Task completion loại các ca safety khỏi mẫu số. Grounding vẫn chỉ có claim đại diện; chưa phải benchmark ngữ nghĩa rộng.
