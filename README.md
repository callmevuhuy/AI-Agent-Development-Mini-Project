# Trợ lý điều hành công tác doanh nghiệp (Global Business Travel Operations Agent)

Nguyên mẫu điều phối ba quy trình nghiệp vụ công tác doanh nghiệp: chuẩn bị trước chuyến đi (Pre-trip), hỗ trợ sự cố trong chuyến đi (In-trip) và rà soát chi phí sau chuyến đi (Post-trip). Hệ thống sử dụng dữ liệu giả lập cục bộ và hỗ trợ hai chế độ thực thi:

- **Chế độ mặc định (`rule` — Ngoại tuyến):** Định tuyến NLU, truy xuất BM25, tính toán, kiểm tra quyền và sinh phản hồi bằng quy tắc xác định; không cần API key hoặc kết nối Internet khi chạy.
- **Chế độ tùy chọn (`gemini` — Hybrid Agent với Gemini API):** Kết hợp mô hình Gemini cho nhận diện ý định (Structured Output), viết lại truy vấn chính sách 1-hop (RAG Query Rewrite), vòng lặp đề xuất công cụ (Function Calling) và tổng hợp câu trả lời có hậu kiểm citation/phê duyệt. Mọi lời gọi công cụ vẫn đi qua cùng tầng kiểm soát phân quyền, JSON Schema và ngân sách bước ở phía máy chủ.

Tài liệu tham chiếu kịch bản trình diễn: [Kịch bản demo web](demo/DEMO_WEB.md) và [Kịch bản kiểm thử hội thoại](demo/DEMO_SCENARIOS.md).

---

## Yêu cầu hệ thống và cài đặt

Yêu cầu **Python 3.11 trở lên** và kết nối Internet ở lần cài đặt dependencies đầu tiên. Thực hiện các lệnh từ thư mục gốc của dự án (thư mục chứa `README.md`, `requirements.txt`, `pyproject.toml` và `data/`).

### Windows (PowerShell)

```powershell
python --version
Test-Path .\pyproject.toml
if (-not (Test-Path .\.venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m travel_agent.app --help
```

Nếu hệ thống dùng launcher `py` thay cho `python`, thay `python` bằng `py -3`. Lệnh `pip check` phải trả `No broken requirements found`. `requirements.txt` cài `jsonschema>=4.23`, `google-genai>=1.0.0`, `pytest>=8.0` và gói dự án ở chế độ chỉnh sửa (`-e .`).

### macOS / Linux (bash hoặc zsh)

```bash
python3 --version
test -f pyproject.toml
if [ ! -d .venv ]; then python3 -m venv .venv; fi
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip check
./.venv/bin/python -m travel_agent.app --help
```

---

## Khởi động giao diện web

### Tùy chọn 1: Chế độ ngoại tuyến mặc định (`rule`)

Không cần thiết lập `GEMINI_API_KEY`.

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m travel_agent.app web --host 127.0.0.1 --port 8080
```

**macOS / Linux:**

```bash
./.venv/bin/python -m travel_agent.app web --host 127.0.0.1 --port 8080
```

### Tùy chọn 2: Chế độ Hybrid với Gemini API (`gemini`)

Thiết lập biến môi trường `GEMINI_API_KEY` và chọn backend `gemini` (hoặc giữ mặc định `rule` và chuyển backend ngay tại mục **Backend xử lý (LLM)** ở thanh bên của giao diện web).

**Windows (PowerShell):**

```powershell
$env:GEMINI_API_KEY = "<YOUR_GEMINI_API_KEY>"
$env:TRAVEL_AGENT_LLM_BACKEND = "gemini"
# Tùy chọn model và timeout (giá trị mặc định bên dưới):
$env:TRAVEL_AGENT_GEMINI_MODEL = "gemini-3.8-flash"
$env:TRAVEL_AGENT_GEMINI_TIMEOUT = "35.0"

