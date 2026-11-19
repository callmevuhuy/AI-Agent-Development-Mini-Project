# Trợ lý điều hành công tác doanh nghiệp

Kịch bản trình bày ba workflow và quyền các role: [Kịch bản demo web](demo/DEMO_WEB.md).

Chat hỗ trợ tối đa bốn yêu cầu trong một tin nhắn, tách bằng dấu chấm phẩy, xuống dòng hoặc liên từ trước một yêu cầu tường minh. Giao diện hiện từng kết quả riêng, giữ lỗi/quyền/outcome của từng phần; đây là các thao tác tuần tự, không phải giao dịch nguyên tử. Injection được kiểm tra trên cả tin nhắn trước khi thực hiện. Mỗi phần giữ budget/retry của lượt riêng.

Phản hồi workflow/handoff không tự đính kèm toàn bộ chi tiết Trip kể cả khi chọn định dạng chi tiết. Thẻ Trip dưới phản hồi mở bằng rê chuột hoặc focus bàn phím, gọi `/api/trip/reference` để kiểm tra lại quyền và đọc nguồn hiện tại. Scope hỗ trợ của Approver chỉ hiện dữ kiện hành trình, không mở hồ sơ chuyến. Citation policy vẫn độc lập với tham chiếu Trip. Muốn đọc đầy đủ, hỏi tường minh “Xem chi tiết chuyến TRIP-…”.

Nguyên mẫu hỗ trợ chuẩn bị chuyến công tác, xử lý sự cố trong chuyến đi và rà soát chi phí sau chuyến đi. Hệ thống chạy ngoại tuyến với dữ liệu giả lập; định tuyến, phân quyền, tính toán và đánh giá được thực hiện bằng quy tắc xác định.

## Tải dự án và chuẩn bị môi trường

Yêu cầu **Python 3.11 trở lên** và Internet khi cài dependencies lần đầu. Không cần API key, Node.js, cơ sở dữ liệu hoặc file `.env`; sau khi cài, demo chạy ngoại tuyến với dữ liệu giả lập.

Clone repository bằng Git hoặc tải **Code → Download ZIP** rồi giải nén. Trong VS Code, chọn **File → Open Folder** mở thư mục dự án, sau đó **Terminal → New Terminal**. Terminal phải ở thư mục chứa `README.md`, `requirements.txt`, `pyproject.toml` và `data/`. Không chạy trong thư mục ZIP chưa giải nén. Các lệnh dưới đây dùng đường dẫn tương đối, không phụ thuộc tên tài khoản hay ổ đĩa.

### Windows / PowerShell

Cài Python và chọn **Add Python to PATH**. Kiểm tra:

```powershell
python --version
Get-Location
Test-Path .\pyproject.toml
```

Python phải từ 3.11 trở lên và lệnh cuối phải trả `True`. Nếu `python` không được nhận diện hoặc mở Microsoft Store, thử `py -3 --version`; nếu lệnh này chạy được, dùng `py -3 -m venv .venv` ở bước tạo môi trường bên dưới. Nếu cả hai đều không chạy được, cài Python rồi mở terminal mới.

**Lần đầu cài đặt** (chỉ tạo `.venv` khi chưa tồn tại):

```powershell
if (-not (Test-Path .\.venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m travel_agent.app --help
```

Nếu dùng `py` thay cho `python`, thay dòng đầu bằng `if (-not (Test-Path .\.venv)) { py -3 -m venv .venv }`.

`pip check` phải báo `No broken requirements found`; lệnh cuối hiển thị các lệnh CLI. `requirements.txt` cài `jsonschema`, `pytest` và chính dự án ở chế độ chỉnh sửa (`-e .`). Dùng trực tiếp Python trong `.venv`, không cần activate hoặc đổi Execution Policy.

**Các lần chạy sau:** bỏ qua bước tạo môi trường, chạy lệnh web hoặc test bên dưới. Khi cập nhật mã nguồn có thay đổi dependencies, dừng demo rồi chạy lại lệnh `pip install -r requirements.txt`.

### macOS / Linux (bash hoặc zsh)

Cài Python 3.11 trở lên bằng công cụ cài đặt của hệ điều hành. Tại thư mục gốc dự án:

```bash
python3 --version
test -f pyproject.toml && echo "Đúng thư mục dự án"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip check
./.venv/bin/python -m travel_agent.app --help
```

Trên Ubuntu/Debian, nếu thiếu `venv`/`ensurepip`, cài gói `python3-venv` (hoặc gói `python3.x-venv` tương ứng với phiên bản đang dùng) rồi tạo lại môi trường. Từ phần tiếp theo, các lệnh minh họa dùng PowerShell; trên macOS/Linux thay `.\.venv\Scripts\python.exe` bằng `./.venv/bin/python`, giữ nguyên arguments.

## Chạy giao diện web

Sau khi cài môi trường, tại thư mục gốc dự án chạy:

```powershell
.\.venv\Scripts\python.exe -m travel_agent.app web --host 127.0.0.1 --port 8080
```

Trên macOS/Linux:

```bash
./.venv/bin/python -m travel_agent.app web --host 127.0.0.1 --port 8080
```

