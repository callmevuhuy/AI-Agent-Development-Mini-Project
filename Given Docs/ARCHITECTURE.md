# Kiến trúc hệ thống

## 1. Luồng tổng thể

Model hoặc planner chỉ đề xuất lời gọi. Application gắn danh tính; dispatcher xác thực; tool là ranh giới đọc/ghi dữ liệu nghiệp vụ giả lập. Memory hỗ trợ nối hội thoại và không thay thế nguồn nghiệp vụ.

```mermaid
flowchart TD
    U[Người dùng và tài khoản demo] --> APP[Application: danh tính, phiên và scope]
    APP --> CONV[Nhận diện ý định và điều phối hội thoại]
    CONV --> PLAN[Planner đề xuất tool và arguments]
    PLAN --> DISP[Dispatcher: registry, allowlist, schema, quyền, budget]
    DISP -->|Từ chối| ERR[Lỗi chung theo scope hoặc lỗi thao tác theo role]
    DISP -->|Hợp lệ| TOOL[Wrapper công cụ]
    TOOL --> MOCK[Hệ thống nghiệp vụ giả lập]
    TOOL --> RAG[Kho policy: ACL, BM25, căn cứ và citation]
    TOOL --> DRAFT[Bản nháp JSON có ID ổn định]
    CONV <--> MEM[Memory theo user và session]
    CONV --> TRACE[Trace an toàn và kết quả cuối]
    CONV --> OUT[Phản hồi hoặc yêu cầu người xử lý]
```

`nlu.py` nhận diện mẫu Anh–Việt, ID/ngày/điểm đến và bốn tuyến. `conversation.py` chọn nhánh theo role, nối ngữ cảnh, chạy workflow và định dạng. `orchestrator.py` đếm lần thử, retry và ghi trace; `dispatcher.py` kiểm tra lời gọi trước khi thực thi. `errors.py` tập trung cách diễn đạt lỗi.

## 2. Quy trình A: trước chuyến đi

```mermaid
flowchart TD
    A[Kiểm tra ID] --> B[Lấy chuyến đi]
    B --> C[Kiểm tra trường bắt buộc]
    C --> D[Lấy trạng thái duyệt]
    D --> E{Có điều kiện chặn?}
    E -->|Hủy hoặc từ chối| H[Cần người xem xét]
    E -->|Không| F[Tra policy và kiểm tra điều kiện]
    F --> G[Tạo checklist draft]
    G --> I[Hoàn tất, chờ duyệt hoặc cần bổ sung]
```

ID sai, không có hồ sơ, ngoài quyền và lỗi tool dừng ở nhánh tương ứng. Trạng thái pending chỉ được phản ánh khi nguồn thực sự trả pending. Thiếu căn cứ/xung đột cần người xử lý.

## 3. Quy trình B: trong chuyến đi

```mermaid
flowchart TD
    A[Kiểm tra ID và quyền] --> B[Lấy hành trình]
    B --> C{Có sự cố?}
    C -->|Không| D[Trả dữ kiện nguồn]
    C -->|Có| E[Tra policy hỗ trợ]
    E --> F[Tạo draft tách facts và hướng dẫn]
    F --> G[Hoàn tất hoặc cần người xem xét]
```

## 4. Quy trình C: sau chuyến đi

```mermaid
flowchart TD
    A[Kiểm tra ID và quyền] --> B[Lấy báo cáo]
    B --> C[Tool tính tổng, kiểm tra ngưỡng và chứng từ]
    C --> D[Tra policy theo danh mục thực tế]
    D --> E[Tạo draft rà soát]
    E --> F[Hoàn tất, cần bổ sung hoặc cần người xem xét]
```

## 5. Ranh giới dữ liệu và quyền

Agent không đọc file nghiệp vụ tùy ý. Application có quyền đọc danh tính, trạng thái giao diện và ghi log; tool wrapper gọi mock systems. Context gồm `user_id`, `role`, `session_id`, có thể thêm `approval_scope` đang pending. Model không được tự khai danh tính trong arguments.

Employee chỉ thấy hồ sơ của mình; Reviewer rà soát dữ liệu được cấp; Approver chỉ đọc đúng loại facts và policy phục vụ scope; Admin chỉ có tool đọc tổng quan/audit. Các API web áp dụng quyền riêng ở server, không chỉ ẩn nút trên giao diện.

## 6. RAG, approval và audit

`request_approval` dành cho Employee sở hữu chuyến, tạo pending không trùng theo cặp ID/action. Quyết định do helper bên ngoài tool set ghi cùng audit có người thực hiện, lý do, thời điểm và run ID.

Kho policy lọc `allowed_roles` trước chấm BM25, phân tích phiên bản và citation. Approver còn bị giới hạn danh mục theo action. Thiếu evidence hoặc xung đột không được biến thành câu trả lời completed.

Hội thoại có bốn tuyến: `SELF_SERVE`, `CLARIFY`, `HANDOFF_STAFF`, `REJECT_SAFETY`. Handoff ghi phiếu mô phỏng trong CSV, không đồng nghĩa đã gửi cho người thật. Trace và CSV hội thoại tách biệt khỏi audit nghiệp vụ.
