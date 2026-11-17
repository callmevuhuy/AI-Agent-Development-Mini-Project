# Đặc tả các quy trình

## Trạng thái và nguồn dữ liệu

Các kết quả cuối: `completed | needs_input | needs_human | awaiting_approval | partial | failed_validation | failed_delivery | failed_budget`.

`trip_approval_status` lấy từ `approvals.json`. Trạng thái yêu cầu review trong `approval_requests.json` được quản lý riêng. Tool chỉ tạo pending; quyết định thuộc helper mô phỏng bên ngoài tool set. Draft có `draft_status=draft_created`, `delivery_status=not_sent|not_published`. Các bước vòng đời tương lai như `publish_requested` và `published` chưa được triển khai thật.

Một run giữ `run_id, workflow, phase, user_context, step_count, max_steps, safe_tool_results, trace, outcome`. Mỗi lần thử gọi tool tăng số bước; chỉ lỗi retryable được retry tối đa hai lần. Hết budget dừng `failed_budget`. Trace giữ tham số đã lọc, mã/thông báo lỗi an toàn và kết quả; không giữ raw query hoặc bí mật.

## Định tuyến theo nhu cầu

| Nhu cầu | Xử lý |
|---|---|
| Lời chào | Trả đúng chức năng của role hiện tại |
| Dữ kiện chuyến/hành trình/duyệt | Tool đọc mock, không dùng memory làm nguồn dữ kiện |
| Chính sách | `search_travel_policy`, có căn cứ và citation |
| Thiếu hoặc nhiều ID phù hợp | Hỏi lại bằng `needs_input` |
| Dữ kiện kèm chính sách | Lấy dữ kiện trước, tra policy có điều kiện |
| Tạo yêu cầu phê duyệt | Chỉ khi Employee yêu cầu tường minh |
| Ra quyết định phê duyệt | Từ chối thao tác qua chat với thông báo riêng theo role |

## A. Chuẩn bị trước chuyến đi

Allowlist: `get_trip_request`, `get_approval_status`, `get_traveler_profile`, `list_my_trips`, `search_travel_policy`, `validate_trip_requirements`, `create_travel_checklist_draft`, `request_approval` và các tool preference.

1. Kiểm tra ID: thiếu → `needs_input`; sai định dạng → `failed_validation`.
2. Lấy chuyến bằng `get_trip_request`; không tồn tại → `not_found`; ngoài quyền → từ chối scope.
3. Kiểm tra trường bắt buộc; lấy trạng thái duyệt bằng `get_approval_status`.
4. Chặn sớm chuyến hủy hoặc phê duyệt bị từ chối → `needs_human`.
5. Tra các danh mục policy bắt buộc theo điểm đến, tối đa 5 kết quả mỗi lần.
6. Gọi `validate_trip_requirements` với facts và evidence; tạo checklist draft khi đủ điều kiện lưu.
7. Kết quả: đủ dữ liệu/evidence và nguồn approved → `completed`; pending thật → `awaiting_approval`; thiếu trường → `needs_input`; thiếu căn cứ hoặc xung đột → `needs_human`. Pending chỉ trả preview, không lưu checklist draft; rejected/cancelled dừng trước bước ghi.

Không khẳng định đã duyệt nếu nguồn chưa trả approved. Lỗi lookup phụ đã được workflow xử lý không được ghi đè lý do dừng nghiệp vụ.

## B. Hỗ trợ sự cố trong chuyến đi

Allowlist: `get_itinerary`, `get_traveler_profile`, `list_my_trips`, `search_travel_policy`, `create_escalation_or_support_draft`, `request_approval` và các tool preference.

1. Kiểm tra ID và quyền.
2. Đọc itinerary, xác định sự cố từ observation; không suy đoán trường không có.
3. Không có sự cố → báo kết quả theo nguồn. Có hoãn/hủy → tra policy hỗ trợ.
4. Tạo bản nháp, tách dữ kiện hành trình khỏi hướng dẫn chính sách có căn cứ.
5. Hướng dẫn đủ → `completed`; hủy chuyến, thiếu hướng dẫn hoặc cần quyết định ngoài thẩm quyền → `needs_human`.

## C. Rà soát chi phí sau chuyến đi

Allowlist: `get_expense_report`, `get_traveler_profile`, `list_my_trips`, `list_my_expenses`, `calculate_expense_summary`, `search_travel_policy`, `create_expense_review_draft` và các tool preference.

