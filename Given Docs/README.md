# Mục lục tài liệu dự án

Đọc yêu cầu gốc trong `Requirement Docs/` trước khi thay đổi hành vi.

| Tệp | Nội dung |
|---|---|
| `AGENTS.md` | Hợp đồng agent và quy tắc triển khai |
| `ARCHITECTURE.md` | Kiến trúc tổng thể và ba quy trình |
| `WORKFLOWS.md` | Các bước, điều kiện dừng và kết quả |
| `TOOL_CARDS.md` | Đặc tả công cụ, arguments và hợp đồng kết quả |
| `DATA_SPEC.md` | Cấu trúc và tình huống dữ liệu giả lập |
| `MEMORY_AND_SAFETY.md` | Memory, quyền và ranh giới an toàn |
| `TEST_MATRIX.md` | Ma trận kiểm thử và tiêu chí đánh giá |
| `PLAN.md` | Kế hoạch, quyết định thiết kế và trạng thái |

Mặc định NLU và BM25 chạy ngoại tuyến bằng quy tắc xác định (`TRAVEL_AGENT_LLM_BACKEND=rule`); hỗ trợ tùy chọn backend Hybrid Gemini API (`src/travel_agent/llm.py`) khi cấu hình `GEMINI_API_KEY`. Tất cả hệ thống và hồ sơ nghiệp vụ đều là giả lập. Tài liệu dùng tiếng Việt; định danh kỹ thuật giữ nguyên để đối chiếu mã nguồn.
