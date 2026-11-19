# Công việc và trạng thái dự án

## Đã hoàn thành trong phạm vi nguyên mẫu

- [x] Dữ liệu giả lập, 19 tool, JSON Schema, registry, allowlist và phân quyền tại dispatcher.
- [x] Ba quy trình trước/trong/sau chuyến đi, bản nháp có ID ổn định, trạng thái dừng trung thực và trích dẫn policy.
- [x] `request_approval` chỉ tạo pending, chỉ dành cho Employee sở hữu chuyến đi, không tạo trùng theo `(trip_id, action_type)`.
- [x] Định tuyến bốn luồng, lookup theo ID/ngày/điểm đến, câu hỏi kết hợp nghiệp vụ và chính sách, kiểm tra ngày bay thực tế.
- [x] Session có TTL; preferences có yêu cầu đồng ý; cách ly user/session.
- [x] CSV UTF-8 BOM có che mẫu token/số thẻ; audit kỹ thuật không chứa nguyên văn tin nhắn.
- [x] Web demo và CLI; Admin xem audit, tải CSV, reset runtime; API các tab lọc dữ liệu theo quyền.
- [x] RAG áp dụng ACL trước xếp hạng, kiểm tra căn cứ, xung đột và loại chỉ thị injection.
- [x] Rà lại happy case và ca không thành công của bốn Employee, Reviewer, Approver, Admin.
- [x] Sửa danh sách chuyến của Employee, preferences của Approver, pending request qua chat và từ chối quyết định phê duyệt qua chat.
- [x] Lỗi scope dùng thông báo chung; lỗi thao tác theo role có thông báo riêng; giữ mã kỹ thuật và không lộ hồ sơ ngoài quyền.
- [x] Bỏ câu nhắc thừa về các hành động chưa thực hiện trong phản hồi.
- [x] Chuyển Markdown sang tiếng Việt và sửa bộ sinh báo cáo để lần chạy sau vẫn tạo tài liệu tiếng Việt.

## Xác minh

Lần kiểm tra mới nhất trên nhánh `team-main` (2026-11-19): **186/186 test pytest đạt** (gồm 180 ca nền, HTTP thật, 2 Node.js UI smoke tests và 6 ca kiểm thử Gemini mock/guard/tool-loop); **62/62 ca evaluation đạt**, không có hồi quy trên tập ca đã lưu. `compileall`, `pip check` và kiểm tra liên kết Markdown không phát hiện lỗi.

Chạy các lệnh trong `README.md`; xem kết quả mới nhất ở `eval/reports/after.md` và `eval/reports/regression.md`. Số lượng test được xác định bởi pytest lúc chạy. Các mốc lịch sử (53 test ngày 2026-11-16, 69/96/109 test ngày 2026-11-17, 150/169/180 test ngày 2026-11-18) chỉ mang tính đối chiếu.

Evaluator có 62 ca xác định, gồm nguyên 31 prompt web. Baseline là lần đo đầu tiên sau khi triển khai, không phải số đo trước khi dự án tồn tại; không suy diễn thành mức cải thiện lịch sử.

## Kế hoạch mở rộng — Tích hợp Gemini API

Mục tiêu: nâng cấp project thành **Hybrid AI Agent** dùng Gemini API (`google-genai`) theo kiến trúc dual-backend (`RuleBased` mặc định cho offline/CI, `Gemini` tùy chọn qua biến môi trường), giữ nguyên 100% lớp kiểm soát tất định (`dispatcher.py`, `registry.py`, `calculate_expense_summary.py`, `validate_trip_requirements.py`, approval gate và strict `HANDOFF_STAFF` template).

### Pre-Phase 1 — Chuẩn bị & dọn nền (Đã hoàn thành trên `team-main`)

- [x] Dọn `data/audit_events.json` về đúng 2 bản ghi seed gốc (`EVT-SEED-001`, `EVT-SEED-002`), loại bỏ dữ liệu demo/test chạy thử bị commit nhầm.
- [x] Bổ sung che Google Gemini API key (`AIza...`) và token (`sk-...`, `ghp_...`, `Bearer ...`) vào `_SECRET_LIKE` trong `src/travel_agent/logging_utils.py` kèm test hồi quy.
- [x] Rà soát và đồng bộ tài liệu/liên kết: đổi tên `demo/DEMO_WEBmd` -> `demo/DEMO_WEB.md`, sửa liên kết hỏng trong `README.md` (`demo/DEMO_WEB.md`, `src/travel_agent/schemas/`) và đồng bộ `TODO.md`.

### Phase 1 — Chuẩn bị SDK/Config, Tầng NLU Structured Output & Budget/Timeout

