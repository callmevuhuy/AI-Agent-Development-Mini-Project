# Bàn giao dự án

## Phạm vi và quy ước làm việc

Dự án Global Business Travel Operations Agent nằm tại thư mục gốc của repository hiện tại. Trước khi sửa hành vi, đọc tài liệu trong `Requirement Docs/` và các tài liệu `Given Docs/AGENTS.md`, `ARCHITECTURE.md`, `WORKFLOWS.md`, `TOOL_CARDS.md`, `DATA_SPEC.md`, `MEMORY_AND_SAFETY.md`.

- Triển khai và kiểm chứng từng hạng mục; báo tiến độ khi có kết quả hoặc vướng mắc đáng kể.
- Báo cáo bằng tiếng Việt: nội dung thay đổi, tệp chính, kết quả kiểm tra, giới hạn và bước tiếp theo.
- Chỉ commit/push khi chủ dự án yêu cầu.
- Dữ liệu hoàn toàn giả lập. Danh tính và phạm vi quyền do application cung cấp; arguments của model không được tự đặt role, user hoặc scope.
- Claim chính sách phải có căn cứ; văn bản truy xuất là dữ liệu không đáng tin cậy, không thể cấp quyền hành động.
- `request_approval` chỉ tạo pending. Quyết định phê duyệt do hệ thống mô phỏng bên ngoài tool set thực hiện.

## Các mốc đã triển khai

| Mốc | Kết quả |
|---|---|
| 1. Dữ liệu và hệ thống giả lập | Dữ liệu chuyến, nhân viên, hành trình, phê duyệt, chi phí và policy; điểm đi Hà Nội (HAN) |
| 2. Công cụ và dispatcher | JSON Schema, 19 tool, registry, allowlist, kiểm tra role/scope, lỗi có cấu trúc và budget |
| 3. Trạng thái và quy trình | RunState, trace, retry, ba workflow A/B/C, bản nháp có ID ổn định |
| 4. RAG | BM25 ngoại tuyến, từ đồng nghĩa tiếng Anh, trích dẫn metadata, loại injection, kiểm tra từ khóa/phủ định và xung đột phiên bản |
| 5. Memory và Approver | Session có TTL, preferences theo user, ghi/xóa có đồng ý, Approver chỉ đọc scope pending |
| 6. Kiểm thử và demo | Pytest, evaluator 31 ca, báo cáo trước/sau, hồi quy, CLI và web demo |

Ngày 2026-11-16 hoàn thiện định tuyến bốn luồng, lookup tự nhiên, kiểm tra ngày bay, chi tiết nhân viên, thông tin thiếu, memory hội thoại và CSV UTF-8 BOM. Mốc đó ghi nhận 53 test; các số này là lịch sử, không phải số test hiện tại.

Ngày 2026-11-17 rà lại hội thoại theo mọi role: danh sách Employee đúng sở hữu; Approver quản lý preferences đúng luồng; tạo pending tường minh qua chat; từ chối quyết định phê duyệt qua chat; phân biệt lỗi scope chung với lỗi thao tác theo role. Bỏ câu nhắc về hành động chưa làm khỏi phản hồi. Toàn bộ tài liệu Markdown của dự án chuyển sang tiếng Việt, giữ tên tool, trường dữ liệu và lệnh thực thi.

## Chi tiết cần giữ khi tiếp tục

- Workflow nằm trong `src/travel_agent/workflows/`; nguồn nghiệp vụ lấy qua tool. `RunState.user_context` thuộc application.
- Mỗi lần thử gọi tool tiêu tốn một bước. Mặc định 8, trần 12; luồng chat pre-trip/mixed dùng 10. Retry tối đa hai lần với lỗi được đánh dấu retryable. Lookup phụ có state riêng.
- Bản nháp lưu JSON tại `data/drafts/`, ID dựa trên `(workflow, source_id)`; chạy lại cập nhật cùng bản. Chỉ báo đã lưu khi tool xác nhận thành công.
- Kho policy cố ý có xung đột hạn mức ăn uống và chunk kiểm thử injection. Không âm thầm bỏ xung đột hoặc dùng injection làm evidence.
- Preferences chỉ ghi khi `memory_write_authorized=true` do application đặt. Session có TTL; memory không giữ trạng thái nghiệp vụ làm nguồn sự thật.
- Approver cần scope chính xác `{trip_id, action_type}` gắn với một bản ghi pending hiện tại; công cụ đọc phụ thuộc action.
- Admin có chức năng reset runtime trên web, nằm ngoài tool set nghiệp vụ. Audit JSON cục bộ không phải kho bất biến production.
- Lỗi scope dùng câu chung không lộ chủ hồ sơ. Lỗi role nêu đúng thao tác và người hỗ trợ, giữ mã `unauthorized_scope`.

## Kiểm tra lại

```powershell
.\.venv\Scripts\python.exe -m pytest -v --basetemp .venv/pytest-tmp
.\.venv\Scripts\python.exe eval/run_eval.py --label after
.\.venv\Scripts\python.exe -m compileall -q src tests eval demo
git diff --check
```

Các ca mới nằm trong `tests/test_conversational_and_fixes.py`; kịch bản thủ công ở `demo/DEMO_SCENARIOS.md`. Giữ nguyên thay đổi runtime của người dùng khi sửa mã hoặc chạy test; bộ test dùng dữ liệu tạm.

## Mẫu báo tiến độ

```text
Hạng mục:
Đã hoàn thành:
Tệp thay đổi:
Kiểm tra và kết quả:
Giới hạn hoặc rủi ro còn lại:
Bước tiếp theo hoặc thông tin cần bổ sung:
Commit/push: chỉ thực hiện khi được yêu cầu
```

Lịch sử chi tiết ở `CHANGELOG.md`; danh sách công việc và giới hạn ở `TODO.md`.
