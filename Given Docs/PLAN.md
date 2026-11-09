# PLAN — Global Business Travel Operations Agent

## 1. Quyết định thiết kế chính
| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.11 | Dễ làm mock, jsonschema, pytest |
| LLM | Interface 2 backend: `RuleBasedPlanner` (deterministic) + LLM thật tùy chọn | Test/eval chạy lặp lại được, không cần API key |
| Retrieval | BM25 hoặc TF-IDF offline + metadata filter theo category | Rẻ, chạy offline, dễ giải thích |
| Mock data | JSON files | Đơn giản, dễ review, không phải prompt chứa facts |
| Điều phối | Orchestrator = state machine theo phase, mỗi workflow một module | Dễ trace, dễ test transition |
| Draft | Ghi file JSON/MD vào `data/drafts/`, ID ổn định | Idempotent, an toàn |

## 2. Phân công deterministic vs LLM
- Deterministic (chạy được khi bỏ LLM): validate ID, dispatcher, allowlist, schema, tính tổng/tỉ lệ/cờ vượt ngưỡng, approval gate, state transition, idempotent draft, trace.
- LLM-assisted (có fallback template): trích `trip_id/report_id` từ câu tự nhiên, chọn tool đề xuất, viết narrative trong draft, query rewrite, giải thích cho user.

## 3. Lộ trình đầy đủ (10 ngày làm việc)
Kế hoạch mặc định triển khai đủ phạm vi mini-project. Rubric tính một lần theo 7 hạng mục của đề bài, tổng 100%: framing 10%, mock systems/function calling 20%, workflow/state 15%, RAG 15%, memory/safety 15%, automation/drafts 10%, evaluation/debugging 15%.

| Ngày | Việc | Output | Rubric |
|---|---|---|---|
| 1 | Đọc spec, chốt contract, dựng skeleton repo, rà kiến trúc và quyền | skeleton + docs đã chốt | Framing 10% |
| 2 | Dataset (6 trips, 4 travelers, 4 itineraries, 3 expenses, policy corpus) + mock systems | `data/`, `mock_systems/` | Phần đầu của Mock/FC |
| 3 | Tool wrappers + JSON Schemas + registry + dispatcher + error contract | `tools/`, `schemas/` | Mock systems & function calling 20% (ngày 2–3) |
| 4 | State, trace, budget, retry, terminal outcomes | `state.py`, `trace.py` | Nền tảng Workflow/state 15% |
| 5 | Workflow C rồi A, có dependency và stop conditions | 2 workflow end-to-end | Phần Workflow/state |
| 6 | Workflow B + approval simulation + ít nhất 3 loại draft + idempotency | 3 workflow end-to-end, drafts | Automation/drafts 10% |
| 7 | RAG: retriever, citation, claim-evidence check, no-result, injection chunk, version conflict | `rag/` | RAG/grounding 15% |
| 8 | Memory: session, preference view/delete, isolation; hoàn tất role-scope safety | `memory/`, safety cases | Memory/safety 15% |
| 9 | Ít nhất 15 test cases, eval runner, đủ metrics, baseline report, root cause | `eval/reports`, traces | Evaluation/debugging 15% |
| 10 | Sửa theo root cause, after/regression report, README, demo ba workflow, limitations | deliverables hoàn chỉnh | Chốt và kiểm tra toàn rubric |

### Nhánh rút gọn khi thời gian bị giới hạn
Rút ngắn độ polish, không bỏ acceptance floor: cả ba workflow chạy end-to-end; dispatcher/schema/authorization/budget/trace; RAG có citation và no-result; memory/isolation; ít nhất ba draft; 15 test bắt buộc; metrics, baseline/after/regression dạng gọn và demo ngắn. Có thể hoãn backend LLM thật, dữ liệu vượt mức tối thiểu, tối ưu retrieval và artifact tùy chọn. Không hoãn Workflow B, memory/isolation hoặc safety tests.

## 4. Milestone kiểm tra
- M1 (cuối ngày 3): gọi tool qua dispatcher, bị từ chối đúng với tool lạ/field lạ/ID sai.
- M2 (cuối ngày 6): 3 workflow chạy end-to-end với planner rule-based.
- M3 (cuối ngày 8): citation truy vết được, isolation pass.
- M4 (cuối ngày 10): 15/15 test, báo cáo before/after.

## 5. Rủi ro và cách giảm
| Rủi ro | Giảm thiểu |
|---|---|
| LLM output không ổn định | Planner rule-based cho test; LLM chỉ là backend tùy chọn |
| Retrieval đúng score nhưng sai claim | Bước claim-to-evidence check riêng |
| Quá nhiều scope | Làm theo thứ tự ưu tiên ở mục 3 |
| Draft duplicate khi retry | `draft_id = hash(workflow, source_id)` + upsert |
| Lộ PII/secret trong trace | Whitelist field khi ghi trace, test kiểm tra |

## 6. Trả lời nhanh câu tự kiểm tra (cần chốt trước khi nộp)
1. Bỏ LLM: validation, dispatcher, tính toán expense, approval gate, state, draft idempotent vẫn chạy.
2. "Có thể được xem xét" ≠ "đã duyệt": chỉ approval system trả `approved` mới được nói đã duyệt.
3. Itinerary mới từ mock API thắng session summary cũ (source of truth).
4. Tool/field ngoài contract: từ chối trước execution, trả `failed_validation`, ghi trace.
5. Không có evidence: nói rõ không tìm thấy policy liên quan, đề nghị needs_human; không suy đoán, không tạo citation.
6. Trace phải có phase, tool, args an toàn, observation status, transition, budget, outcome để phân biệt lỗi routing / tool / state.

## 7. Decisions Log
| # | Quyết định | Ảnh hưởng |
|---|---|---|
| D1 | `request_approval` chỉ tạo `pending`; `approved/rejected` đến từ fixture approval | Agent không tự duyệt; PDF vẫn đủ 3 trạng thái ở approval system |
| D2 | Schema duy nhất `request_approval(trip_id, action_type, action_summary)`; idempotent theo `(trip_id, action_type)` | Registry, wrapper, test dùng chung (TOOL_CARDS) |
| D3 | Role matrix Employee/Reviewer/Approver + `users.json`; `user_context` do application gắn | Dispatcher có mock authorization rõ ràng (MEMORY_AND_SAFETY) |
| D4 | Thêm ARCHITECTURE.md với sơ đồ tổng thể và 3 workflow dọc (Mermaid) | Đáp ứng deliverable 5 |
| D5 | Citation: `section` là locator chính, `page` nullable; format `[doc_id §section v<version> · chunk_id]` | Khớp PDF, không bịa số trang |
| D6 | Tách `trip_approval_status` và `draft_status`; outcome `awaiting_approval` chỉ khi có approval pending thật | Hết nhập nhằng |
| D7 | `requirements.json` định nghĩa evidence đủ theo destination | `validate_trip_requirements` thật sự deterministic |
| D8 | Version conflict: mặc định `needs_human`; chỉ ưu tiên bản mới khi bản cũ `superseded` | T09 kiểm thử được |
| D9 | Rubric bám đúng 7 trọng số của đề bài; hạng mục mock/function calling chỉ tính một lần | Tổng trọng số luôn 100% |
| D10 | Approver chỉ xem một approval request pending được application đưa vào review scope; không duyệt hoặc ghi dữ liệu qua agent | Least privilege, kiểm thử cả allowed/denied |