- [x] Bổ sung dependency `google-genai` vào `requirements.txt` / `pyproject.toml`.
- [x] Thêm cấu hình vào `src/travel_agent/config.py`: `TRAVEL_AGENT_LLM_BACKEND` (`rule` | `gemini`), `GEMINI_API_KEY` (chỉ đọc từ env, không ghi vào trace/audit/CSV), `TRAVEL_AGENT_GEMINI_MODEL` (mặc định `gemini-2.5-flash`), `TRAVEL_AGENT_GEMINI_TIMEOUT`, và ngân sách bước tổng cho mỗi tin nhắn (`TOTAL_TURN_MAX_STEPS` / `TurnBudget`).
- [x] Tạo `src/travel_agent/llm.py` với interface thống nhất (`RuleBasedBackend` + `GeminiBackend`) và adapter sạch tách khỏi `_single_turn()` trong `conversation.py`.
- [x] Chạy lớp guard vòng 1 của `nlu.py` (`_SAFETY_PATTERNS`, malformed ID) trước khi gọi Gemini; dùng Gemini Structured Output (`response_mime_type="application/json"` + `response_json_schema`) để trích xuất `RouteDecision` cho câu tự nhiên, tiếng Việt có dấu/đại từ và ý định đa nghĩa.
- [x] Cài đặt fallback tự động về `nlu.route_message_intent()` hoặc `HANDOFF_STAFF` khi Gemini API lỗi, timeout hoặc `429`.

### Phase 2 — RAG 1-Hop Query Rewrite & Grounded Narrative (có Hậu kiểm)

- [x] Mở rộng 1-hop Query Rewrite (`<= 1` lần, `<= 200` ký tự, ghi `transition="query_rewrite"` vào `trace`) bằng Gemini khi `search_travel_policy` trả `no_result: true` hoặc truy vấn tiếng Việt ngoài từ điển cố định.
- [x] Cho phép Gemini viết lại câu trả lời tự nhiên ở tuyến `SELF_SERVE` dựa trên JSON verified facts và citations; giữ nguyên template cứng cho `HANDOFF_STAFF`, `CLARIFY`, `REJECT_SAFETY`.
- [x] Xây dựng Post-Generation Guard (`check_generated_response`): kiểm tra giữ đủ citation và chặn khẳng định `"approved"` khi `trip_approval_status != "approved"`, tự fallback về formatter deterministic nếu vi phạm.

### Phase 3 — Gemini Function Calling / Agent Tool-Use Loop (theo góp ý `Report/report.md`)

- [x] Cho phép Gemini đề xuất tên tool và arguments từ `registry.py` qua `dispatcher.py` (application vẫn cấp `user_context`, kiểm tra RBAC/scope/JSON Schema và quyết định bước dừng).
- [x] Ghi đầy đủ vết đề xuất tool của model (`llm_tool_proposal`), kết quả `dispatcher`, observation và quyết định bước tiếp theo trong `RunState.trace`, bị giới hạn bởi tổng budget toàn tin nhắn và timeout.

### Phase 4 — Testing (Mocked + Live) & Evaluation

- [x] Giữ nguyên toàn bộ 180 `pytest` và 62 ca `eval/run_eval.py` chạy mặc định với `TRAVEL_AGENT_LLM_BACKEND=rule` (offline, miễn phí, repeatable).
- [x] Tạo `tests/test_llm_gemini.py` dùng Mock Gemini Client kiểm chứng: JSON NLU parsing, timeout/`429` fallback, 1-hop query rewrite, tool-use loop qua `dispatcher`, Post-Generation Guard và injection resistance.
- [x] Tạo `eval/run_eval_llm.py` (`--backend rule|gemini|both`) trên tập câu độc lập (paraphrase, tiếng Việt tự nhiên, phủ định, xung đột policy, injection) — đã xác minh chạy baseline/guard không key; chờ chạy live với `GEMINI_API_KEY` thật khi nghiệm thu online.

### Phase 5 — Cập nhật Web Demo UI & Tài liệu

- [x] Bổ sung bộ chọn/badge backend (`RuleBased` vs `Gemini`) trên `src/travel_agent/web_demo.py` kèm hiển thị `llm` (`latency_ms`, `fallback_used`, `query_rewritten`, `tool_loop_steps`) và `total_step_budget` trong `Memory & Trace`.
- [x] Cập nhật `README.md`, `TODO.md` và `CHANGELOG.md` sau khi hoàn thành tích hợp.

## Chỉ cần khi mở rộng dự án

- [ ] Thêm kiểm tra căn cứ ngữ nghĩa để hỗ trợ diễn đạt lại và quy định phức tạp.
- [ ] Thay tài khoản demo bằng đăng nhập và phân công phê duyệt thật.
- [ ] Dùng cơ sở dữ liệu, kiểm soát ghi đồng thời, mã hóa và chính sách lưu/xóa log phù hợp vận hành.
- [ ] Bổ sung tổng budget cho toàn bộ tin nhắn, timeout cưỡng chế và đo hiệu quả trên nhiều dữ liệu hơn.
- [ ] Tích hợp LLM hoặc dịch vụ bên ngoài chỉ khi có yêu cầu mở rộng phạm vi rõ ràng.

Đặt vé, thanh toán, hoàn tiền, gửi email, chạy lịch nền và dùng dữ liệu cá nhân thật vẫn nằm ngoài phạm vi mini-project.
