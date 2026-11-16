# Tài liệu Đối chiếu và Dẫn chứng Tuân thủ Đặc tả Yêu cầu
## Project: Global Business Travel Operations Agent
**Đối chiếu chuẩn với:** `Global_Business_Travel_Operations_Agent_Mini_Project.pdf`

---

## Mục 1 & 2: Bối cảnh & Mục tiêu học tập

- **Prototype học tập, có giới hạn quyền hạn:** Agent hoạt động hoàn toàn offline với các mock systems. Mọi thao tác ghi chỉ tạo bản nháp sandbox mang tính idempotent lưu tại [data/drafts/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/drafts). Không có quyền tự trị production.
- **Workflow có evidence và terminal outcomes rõ ràng:** Kết thúc ở các trạng thái quy chuẩn: `completed`, `needs_input`, `needs_human`, `awaiting_approval`, `partial`, `failed_validation`, `failed_delivery`, `failed_budget` được quản lý bởi [RunState](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/state.py#L9-L18).
- **Tách tính toán xác định khỏi LLM:** Mọi tính toán số học, tỉ lệ, ngưỡng chi phí được xử lý xác định 100% trong code [calculate_expense_summary.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/calculate_expense_summary.py).

---

## Mục 3: Phạm vi và ranh giới

| Yêu cầu trong PDF | Dẫn chứng hiện thực trong Code / Dữ liệu |
|---|---|
| **Dữ liệu giả lập 100%** | Toàn bộ dữ liệu nằm trong thư mục [data/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data) (`trips.json`, `travelers.json`, `itineraries.json`, `expenses.json`, `policy_chunks.json`). |
| **Hỗ trợ 3 giai đoạn** | 3 module workflow độc lập tại [src/travel_agent/workflows/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows): [a_pretrip.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows/a_pretrip.py), [b_intrip.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows/b_intrip.py), [c_posttrip.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows/c_posttrip.py). |
| **Chỉ tạo draft sandbox** | [draft_workspace.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/mock_systems/draft_workspace.py) lưu nháp vào `data/drafts/` với `delivery_status` là `"not_sent"` hoặc `"not_published"`. |
| **Quy tắc cốt lõi: Không action thật** | Ranh giới kiểm soát tại [nlu.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/nlu.py#L100-L105) và [conversation.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/conversation.py#L251) tự động chuyển các yêu cầu booking/thanh toán thật sang `HANDOFF_STAFF` kèm ticket mô phỏng `HND-XXXXXXXX`. |

---

## Mục 4: Agent Contract bắt buộc

| Trường contract | Quy định trong PDF | Hiện thực và Dẫn chứng cụ thể |
|---|---|---|
| **User roles** | Employee, Travel Operations Reviewer, Approver (giả lập). | File [data/users.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/users.json): `U-EMP-001`..`004` (Employee), `U-REV-001` (Reviewer), `U-APR-001` (Approver), `U-ADM-001` (Admin). |
| **Goal** | Chuẩn bị, theo dõi và rà soát chuyến công tác quốc tế bằng dữ liệu/policy giả lập. | Hệ thống prompt, NLU router và 3 workflows A, B, C. |
| **Input** | User message; các ID như `trip_id`, `report_id`, `traveler_id`. | Trích xuất chuẩn xác qua Regex trong [nlu.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/nlu.py#L129-L148). |
| **Output** | Grounded response, checklist/draft, workflow status hoặc yêu cầu human review. | Structured outcome và text response có format citation trong [conversation.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/conversation.py#L285-L330). |
| **Allowed tools** | Chỉ tools đăng ký trong registry và allowlist của từng workflow. | [registry.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/registry.py#L69-L74): `WORKFLOW_ALLOWLISTS` giới hạn công cụ riêng biệt cho `pretrip`, `intrip`, `posttrip`, `admin`. |
| **Forbidden actions** | Không booking, payment, refund, external email, arbitrary exec. | Không có tool nào thực hiện network, email hay shell call; chỉ có read tools và draft tools. |
| **Source of truth** | Mock systems; không dùng memory cũ cho trạng thái chuyến đi/duyệt. | [dispatcher.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/dispatcher.py#L104-L116): Mọi fact được refresh trực tiếp từ mock systems, không lấy từ session memory. |
| **Budgets** | Có `max_steps`; retry limit tối thiểu cho transient error. | [config.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/config.py#L27-L28): `DEFAULT_MAX_STEPS = 8`, `MAX_ALLOWED_STEPS = 12`; [orchestrator.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/orchestrator.py#L9): `MAX_TOOL_RETRIES = 2`. |
| **Evidence** | Safe trace, tool observations, metadata, citations, test results. | [state.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/state.py#L42-L56) ghi nhận safe trace cho từng event; kết quả lưu tại [eval/traces/workflow_traces.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/traces/workflow_traces.json). |

---

## Mục 5: Kiến trúc Prototype

Sơ đồ kiến trúc toàn diện và 3 luồng dọc được đặc tả chi tiết tại [Given Docs/ARCHITECTURE.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/ARCHITECTURE.md). Luồng điều phối trung tâm bao gồm:
`User Input` -> `Application Scope Injection` -> `NLU 4-flow router` -> `Orchestrator + State` -> `Dispatcher (Schema, Role, Budget Validation)` -> `Narrow Mock Tools` -> `Idempotent Draft Workspace / Terminal Outcomes`.

---

## Mục 6 & 6.1: Hệ thống Giả lập & Dẫn chứng Dataset Tối thiểu

### Bảng đối chiếu các mock tool tối thiểu (Mục 6)

1. **Travel Request System**: [get_trip_request.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/get_trip_request.py) (`get_trip_request(trip_id)`).
2. **Traveler Profile System**: [get_traveler_profile.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/get_traveler_profile.py) (`get_traveler_profile(traveler_id)`).
3. **Itinerary System**: [get_itinerary.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/get_itinerary.py) (`get_itinerary(trip_id)`).
4. **Approval System**: [get_approval_status.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/get_approval_status.py) (`get_approval_status(trip_id)`) & [request_approval.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/request_approval.py) (`request_approval(trip_id, action_type, action_summary)`).
5. **Policy Knowledge Base**: [search_travel_policy.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/search_travel_policy.py) (`search_travel_policy(query, category, max_results)`).
6. **Expense System**: [get_expense_report.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/get_expense_report.py) (`get_expense_report(report_id)`) & [calculate_expense_summary.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/calculate_expense_summary.py) (`calculate_expense_summary(report_id)`).
7. **Draft Workspace (ít nhất 2 tools)**: Có 3 tools: [create_travel_checklist_draft.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/create_travel_checklist_draft.py), [create_escalation_or_support_draft.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/create_escalation_or_support_draft.py), [create_expense_review_draft.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/create_expense_review_draft.py).

---

### Dẫn chứng chi tiết Dataset tối thiểu (Mục 6.1)

#### 1. Ít nhất 6 Travel Requests tại [data/trips.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/trips.json):
Có đúng **6 bản ghi**:
- `TRIP-2026-001` (Singapore): Case **Pending approval** (`travel_status: "submitted"`, đối chiếu [data/approvals.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/approvals.json) trạng thái `"pending"`).
- `TRIP-2026-002` (Tokyo): Case **Valid / Approved** (`travel_status: "confirmed"`, approval `"approved"`).
- `TRIP-2026-003` (Berlin): Case **Missing field** (thiếu hoàn toàn trường bắt buộc `purpose`, `travel_status: "draft"`).
- `TRIP-2026-004` (London): Case **Rejected approval** (`travel_status: "submitted"`, đối chiếu `approvals.json` trạng thái `"rejected"`).
- `TRIP-2026-005` (Bangkok): Case **Cancelled mock case** (`travel_status: "cancelled"`).
- `TRIP-2026-006` (Sydney): Case **Valid / Happy path** (`travel_status: "confirmed"`, approval `"approved"`).

#### 2. Ít nhất 4 Traveler Profiles tại [data/travelers.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/travelers.json):
Có đúng **4 nhân viên** thuộc **2 phòng ban** khác nhau, không có PII nhạy cảm:
- `EMP-001` (Alex Nguyen) - Department: **Sales**
- `EMP-002` (Jamie Tran) - Department: **Engineering**
- `EMP-003` (Taylor Pham) - Department: **Sales**
- `EMP-004` (Morgan Le) - Department: **Engineering**

#### 3. Ít nhất 4 Itineraries tại [data/itineraries.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/itineraries.json):
Có **5 lịch trình** (vượt yêu cầu 4):
- `TRIP-2026-001`: Flight MOCK-101 (`status: "scheduled"`).
- `TRIP-2026-002`: Case **Flight delay mock** (Flight MOCK-202 `status: "delayed"`, disruption type `"flight_delay"`, `delay_minutes: 240`).
- `TRIP-2026-004`: Flight MOCK-404 (`status: "scheduled"`).
- `TRIP-2026-005`: Case **Flight cancelled mock** (Flight MOCK-505 `status: "cancelled"`, disruption type `"flight_cancelled"`).
- `TRIP-2026-006`: Flight MOCK-606 (`status: "scheduled"`).

#### 4. Ít nhất 3 Expense Reports tại [data/expenses.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/expenses.json):
Có đúng **3 báo cáo chi phí**:
- `EXP-2026-001`: Case **Valid / Happy path** (3 line items có đầy đủ ngày và `receipt_attached: true`).
- `EXP-2026-002`: Case **Thiếu chứng từ & thiếu field** (`ITEM-002-01` có `receipt_attached: false`; `ITEM-002-02` thiếu trường `date`).
- `EXP-2026-003`: Case **Vượt ngưỡng policy / Xung đột phiên bản** (2 line items ăn uống meals tổng cộng \$90.00, vượt định mức \$75.00 của v1.0 và chạm trần \$90.00 của v2.0 đang conflict).

#### 5. Ít nhất 8 Policy Chunks tại [data/policy_chunks.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data/policy_chunks.json):
Có **13 chunks** (vượt yêu cầu 8), phủ đủ 5 categories bắt buộc:
- `travel`: `POL-TRAVEL-PRETRIP-001`, `POL-TRAVEL-DISRUPT-001`.
- `expense`: `POL-EXP-LODGE-001`, `POL-EXP-MEAL-V1`, `POL-EXP-MEAL-V2`, `POL-EXP-TRANS-001`, `POL-EXPENSE-TEST-001`.
- `visa`: `POL-VISA-SG-001`, `POL-VISA-AU-001`.
- `insurance`: `POL-INS-001`, `POL-INS-002`.
- `approval`: `POL-APR-001`, `POL-APR-002`.
- **Đầy đủ 7 trường metadata bắt buộc trên từng chunk:** `chunk_id`, `doc_id`, `source`, `section`, `version`, `category`, `text`.

---

## Mục 7: Function Calling bắt buộc

- **7.1 Quy tắc thực thi:**
  1. Mô hình chỉ đề xuất tool name và arguments, không tự chạy code.
  2. Dispatcher tại [dispatcher.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/dispatcher.py#L149-L178) kiểm định nghiêm ngặt: Registry -> Allowlist -> Draft202012 JSON Schema Validator -> Authorization/Domain Scope -> Step Budget.
  3. Mọi tool implementation đều độc lập, trách nhiệm hẹp và trả structured dict.
  4. Agent chỉ dựa trên `observation` trả về từ tool làm evidence.
  5. Tuyệt đối không dùng `eval`, `globals()`, shell tool hay câu SQL động.
- **7.2 Tool schema:** 100% schema tại [schemas/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/schemas) có `"additionalProperties": false`.
- **7.3 Result contract:** Format chuẩn `{ok: True, data: ..., meta: {source: ..., read_only: ...}}` và `{ok: False, error: {code: ..., message: ..., retryable: ...}}`.

---

## Mục 8: Ba Workflow Nghiệp vụ Bắt buộc

### 8.1 Workflow A — Pre-trip Planning and Compliance ([a_pretrip.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows/a_pretrip.py))
Tuân thủ chuẩn xác 100% chuỗi 6 bước trong PDF:
1. `validate trip_id` (Regex format check).
2. `get_trip_request` (Lấy thông tin chuyến đi).
3. `get_approval_status` (Lấy trạng thái duyệt; nếu `rejected` dừng ngay `needs_human`).
4. `search_travel_policy` (Lấy policy evidence theo destination và category).
5. `validate_trip_requirements` (Kiểm định facts + approval + policy evidence).
6. `create_travel_checklist_draft` (Lưu checklist draft idempotent).
*Terminal outcomes:* `completed`, `needs_input`, `needs_human`, `awaiting_approval`.

### 8.2 Workflow B — In-trip Disruption Support ([b_intrip.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows/b_intrip.py))
1. `validate trip_id`.
2. `get_itinerary` (Đọc chuyến bay và disruption fact).
3. Xác định disruption observation (delay/cancel; không suy đoán).
4. `search_travel_policy` (Lấy hướng dẫn hỗ trợ sự cố).
5. `create_escalation_or_support_draft` (Tách rõ facts và policy guidance).
*Terminal outcomes:* `completed`, `needs_human` (tuyệt đối không tự đổi vé, chi tiền).

### 8.3 Workflow C — Post-trip Expense Pre-check ([c_posttrip.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/workflows/c_posttrip.py))
1. `validate report_id`.
2. `get_expense_report`.
3. `calculate_expense_summary` (Tính toán xác định tổng, tỉ lệ, cờ vượt ngưỡng; LLM không tự tính).
4. `search_travel_policy` cho các category liên quan.
5. `create_expense_review_draft` (Tạo bản nháp rà soát chi phí).
*Terminal outcomes:* `completed`, `needs_input`, `needs_human`.

---

## Mục 9: State và Memory

- **9.1 State bắt buộc ([state.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/state.py)):** Mỗi run lưu đầy đủ: `run_id`, `workflow`, `phase`, `user_context` (scope), `step_count`, `max_steps`, `safe_tool_results`, `trace`, `outcome`.
- **9.2 Memory policy ([store.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/memory/store.py)):**
  - Session state lưu ngữ cảnh gần: `active_trip_id`, `active_report_id` có cơ chế hết hạn TTL.
  - Persistent preference lưu `response_language`, `preferred_output_format` chỉ khi có cờ đồng ý tường minh `memory_write_authorized=True`.
  - Phân tách độc lập `user_id`, `session_id`, `run_id`.
  - Không lưu PII (hộ chiếu, thẻ tín dụng, token...).
  - Cung cấp tool xem và xóa preference: `get_preference`, `delete_preference`.

---

## Mục 10: Agentic RAG và Grounding

- **10.1 Retrieval policy:** Phân định rõ ràng greeting (trả lời trực tiếp), status chuyến đi (gọi mock read API), chính sách (gọi `search_travel_policy`).
- **10.2 Citation & Evidence:**
  - Citation giữ nguyên: `source/doc_id`, `section`, `version`, `chunk_id`.
  - [claim_evidence_check.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/rag/claim_evidence_check.py) đối chiếu từ vựng và cực tính.
  - [query_rewrite.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/rag/query_rewrite.py) thực thi chuẩn hóa truy vấn tối đa 1 lần/branch, không đổi ý nghĩa người dùng và có ghi nhận sự kiện `query_rewrite` vào trace.
  - Loại bỏ các chunk tiêm nhiễm (`POL-EXPENSE-TEST-001`).

---

## Mục 11: Automation, Approval và Delivery Status

- **11.1 Artifact draft:** Cả 3 loại draft (Checklist, Support Note, Expense Review) đều lưu đầy đủ: `draft_id`, `source_id`, `source_ids`, `status`, `draft_status: "draft_created"`, `delivery_status: "not_sent" | "not_published"`.
- **11.2 Approval simulation:** `request_approval` chỉ tạo bản ghi `pending`. Agent tuyệt đối không có quyền tự phê duyệt hoặc từ chối.
- **11.3 Idempotency & Partial failure:** Sử dụng SHA-256 hash của `(workflow, source_id)` làm `draft_id` ổn định; retry tái sử dụng bản ghi, không nhân bản.

---

## Mục 12: Safety Requirements (9 Lớp Kiểm soát An toàn)

| Lớp kiểm soát | Cơ chế hiện thực trong dự án |
|---|---|
| **1. Input validation** | Regex validation cho mọi ID (`^TRIP-\d{4}-\d{3}$`, `^EXP-\d{4}-\d{3}$`), kiểm tra query length <= 240 ký tự. |
| **2. Tool allowlist** | [registry.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/registry.py#L69-L74) chặn mọi tool nằm ngoài allowlist của workflow trước khi chạy. |
| **3. Validation** | Schema validation bằng Draft202012Validator với `additionalProperties: false`. |
| **4. Least privilege** | Tools chỉ có quyền đọc dữ liệu mock hoặc ghi bản nháp sandbox. Tuyệt đối không có lệnh write production. |
| **5. Budgets** | Giới hạn bước gọi tối đa (8 bước), trần cứng 12 bước, tối đa 2 lần retry cho lỗi tạm thời (`retryable: True`). |
| **6. Data boundary** | Phân quyền nghiêm ngặt theo role và user ID; Employee chỉ xem dữ liệu của mình; Approver cần pending approval scope. |
| **7. Approval boundary** | Phê duyệt thực tế chỉ được thực hiện bởi actor ngoài qua helper `record_external_decision`. |
| **8. Prompt injection** | Chặn các mẫu chỉ thị tiêm nhiễm trong câu hỏi người dùng và lọc bỏ chunk policy độc hại. |
| **9. Audit trace** | Ghi nhận safe trace không chứa PII, ghi nhật ký ra file CSV UTF-8 BOM có che số thẻ/token. |

---

## Mục 13: Evaluation & Debugging

- **13.1 Đầy đủ 15 Test Cases bắt buộc (được kiểm thử trong [eval/run_eval.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/run_eval.py)):**
  1. `T01_pretrip_happy`: Pre-trip happy path có policy evidence.
  2. `T02_intrip_delay`: In-trip delay mock case.
  3. `T03_expense_happy`: Expense pre-check happy path.
  4. `T04_missing_id`: Missing trip ID.
  5. `T05_invalid_format`: Invalid trip/report ID format.
  6. `T06_unknown_id`: Unknown trip/report ID.
  7. `T07_pending` & `T07_rejected`: Pending/rejected approval.
  8. `T08_no_evidence`: Policy no-result hoặc evidence thiếu.
  9. `T09_version_conflict`: Policy version conflict mock case.
  10. `T10_retry_limit`: Tool timeout/unavailable có retry limit.
  11. `T11_budget`: Budget exceeded.
  12. `T12_user_injection`: Prompt injection-like request từ user.
  13. `T13_chunk_injection`: Injection-like text trong retrieved policy chunk.
  14. `T14_memory_isolation`: Cross-user memory isolation.
  15. `T15_draft_idempotency`: Retry draft với cùng ID, không tạo duplicate artifact.
- **13.2 Đầy đủ 6 nhóm Metrics:** `task_completion_rate` (1.0), `tool_selection_accuracy` (1.0), `argument_accuracy` (1.0), `grounding_citation_accuracy` (1.0), `safety_test_pass_rate` (1.0), và **Efficiency** (`efficiency_average_steps`: 5.0, `efficiency_average_tool_calls`: 5.0, `efficiency_average_retrieval_calls`: 2.0, `efficiency_total_retries_tested`: 2).
- **13.3 Trace & Phân loại lỗi theo 8 nhóm:** Báo cáo chi tiết ma trận 8 nhóm tại [eval/reports/root_cause.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/reports/root_cause.md).

---

## Mục 14: Danh mục 10 Deliverables Bắt buộc

1. **Source code:** Thư mục [src/travel_agent/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent).
2. **README setup và chạy:** [README.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/README.md).
3. **Mock datasets và policy corpus:** Thư mục [data/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/data).
4. **Agent contract, tool cards, JSON Schemas:** [Given Docs/AGENTS.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/AGENTS.md), [Given Docs/TOOL_CARDS.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/TOOL_CARDS.md), [schemas/](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/schemas).
5. **Sơ đồ kiến trúc & ba workflow theo chiều dọc:** [Given Docs/ARCHITECTURE.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/ARCHITECTURE.md).
6. **Memory policy và mô tả data boundaries:** [Given Docs/MEMORY_AND_SAFETY.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/MEMORY_AND_SAFETY.md).
7. **Test matrix, traces tiêu biểu, metric report và root-cause analysis:** [Given Docs/TEST_MATRIX.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/TEST_MATRIX.md), [eval/traces/workflow_traces.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/traces/workflow_traces.json), [eval/reports/after.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/reports/after.md), [eval/reports/root_cause.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/reports/root_cause.md).
8. **Báo cáo cải tiến baseline/after/regression:** [eval/reports/baseline.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/reports/baseline.md), [eval/reports/after.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/reports/after.md), [eval/reports/regression.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/reports/regression.md).
9. **Demo walkthrough ngắn:** [demo/DEMO_SCENARIOS.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/demo/DEMO_SCENARIOS.md), [demo/run_demo.ps1](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/demo/run_demo.ps1), [demo/web_demo.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/demo/web_demo.py).
10. **Phần nêu rõ giới hạn và safety boundaries:** [README.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/README.md#L117-L122) và [Given Docs/AGENTS.md](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/Given%20Docs/AGENTS.md).

---

## Mục 16: Tiêu chí Nghiệm thu Tối thiểu

1. **Ba workflow chạy được với mock data:** Đã kiểm chứng tự động qua 54 unit tests và 31 evaluation cases.
2. **Agent chỉ tương tác với mock systems qua function calling:** Toàn bộ lệnh gọi đi qua Dispatcher và Tool registry hẹp, không truy cập trực tiếp nguồn nghiệp vụ.
3. **Có ít nhất một safe failure và một needs_human/awaiting_approval:** Test T05 (`failed_validation`), T07 (`awaiting_approval`), T07 (`needs_human`).
4. **Policy claims có citation truy vết đầy đủ:** Giữ đúng `source`, `section`, `version`, `chunk_id`.
5. **Không có booking/payment thật và credential thật:** Được đảm bảo ở tầng ranh giới NLU và hệ thống sandbox.
6. **Kiểm thử đầy đủ input invalid, no-evidence, tool failure, injection, cross-user isolation:** Bao phủ qua các ca T04-T14.
7. **Trace cho phép reviewer xác định Agent đã làm gì, lý do dừng và bằng chứng hỗ trợ:** Thể hiện rõ ràng trong [eval/traces/workflow_traces.json](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/eval/traces/workflow_traces.json).

---

## Mục 17: Giải đáp Chi tiết 6 Câu hỏi Tự kiểm tra Trước khi Nộp bài

### Câu hỏi 1: Nếu bỏ LLM, phần nào của workflow vẫn phải chạy deterministic?
**Trả lời:**
Toàn bộ phần lõi nghiệp vụ vẫn vận hành deterministic 100%, bao gồm:
1. Kiểm định định dạng tham số đầu vào (Regex ID validation).
2. Chuỗi điều phối tool và kiểm tra quyền hạn (Dispatcher allowlist, schema check, role ACL).
3. Tính toán số học, cộng dồn tổng chi phí, tính tỉ lệ và gắn cờ vi phạm định mức ([calculate_expense_summary.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/tools/calculate_expense_summary.py)).
4. Quản lý trạng thái và ngân sách thực thi (`step_count`, `max_steps`, retry limit).
5. Khởi tạo bản nháp sandbox idempotent và chuyển đổi trạng thái kết thúc (Terminal outcomes: `completed`, `needs_input`, `needs_human`, `awaiting_approval`).

### Câu hỏi 2: Nếu policy evidence nói một khoản chi “có thể được xem xét”, Agent có được kết luận “đã được duyệt” không? Vì sao?
**Trả lời:**
Tuyệt đối **KHÔNG**.
*Vì sao:*
- Quy tắc cốt lõi của đề bài (Mục 3) ghi rõ: *"Evidence từ policy không tự cho phép action. Mọi action có tác động chỉ dừng ở draft, needs_human hoặc awaiting_approval"*.
- Cụm từ "có thể được xem xét" thể hiện tính điều kiện hoặc thuộc thẩm quyền đánh giá của con người (human discretion), không phải quyết định phê duyệt đã hoàn tất.
- Quyền phê duyệt chi phí chỉ thuộc về người có thẩm quyền (Approver) ngoài hệ thống. Agent chỉ trích dẫn điều khoản chính sách dưới dạng bằng chứng tham khảo và trả về trạng thái `needs_human` hoặc `awaiting_approval`.

### Câu hỏi 3: Nếu API mock trả itinerary mới khác session summary cũ, source nào được ưu tiên?
**Trả lời:**
Nguồn **API mock (Source of truth)** luôn luôn được ưu tiên tuyệt đối.
*Giải thích:*
Theo Mục 4 và Mục 9.2: *"Travel status, itinerary, approval và expense facts luôn lấy lại từ mock source of truth; không dùng persistent memory cũ thay thế"*. Session state trong bộ nhớ chỉ đóng vai trò ngữ cảnh hội thoại tạm thời (short-term context, ví dụ `active_trip_id`), không được dùng để thay thế trạng thái thực tế từ Mock system.

### Câu hỏi 4: Nếu tool request chứa một tool name hoặc field ngoài contract, dispatcher làm gì?
**Trả lời:**
Dispatcher sẽ lập tức **từ chối thực thi (Reject)** và trả về mã lỗi có cấu trúc:
- Nếu sai hoặc ngoài `tool_name`: Dispatcher trả về `{"ok": false, "error": {"code": "not_allowed", "message": "Tool is not allowed in this workflow.", "retryable": false}}`.
- Nếu chứa trường (field) nằm ngoài contract: Bộ kiểm định JSON Schema với `"additionalProperties": false` sẽ bắt lỗi và Dispatcher trả về `{"ok": false, "error": {"code": "invalid_argument", "message": "Tool arguments do not match the registered schema.", "retryable": false}}`.
Dispatcher tuyệt đối không chạy lệnh `eval()`, không bỏ qua tham số lạ và ghi nhận sự kiện lỗi an toàn vào trace.

### Câu hỏi 5: Nếu retrieval không tìm thấy evidence, Agent cần nói gì và không được nói gì?
**Trả lời:**
- **Agent CẦN nói:** Thông báo trung thực rằng không tìm thấy điều khoản hoặc bằng chứng chính sách phù hợp trong cơ sở tri thức hiện tại để hỗ trợ yêu cầu, và chuyển giao vụ việc cho nhân viên chuyên môn xử lý (`needs_human` hoặc mẫu Staff Handoff Ticket).
- **Agent KHÔNG ĐƯỢC nói:** Tuyệt đối không được bịa đặt điều khoản (hallucination), không được suy đoán chính sách công ty theo kiến thức chung bên ngoài, và không được đưa ra bất kỳ kết luận khẳng định nào về việc được phép hay không được phép nếu thiếu citation xác thực.

### Câu hỏi 6: Trace của nhóm có đủ để phân biệt lỗi routing, tool implementation và state transition không?
**Trả lời:**
Hoàn toàn **ĐỦ** và phân biệt một cách rõ ràng:
- **Lỗi Routing:** Nhận diện khi `action: "run_started"` được ghi nhận nhưng thông điệp bị phân loại sai workflow trong [nlu.py](file:///d:/Local%20Folder/Document/GitHub/AI-Agent-Development-Mini-Project/src/travel_agent/nlu.py) hoặc NLU trả về `REJECT_SAFETY` trước khi bất kỳ `tool_call` nào được đưa vào trace.
- **Lỗi Tool Implementation:** Thể hiện khi sự kiện trong trace có `action: "tool_call"`, `tool: "<tên_tool>"` nhưng `observation_status: "error"` hoặc kết quả trả về mã lỗi (`not_found`, `unavailable`, `invalid_argument`), kèm `transition: "tool_failed"` hoặc `transition: "retry_scheduled"`.
- **Lỗi State Transition:** Thể hiện khi các tool calls đã thành công (`observation_status: "ok"`, `transition: "tool_succeeded"`), nhưng phase tiếp theo hoặc `transition: "terminal"` kết thúc ở outcome không khớp với điều kiện nghiệp vụ (ví dụ: trip bị `cancelled` nhưng lại kết thúc ở phase `pretrip_draft` thay vì dừng sớm ở `pretrip_validation`).
Mỗi sự kiện trong trace đều lưu đầy đủ: `case_id`, `run_id`, `phase`, `action`, `tool`, `safe_args`, `observation_status`, `transition`, `budget: {step, max}`, và `outcome`.
