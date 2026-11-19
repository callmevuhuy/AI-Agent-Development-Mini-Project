# Nhật ký thay đổi

## 2026-11-19 — Hoàn thiện tương thích đa model Gemini, báo cáo số liệu & dọn bàn giao

- **Tương thích đa phiên bản Gemini & xử lý `504` ([config.py](src/travel_agent/config.py), [llm.py](src/travel_agent/llm.py)):** Đặt mặc định `gemini-3.8-flash`, hỗ trợ `gemini-4-hydrogen`, `gemini-3.1-flash-lite`, `gemini-3.5-flash` và auto-discovery qua `client.models.list()`; chuyển sang `client_args={"timeout": ...}` (bỏ `X-Server-Timeout`), đặt `HttpRetryOptions(attempts=1)` và `ThinkingLevel.LOW`/`MINIMAL` kèm auto-fallback.
- **Chuẩn hóa OpenAPI Schema & Web UI Online/Offline ([llm.py](src/travel_agent/llm.py), [web_demo.py](src/travel_agent/web_demo.py), [conversation.py](src/travel_agent/conversation.py)):** Chuyển JSON Schema sang OpenAPI `types.Schema` cho Function Calling & NLU; sửa badge chỉ hiện `Gemini Online` khi thực sự gọi API; thêm `/api/llm/check`, `/api/llm/models` và cảnh báo fallback.
- **Báo cáo & Dọn bàn giao ([Report/report.md](Report/report.md), [.gitignore](.gitignore)):** Viết lại báo cáo với đầy đủ số liệu đo đạc trước/sau; xóa tệp dư `build_presentation.py` và các file tạm/cache runtime trong `data/`; cập nhật `Given Docs/`, `HANDOFF.md`, `TODO.md`, `README.md`.
- **Kiểm chứng:** `191/191 pytest`, `62/62 evaluator`, `pip check`, `compileall`, `git diff --check` và xác minh không có liên kết Markdown gãy.

## 2026-11-19 — Tích hợp Hybrid Gemini API (Phase 1–5) & Pre-Phase 1

- **Pre-Phase 1:** Làm sạch `data/audit_events.json` về 2 bản ghi seed (`EVT-SEED-001`, `EVT-SEED-002`); bổ sung che key Google API (`AIza...`) và token vào `logging_utils.py`; sửa tên `demo/DEMO_WEB.md` và liên kết hỏng trong `README.md`.
- **Phase 1–3 (`src/travel_agent/llm.py`, `config.py`, `conversation.py`):** Thêm `google-genai>=1.0.0`, cấu hình `TRAVEL_AGENT_LLM_BACKEND` (`rule` mặc định | `gemini`), `TurnBudget` cho toàn tin nhắn (`TOTAL_TURN_MAX_STEPS = 32`); Structured Output NLU với round-1 safety guard trước khi gọi API; 1-hop RAG query rewrite; tổng hợp câu trả lời có Post-Generation Guard (`check_generated_response`); và Gemini Function Calling / tool-use loop qua `dispatcher.py` có fallback tự động khi lỗi/timeout/`429`.
- **Phase 4–5 (`tests/test_llm_gemini.py`, `eval/run_eval_llm.py`, `web_demo.py`):** Bổ sung bộ test mock Gemini cho đủ 5 phase, script `eval/run_eval_llm.py` cho tập câu độc lập, và selector chọn backend (`RuleBased` vs `Gemini`) cùng metadata `llm` / `total_step_budget` trong `Memory & Trace` của Web Demo.

## 2026-11-18 — Phản hồi gọn, nhiều yêu cầu và tham chiếu Trip

- Bỏ chèn chi tiết hồ sơ Trip theo preference detailed vào workflow/handoff/clarification; giữ thông tin phục vụ đúng câu hỏi và đọc đầy đủ khi được yêu cầu tường minh.
- Tách tối đa bốn yêu cầu theo dấu phân cách rõ ràng, xử lý tuần tự với quyền/kết quả/trace riêng; không tự mở rộng scope, kiểm tra injection trên cả tin nhắn trước thực thi.
- Thêm thẻ Trip mở bằng hover/focus; endpoint đọc lại nguồn qua dispatcher và kiểm tra quyền hiện tại, chỉ trả trường phù hợp scope. Thẻ Trip không thay thế citation policy.
- Thêm test nhiều yêu cầu, lỗi từng phần, giới hạn batch, dữ kiện gọn, tham chiếu theo role/scope, thu hồi quyền, HTTP và JavaScript rendering.
- Kiểm chứng: 180 test pytest và 62/62 ca evaluator đạt.

## 2026-11-18 — Bổ sung kiểm thử requirement và kịch bản bảo vệ

