# WORKFLOWS

Terminal outcomes: `completed | needs_input | needs_human | awaiting_approval | partial | failed_validation | failed_delivery | failed_budget`.
Draft lifecycle: `draft_created -> awaiting_approval -> approved -> publish_requested -> published` (trong project không có `published` thật). `delivery_status` luôn `not_sent` / `not_published`.

## Định nghĩa trạng thái (tránh nhầm lẫn)
- `trip_approval_status`: trạng thái duyệt chuyến từ approval system (`pending | approved | rejected`).
- `approval_request_status`: trạng thái review trong `approval_requests.json`; tool chỉ tạo pending, còn decision do mock external helper cập nhật.
- `draft_status`: vòng đời artifact (`draft_created -> awaiting_approval -> approved -> publish_requested -> published`).
- Terminal outcome `awaiting_approval` chỉ dùng khi có approval request đang `pending` thật (trip pending hoặc `request_approval` vừa tạo).
- `request_approval` chỉ được gọi tường minh bởi Employee cho trip của chính user; tool chỉ tạo `pending`, không bao giờ trả `approved`.

## Run state (bắt buộc)
`run_id, workflow, phase, user_id, role, session_id, step_count, max_steps, safe_tool_results, trace[], outcome`

`step_count` tăng một lần cho mỗi lần gọi dispatcher; retry cũng tiêu thụ một bước. Mọi call đi qua `run_tool`; chỉ retry lỗi có `retryable: true`, tối đa 2 lần. Khi hết budget, dừng với `failed_budget`. Trace chỉ lưu ID đã kiểm tra, category, độ dài query, trạng thái/result code và source; không lưu raw query, action summary, session ID hoặc tool output.

## Retrieval routing
| Nhu cầu | Xử lý |
|---|---|
| Greeting / viết lại text có sẵn | Trả lời trực tiếp |
| Status trip/itinerary/approval | Mock read tool |
| Claim về policy | `search_travel_policy` |
| Thiếu ID | `needs_input` hỏi lại |
| Facts live + policy | Facts trước, retrieval có điều kiện |

Policy search chạy BM25 offline và trả `results`, `no_result`, citations, `version_conflicts`, `resolved_versions` và danh sách chunk injection đã loại. Claim dạng policy chỉ được xuất nếu `check_claim` tìm thấy đủ terms trong cùng một câu trusted evidence, polarity trùng khớp; nếu không thì không phát biểu claim. Đây là lexical baseline, chưa phải semantic entailment.

## A — Pre-trip Planning and Compliance
Allowlist: `get_trip_request, get_approval_status, search_travel_policy, validate_trip_requirements, create_travel_checklist_draft, get_traveler_profile, request_approval` (plus scoped preference tools)
```
1  validate trip_id (regex)            -> fail: failed_validation / thiếu: needs_input
2  get_trip_request                    -> not found: failed_validation(unknown_id)
3  validator obtains trip approval status from the approval source
4  search_travel_policy(destination, category)  (<=1 rewrite, top_k<=5)
5  validate_trip_requirements(facts, evidence)  [deterministic theo requirements.json: field đủ? approval? category evidence đủ?]
6  create_travel_checklist_draft(trip_id, checklist) [idempotent; stable draft_id]
7  outcome:
   - field thiếu            -> needs_input
   - approval pending       -> awaiting_approval (checklist vẫn draft, không nói "đã duyệt")
   - approval rejected      -> needs_human
   - evidence không đủ      -> needs_human + limitation
   - approved + evidence ok -> completed
```
Rules: chỉ claim policy khi có citation; không nói "đã duyệt" nếu source chưa `approved`.

## B — In-trip Disruption Support
Allowlist: `get_itinerary, search_travel_policy, create_escalation_or_support_draft, request_approval` (plus scoped preference tools)
```
1  validate trip_id
2  get_itinerary
3  xác định disruption từ observation (delay/cancel) — không suy đoán nếu field không có
4  search_travel_policy (emergency/disruption guidance) khi cần
5  create_escalation_or_support_draft (tách "Itinerary facts" và "Policy guidance", idempotent)
6  outcome: completed (guidance đủ) | needs_human (policy thiếu / cancelled / cần chi tiền, đổi vé)
```
Rules: không đổi vé, đặt khách sạn, chi tiền hay gửi request. Action-like/cancelled/missing guidance -> `needs_human`.

## C — Post-trip Expense Pre-check
Allowlist: `get_expense_report, calculate_expense_summary, search_travel_policy, create_expense_review_draft`
```
1  validate report_id
2  get_expense_report
3  deterministic validation (receipt thiếu, field thiếu) + calculate_expense_summary (tổng, tỉ lệ, cờ vượt ngưỡng)
4  search_travel_policy theo từng category liên quan
5  create_expense_review_draft (facts + policy evidence + items cần reviewer kiểm tra, idempotent)
6  outcome: completed | needs_input (thiếu chứng từ/field) | needs_human (vượt ngưỡng / policy conflict)
```
Rules: LLM không tự tính; không kết luận "được hoàn tiền"/"đã phê duyệt".

Các workflow A/B/C lưu artifact vào `data/drafts/` bằng `draft_id` ổn định theo `(workflow, source_id)`; retry cập nhật cùng artifact. Draft chỉ là sandbox, `delivery_status` luôn `not_sent` hoặc `not_published`. Workflow không tạo approval request ngầm; Employee chỉ tạo request khi yêu cầu rõ ràng qua `request_approval`.

## Stop conditions chung
- `step_count >= max_steps` -> `failed_budget`.
- Tool lỗi `retryable` -> retry tối đa 2, hết -> `partial` hoặc `failed_validation` theo bước.
- Bước sau fail nhưng draft trước đã tạo -> `partial` (không báo success chung chung).

## Approval request and Admin review
- `request_approval(trip_id, action_type, action_summary)` is Employee-only and trip-owner scoped. Repeated `(trip_id, action_type)` returns the existing request; it never approves, rejects, sends, or publishes.
- Admin workflow exposes only `admin_list_trips` and `admin_get_audit_history`, both read-only. Audit history includes safe workflow outcomes, approval request creation, and external mock decision events with a structured reason.
- Policy search filters each chunk by `allowed_roles` before ranking. Approver needs a pending `approval_scope`; `checklist_review` may search approval/travel/visa/insurance, `escalation` may search travel, and `publish_request` may search approval. Admin cannot search policy.
