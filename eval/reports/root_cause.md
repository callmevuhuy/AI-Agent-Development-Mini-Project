# Phân tích nguyên nhân gốc và nhóm lỗi

Tài liệu phục vụ mục 13.3 và 14.7 của đề bài. Các nhóm lỗi mô tả nguyên nhân và cách kiểm chứng, không đồng nghĩa mọi khả năng đều đã xảy ra trong vận hành.

## 1. Tám nhóm lỗi

| Nhóm | Tình huống | Nguyên nhân | Cách xử lý và bằng chứng |
|---|---|---|---|
| Định tuyến | Câu tự nhiên không ID, câu hỏi nhiều ý hoặc thao tác ngoài quyền | Chọn nhầm workflow hoặc nhầm dữ kiện với hành động | NLU bốn tuyến; test lookup, role, yêu cầu pending và quyết định approval |
| Trích tham số | ID thiếu, sai hoặc không tồn tại | Định dạng và hồ sơ không khớp | Schema/regex; T04, T05, T06 |
| Triển khai tool | Tổng sai, tool gọi ngầm nguồn khác làm mất dấu vết | Tính toán hoặc ranh giới trách nhiệm chưa rõ | Tool tính toán xác định; đọc approval qua tool riêng; test chi phí |
| Xử lý observation | Xung đột danh mục không liên quan vẫn chặn báo cáo; lỗi phụ ghi đè lý do chính | Dùng observation không đúng vai trò trong workflow | Chỉ kiểm tra danh mục có trong báo cáo; không đưa lỗi phụ đã xử lý lên làm lỗi cuối |
| Trạng thái/chuyển bước | Tiếp tục sau chuyến hủy hoặc approval bị từ chối | Kiểm tra điều kiện dừng sai thứ tự | Chặn sớm theo nguồn; test pending/rejected/cancelled |
| Dừng/thử lại | Retry vô hạn hoặc vượt budget | Thiếu giới hạn lần thử và bước | Orchestrator retry tối đa hai lần, dispatcher kiểm tra budget; T10, T11 |
| Căn cứ/trích dẫn | Claim không được chunk hỗ trợ | Nhầm điểm BM25 cao với tính đúng ngữ nghĩa | Kiểm tra từ khóa/cùng câu/cùng phủ định, giữ metadata; T08, T18 |
| An toàn/quyền | User hoặc chunk tiêm chỉ thị, truy cập chéo | Tin đầu vào như chỉ thị hoặc lọc quyền quá muộn | ACL trước ranking, dispatcher kiểm tra role/scope, memory cách ly; T12–T16 |

## 2. Các cải tiến đã thực hiện

### Chuỗi trước chuyến đi

Tách đọc trạng thái duyệt khỏi kiểm tra điều kiện để trace thể hiện rõ `get_trip_request` → `get_approval_status` → policy → validator → draft. Budget phụ thuộc số danh mục và cách gọi; mặc định state 8, chat pre-trip/mixed 10, trần cấu hình 12. Không khẳng định mọi lượt đều đúng 8 bước.

### ACL policy

Lọc role trước BM25, phiên bản và citation để chunk ngoài quyền không rò qua kết quả phụ. Approver phải có request pending và category theo action. Xem `src/travel_agent/mock_systems/policy_kb.py` và `dispatcher.py`.

### Chi phí và ngày bay

Khoản meals nằm trong mọi hạn mức active không được đánh cờ vượt ngưỡng. Conflict của meals không chặn báo cáo chỉ có lodging. Lookup chuyến bay phải dùng ngày departure/arrival, không chỉ kiểm tra ngày hỏi thuộc khoảng công tác.

### Rà soát hội thoại ngày 2026-11-17

| Phát hiện | Sửa | Test hồi quy |
|---|---|---|
| Employee hỏi danh sách bị chuyển sang Admin | Dùng list_my_trips theo chủ hồ sơ | Bốn Employee chỉ thấy các ID của mình |
| Approver quản lý preference bị chuyển sang scoped review | Cho nhánh preference đi đúng memory tool | Lưu tùy chọn khi không cần scope nghiệp vụ |
| Tạo pending và quyết định approval bị lẫn với handoff | NLU phân biệt hai intent; chỉ Employee chủ chuyến được tạo pending | Pending/idempotency; policy question không tạo request; role bị cấm không ghi dữ liệu |
| Admin/Approver ID sai bị nhánh role che mất | Kiểm tra route từ chối trước nhánh role | invalid_argument thay vì đọc hồ sơ scope |
| Approver hỏi itinerary nhưng nhận trip facts | Chọn đúng tool cần đọc và để dispatcher từ chối loại thông tin ngoài quyền | Không báo completed với dữ kiện thay thế |
| Lỗi approval lookup phụ ghi đè chuyến hủy | Chỉ đưa lỗi chưa được xử lý lên nhánh lỗi cuối | Employee 004 nhận lý do cần người xem xét |
| Câu lỗi liệt kê toàn bộ quyền | Scope chung; role nêu đúng thao tác và người hỗ trợ | So thông báo chung bằng nhau, lỗi role khác nhau |
| Phản hồi chứa câu nhắc việc chưa làm | Bỏ khỏi template và thông báo thành công | Kiểm tra mọi nhánh role và workflow |
| Markdown tiếng Anh và đường dẫn máy cũ | Việt hóa tài liệu, sửa link và bộ sinh báo cáo | Soát Markdown và chạy lại evaluator |

## 3. Giới hạn của bằng chứng

Pytest xác minh các nhánh cụ thể trong code trên dữ liệu tạm; không chứng minh an toàn production. Evaluator 31 ca dùng quy tắc xác định; phần grounding chỉ có claim đại diện. Chưa có LLM thật, suy luận ngữ nghĩa rộng, đăng nhập production, audit chống sửa hoặc timeout cưỡng chế. Số đo lịch sử giữ nguyên, không được viết lại như kết quả đo trước triển khai.
