# Đối chiếu yêu cầu và bằng chứng triển khai

Dự án: Global Business Travel Operations Agent. Đối chiếu với [đề bài PDF](Requirement%20Docs/Global_Business_Travel_Operations_Agent_Mini_Project.pdf). Các đường dẫn dưới đây trỏ tới repository hiện tại; số test lịch sử không được coi là kết quả xác minh mới nhất.

## Mục 1 và 2: bối cảnh, mục tiêu học tập

Nguyên mẫu hỗ trợ nhân viên và Travel Operations trước, trong và sau công tác. Mục tiêu là chứng minh workflow, evidence, giới hạn quyền và khả năng đánh giá; không phải agent tự trị production.

Trạng thái và trace nằm ở [state.py](src/travel_agent/state.py), [trace.py](src/travel_agent/trace.py). Tính toán nằm ở [calculate_expense_summary.py](src/travel_agent/tools/calculate_expense_summary.py). Bản nháp được lưu qua [draft_workspace.py](src/travel_agent/mock_systems/draft_workspace.py).

## Mục 3: phạm vi

| Yêu cầu | Bằng chứng |
|---|---|
| Dữ liệu giả lập | [data/](data/): chuyến, nhân viên, hành trình, phê duyệt, chi phí, policy |
| Ba giai đoạn | [workflows/](src/travel_agent/workflows/): a_pretrip, b_intrip, c_posttrip |
| Bản nháp có ID và nguồn | JSON tại data/drafts, draft_id ổn định, delivery_status trung thực |
| Policy không cấp quyền hành động | Dispatcher kiểm tra role/scope độc lập; yêu cầu tác động ngoài khả năng cần người xử lý |
| Ngoài phạm vi | Giao dịch thật, visa/bảo hiểm thật, email, credential, API bên ngoài, lịch nền và production |

## Mục 4: hợp đồng agent

| Thành phần | Hiện thực |
|---|---|
| Người dùng | Employee, Reviewer, Approver; thêm Admin giả lập trong users.json |
| Mục tiêu | Chuẩn bị, theo dõi và rà soát chuyến bằng dữ liệu/chính sách giả lập |
| Đầu vào | Tin nhắn và ID trip/report/traveler; [nlu.py](src/travel_agent/nlu.py) nhận diện theo mẫu |
| Đầu ra | Facts có nguồn, citation, draft, trạng thái hoặc yêu cầu bổ sung/người xem xét |
| Công cụ được phép | 19 tool đăng ký và allowlist workflow trong [registry.py](src/travel_agent/registry.py) |
| Nguồn sự thật | Mock systems, đọc lại qua tool; memory chỉ giữ ngữ cảnh/tùy chọn |
| Ngân sách | 8 bước mặc định một state, trần 12, chat pre-trip/mixed dùng 10; retry tối đa 2 |
| Bằng chứng | Safe trace, observations, metadata, citations, pytest và evaluator |

Các kết quả cuối: `completed`, `needs_input`, `needs_human`, `awaiting_approval`, `partial`, `failed_validation`, `failed_delivery`, `failed_budget`. `unauthorized_scope` là mã lỗi, không phải một terminal outcome riêng.

## Mục 5: kiến trúc

Xem [kiến trúc tổng thể và ba sơ đồ quy trình](Given%20Docs/ARCHITECTURE.md). Application cấp context; planner chỉ đề xuất; dispatcher kiểm tra; tool gọi mock systems; orchestrator quản lý bước/retry/trace; conversation định dạng phản hồi. API web có kiểm tra quyền tại server.

## Mục 6: dữ liệu và hệ thống giả lập

| Nhóm | Số lượng và tình huống |
|---|---|
| Chuyến đi | 6: 001 pending, 002 hợp lệ, 003 thiếu purpose, 004 rejected, 005 cancelled, 006 hợp lệ/visa |
| Nhân viên | 4: Alex/Taylor thuộc Sales; Jamie/Morgan thuộc Engineering; tên hoàn toàn giả lập |
| Hành trình | 5: 001, 002, 004, 005, 006; 002 hoãn 240 phút, 005 hủy chuyến |
| Báo cáo chi phí | 3: 001 hợp lệ; 002 thiếu chứng từ/trường; 003 có meals cần xem xét conflict |
| Policy chunk | 13 thuộc travel, expense, visa, insurance, approval; có conflict và injection giả |

