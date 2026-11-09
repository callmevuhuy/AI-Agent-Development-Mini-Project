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
| request_approval | Approval | mock write (pending only) | trip_id, action_type, action_summary | xem mục Approval contract |
| search_travel_policy | Policy KB | read | query (<=200), category (enum), max_results (1..5) | trả chunk + metadata (gồm `page` nullable) + score |
| get_expense_report | Expense | read | report_id | regex `^EXP-\d{4}-\d{3}$` |
| calculate_expense_summary | Expense | deterministic | report_id | tổng, tỉ lệ theo category, cờ ngưỡng, thiếu receipt |
| validate_trip_requirements | Validator | deterministic | trip_facts, evidence_refs | trả danh sách missing/blocking |
| create_travel_checklist_draft | Draft Workspace | draft | trip_id | idempotent |
| create_escalation_or_support_draft | Draft Workspace | draft | trip_id, disruption_ref | idempotent |
| create_expense_review_draft | Draft Workspace | draft | report_id | idempotent |
| (optional) create_approval_packet_draft | Draft Workspace | draft | trip_id | |
| memory: get/set/delete_preference | Memory | scoped | get/delete: key; set: key, value | user scope lấy từ `user_context`; chỉ khi user yêu cầu lưu |

## Mỗi tool card cần có
Mục đích · Args schema · Preconditions · Validation · Result schema · Error codes · Side effects (none/draft only) · Workflows được phép dùng.

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
- `approved` / `rejected` do approval system (fixture `approvals.json`) quyết định. Trong test, chuyển trạng thái chỉ qua helper của fixture, không qua tool của agent.
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
      "action_summary": {"type": "string", "minLength": 5, "maxLength": 300}
    },
    "required": ["trip_id", "action_type", "action_summary"],
    "additionalProperties": false
  }
}
```
- Idempotency key: `(trip_id, action_type)`; gọi lại khi đã có record pending trả lại record cũ (`meta.reused: true`), không tạo bản trùng.
- `action_summary` là text không tin cậy: chỉ lưu và hiển thị, không bao giờ diễn giải thành lệnh.
- Khi record là `pending` hoặc `rejected`: workflow không thực hiện write/external action nào.

## Citation format (chốt)
Giữ nguyên `source, doc_id, section, page (nullable), version, chunk_id` từ search result đến draft/response. `section` là locator chính; `page` chỉ có khi corpus có phân trang, không bịa.
Hiển thị: `[doc_id §section v<version> · chunk_id]` (thêm `p.<page>` nếu có).