1. Kiểm tra ID và quyền; đọc báo cáo.
2. Tool tính tổng, tỷ lệ, cờ ngưỡng, chứng từ và trường thiếu.
3. Tra policy chỉ cho những danh mục thực sự có trong báo cáo.
4. Tạo draft với facts, căn cứ và mục cần Reviewer xem xét.
5. Kết quả: hợp lệ → `completed`; thiếu thông tin/chứng từ → `needs_input`; vượt ngưỡng hoặc xung đột → `needs_human`.

## Draft và lỗi giữa chừng

Draft ghi JSON vào `data/drafts/`, ID ổn định theo `(workflow, source_id)`; retry cập nhật cùng bản. Nếu bước sau lỗi, không báo hoàn thành chung chung: trả `partial`, `failed_budget` hoặc kết quả phù hợp và giữ chi tiết lỗi. Workflow không tự tạo pending ngầm.

## Tạo pending và đọc quản trị

`request_approval(trip_id, action_type, action_summary)` chỉ dành cho Employee sở hữu chuyến. Cặp ID/action lặp lại trả yêu cầu cũ; yêu cầu đã resolved không được tạo lại. Chat phân biệt thao tác tạo pending với quyết định approve/reject.

Admin chỉ dùng `admin_list_trips`, `admin_get_audit_history` ở lớp tool; tải CSV và reset demo là chức năng application. Reviewer dùng `list_my_trips` để xem toàn bộ dữ liệu được cấp; Employee dùng cùng tool nhưng chỉ thấy chuyến của mình.

## RAG và Approver

Lọc `allowed_roles` trước BM25, kiểm tra phiên bản và tạo citation. Approver chỉ đọc đúng pending scope và danh mục theo action. Nếu không có evidence hoặc có xung đột, chuyển `needs_human`, không báo completed. Kiểm tra claim hiện dựa trên từ khóa, cùng câu và cùng cực tính, chưa phải suy luận ngữ nghĩa.

## Bốn tuyến hội thoại

- `SELF_SERVE`: tác vụ hợp lệ, lời chào, danh sách theo quyền, preferences, policy và pending request tường minh.
- `CLARIFY`: thiếu ID, ngày không khớp, nhiều hồ sơ phù hợp hoặc thiếu trường/chứng từ.
- `HANDOFF_STAFF`: cần người xem xét; mẫu cố định `[HANDOFF TO STAFF | Ticket: HND-...]`, chỉ có facts và citation đã xác minh; ghi hàng đợi demo.
- `REJECT_SAFETY`: injection, ID sai, ngoài scope hoặc thao tác bị cấm theo role. Phản hồi scope dùng chung; lỗi role mô tả đúng thao tác. Không kèm câu nhắc thừa về việc agent chưa thực hiện.

## Cập nhật workspace và phản hồi

Trips có bốn tác vụ riêng: xem chi tiết, xem hành trình, kiểm tra checklist và yêu cầu hỗ trợ. Admin xem audit liên quan; Approver xem danh sách pending được phân công trong Trips, rồi đọc hồ sơ theo scope qua chat. Chọn tác vụ gửi đúng ý định, không ghép đọc dữ kiện với checklist. Ngữ cảnh phiên giữ tác vụ cần làm rõ và ngôn ngữ khi người dùng trả lời bằng ID.

Draft giữ mã `DR-…` độc lập với Trip/Expense nguồn. Employee chủ hồ sơ và Reviewer được mở đầy đủ dữ kiện nguồn, hành trình, các trường thiếu và nội dung/citation bản nháp. Chỉ ghi chú, mục đích đề xuất và checklist đề xuất được sửa. Các API `/api/draft/detail`, `/api/draft/save`, `/api/draft/recheck` kiểm tra quyền tại server; không cho sửa identity, approval, dữ kiện nguồn hoặc citation. Kiểm tra lại dùng nguồn thật của mock; nội dung đề xuất được giữ qua lần tạo lại, không tự làm nguồn đầy đủ.

Thông báo không có chức năng không tự tạo phiếu. Pending hiển thị riêng với trạng thái chuyến; yêu cầu hỗ trợ có trạng thái riêng trên Trips. Thẻ prompt dùng nhãn kết quả mong đợi và mã CASE. Các nhánh an toàn kiểm tra nguyên câu tiếng Việt trước lookup/clarification.

Evaluator bổ sung 31 thẻ web vào 31 ca nền; tỷ lệ chọn tool và arguments đo trên các thẻ, số bước/retry lấy từ trace. Task completion loại các ca safety khỏi mẫu số. Grounding vẫn chỉ có claim đại diện; chưa phải benchmark ngữ nghĩa rộng.