[DATA_SPEC.md](Given%20Docs/DATA_SPEC.md) ghi rõ ID, chủ hồ sơ và trường dữ liệu. Báo cáo EXP-2026-003 có meals tổng 90 USD; hạn mức active trong fixture là 70 USD và 85 USD, không phải 75/90 như mô tả cũ. Mỗi chunk có đủ chunk/doc/source/section/version/category/text; page chỉ dùng khi nguồn có.

## Mục 7: function calling

1. Model đề xuất tên và arguments, không tự chạy code.
2. [Dispatcher](src/travel_agent/dispatcher.py) kiểm tra registry, allowlist, schema/định dạng, quyền và budget trước handler.
3. Wrapper có trách nhiệm hẹp, trả kết quả có cấu trúc.
4. Facts trong phản hồi dựa trên observation từ tool.
5. Không dùng eval, tên hàm tùy ý, shell hoặc SQL do model tạo.

Schema trong [schemas/](src/travel_agent/schemas/) dùng `additionalProperties:false`. Thành công có ok/data/meta; lỗi có code/message/retryable. Output check xác nhận cấu trúc cơ bản, không thay thế kiểm tra đúng nghiệp vụ hoặc grounding.

## Mục 8: ba quy trình bắt buộc

| Quy trình | Chuỗi triển khai và kết quả |
|---|---|
| A — trước chuyến | Kiểm tra ID → get_trip_request → get_approval_status → search_travel_policy → validate_trip_requirements → create_travel_checklist_draft; completed/needs_input/needs_human/awaiting_approval |
| B — trong chuyến | Kiểm tra ID → get_itinerary → xác định sự cố → search_travel_policy → create_escalation_or_support_draft; completed hoặc needs_human |
| C — sau chuyến | Kiểm tra ID → get_expense_report → calculate_expense_summary → search_travel_policy → create_expense_review_draft; completed/needs_input/needs_human |

Nguồn: [A](src/travel_agent/workflows/a_pretrip.py), [B](src/travel_agent/workflows/b_intrip.py), [C](src/travel_agent/workflows/c_posttrip.py). Thiếu trường, quyền hoặc tool lỗi có thể dừng sớm; không khẳng định mọi lượt luôn chạy đủ chuỗi.

## Mục 9: trạng thái và memory

[RunState](src/travel_agent/state.py) giữ ID lượt, workflow/phase, context, số bước, budget, kết quả tool an toàn, trace và outcome.

[Memory store](src/travel_agent/memory/store.py) tách session theo user/phiên và preferences theo user. Session chỉ có các khóa được cấp, gồm ngữ cảnh tác vụ đang làm rõ và ngôn ngữ phiên và TTL 30 phút; hết hạn được xử lý khi đọc. Preferences chỉ gồm ngôn ngữ và định dạng; ghi/xóa cần đồng ý rõ ràng. Có công cụ xem/xóa. Không nhận khóa lưu dữ liệu nhạy cảm hoặc nguyên văn hội thoại.

CSV hội thoại là log riêng có lọc mẫu token/số thẻ; không được mô tả toàn hệ thống là không lưu nội dung chat. Bộ lọc chưa bao phủ mọi PII.

## Mục 10: RAG và kiểm tra căn cứ

Lời chào không truy xuất; facts nghiệp vụ lấy mock tool; claim policy dùng search_travel_policy. ACL lọc trước BM25 và citation. Mỗi citation giữ nguồn/mục/phiên bản/chunk, page khi có dữ liệu.

[claim_evidence_check.py](src/travel_agent/rag/claim_evidence_check.py) kiểm tra từ khóa trong cùng câu và cùng phủ định; [query_rewrite.py](src/travel_agent/rag/query_rewrite.py) giới hạn một rewrite mỗi nhánh có trace. Chunk injection bị loại. Điểm BM25 không bảo đảm căn cứ đủ; chưa có kiểm tra suy luận ngữ nghĩa tổng quát.

## Mục 11: bản nháp, approval và lỗi một phần

