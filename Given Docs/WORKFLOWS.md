# WORKFLOWS

Terminal outcomes: `completed | needs_input | needs_human | awaiting_approval | partial | failed_validation | failed_delivery | failed_budget`.
Draft lifecycle: `draft_created -> awaiting_approval -> approved -> publish_requested -> published` (trong project không có `published` thật). `delivery_status` luôn `not_sent` / `not_published`.

## Định nghĩa trạng thái (tránh nhầm lẫn)
- `trip_approval_status`: trạng thái duyệt chuyến từ approval system (`pending | approved | rejected`).
- `draft_status`: vòng đời artifact (`draft_created -> awaiting_approval -> approved -> publish_requested -> published`).
- Terminal outcome `awaiting_approval` chỉ dùng khi có approval request đang `pending` thật (trip pending hoặc `request_approval` vừa tạo).
- `request_approval` chỉ tạo `pending`; không bao giờ trả `approved`.

## Run state (bắt buộc)
`run_id, workflow, phase, user_id, role, session_id, step_count, max_steps, safe_tool_results, trace[], outcome`

## Retrieval routing
| Nhu cầu | Xử lý |
|---|---|
| Greeting / viết lại text có sẵn | Trả lời trực tiếp |
| Status trip/itinerary/approval | Mock read tool |
| Claim về policy | `search_travel_policy` |
| Thiếu ID | `needs_input` hỏi lại |
| Facts live + policy | Facts trước, retrieval có điều kiện |

## A — Pre-trip Planning and Compliance
Allowlist: `get_trip_request, get_approval_status, search_travel_policy, validate_trip_requirements, create_travel_checklist_draft, request_approval, get_traveler_profile`
```
1  validate trip_id (regex)            -> fail: failed_validation / thiếu: needs_input
2  get_trip_request                    -> not found: failed_validation(unknown_id)
3  get_approval_status
4  search_travel_policy(destination, category)  (<=1 rewrite, top_k<=5)
5  validate_trip_requirements(facts, evidence)  [deterministic theo requirements.json: field đủ? approval? category evidence đủ?]
6  create_travel_checklist_draft(trip_id)       [idempotent]
7  outcome:
   - field thiếu            -> needs_input
   - approval pending       -> awaiting_approval (checklist vẫn draft, không nói "đã duyệt")
   - approval rejected      -> needs_human
   - evidence không đủ      -> needs_human + limitation
   - approved + evidence ok -> completed
```
Rules: chỉ claim policy khi có citation; không nói "đã duyệt" nếu source chưa `approved`.

## B — In-trip Disruption Support
Allowlist: `get_itinerary, search_travel_policy, create_escalation_or_support_draft, request_approval`
```
1  validate trip_id
2  get_itinerary
3  xác định disruption từ observation (delay/cancel) — không suy đoán nếu field không có
4  search_travel_policy (emergency/disruption guidance) khi cần
5  create_escalation_or_support_draft  (tách "Itinerary facts" và "Policy guidance")
6  outcome: completed (guidance đủ) | needs_human (policy thiếu / cancelled / cần chi tiền, đổi vé)
```
Rules: không đổi vé, đặt khách sạn, chi tiền. Action-like -> `request_approval` mock hoặc `needs_human`.

## C — Post-trip Expense Pre-check
Allowlist: `get_expense_report, calculate_expense_summary, search_travel_policy, create_expense_review_draft`
```
1  validate report_id
2  get_expense_report
3  deterministic validation (receipt thiếu, field thiếu) + calculate_expense_summary (tổng, tỉ lệ, cờ vượt ngưỡng)
4  search_travel_policy theo từng category liên quan
5  create_expense_review_draft (facts + policy evidence + items cần reviewer kiểm tra)
6  outcome: completed | needs_input (thiếu chứng từ/field) | needs_human (vượt ngưỡng / policy conflict)
```
Rules: LLM không tự tính; không kết luận "được hoàn tiền"/"đã phê duyệt".

## Stop conditions chung
- `step_count >= max_steps` -> `failed_budget`.
- Tool lỗi `retryable` -> retry tối đa 2, hết -> `partial` hoặc `failed_validation` theo bước.
- Bước sau fail nhưng draft trước đã tạo -> `partial` (không báo success chung chung).