- Thêm 19 ca kiểm tra sâu về dispatcher, output, lỗi lưu draft, idempotency ba workflow, thiếu policy, nguồn mới và dataset.
- Pending approval chỉ trả checklist preview, không ghi artifact theo mục 11.2. Sửa kỳ vọng chọn tool của thẻ pending từ tạo draft sang validation.
- Thêm kịch bản demo giáo viên gồm 12 bước chính và các ca tùy chọn.
- Kiểm chứng: 169 pytest đạt, 62/62 ca evaluator đạt; kỳ vọng chọn tool đã cập nhật theo approval gate.

## 2026-11-18 — Đồng bộ quyền giữa Trips và chat

- Bỏ tự đổi scope khi bấm dòng Trips; chỉ bật nút trùng cả chuyến và loại yêu cầu với scope đang chọn.
- Không tự chuyển yêu cầu xem chi tiết thành xem hành trình trong scope hỗ trợ. Hai loại dữ kiện được dispatcher kiểm tra riêng.
- Trips gửi tác vụ xác định tới `/api/trip/action`; server đối chiếu dòng với scope và kiểm tra quyền qua cùng bộ điều phối/dispatcher của chat.
- Menu theo quyền: Reviewer không có tạo yêu cầu phê duyệt, Admin chỉ có audit, Employee chỉ thấy chuyến của mình. Bổ sung hồi quy gọi trực tiếp API, lệch scope hai chiều, hai yêu cầu cùng Trip, quyền role và truy cập chéo; không tạo dữ kiện/draft/pending/handoff khi bị từ chối.
- Kiểm chứng: 150 test pytest và 62 ca evaluator đạt; kiểm tra JavaScript gồm scope/nút/menu/payload. Server demo trả HTTP 403 cho yêu cầu Trips lệch scope.

## 2026-11-17 — Phân công Approver và testcase Reviewer

- Thay thẻ hành trình Sydney bằng ca Reviewer yêu cầu tạo pending, phải bị từ chối theo role.
- Bổ sung assigned_approver_id vào hai seed và pending mới; danh sách Trips chỉ trả metadata các yêu cầu pending được phân công. Chọn dòng đặt scope phù hợp cho lần đọc; server xác minh lại, không cấp quyền chỉ từ dropdown.
- Kiểm tra phân công khi đọc facts/policy và trong helper quyết định mô phỏng. Scope hết hiệu lực khi đổi người hoặc resolved; không có dữ liệu hiển thị danh sách rỗng, không handoff.
- Thông báo thiếu quyền tách khỏi giới hạn chức năng. Bổ sung test sai người, giả scope, thiếu phân công, scope cũ, API, danh sách rỗng và frontend chọn dòng.


## 2026-11-17 — Workspace và hồi quy prompt web

- Tách đọc chuyến/hành trình khỏi checklist; làm rõ nhiều lượt giữ ý định/ngôn ngữ; câu hỏi hạn mức trả đủ số và citation.
- Chặn câu injection tiếng Việt ngay đầu; giới hạn chức năng không tự handoff; pending không tạo ticket thừa.
- Trips có menu tác vụ theo role và trạng thái hỗ trợ riêng. Draft có mã độc lập, xem đầy đủ nguồn/trường thiếu, chỉnh đề xuất theo whitelist và kiểm tra lại từ nguồn.
- Cập nhật toàn bộ nhãn thẻ theo phản hồi mong đợi, sửa ID/mô tả sai. Evaluator có thêm 31 ca web; test chỉnh draft kiểm tra quyền và không sửa dữ liệu nguồn.


Lịch sử theo hạng mục. Ngày chỉ ghi khi có bằng chứng; các số test ở từng mốc là lịch sử. Xem báo cáo hiện tại để xác định trạng thái mới nhất.

## 2026-11-17 — Rà soát role, phản hồi và tài liệu tiếng Việt

- Tách lỗi dữ liệu ngoài scope dùng câu chung khỏi lỗi thao tác có mô tả riêng theo role; giữ code và không lộ người sở hữu hồ sơ.
- Sửa danh sách Employee thành lookup theo chủ, preferences Approver đi đúng memory, nhận diện yêu cầu pending tường minh, phân biệt với quyết định phê duyệt và câu hỏi policy.
- Chặn ID sai trước nhánh Admin/Approver; Approver hỏi itinerary phải qua đúng tool thay vì nhận trip facts thay thế. Thiếu policy/xung đột của Approver cần người xem xét.
- Giữ đúng lý do nghiệp vụ khi lỗi tra cứu phụ đã được xử lý; bỏ câu nhắc thừa về hành động chưa làm trong phản hồi.
- Bổ sung ma trận happy case, thiếu dữ liệu, ngoài scope và lỗi thao tác cho bốn Employee, Reviewer, Approver, Admin; đối chiếu các test cũ và thay kỳ vọng câu chữ đã được chủ dự án yêu cầu đổi.
- Chuyển tài liệu Markdown sang tiếng Việt, giữ định danh và lệnh; sửa bộ sinh báo cáo để các lần đánh giá sau cũng tạo tiếng Việt.
- Xác minh: 96 test pytest đạt, 31/31 ca evaluation đạt; không hồi quy trên tập ca cũ. Kiểm tra biên dịch và liên kết nội bộ của 19 tài liệu Markdown đạt.

