# TOOL_CARDS

`user_context` (user_id, role, session_id; optional application-owned `approval_scope`) do application gắn vào, KHÔNG nằm trong args của model và model không thể khai báo. Dispatcher đối chiếu mọi ID do model đề xuất với scope này trước khi tool đọc dữ liệu. Với memory tools, `user_id` và `session_id` luôn lấy từ context; schema của model chỉ nhận `key`/`value` cần thiết. Phân quyền theo role: xem docs/MEMORY_AND_SAFETY.md mục 2.

Mọi schema: `type: object`, `additionalProperties: false`, có `required`. Kết quả: `{ok, data, meta{source, read_only}}` hoặc `{ok:false, error{code, message, retryable}}`.
Error codes gợi ý: `invalid_argument, not_found, not_allowed, unauthorized_scope, budget_exceeded, timeout, unavailable`.

| Tool | Hệ thống | Loại | Args | Ghi chú |
|---|---|---|---|---|
| get_trip_request | Travel Request | read | trip_id | regex `^TRIP-\d{4}-\d{3}$` |
| get_traveler_profile | Traveler Profile | read | traveler_id | chỉ field không nhạy cảm |
| get_itinerary | Itinerary | read | trip_id | gồm disruption status |
| get_approval_status | Approval | read | trip_id | source of truth về approval |
| request_approval | Approval | registered; Employee-owned trip | trip_id, action_type, action_summary | chỉ tạo pending; idempotent theo `(trip_id, action_type)` |
| search_travel_policy | Policy KB | read | query (<=200), category (enum), max_results (1..5) | trả chunk + metadata (gồm `page` nullable) + score |
| get_expense_report | Expense | read | report_id | regex `^EXP-\d{4}-\d{3}$` |
| calculate_expense_summary | Expense | deterministic | report_id | tổng, tỉ lệ theo category, cờ ngưỡng, thiếu receipt |
| validate_trip_requirements | Validator | deterministic | trip_facts, evidence_refs | trả danh sách missing/blocking |
| create_travel_checklist_draft | Draft Workspace | draft | trip_id, checklist | idempotent by `(pretrip, trip_id)` |
| create_escalation_or_support_draft | Draft Workspace | draft | trip_id, support_draft | idempotent by `(intrip, trip_id)` |
| create_expense_review_draft | Draft Workspace | draft | report_id, review_preview | idempotent by `(posttrip, report_id)` |
| (optional) create_approval_packet_draft | Draft Workspace | draft | trip_id | |
| get_preference | Memory | scoped read | key | chỉ preference whitelist của user hiện tại |
| set_preference | Memory | scoped write | key, value | chỉ khi application xác nhận user yêu cầu lưu |
| delete_preference | Memory | scoped write | key | chỉ khi application xác nhận user yêu cầu xóa |
| admin_list_trips | Travel Request | Admin read-only | none | list mọi mock trip; không sửa |
| admin_get_audit_history | Audit log | Admin read-only | trip_id? / report_id? | lọc lịch sử; không sửa/xóa |

## Mỗi tool card cần có
Mục đích · Args schema · Preconditions · Validation · Result schema · Error codes · Side effects (none/draft only) · Workflows được phép dùng.

Draft tools chỉ ghi JSON vào `data/drafts/`; nội dung là inert data, giới hạn 32 KiB, ghi atomically và không được gửi/publish. Tool trả `draft_id`, `draft_status`, `delivery_status`, và `reused` để workflow xác nhận lần ghi/update.

Policy search dùng BM25 offline, trả citation locator và `no_result`; chunk có câu lệnh kiểu prompt injection bị loại khỏi evidence và chỉ để lại safety event với chunk ID. Version conflict cùng `doc_id` + `section` trả cùng citations, không tự chọn bản. Claim grounding yêu cầu từ khóa nội dung khớp trong một câu trusted evidence và cùng polarity; đây là baseline lexical, không phải NLI.

## Mẫu schema (search_travel_policy)
```json
{
  "name": "search_travel_policy",
  "description": "Tìm chunk policy giả lập. Chỉ đọc.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "minLength": 3, "maxLength": 200},
      "category": {"type": "string", "enum": ["travel","expense","visa","insurance","approval"]},
      "max_results": {"type": "integer", "minimum": 1, "maximum": 5}
    },
    "required": ["query", "category"],
    "additionalProperties": false
  }
}
```

## Dispatcher checklist (theo thứ tự)
registry -> workflow allowlist -> JSON Schema -> domain validation -> mock authorization (user/session từ context) -> budget -> execute -> validate output -> trace.

## Approval contract (chốt)
- `request_approval` CHỈ tạo record `pending`. Tool không bao giờ trả `approved` hoặc `rejected`.
- `approved` / `rejected` do external mock approval helper cập nhật fixture `approvals.json`; helper append event có actor, role, reason code/text, timestamp và run id. Agent tool không có quyền gọi helper.
- Schema duy nhất (registry, wrapper, test dùng chung):
```json
{
  "name": "request_approval",
  "description": "Tạo yêu cầu phê duyệt mô phỏng ở trạng thái pending. Không phê duyệt, không thực thi action.",
  "parameters": {
    "type": "object",
    "properties": {
      "trip_id": {"type": "string", "pattern": "^TRIP-\\d{4}-\\d{3}$"},
      "action_type": {"type": "string", "enum": ["checklist_review", "escalation", "publish_request"]},
      "action_summary": {"type": "string", "minLength": 5, "maxLength": 240}
    },
    "required": ["trip_id", "action_type", "action_summary"],
    "additionalProperties": false
  }
}
```
- Idempotency key: `(trip_id, action_type)`; khi pending, gọi lại trả record cũ (`meta.reused: true`), không tạo bản trùng. Nếu record đã resolved, tool từ chối và không trả trạng thái quyết định.
- Tool chỉ dành cho Employee và trip thuộc user hiện tại. `action_summary` có giới hạn 240 ký tự.
- `action_summary` là text không tin cậy: chỉ lưu và hiển thị, không bao giờ diễn giải thành lệnh.
- Khi record là `pending` hoặc `rejected`: workflow không thực hiện write/external action nào.
- Admin chỉ có `admin_list_trips`/`admin_get_audit_history`; RAG ACL lọc `allowed_roles` trước BM25. Approver cần pending scope; categories: checklist_review → approval/travel/visa/insurance, escalation → travel, publish_request → approval. Admin không có RAG access.

## Citation format (chốt)
Giữ nguyên `source, doc_id, section, page (nullable), version, chunk_id` từ search result đến draft/response. `section` là locator chính; `page` chỉ có khi corpus có phân trang, không bịa.
Hiển thị: `[doc_id §section v<version> · chunk_id]` (thêm `p.<page>` nếu có).
