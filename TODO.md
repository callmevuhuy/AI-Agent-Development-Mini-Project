# TODO — Global Business Travel Operations Agent

**Trạng thái:** các công việc trong phase 6 và hai phần mở rộng Admin/RAG ACL đã hoàn thành cho deterministic mock prototype (2026-11-09). Không còn TODO bắt buộc trong phạm vi hiện tại.

## Đã hoàn thành

- [x] `request_approval`: JSON Schema, registry/allowlist, dispatcher, persistence, chỉ tạo `pending`, idempotent theo `(trip_id, action_type)`, Employee và trip-owner scoped.
- [x] Application entry point, deterministic planner, CLI, chạy được A/B/C và lệnh tạo pending request.
- [x] Test matrix: 43 automated pytest cases; bao gồm workflows, input/error paths, retry/budget, RAG, citation, memory isolation, draft idempotency, approval and role boundaries.
- [x] Evaluation runner: 25 cases; baseline và after đều 25/25. Ghi metrics/case results tại `eval/reports/` và workflow traces tại `eval/traces/`.
- [x] Root-cause notes, regression report, README setup/run/limitations và script demo ba workflows + Admin view.
- [x] Admin mock role `U-ADM-001`: chỉ đọc toàn bộ trip overview và audit history; không có quyền RAG, draft, preference, approval request/decision hay business write.
- [x] Audit events append-only qua tool boundary cho workflow outcomes, request creation và external mock approval decisions; có actor/role/action/IDs/outcome/reason/timestamp/run ID. Không có tool chỉnh sửa/xóa log.
- [x] RAG ACL: `allowed_roles` được áp dụng trước ranking, version conflict và citation. Approver còn cần pending scope và category hợp lệ; Admin mặc định không được tìm policy.
- [x] Đồng bộ PLAN, architecture, workflows, tool cards, data spec, safety matrix, handoff và changelog.

## Đã xác nhận bằng kiểm tra

- `python -m pytest -q`: 43 passed.
- `python eval/run_eval.py --label baseline`: 25/25 passed.
- `python eval/run_eval.py --label after`: 25/25 passed, không có regression trên tập case chung.
- `python -m compileall -q src tests eval` và `git diff --check` thành công.

Baseline là lần đo số liệu đầu tiên sau khi các tính năng đã được triển khai; không có benchmark lịch sử trước thay đổi. Evaluation là deterministic mock suite, không phải benchmark chất lượng LLM quy mô lớn.

## Ngoài phạm vi hiện tại (chỉ cần nếu project mở rộng)

- Semantic entailment/NLI để bổ sung hoặc thay lexical grounding baseline.
- LLM thật, identity provider, storage/audit production và chính sách retention vận hành.
- Real API/booking/payment/email, deployment, background job hoặc dữ liệu nhân viên thật.