## 2026-11-17 — Việt hóa lỗi và thống nhất dữ liệu web

- Giữ error.message từ tool lên workflow/chat/trace. API và frontend hiển thị lỗi tiếng Việt cùng mã tra cứu.
- Các tab lọc dữ liệu theo role/chủ hồ sơ; xóa nội dung và bỏ phản hồi cũ khi đổi tài khoản.
- Dùng nhãn Anh–Việt dễ hiểu cho Chat, Trips, Drafts, Handoff, Audit log, Memory & Trace; bỏ số bước/token mô phỏng gây hiểu nhầm.
- Trước đợt rà soát tiếp theo có 69 test, trong đó 68 đã chạy trong sandbox và một HTTP test từng cần quyền kết nối localhost. Môi trường `.venv` sau đó được cài từ requirements và demo bật tại port 8080.

## 2026-11-16 — Đồng bộ tài liệu và cài đặt

- Bổ sung `jsonschema>=4.23`, `pytest>=8.0`, `-e .` vào requirements để cài một bước.
- Viết lại README theo giọng kỹ thuật; đồng bộ Given Docs với 19 tool, bốn tuyến, TTL, CSV và chức năng Admin trên web.
- Dữ liệu audit được đưa về seed sạch trước lần commit của mốc này.

## 2026-11-16 — Chi tiết nhân viên và thông tin thiếu

- Thêm `get_traveler_profile` vào allowlist in-trip/post-trip. Bổ sung dữ kiện nhân viên trong phản hồi được cấp quyền, danh sách Reviewer và tóm tắt handoff; giữ giới hạn hồ sơ của Approver/Admin.
- Bổ sung `_format_clarify_workflow`, trả validation/report khi thiếu dữ liệu để chỉ rõ trạng thái checklist, nguồn duyệt, cấu hình policy và trường/chứng từ cần bổ sung.
- Mở rộng test hội thoại để kiểm tra hai nhóm sửa này.

## 2026-11-16 — Kiểm tra ngày bay và ngày khởi hành

- Phát hiện lookup Tokyo ngày 9/12 khớp sai vì chỉ dựa khoảng 8–12/12 của chuyến, trong khi MOCK-202 bay ngày 8/12.
- In-trip đối chiếu departure/arrival bằng get_itinerary; pre-trip đối chiếu start_date. Sai ngày trả CLARIFY với lịch nguồn.
- NLU đọc thêm YYYY/MM/DD và DD Month; bổ sung test hồi quy.

## 2026-11-16 — Giai đoạn 5: lookup tự nhiên và trình diễn role

- Thêm list_my_trips/list_my_expenses, schema, registry và trace; Employee xem của mình, Reviewer xem toàn bộ.
- Lookup theo điểm đến/ngày, hỗ trợ ngày tương đối qua config, hỏi lại khi nhiều hoặc không có kết quả.
- Cải thiện xuống dòng, nguồn/citation, tuyến bay, giờ và trạng thái. Web thêm Approver scope, gợi ý theo role, xóa chat khi đổi user, kiểm tra Admin cho CSV/reset.
- Thêm kịch bản demo, cập nhật PowerShell và README. Mốc này có 53 pytest case; mở rộng evaluator. Không commit/push trong phiên triển khai đó.

## 2026-11-16 — Giai đoạn 4: web demo và kiểm thử

- Thêm HTTP server thư viện chuẩn, giao diện chat/chọn role/memory/trace/handoff/CSV và CLI web.
- Demo trình diễn ba workflow và hàng đợi; thêm 8 test tổng hợp cho các giai đoạn 1–4.
- Evaluator tăng từ 25 lên 29 ca; after 29/29, không hồi quy. Pytest đạt 51; compileall và kiểm tra diff đạt.
- Đồng bộ README, HANDOFF, TODO, .gitignore và Given Docs. Không commit/push trong phiên đó.

## 2026-11-16 — Giai đoạn 3: memory và hội thoại

