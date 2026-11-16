# TODO — Global Business Travel Operations Agent

**Trạng thái:** Các công việc cốt lõi và gói nâng cấp bàn giao (English NLU, 4-flow routing, Strict Staff Handoff, Short/Long-term Memory integration, UTF-8 CSV logger, Zero-dependency Web Demo, và vá các bug logic/budget nền) đã hoàn thành (2026-11-16). Không còn TODO bắt buộc trong phạm vi hiện tại.

## Đã hoàn thành

- [x] `request_approval`: JSON Schema, registry/allowlist, dispatcher, persistence, chỉ tạo `pending`, idempotent theo `(trip_id, action_type)`, Employee và trip-owner scoped.
- [x] Application entry point, English NLU router (`nlu.py`), 4-flow conversational orchestrator (`conversation.py`: `SELF_SERVE`, `CLARIFY`, `HANDOFF_STAFF`, `REJECT_SAFETY`), CLI (`message`, `chat`, `handoffs`, `logs`, `web`), và zero-dependency Web Demo (`demo/web_demo.py`).
- [x] Memory integration: nối short-term session (`active_trip_id`, `active_report_id`, `pending_slot`, TTL) và long-term preference formatting (`preferred_output_format`) vào luồng chat.
- [x] UTF-8 BOM CSV Logger (`logging_utils.py`): ghi `data/logs/chat_history.csv` và `data/logs/handoff_queue.csv` (có che token/số thẻ nhạy cảm), giữ `audit_events.json` sạch raw message.
- [x] Test matrix: 53 automated pytest cases; bao gồm workflows, bug fixes (`meals` threshold, `rejected` blocking priority, draft source check), natural-language lookup without raw IDs, mixed NLU, synonym RAG, memory isolation + TTL, strict handoff, role-distinct capabilities, UTF-8 CSV logging, và Web Demo HTTP + Admin reset/export guards.
- [x] Evaluation runner: 31 cases; `after` đạt 31/31, không có regression. Ghi metrics/case results tại `eval/reports/` và workflow traces tại `eval/traces/`.
- [x] Root-cause notes, regression report, README setup/run/limitations và script demo ba workflows + Admin view.
- [x] Admin mock role `U-ADM-001`: chỉ đọc toàn bộ trip overview và audit history; không có quyền RAG, draft, preference, approval request/decision hay business write.
- [x] Audit events append-only qua tool boundary cho workflow outcomes, request creation và external mock approval decisions; có actor/role/action/IDs/outcome/reason/timestamp/run ID. Không có tool chỉnh sửa/xóa log.
- [x] RAG ACL: `allowed_roles` được áp dụng trước ranking, version conflict và citation. Approver còn cần pending scope và category hợp lệ; Admin mặc định không được tìm policy.
- [x] Đồng bộ PLAN, architecture, workflows, tool cards, data spec, safety matrix, handoff và changelog.

## Đã xác nhận bằng kiểm tra

- `python -m pytest -v`: 53 passed.
- `python eval/run_eval.py --label after`: 31/31 passed, không có regression trên tập case chung.
- `python -m compileall -q src tests eval demo` và `git diff --check` thành công.

Baseline là lần đo số liệu đầu tiên sau khi các tính năng đã được triển khai; không có benchmark lịch sử trước thay đổi. Evaluation là deterministic mock suite, không phải benchmark chất lượng LLM quy mô lớn.

## Ngoài phạm vi hiện tại (chỉ cần nếu project mở rộng)

- Semantic entailment/NLI để bổ sung hoặc thay lexical grounding baseline.
- LLM thật, identity provider, storage/audit production và chính sách retention vận hành.
- Real API/booking/payment/email, deployment, background job hoặc dữ liệu nhân viên thật.