.\.venv\Scripts\python.exe -m travel_agent.app web --host 127.0.0.1 --port 8080
```

**macOS / Linux:**

```bash
export GEMINI_API_KEY="<YOUR_GEMINI_API_KEY>"
export TRAVEL_AGENT_LLM_BACKEND="gemini"
export TRAVEL_AGENT_GEMINI_MODEL="gemini-3.8-flash"
export TRAVEL_AGENT_GEMINI_TIMEOUT="35.0"

./.venv/bin/python -m travel_agent.app web --host 127.0.0.1 --port 8080
```

Truy cập [http://127.0.0.1:8080](http://127.0.0.1:8080) trên trình duyệt cục bộ. Nếu cổng `8080` đã được sử dụng, đổi tham số `--port` (ví dụ `--port 8081`).

Giao diện web gồm các màn hình: **Chat với Agent**, **Trips · Chuyến công tác**, **Drafts · Bản nháp**, **Handoff · Yêu cầu hỗ trợ**, **Audit log · Nhật ký hoạt động**, và **Memory & Trace**. Khi chọn tài khoản mới trên giao diện, dữ liệu hiển thị của tài khoản cũ được xóa và các phản hồi đến muộn bị bỏ qua.

---

## Chạy bằng dòng lệnh (CLI)

Các lệnh CLI dùng chung cấu hình biến môi trường (`TRAVEL_AGENT_LLM_BACKEND=rule` hoặc `gemini`). Trên macOS/Linux thay `.\.venv\Scripts\python.exe` bằng `./.venv/bin/python`.

```powershell
# Hội thoại nhiều lượt (chế độ tương tác)
.\.venv\Scripts\python.exe -m travel_agent.app chat --user U-EMP-002 --session demo-1

# Gửi một tin nhắn đơn
.\.venv\Scripts\python.exe -m travel_agent.app message --user U-EMP-002 --text "Chuyến bay TRIP-2026-002 bị trễ, tôi nên làm gì?"

# Chạy trực tiếp ba quy trình nghiệp vụ
.\.venv\Scripts\python.exe -m travel_agent.app run pretrip --user U-EMP-002 --id TRIP-2026-006
.\.venv\Scripts\python.exe -m travel_agent.app run intrip --user U-EMP-002 --id TRIP-2026-002
.\.venv\Scripts\python.exe -m travel_agent.app run posttrip --user U-EMP-002 --id EXP-2026-001

# Tạo yêu cầu phê duyệt trạng thái pending (chỉ Employee sở hữu chuyến đi)
.\.venv\Scripts\python.exe -m travel_agent.app request-approval --user U-EMP-001 --trip TRIP-2026-001 --action checklist_review --summary "Đề nghị xem xét checklist."