- Session bổ sung active_report_id, pending_slot, xóa khóa và TTL; tự tách thư mục khi test.
- CSV chat/handoff UTF-8 BOM, che mẫu token/số thẻ; audit không chứa raw message.
- conversation.py điều phối bốn tuyến, ngữ cảnh nhiều lượt, preference định dạng, quản lý tùy chọn và mẫu handoff xác định.
- CLI thêm chat, handoffs, logs và cập nhật message. Pytest đạt 43; không commit/push trong phiên đó.

## 2026-11-16 — Giai đoạn 2: NLU và RAG ngoại tuyến

- NLU chuẩn hóa NFKC, đọc ID chuẩn/sai, preferences, tách mệnh đề, nhận diện injection và bốn tuyến; planner dùng chung NLU.
- BM25 có rút gọn từ tiếng Anh, từ đồng nghĩa chuyên ngành và mở rộng mẫu loại injection. Pytest đạt 43; không commit/push trong phiên đó.

## 2026-11-16 — Giai đoạn 1: sửa lõi và cấu hình

- config.py tập trung đường dẫn, budget, TTL và biến môi trường.
- Sửa meals nằm trong mọi bản active không bị đánh cờ; chặn rejected/cancelled trước điểm đến chưa cấu hình; tăng trần budget lên 12, mặc định 8.
- Kiểm tra nguồn trước draft, bắt buộc trip_id trong trip_facts, lọc args trace, khóa quyết định mock, bỏ import thừa và tài khoản Admin trùng trong tài liệu.
- Pytest đạt 43; không commit/push trong phiên đó.

## 2026-11-09 — Hoàn thành mốc 6 và công việc còn lại

- Thêm điểm vào application/planner/CLI cho ba workflow, pending request và chức năng đọc Admin.
- Đăng ký request_approval theo sở hữu, helper quyết định ngoài tool set và audit sự kiện có lý do/người thực hiện.
- Thêm tool Admin, ACL theo chunk và lọc trước retrieval; mở rộng dữ liệu tổng hợp, sửa conflict không liên quan chặn báo cáo.
- Pytest 43 ca đạt; evaluator 25/25; lưu trace/chỉ số và kiểm tra compile/diff. Không commit/push trong phiên đó.

## 2026-11-09 — Rà soát phạm vi và danh sách công việc

- Tạo TODO và đối chiếu đề bài, tài liệu, mã, dữ liệu, test. Xác nhận 6 chuyến, 4 nhân viên, 5 itinerary, 3 báo cáo và 13 chunk.
- Tại thời điểm rà soát ban đầu, request_approval chưa đăng ký, chưa có application/planner/evaluator/demo; 19 test chỉ tập trung RAG/memory/Approver. Đây là trạng thái lịch sử trước các mốc triển khai tiếp theo.
- Không thay hành vi mã nguồn, không commit/push trong phiên đó.

## 2026-11-09 — Mục 3: bản nháp và quy trình

- Thêm HANDOFF, workspace draft ghi JSON nguyên tử, ID SHA-256 theo workflow/nguồn.
- Đăng ký ba tool draft và kiểm tra quyền Employee; nối ba workflow với draft, dùng nguồn approval trong ngân sách lúc đó.
- Bổ sung hoãn/hủy/thiếu chi tiết/không có sự cố. Kiểm tra bằng assert, compile và diff; chưa chạy pytest/evaluator ở mốc này.

## 2026-11-09 — Mục 4 và 5: RAG, memory, Approver

- Thay trùng token bằng BM25 ngoại tuyến; citation giữ doc/section/version/chunk/page.
- Kết quả rỗng rõ ràng, loại chunk chỉ thị, grounding theo câu/phủ định, kiểm tra xung đột và supersession.
- Nối evidence vào in-trip, thông tin phiên bản vào checklist/expense draft; thêm memory theo scope, giá trị cho phép, đồng ý ghi/xóa và chống chọn user/session qua args.
- Thêm approval_requests fixture; mỗi lượt đọc Approver kiểm tra pending scope và tool theo action.
- Có 19 test chuyên biệt đạt, compile/diff đạt; đánh giá toàn dự án và demo còn ở mốc 6 khi đó.

## Các mốc sớm hơn — không còn ngày xác nhận

- Tạo dữ liệu chuyến/nhân viên/hành trình/approval/expense/policy giả lập từ Hà Nội.
- Tool JSON Schema, registry, allowlist, dispatcher, quyền, lỗi cấu trúc và budget.
- Run state, trace an toàn, retry và kết quả cuối.
- Bản xem trước checklist/chi phí chưa lưu draft; workflow in-trip chưa triển khai tại thời điểm đó. Chỉ có kiểm tra nhanh, chưa có bộ pytest/evaluator.