Giữ terminal này đang chạy và tự mở [http://127.0.0.1:8080](http://127.0.0.1:8080) trong trình duyệt **trên cùng máy**. Nhấn **Ctrl+C** trong terminal chạy server để dừng. Mở terminal thứ hai tại cùng thư mục dự án nếu muốn chạy CLI/test song song; không tạo lại `.venv` khi demo đang chạy.

Nếu cổng 8080 đang được dùng hoặc báo `WinError 10048`, dừng phiên demo cũ hoặc chọn cổng khác:

```powershell
.\.venv\Scripts\python.exe -m travel_agent.app web --host 127.0.0.1 --port 8081
```

Khi đó mở [http://127.0.0.1:8081](http://127.0.0.1:8081). Giao diện có Chat, Trips, Drafts, Handoff, Audit log và Memory & Trace. Tài khoản được chọn từ dữ liệu giả lập, chưa phải đăng nhập production. Kịch bản trình diễn: [Kịch bản demo web](demo/DEMO_WEB.md).

### Xử lý lỗi môi trường

- **`Unable to copy ... venvlauncher.exe ... .venv\Scripts\python.exe`**: đang tạo lại môi trường và có thể gặp file bị khóa. Dừng web demo bằng **Ctrl+C** tại terminal đang chạy demo, dừng các phiên Python/debugger dùng môi trường này. Nếu `.venv` vẫn chạy được, không tạo lại; kiểm tra bằng `.\.venv\Scripts\python.exe -m pip check` rồi chạy demo. Không chạy `python -m venv .venv` trong lúc môi trường đang được sử dụng.
- **Môi trường hỏng, sao chép từ máy khác hoặc chuyển đường dẫn**: `.venv` không dùng để chia sẻ giữa các máy. Sau khi dừng mọi tiến trình dùng môi trường, đổi tên `.venv` thành một thư mục dự phòng chưa tồn tại (ví dụ `Rename-Item -LiteralPath .venv -NewName .venv.backup` trong PowerShell), rồi làm lại bước cài đặt lần đầu. Nếu vẫn lỗi ghi file, kiểm tra quyền ghi thư mục hoặc phần mềm bảo vệ trên máy.
- **`No module named travel_agent`, `jsonschema` hoặc `pytest`**: dùng đúng Python của `.venv`, kiểm tra đang ở thư mục gốc rồi chạy lại `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **Không tìm thấy `.venv\Scripts\python.exe`**: môi trường chưa được tạo thành công hoặc là môi trường của hệ điều hành khác; xử lý như môi trường hỏng ở trên.
- **Không tìm thấy `requirements.txt` hoặc `pyproject.toml`**: mở terminal ở thư mục gốc dự án.
- **Cài dependencies lỗi mạng/proxy**: kiểm tra kết nối Internet và cấu hình proxy của máy, sau đó chạy lại lệnh cài; chưa chạy demo/test khi cài đặt còn báo lỗi.
- **`WinError 10013` khi mở localhost hoặc chạy test HTTP**: môi trường thực thi có thể chặn socket. Trong Codex cần cho phép lệnh chạy ngoài sandbox; hoặc chạy trong PowerShell cục bộ. Nếu vẫn lỗi, kiểm tra quyền mạng/firewall của Python và thử cổng khác.

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

Sau khi cài dependencies, mở terminal tại thư mục gốc dự án. Lệnh đầu chạy toàn bộ test; lệnh thứ hai chỉ chạy nhóm test quyền và memory. Evaluator tạo báo cáo đánh giá; `compileall` kiểm tra cú pháp.

```powershell
.\.venv\Scripts\python.exe -m pytest -v --basetemp .venv/pytest-tmp
.\.venv\Scripts\python.exe -m pytest tests -v -k "scope or permission or role or preference or ttl" --basetemp .venv/pytest-tmp
.\.venv\Scripts\python.exe eval/run_eval.py --label after
.\.venv\Scripts\python.exe -m compileall -q src tests eval demo
```

Trên macOS/Linux, chạy toàn bộ test và đánh giá bằng:

```bash
./.venv/bin/python -m pytest -v --basetemp .venv/pytest-tmp
./.venv/bin/python eval/run_eval.py --label after
./.venv/bin/python -m compileall -q src tests eval demo
```

Test thành công kết thúc bằng `passed`, không có `failed`/`ERROR`; evaluator in số ca `passed`/`failed` và đường dẫn báo cáo. `compileall -q` thành công không in lỗi. Thư mục `.venv/pytest-tmp` dành riêng cho pytest và được pytest dọn lại mỗi lần chạy; không lưu tài liệu vào đó hoặc chạy nhiều bộ test đồng thời với cùng `--basetemp`.

Pytest và evaluator dùng bản sao dữ liệu tạm. Evaluator ghi kết quả vào `eval/reports/` và trace vào `eval/traces/`. Hội thoại demo ghi CSV có che mẫu token/số thẻ; audit kỹ thuật không ghi nguyên văn tin nhắn. Đây chưa phải cơ chế lọc mọi loại dữ liệu nhạy cảm.

Xem [kịch bản demo](demo/DEMO_SCENARIOS.md), [ma trận kiểm thử](Given%20Docs/TEST_MATRIX.md) và [đối chiếu yêu cầu](REQUIREMENTS_COMPLIANCE_EVIDENCE.md).

## Danh mục bàn giao theo mục 14 của đề bài

| Mục | Dẫn chứng |
|---|---|
| 14.1 Mã nguồn | `src/travel_agent/` |
| 14.2 Cài đặt và chạy | Tài liệu này |
| 14.3 Dữ liệu và kho chính sách | `data/` |
| 14.4 Hợp đồng agent, tool và schema | `Given Docs/AGENTS.md`, `Given Docs/TOOL_CARDS.md`, `src/travel_agent/schemas/` |
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