# Truy vấn chỉ đọc dành cho Admin và đọc log CSV
.\.venv\Scripts\python.exe -m travel_agent.app admin-trips --user U-ADM-001
.\.venv\Scripts\python.exe -m travel_agent.app admin-audit --user U-ADM-001 --trip TRIP-2026-004
.\.venv\Scripts\python.exe -m travel_agent.app handoffs --status open
.\.venv\Scripts\python.exe -m travel_agent.app logs --limit 20
```

---

## Cấu hình biến môi trường

| Biến | Mặc định | Công dụng |
|---|---|---|
| `TRAVEL_AGENT_DATA_DIR` | `data/` | Thư mục chứa dữ liệu JSON giả lập |
| `TRAVEL_AGENT_DRAFT_DIR` | `data/drafts/` | Nơi lưu bản nháp nghiệp vụ |
| `TRAVEL_AGENT_MEMORY_DIR` | `data/memory/` | Nơi lưu ngữ cảnh phiên và tùy chọn cá nhân |
| `TRAVEL_AGENT_LOG_DIR` | `data/logs/` | Nơi lưu tệp CSV UTF-8 BOM |
| `TRAVEL_AGENT_DEMO_TODAY` | Ngày hệ thống | Ngày tham chiếu định dạng `YYYY-MM-DD` cho truy vấn tương đối |
| `TRAVEL_AGENT_LLM_BACKEND` | `rule` | Backend xử lý ngôn ngữ: `rule` (ngoại tuyến) hoặc `gemini` (Gemini API) |
| `GEMINI_API_KEY` | Không đặt | Khóa API Google Gemini; chỉ đọc từ môi trường, không lưu vào trace, audit hoặc CSV |
| `TRAVEL_AGENT_GEMINI_MODEL` | `gemini-3.8-flash` | Tên model Gemini (`gemini-3.8-flash`, `gemini-4-hydrogen`, `gemini-3.1-flash-lite`, `gemini-3.5-flash`, ...) |
| `TRAVEL_AGENT_GEMINI_TIMEOUT` | `35.0` | Giới hạn thời gian chờ phản hồi API Gemini (giây, trong khoảng `5.0`–`90.0`) |

Dữ liệu chuyến đi giả lập nằm trong khoảng từ `2026-12-01` đến `2027-01-07`.

---

## Kiến trúc xử lý và ranh giới an toàn

### 1. Định tuyến bốn luồng

| Tuyến | Phạm vi áp dụng |
|---|---|
| `SELF_SERVE` | Lời chào, danh sách chuyến theo quyền, ba quy trình nghiệp vụ, tra cứu chính sách có nguồn, quản lý tùy chọn cá nhân, tạo yêu cầu `pending` tường minh và thao tác quản trị chỉ đọc |
| `CLARIFY` | Thiếu mã định danh, nhiều bản ghi khớp cùng lúc, ngày bay không trùng lịch sử hoặc thiếu chứng từ bắt buộc |
| `HANDOFF_STAFF` | Thiếu bằng chứng chính sách, xung đột phiên bản chính sách đang hiệu lực, chuyến đi bị hủy/cần can thiệp hoặc người dùng yêu cầu nhân viên hỗ trợ |
| `REJECT_SAFETY` | Sai định dạng ID, chỉ thị vượt quy tắc (injection), thao tác ngoài thẩm quyền vai trò hoặc truy cập bản ghi ngoài phạm vi |

Chat hỗ trợ tối đa bốn yêu cầu độc lập trong một tin nhắn (tách bằng dấu chấm phẩy, xuống dòng hoặc liên từ trước yêu cầu tường minh); tin nhắn được kiểm tra an toàn tổng thể trước khi thực thi từng phần tuần tự.

### 2. Lớp Hybrid Gemini API (`src/travel_agent/llm.py`)

Khi kích hoạt backend `gemini`:

1. **Tiền kiểm an toàn (Round-1 Guard):** Các mẫu prompt injection, chuỗi vượt `1000` ký tự và ID sai định dạng bị chặn bởi `nlu.py` trước khi phát sinh lời gọi API Gemini.
2. **NLU có cấu trúc:** Sử dụng Structured Output (`response_json_schema`) để phân loại ý định, đại từ nối ngữ cảnh và trích xuất thực thể; từ chối hoặc bỏ qua mọi trường cố gắng thay đổi `user_id`, `role` hoặc `approval_scope`.
3. **Vòng lặp gọi công cụ & Hậu kiểm:** Đề xuất công cụ và tham số từ `TOOL_REGISTRY` đi qua `run_tool()` → `dispatcher.dispatch()`, giữ nguyên kiểm tra JSON Schema (`Draft202012Validator`), quyền sở hữu và phạm vi duyệt. Mọi phản hồi `SELF_SERVE` do model tạo đều qua `check_generated_response()` để bảo đảm giữ trích dẫn và không khẳng định trạng thái đã duyệt/hoàn tiền khi `trip_approval_status != "approved"`.
4. **Cơ chế Fallback:** Khi thiếu `GEMINI_API_KEY`, quá thời gian chờ (`timeout`), gặp giới hạn tốc độ (`429`) hoặc đầu ra không qua hậu kiểm, hệ thống tự động chuyển về luồng `rule` tương ứng.

### 3. Vai trò và phân quyền

| Tài khoản | Role | Quyền chính | Giới hạn |
|---|---|---|---|
| `U-EMP-001` đến `U-EMP-004` | Employee | Xem/xử lý chuyến, hành trình, chi phí, tùy chọn cá nhân và tạo yêu cầu `pending` cho chuyến của mình | Không truy cập hồ sơ người khác hoặc audit log |
| `U-REV-001` | Reviewer | Rà soát mọi chuyến đi, chi phí, bản nháp và tra cứu chính sách được cấp | Không tạo yêu cầu phê duyệt thay Employee hoặc ra quyết định phê duyệt |
| `U-APR-001` | Approver | Đọc hồ sơ và danh mục chính sách thuộc một `approval_scope` đang `pending` được phân công; quản lý tùy chọn cá nhân | Không duyệt danh sách toàn công ty, không rà soát chi phí, không tạo bản nháp và không phê duyệt qua chat |
| `U-ADM-001` | Admin | Xem tổng quan chuyến đi, audit log, hàng đợi handoff, tải CSV và reset dữ liệu chạy thử | Không chạy quy trình nghiệp vụ, không tra cứu chính sách và không dùng bộ nhớ cá nhân |

### 4. Bộ nhớ, Dispatcher và Ngân sách bước

- **Bộ nhớ:** Session memory lưu `active_trip_id`, `active_report_id`, `last_workflow`, `pending_slot`, `pending_intent`, `session_language` theo `(user_id, session_id)` với TTL mặc định 30 phút (`1800s`). Preferences (`response_language`, `preferred_output_format`) chỉ ghi hoặc xóa khi có yêu cầu hợp lệ (`memory_write_authorized=true`).
- **Dispatcher & Budget:** Mỗi `RunState` có mặc định 8 bước (10 bước cho pre-trip/mixed qua chat, trần `12` bước) và tối đa 2 lần thử lại đối với lỗi `retryable=true`. Toàn bộ một lượt `handle_turn()` (bao gồm tra cứu phụ và batch tối đa 4 yêu cầu) bị giới hạn bởi ngân sách tổng `TOTAL_TURN_MAX_STEPS = 32` (`TurnBudget`).
- **Thao tác Web & Tham chiếu:** Menu Trips dùng `/api/trip/action` kiểm tra lại quyền và `approval_scope` tại máy chủ. Các thẻ tham chiếu Trip mở trên giao diện gọi `/api/trip/reference` để đọc lại dữ liệu nguồn hiện tại theo quyền. API quản lý bản nháp (`/api/draft/detail`, `/api/draft/save`, `/api/draft/recheck`) chỉ cho phép chỉnh các trường đề xuất được liệt kê và luôn đối chiếu dữ liệu nguồn bất biến.

---

## Cấu trúc dự án

| Đường dẫn | Nội dung |
|---|---|
| `data/` | Dữ liệu giả lập (`trips.json`, `expenses.json`, `policy_chunks.json`, `audit_events.json`, `approval_requests.json`, ...) và thư mục runtime |
| `src/travel_agent/app.py` | Điểm vào ứng dụng và giao diện dòng lệnh (CLI) |
| `src/travel_agent/config.py` | Cấu hình đường dẫn runtime, ngân sách bước và biến môi trường LLM |
| `src/travel_agent/nlu.py` | Tiền kiểm an toàn và nhận diện ý định/thực thể xác định |
| `src/travel_agent/llm.py` | Dual-backend `RuleBased` / `Gemini API` (NLU, 1-hop query rewrite, Tool Loop, Post-Guard, `TurnBudget`) |
| `src/travel_agent/conversation.py` | Điều phối hội thoại bốn luồng và định dạng phản hồi |
| `src/travel_agent/dispatcher.py` | Kiểm tra hợp đồng công cụ, JSON Schema và phân quyền tại máy chủ |
| `src/travel_agent/registry.py` | Đăng ký 19 công cụ và allowlist theo quy trình |
| `src/travel_agent/schemas/` | JSON Schema định nghĩa tham số của 19 công cụ |
| `src/travel_agent/errors.py` | Thông báo lỗi chuẩn hóa theo mã kỹ thuật và vai trò |
| `src/travel_agent/memory/` | Lưu trữ ngữ cảnh phiên và tùy chọn cá nhân theo cơ chế ghi nguyên tử |
| `src/travel_agent/rag/` | Truy xuất BM25 ngoại tuyến, trích dẫn, kiểm tra căn cứ và xung đột phiên bản |
| `src/travel_agent/workflows/` | Ba quy trình Pre-trip (`a_pretrip.py`), In-trip (`b_intrip.py`), Post-trip (`c_posttrip.py`) |
| `src/travel_agent/web_demo.py` | HTTP server thư viện chuẩn và giao diện web demo |
| `tests/`, `eval/` | Bộ kiểm thử tự động (`pytest`, Node UI smoke) và kịch bản đánh giá |

---

## Kiểm thử và đánh giá

Các bộ kiểm thử tiêu chuẩn chạy hoàn toàn ngoại tuyến ở chế độ `rule` và sử dụng bản sao dữ liệu tạm thời.

**Windows (PowerShell):**

```powershell
# Toàn bộ bộ test tự động (gồm HTTP test và Gemini mock tests)
.\.venv\Scripts\python.exe -m pytest -v --basetemp .venv/pytest-tmp