Ba draft gồm checklist, hỗ trợ sự cố và rà soát chi phí. Mỗi bản có draft_id/source/status/delivery_status; ID băm từ workflow/nguồn giúp retry không tạo trùng. Chỉ xác nhận đã lưu khi tool trả thành công.

request_approval chỉ tạo pending theo chủ sở hữu. Chat hỗ trợ yêu cầu tường minh, không nhầm câu hỏi policy với tạo request. Quyết định approve/reject thuộc hệ thống mô phỏng bên ngoài. Lỗi bước sau trả outcome không hoàn tất, giữ nguyên lỗi thay vì báo thành công chung.

## Mục 12: chín lớp bảo vệ

| Lớp | Cơ chế |
|---|---|
| Đầu vào | Regex ID, trường bắt buộc; policy query 3–200 ký tự; action_summary 5–240 ký tự |
| Allowlist | Danh sách tool riêng từng workflow |
| Validation | JSON Schema chặn trường thừa và sai kiểu; kiểm tra kết quả cơ bản |
| Quyền tối thiểu | Read/draft/pending trong mock; không có tool thực thi tùy ý |
| Budget | Giới hạn bước từng state và retry có điều kiện; lookup phụ có state riêng |
| Ranh giới dữ liệu | Role, chủ sở hữu, user/session, scope pending |
| Approval | Agent không có tool ra quyết định |
| Injection | Phát hiện mẫu đầu vào và loại chunk không đáng tin khỏi evidence |
| Audit | Trace an toàn, audit kỹ thuật và CSV vận hành tách biệt |

Lỗi dữ liệu ngoài scope dùng câu chung, không lộ chủ hồ sơ. Lỗi thao tác của role nêu đúng chức năng bị hạn chế và người hỗ trợ. Bỏ câu nhắc việc chưa làm khỏi phản hồi không làm thay đổi các lớp bảo vệ.

## Mục 13: kiểm thử, đánh giá và phân tích lỗi

Nhóm ca T01–T15 trong [ma trận kiểm thử](Given%20Docs/TEST_MATRIX.md) bao phủ ba happy case; thiếu/sai/không có ID; pending/rejected; thiếu evidence; conflict; retry; budget; injection từ user/chunk; memory isolation; draft không trùng. Các test bổ sung kiểm tra role/scope, schema, citation, lookup, CSV, HTTP và UI reset/export.

Đợt rà soát 2026-11-17 thêm ma trận bốn Employee và ba role còn lại, thông báo scope chung/thao tác riêng, pending tường minh qua chat, preferences Approver, ID sai trước nhánh role và itinerary không được thay thế bằng trip facts. Xem kết quả chạy pytest thực tế; không giữ các số 53/54 cũ như kết quả hiện tại.

Đợt sửa 2026-11-18 đối chiếu thêm đường vào Trips với chat: giữ scope người dùng đã chọn, khóa dòng không trùng cả chuyến và loại yêu cầu, kiểm tra lại tại server, không đổi loại dữ kiện để hợp thức hóa quyền. `tests/test_trip_action_permissions.py` kiểm tra hai chiều lệch scope, hai yêu cầu cùng Trip, role/ownership, gọi API trực tiếp và JavaScript của nút/menu/payload (`trip_actions_ui_smoke.cjs`, cần Node.js; thiếu Node thì riêng ca này được bỏ qua). Lần xác minh có Node.js: **150/150 pytest**, **62/62 evaluator** đạt. Các ca mới kiểm tra cùng nguyên tắc quyền tối thiểu ở mục 12; không mở rộng quyền Approver.

Evaluator có 62 ca (31 nền và 31 prompt web), ghi các chỉ số hoàn thành, lựa chọn tool/arguments, căn cứ/citation, safety và hiệu quả. Báo cáo mới nhất: [after.md](eval/reports/after.md), [regression.md](eval/reports/regression.md). Giá trị 1.0 trên dữ liệu nhỏ không chứng minh chất lượng suy luận tổng quát. Phân loại tám nhóm lỗi ở [root_cause.md](eval/reports/root_cause.md).

## Mục 14: mười sản phẩm bàn giao

