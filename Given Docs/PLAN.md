# Kế hoạch và quyết định thiết kế

## 1. Lựa chọn chính

| Vấn đề | Lựa chọn hiện tại | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.11 trở lên | Thuận tiện cho mock, JSON Schema và pytest |
| Planner | Dual-backend: Quy tắc xác định (`rule` mặc định) + Gemini API (`gemini` tùy chọn) | Offline lặp lại được; hỗ trợ NLU & Tool Loop khi bật API |
| Truy xuất | BM25 ngoại tuyến, lọc category và ACL | Dễ giải thích và kiểm chứng |
| Lưu trữ | File JSON/CSV cục bộ | Phù hợp nguyên mẫu, dễ xem dữ liệu |
| Điều phối | Theo phase, mỗi workflow một module | Dễ truy vết điều kiện dừng |
| Bản nháp | JSON với ID ổn định và ghi nguyên tử | Thử lại không tạo trùng |

## 2. Phần xác định và phần có thể mở rộng bằng LLM

Kiểm tra ID, schema, quyền, tính toán, approval gate, trạng thái, budget, retry, draft và trace luôn chạy bằng code xác định ngay cả khi bật LLM. Các việc như nhận diện cách diễn đạt, đề xuất tool/arguments qua Function Calling, viết lại truy vấn RAG và diễn giải câu trả lời được hỗ trợ qua backend tùy chọn ở `src/travel_agent/llm.py` (`RuleBased` mặc định / `Gemini API` khi có `GEMINI_API_KEY`), vẫn đi qua cùng `dispatcher.py` và hậu kiểm citation/approval.

## 3. Lộ trình mười ngày ban đầu

| Ngày | Công việc | Sản phẩm và hạng mục chấm |
|---|---|---|
| 1 | Đọc đề, chốt hợp đồng và kiến trúc | Khung mã/tài liệu; xác định bài toán 10% |
| 2 | Dữ liệu tối thiểu và mock systems | 6 chuyến, 4 nhân viên, ít nhất 4 itinerary, 3 báo cáo, kho policy |
| 3 | Wrapper, schema, registry, dispatcher | Hệ thống giả lập/function calling 20%, tính chung ngày 2–3 |
| 4 | State, trace, budget, retry, kết quả cuối | Nền tảng workflow/trạng thái 15% |
| 5 | Quy trình C rồi A | Hai luồng chạy xuyên suốt |
| 6 | Quy trình B, approval và ba draft | Tự động hóa/bản nháp 10% |
| 7 | RAG, citation, căn cứ, injection, phiên bản | Truy xuất/căn cứ 15% |
| 8 | Memory, đồng ý, cách ly và role/scope | Memory/an toàn 15% |
| 9 | Ít nhất 15 ca, evaluator và nguyên nhân gốc | Đánh giá/gỡ lỗi 15% |
| 10 | Sửa lỗi, báo cáo sau sửa/hồi quy và demo | Kiểm tra toàn bộ tiêu chí |

Nếu thiếu thời gian, giảm độ trau chuốt hoặc backend tùy chọn; không bỏ ba workflow, dispatcher/schema/quyền/budget/trace, RAG có citation/kết quả rỗng, memory/cách ly, ba draft và các test bắt buộc. Bảy trọng số chỉ tính một lần, tổng 100%.

## 4. Mốc kiểm tra và trạng thái

- M1: gọi tool qua dispatcher, chặn tool/trường lạ và ID sai.
- M2: ba quy trình chạy xuyên suốt với planner quy tắc.
- M3: citation truy vết được, memory và scope cách ly đúng.
- M4: test nghiệm thu, số đo, nguyên nhân gốc, báo cáo trước/sau/hồi quy, demo.

Các mốc cốt lõi đã triển khai. Ngày 2026-11-16 có 53 test và 31/31 ca đánh giá, lookup tự nhiên, memory hội thoại, CSV và web demo. Ngày 2026-11-17 rà lại ma trận role/thao tác, sửa các luồng chat bị định tuyến sai, bỏ câu nhắc thừa trong phản hồi và Việt hóa toàn bộ Markdown. Xem pytest và báo cáo sau sửa để biết kết quả hiện tại; số test của các mốc cũ chỉ mang ý nghĩa lịch sử.

## 5. Rủi ro và giảm thiểu

| Rủi ro | Biện pháp và giới hạn |
|---|---|
| Diễn đạt không khớp mẫu | Planner quy tắc ổn định nhưng chưa hiểu ngôn ngữ tổng quát |
| Điểm truy xuất cao nhưng claim sai | Kiểm tra claim/evidence riêng; hiện chỉ là baseline từ khóa |
| Mở rộng quá phạm vi | Ưu tiên mốc nghiệm thu, giữ thao tác tác động ở draft/pending |
| Retry tạo trùng draft | ID từ workflow/nguồn, cập nhật cùng bản |
| Lộ thông tin trong lỗi | Scope dùng thông báo chung, trace và CSV lọc trường/mẫu nhạy cảm |
| Nhầm thao tác theo role | Ma trận chat cả happy case và ca bị từ chối; lỗi nêu đúng thao tác |
| Báo cáo lại thành tiếng Anh | Bộ sinh báo cáo dùng tiếng Việt, giữ mã trường và case |

## 6. Câu tự kiểm tra

1. Bỏ LLM: validation, dispatcher, tính chi phí, approval gate, state và draft vẫn chạy.
2. Policy nói có thể xem xét không đồng nghĩa đã duyệt; chỉ nguồn approval được xác nhận mới quyết định trạng thái.
3. Itinerary mới từ mock tool ưu tiên hơn ngữ cảnh cũ.
4. Tool/trường ngoài hợp đồng bị chặn trước thực thi và có trace.
5. Không có evidence thì nói rõ giới hạn, cần người kiểm tra, không suy đoán hoặc tạo citation.
6. Trace phải giúp phân biệt lỗi định tuyến, trích tham số, tool, xử lý observation, trạng thái, retry, căn cứ và an toàn.

## 7. Nhật ký quyết định

| Mã | Quyết định | Tác động |
|---|---|---|
| D1 | Tool approval chỉ tạo pending | Agent không tự quyết định |
| D2 | Một schema cho ID/action/summary, khóa không trùng ID/action | Registry, wrapper và test dùng chung |
| D3 | Context do application cung cấp | Model không tự cấp quyền |
| D4 | Sơ đồ tổng thể và ba workflow | Đáp ứng kiến trúc bàn giao |
| D5 | Section là locator chính, page có thể null | Citation truy vết, không bịa trang |
| D6 | Tách trạng thái chuyến, yêu cầu và draft | Tránh nhận nhầm đã duyệt/đã phát hành |
| D7 | Luật điều kiện trong requirements.json | Kiểm tra nghiệp vụ xác định |
| D8 | Xung đột active cần người xử lý | Không tự chọn phiên bản thuận tiện |
| D9 | Bám bảy trọng số đề bài | Tổng 100% |
| D10 | Approver đọc một scope pending theo action | Quyền tối thiểu, test cho phép và từ chối |
| D11 | Lỗi scope chung, lỗi thao tác riêng theo role | Phản hồi gọn và đúng nguyên nhân |