# Nhóm test phân quyền và bộ nhớ
.\.venv\Scripts\python.exe -m pytest tests -v -k "scope or permission or role or preference or ttl" --basetemp .venv/pytest-tmp

# Bộ đánh giá định lượng 62 ca xác định
.\.venv\Scripts\python.exe eval/run_eval.py --label after

# Kiểm tra biên dịch cú pháp
.\.venv\Scripts\python.exe -m compileall -q src tests eval demo
```

**Đánh giá so sánh khi có `GEMINI_API_KEY` (tùy chọn):**

```powershell
$env:GEMINI_API_KEY = "<YOUR_GEMINI_API_KEY>"
.\.venv\Scripts\python.exe eval/run_eval_llm.py --backend both
```

Tệp CSV hội thoại và hàng đợi handoff (`chat_history.csv`, `handoff_queue.csv`) dùng mã hóa UTF-8 BOM và che một số mẫu nhạy cảm (số thẻ 13–19 chữ số, token `sk-...`, `ghp_...`, `Bearer ...` và Google API key `AIza...`). Audit JSON kỹ thuật không lưu nguyên văn tin nhắn người dùng.

Xem thêm: [Kịch bản demo web](demo/DEMO_WEB.md), [Ma trận kiểm thử](Given%20Docs/TEST_MATRIX.md) và [Đối chiếu yêu cầu](REQUIREMENTS_COMPLIANCE_EVIDENCE.md).

---

## Danh mục bàn giao theo mục 14

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
| 14.10 Giới hạn | Mục Giới hạn bên dưới và `Given Docs/AGENTS.md` |

---

## Giới hạn hiện tại

- Ở chế độ ngoại tuyến (`rule`), NLU và BM25 phụ thuộc vào mẫu từ khóa và cấu trúc câu tiếng Anh/tiếng Việt đã định nghĩa; ở chế độ `gemini`, chất lượng nhận diện câu tự nhiên và suy luận đa bước phụ thuộc vào model và kết nối Gemini API.
- Bộ kiểm tra căn cứ cục bộ (`claim_evidence_check.py`) kiểm tra theo tập từ khóa và phủ định tiếng Anh; hậu kiểm LLM kiểm tra giữ trích dẫn và chặn khẳng định phê duyệt chưa được xác thực, chưa thay thế mô hình NLI ngữ nghĩa chuyên biệt.
- Lưu trữ JSON/CSV cục bộ và tài khoản demo chưa thay thế cơ sở dữ liệu quan hệ, hệ thống xác thực người dùng, mã hóa lưu trữ hoặc cơ chế kiểm soát ghi đồng thời đa tiến trình ở môi trường production.
- Agent chỉ tạo bản nháp và yêu cầu `pending`; các thao tác đặt vé, thanh toán, hoàn tiền, quyết định phê duyệt, gửi email và tác vụ nền nằm ngoài phạm vi nguyên mẫu.
