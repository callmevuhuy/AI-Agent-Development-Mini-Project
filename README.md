# Trợ lý điều hành công tác doanh nghiệp

Kịch bản trình bày ba workflow và quyền các role: [Demo cho giáo viên](demo/DEMO_GIAO_VIEN.md).

Chat hỗ trợ tối đa bốn yêu cầu trong một tin nhắn, tách bằng dấu chấm phẩy, xuống dòng hoặc liên từ trước một yêu cầu tường minh. Giao diện hiện từng kết quả riêng, giữ lỗi/quyền/outcome của từng phần; đây là các thao tác tuần tự, không phải giao dịch nguyên tử. Injection được kiểm tra trên cả tin nhắn trước khi thực hiện. Mỗi phần giữ budget/retry của lượt riêng.

Phản hồi workflow/handoff không tự đính kèm toàn bộ chi tiết Trip kể cả khi chọn định dạng chi tiết. Thẻ Trip dưới phản hồi mở bằng rê chuột hoặc focus bàn phím, gọi `/api/trip/reference` để kiểm tra lại quyền và đọc nguồn hiện tại. Scope hỗ trợ của Approver chỉ hiện dữ kiện hành trình, không mở hồ sơ chuyến. Citation policy vẫn độc lập với tham chiếu Trip. Muốn đọc đầy đủ, hỏi tường minh “Xem chi tiết chuyến TRIP-…”.

Nguyên mẫu hỗ trợ chuẩn bị chuyến công tác, xử lý sự cố trong chuyến đi và rà soát chi phí sau chuyến đi. Hệ thống chạy ngoại tuyến với dữ liệu giả lập; định tuyến, phân quyền, tính toán và đánh giá được thực hiện bằng quy tắc xác định.

## Cài đặt môi trường

Yêu cầu Python 3.11 trở lên. Tại thư mục dự án, chạy PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

`requirements.txt` cài `jsonschema`, `pytest` và chính dự án ở chế độ chỉnh sửa (`-e .`). Có thể dùng trực tiếp Python trong `.venv` mà không cần kích hoạt môi trường.

## Chạy giao diện web

```powershell
.\.venv\Scripts\python.exe -m travel_agent.app web --port 8080
```