1. [Mã nguồn](src/travel_agent/).
2. [Cài đặt và chạy](README.md).
3. [Dữ liệu và kho policy](data/).
4. [Hợp đồng agent](Given%20Docs/AGENTS.md), [tool](Given%20Docs/TOOL_CARDS.md), [schema](src/travel_agent/schemas/).
5. [Kiến trúc và ba sơ đồ](Given%20Docs/ARCHITECTURE.md).
6. [Memory và an toàn](Given%20Docs/MEMORY_AND_SAFETY.md).
7. [Ma trận test](Given%20Docs/TEST_MATRIX.md), [trace mẫu](eval/traces/workflow_traces.json), [nguyên nhân gốc](eval/reports/root_cause.md).
8. [Baseline](eval/reports/baseline.md), [sau sửa](eval/reports/after.md), [hồi quy](eval/reports/regression.md).
9. [Kịch bản demo](demo/DEMO_SCENARIOS.md), [script](demo/run_demo.ps1), [điểm vào web](demo/web_demo.py).
10. [Giới hạn](README.md#giới-hạn-hiện-tại) và hợp đồng an toàn.

## Mục 15: đối chiếu trọng số

| Hạng mục | Trọng số | Bằng chứng chính |
|---|---|---|
| Bài toán và kiến trúc | 10% | README, ARCHITECTURE |
| Mock và function calling | 20% | data, tool, schema, dispatcher |
| Workflow và state | 15% | Ba workflow, RunState, retry/budget |
| RAG và grounding | 15% | rag, metadata/citation và test |
| Memory/an toàn/approval | 15% | store, role/scope, ACL và test |
| Tự động hóa/bản nháp | 10% | Ba draft, nguồn và ID ổn định |
| Đánh giá/gỡ lỗi | 15% | pytest, evaluator, report, root cause |

Đây là ánh xạ bằng chứng, không tự chấm điểm hay khẳng định đạt mọi tiêu chí production.

## Mục 16: điều kiện nghiệm thu tối thiểu

Ba workflow chạy trên mock qua function calling; có từ chối an toàn và trường hợp needs_human/awaiting_approval; claim có citation truy vết; không dùng giao dịch/credential thật; test có invalid input, thiếu evidence, tool failure, injection, cách ly; trace cho biết hành động, lý do dừng và căn cứ. Kiểm tra các điều kiện bằng mã/test, không chỉ bằng văn bản mô tả.

## Mục 17: giải đáp sáu câu tự kiểm tra

### 1. Bỏ LLM thì phần nào vẫn chạy xác định?

ID/schema, dispatcher, role/scope, tính tổng/ngưỡng chi phí, approval gate, state, budget/retry, ID draft và trace. Các phần này phải do code kiểm soát; planner hiện cũng dùng quy tắc nên test không cần API key.

### 2. Policy nói có thể được xem xét thì agent có được nói đã duyệt?

Không. Policy là điều kiện tham khảo, không phải quyết định. Chỉ nguồn approval xác nhận mới được nêu trạng thái approved. Agent nêu evidence và chuyển người có quyền xử lý.

### 3. Itinerary từ mock mới khác ngữ cảnh cũ thì ưu tiên gì?

Ưu tiên observation mới từ mock tool. Session chỉ giúp xác định đang nói đến chuyến nào, không chứng minh trạng thái chuyến bay hiện tại.

### 4. Tool hoặc field ngoài hợp đồng bị xử lý thế nào?

Tool chưa đăng ký/ngoài allowlist trả not_allowed; args sai hoặc thừa trường trả invalid_argument. Handler không chạy; orchestrator ghi trace lần thử. Không dùng eval hoặc bỏ qua tham số lạ.

### 5. Không tìm thấy evidence thì nói gì?

Nêu chưa tìm thấy căn cứ phù hợp và cần Travel Operations/Reviewer kiểm tra; trả needs_human khi phù hợp. Không tự điền policy, không khẳng định được duyệt/hoàn tiền và không tạo citation giả.

### 6. Trace đủ phân biệt lỗi ở đâu?

Đối chiếu phase, action/tool, safe_args, observation_status, transition, budget, outcome và lỗi an toàn để phân biệt định tuyến, tham số, triển khai tool, observation, state, retry, grounding và quyền. Nếu lỗi do bước phụ đã được workflow xử lý, không suy nó thành nguyên nhân cuối của lượt.