Mở [web demo](http://127.0.0.1:8080). Giao diện có Chat, Trips, Drafts, Handoff, Audit log và Memory & Trace, đi kèm mô tả tiếng Việt. Tài khoản được chọn từ dữ liệu giả lập, chưa phải đăng nhập production.

Thông báo lỗi luôn dùng tiếng Việt và giữ mã kỹ thuật để tra cứu. Truy cập dữ liệu ngoài phạm vi dùng thông báo chung; thao tác không phù hợp với role nêu rõ role, thao tác bị hạn chế và người có thể hỗ trợ. Phản hồi chỉ trình bày kết quả, căn cứ và bước tiếp theo; không chèn câu nhắc thừa về các hành động agent chưa làm.

API của các tab áp dụng quyền tại server: Employee chỉ xem chuyến và bản nháp của mình; Reviewer xem được các chuyến và bản nháp; Approver đọc hồ sơ trong phạm vi phê duyệt qua chat; Admin xem tổng quan, audit, tải CSV và reset dữ liệu chạy thử. Lịch sử chat và hàng đợi hỗ trợ giới hạn theo tài khoản, riêng Admin được xem toàn bộ. Đổi tài khoản sẽ xóa nội dung đang hiển thị và bỏ qua phản hồi cũ đến muộn.

## Chạy bằng dòng lệnh

```powershell
# Hội thoại nhiều lượt
.\.venv\Scripts\python.exe -m travel_agent.app chat --user U-EMP-002 --session demo-1

# Một câu hỏi có mã chuyến đi
.\.venv\Scripts\python.exe -m travel_agent.app message --user U-EMP-002 --text "Chuyến bay TRIP-2026-002 bị trễ, tôi nên làm gì?"

# Ba quy trình nghiệp vụ
.\.venv\Scripts\python.exe -m travel_agent.app run pretrip --user U-EMP-002 --id TRIP-2026-006
.\.venv\Scripts\python.exe -m travel_agent.app run intrip --user U-EMP-002 --id TRIP-2026-002
.\.venv\Scripts\python.exe -m travel_agent.app run posttrip --user U-EMP-002 --id EXP-2026-001

# Tạo yêu cầu phê duyệt đang chờ, chỉ cho chủ chuyến đi
.\.venv\Scripts\python.exe -m travel_agent.app request-approval --user U-EMP-001 --trip TRIP-2026-001 --action checklist_review --summary "Đề nghị xem xét checklist."

# Chức năng chỉ đọc dành cho Admin
.\.venv\Scripts\python.exe -m travel_agent.app admin-trips --user U-ADM-001
.\.venv\Scripts\python.exe -m travel_agent.app admin-audit --user U-ADM-001 --trip TRIP-2026-004
.\.venv\Scripts\python.exe -m travel_agent.app handoffs --status open
.\.venv\Scripts\python.exe -m travel_agent.app logs --limit 20
```

## Cấu hình môi trường

| Biến | Mặc định | Công dụng |
|---|---|---|
| `TRAVEL_AGENT_DATA_DIR` | `data/` | Thư mục dữ liệu JSON giả lập |
| `TRAVEL_AGENT_DRAFT_DIR` | `data/drafts/` | Nơi lưu bản nháp |
| `TRAVEL_AGENT_MEMORY_DIR` | `data/memory/` | Nơi lưu ngữ cảnh phiên và tùy chọn |
| `TRAVEL_AGENT_LOG_DIR` | `data/logs/` | Nơi lưu CSV UTF-8 BOM |
| `TRAVEL_AGENT_DEMO_TODAY` | Ngày hệ thống | Ngày tham chiếu ISO cho câu hỏi hôm nay/ngày mai |

Lịch giả lập nằm trong khoảng `2026-12-01` đến `2027-01-07`. Dùng ID hoặc ngày đầy đủ để kết quả không phụ thuộc ngày chạy.

## Định tuyến hội thoại

| Tuyến | Khi sử dụng |
|---|---|
| `SELF_SERVE` | Lời chào, danh sách chuyến theo quyền, quy trình nghiệp vụ, tra cứu chính sách, quản lý tùy chọn, tạo yêu cầu pending tường minh và chức năng quản trị chỉ đọc |
| `CLARIFY` | Thiếu ID, nhiều chuyến phù hợp, ngày không khớp hoặc thiếu thông tin/chứng từ |
| `HANDOFF_STAFF` | Thiếu căn cứ, xung đột chính sách, sự cố cần người xử lý, chuyến bị hủy hoặc người dùng yêu cầu chuyển hỗ trợ |
| `REJECT_SAFETY` | ID sai, chỉ thị vượt quy tắc, thao tác bị cấm theo role hoặc dữ liệu ngoài scope |

`request_approval` tạo pending khi Employee yêu cầu rõ ràng, ví dụ `Yêu cầu phê duyệt checklist TRIP-2026-006`. Yêu cầu quyết định phê duyệt qua chat bị từ chối riêng, không bị nhầm thành thao tác tạo pending.

## Vai trò và quyền

| Tài khoản | Role | Quyền chính | Giới hạn |
|---|---|---|---|
| `U-EMP-001` đến `U-EMP-004` | Employee | Xem và xử lý chuyến, hành trình, chi phí, tùy chọn của mình; tạo pending cho chuyến của mình | Không đọc dữ liệu người khác hoặc audit |
| `U-REV-001` | Reviewer | Rà soát mọi chuyến, chi phí, bản nháp và chính sách được cấp | Không tạo yêu cầu thay Employee hoặc quyết định phê duyệt |
| `U-APR-001` | Approver | Đọc hồ sơ và danh mục chính sách thuộc một `approval_scope` đang pending; quản lý tùy chọn cá nhân | Không duyệt danh sách rộng, rà soát chi phí, tạo draft hoặc ra quyết định qua agent |
| `U-ADM-001` | Admin | Xem tổng quan, audit, hàng đợi hỗ trợ, tải CSV và reset runtime | Không chạy quy trình nghiệp vụ, tra policy hoặc dùng memory cá nhân |

## Memory và dispatcher

Session memory giữ `active_trip_id`, `active_report_id`, `last_workflow`, `pending_slot`, `pending_intent`, `session_language` theo người dùng và phiên; TTL mặc định 30 phút, gia hạn khi ghi. Preferences chỉ gồm ngôn ngữ và định dạng phản hồi, chỉ ghi/xóa khi người dùng yêu cầu. Dữ kiện nghiệp vụ luôn lấy lại từ công cụ.

Dispatcher kiểm tra registry, allowlist theo workflow, JSON Schema, quyền theo role/scope, ngân sách và cấu trúc kết quả. Orchestrator điều phối retry và ghi trace. Mặc định có 8 bước cho một `RunState`, trần cấu hình 12; chat pre-trip/mixed dùng 10. Lookup phụ có state riêng nên đây không phải trần tổng cho toàn bộ tin nhắn. Chỉ retry lỗi `retryable=true`, tối đa hai lần sau lần gọi đầu.

## Cấu trúc dự án

| Đường dẫn | Nội dung |
|---|---|
| `data/` | Dữ liệu giả lập và các thư mục runtime: bản nháp, memory, CSV |
| `src/travel_agent/app.py` | Điểm vào ứng dụng và CLI |
| `src/travel_agent/nlu.py` | Nhận diện ID, ngày, điểm đến, ý định theo mẫu Anh–Việt |
| `src/travel_agent/conversation.py` | Điều phối hội thoại và định dạng phản hồi |
| `src/travel_agent/dispatcher.py` | Kiểm tra tool call và phân quyền |
| `src/travel_agent/registry.py` | 19 công cụ và allowlist |
| `src/travel_agent/errors.py` | Thông báo lỗi chung và lỗi thao tác theo role |
| `src/travel_agent/memory/` | Lưu ngữ cảnh phiên và tùy chọn |
| `src/travel_agent/rag/` | BM25 ngoại tuyến, citation, kiểm tra căn cứ và phiên bản |
| `src/travel_agent/workflows/` | Ba quy trình trước, trong và sau chuyến đi |
| `src/travel_agent/web_demo.py` | HTTP server và giao diện web |
| `tests/`, `eval/` | Test tự động, đánh giá và báo cáo |

## Kiểm thử và ghi log

```powershell
.\.venv\Scripts\python.exe -m pytest -v --basetemp .venv/pytest-tmp
.\.venv\Scripts\python.exe -m pytest tests -v -k "scope or permission or role or preference or ttl" --basetemp .venv/pytest-tmp
.\.venv\Scripts\python.exe eval/run_eval.py --label after
.\.venv\Scripts\python.exe -m compileall -q src tests eval demo
```

Pytest và evaluator dùng bản sao dữ liệu tạm. Evaluator ghi kết quả vào `eval/reports/` và trace vào `eval/traces/`. Hội thoại demo ghi CSV có che mẫu token/số thẻ; audit kỹ thuật không ghi nguyên văn tin nhắn. Đây chưa phải cơ chế lọc mọi loại dữ liệu nhạy cảm.

Xem [kịch bản demo](demo/DEMO_SCENARIOS.md), [ma trận kiểm thử](Given%20Docs/TEST_MATRIX.md) và [đối chiếu yêu cầu](REQUIREMENTS_COMPLIANCE_EVIDENCE.md).

## Danh mục bàn giao theo mục 14 của đề bài

| Mục | Dẫn chứng |
|---|---|
| 14.1 Mã nguồn | `src/travel_agent/` |
| 14.2 Cài đặt và chạy | Tài liệu này |
| 14.3 Dữ liệu và kho chính sách | `data/` |
| 14.4 Hợp đồng agent, tool và schema | `Given Docs/AGENTS.md`, `Given Docs/TOOL_CARDS.md`, `schemas/` |
| 14.5 Kiến trúc và ba quy trình | `Given Docs/ARCHITECTURE.md` |
| 14.6 Memory và ranh giới dữ liệu | `Given Docs/MEMORY_AND_SAFETY.md` |
| 14.7 Test và phân tích lỗi | `Given Docs/TEST_MATRIX.md`, `eval/reports/root_cause.md` |
| 14.8 Đánh giá trước/sau và hồi quy | `eval/reports/` |
| 14.9 Demo | `demo/` |
| 14.10 Giới hạn | Phần dưới và `Given Docs/AGENTS.md` |

## Giới hạn hiện tại

- NLU nhận diện bằng mẫu và từ khóa; chưa hiểu mọi cách diễn đạt tiếng Anh hoặc tiếng Việt. BM25 chủ yếu dựa trên ngôn ngữ của kho chính sách.
- Kiểm tra căn cứ dùng từ khóa, câu và phủ định; chưa có mô hình suy luận ngữ nghĩa hoặc LLM bên ngoài.
- JSON/CSV cục bộ chưa có cơ sở dữ liệu, đăng nhập, mã hóa hay audit bất biến cấp production. Memory chưa có cơ chế giải quyết ghi đồng thời ở nhiều tiến trình.
- Agent chỉ tạo bản nháp và yêu cầu pending. Đặt vé, thanh toán, hoàn tiền, quyết định phê duyệt, gửi email, lập lịch nền và tích hợp bên ngoài nằm ngoài phạm vi.

## Cập nhật workspace và phản hồi

Trips có bốn tác vụ riêng: xem chi tiết, xem hành trình, kiểm tra checklist và yêu cầu hỗ trợ. Admin xem audit liên quan; Approver xem danh sách pending được phân công trong Trips, rồi đọc hồ sơ theo scope qua chat. Chọn tác vụ gửi đúng ý định, không ghép đọc dữ kiện với checklist. Ngữ cảnh phiên giữ tác vụ cần làm rõ và ngôn ngữ khi người dùng trả lời bằng ID.

Draft giữ mã `DR-…` độc lập với Trip/Expense nguồn. Employee chủ hồ sơ và Reviewer được mở đầy đủ dữ kiện nguồn, hành trình, các trường thiếu và nội dung/citation bản nháp. Chỉ ghi chú, mục đích đề xuất và checklist đề xuất được sửa. Các API `/api/draft/detail`, `/api/draft/save`, `/api/draft/recheck` kiểm tra quyền tại server; không cho sửa identity, approval, dữ kiện nguồn hoặc citation. Kiểm tra lại dùng nguồn thật của mock; nội dung đề xuất được giữ qua lần tạo lại, không tự làm nguồn đầy đủ.

Thông báo không có chức năng không tự tạo phiếu. Pending hiển thị riêng với trạng thái chuyến; yêu cầu hỗ trợ có trạng thái riêng trên Trips. Thẻ prompt dùng nhãn kết quả mong đợi và mã CASE. Các nhánh an toàn kiểm tra nguyên câu tiếng Việt trước lookup/clarification.

Evaluator bổ sung 31 thẻ web vào 31 ca nền; tỷ lệ chọn tool và arguments đo trên các thẻ, số bước/retry lấy từ trace. Task completion loại các ca safety khỏi mẫu số. Grounding vẫn chỉ có claim đại diện; chưa phải benchmark ngữ nghĩa rộng.

## Yêu cầu được phân công cho Approver

Trips của Approver chỉ trả metadata tối thiểu cho request `pending` có `assigned_approver_id` bằng tài khoản hiện tại. Hai seed 001/checklist_review và 002/escalation thuộc U-APR-001; không thêm Trip mới. Danh sách rỗng hiển thị thông báo bình thường, không tạo handoff. Server kiểm tra lại quyền khi đọc chi tiết; chọn scope phía client không tự cấp quyền. Thiếu phân công, đổi người hoặc request đã resolved đều làm scope cũ mất hiệu lực.

Chọn scope tường minh trước khi xem; nút trên dòng khác chuyến hoặc khác loại yêu cầu bị khóa và không tự đổi scope. `checklist_review`/`publish_request` đọc hồ sơ chuyến và trạng thái duyệt; `escalation` đọc hành trình. Yêu cầu xem chi tiết không tự chuyển thành xem hành trình. Trips gửi tác vụ cụ thể qua `/api/trip/action`, dùng cùng bộ điều phối và dispatcher với chat. Server kiểm tra scope của dòng, phân công hiện tại, loại dữ kiện và quyền của tài khoản. Menu lấy `allowed_actions` từ server: Employee có bốn tác vụ; Reviewer không có tạo yêu cầu phê duyệt; Admin chỉ có audit.

Yêu cầu pending mới được application mô phỏng phân công mặc định cho U-APR-001; model không được truyền người phê duyệt qua arguments. Helper quyết định bên ngoài tool set cũng phải kiểm tra phân công. Chưa có quyết định approve/reject qua chat.

Lỗi quyền dùng câu “Bạn không có quyền truy cập dữ liệu hoặc thực hiện thao tác này”, giữ code unauthorized_scope. Không dùng câu này cho giới hạn chức năng (ví dụ đặt phòng) hoặc lỗi đầu vào. Thiếu scope được nhắc chọn request được phân công, không tự tạo phiếu hỗ trợ.
