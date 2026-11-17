import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors
    C_PRIMARY = RGBColor(15, 23, 42)      # Slate 900
    C_HEADER_BG = RGBColor(30, 41, 59)    # Slate 800
    C_ACCENT_BLUE = RGBColor(37, 99, 235) # Blue 600
    C_ACCENT_TEAL = RGBColor(13, 148, 136)# Teal 600
    C_TEXT_DARK = RGBColor(51, 65, 85)    # Slate 700
    C_TEXT_MUTED = RGBColor(100, 116, 139)# Slate 500
    C_CARD_BG = RGBColor(248, 250, 252)   # Slate 50
    C_CARD_BORDER = RGBColor(226, 232, 240)
    C_WHITE = RGBColor(255, 255, 255)
    C_GREEN = RGBColor(16, 185, 129)

    def add_header(slide, title_text, category_text="GLOBAL BUSINESS TRAVEL OPERATIONS AGENT"):
        # Header background banner
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = C_ACCENT_BLUE
        
        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = C_PRIMARY

    def add_card(slide, left, top, width, height, title, items, badge="", bg_color=C_CARD_BG):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = C_CARD_BORDER
        shape.line.width = Pt(1)
        
        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.2)
        tf.margin_bottom = Inches(0.2)
        
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(15)
        p_title.font.bold = True
        p_title.font.color.rgb = C_PRIMARY
        
        if badge:
            p_b = tf.add_paragraph()
            p_b.text = badge.upper()
            p_b.font.size = Pt(9)
            p_b.font.bold = True
            p_b.font.color.rgb = C_ACCENT_TEAL
            p_b.space_after = Pt(6)
            
        for item in items:
            p = tf.add_paragraph()
            p.text = f"•  {item}"
            p.font.size = Pt(11)
            p.font.color.rgb = C_TEXT_DARK
            p.space_before = Pt(4)

    def set_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # ==================== SLIDE 1: Title ====================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = C_PRIMARY
    bg1.line.fill.background()

    t_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(3.5))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "MINI-PROJECT PROTOTYPE"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = RGBColor(96, 165, 250)
    
    p = tf1.add_paragraph()
    p.text = "Global Business Travel Operations Agent"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.space_after = Pt(14)
    
    p = tf1.add_paragraph()
    p.text = "Kiến trúc Điều phối An toàn, Function Calling 5 Lớp & Agentic RAG có Grounding"
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(203, 213, 225)
    
    p = tf1.add_paragraph()
    p.text = "Offline Deterministic Architecture  •  Draft Sandbox  •  Zero Real Action  •  Human-in-the-Loop"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_before = Pt(20)

    set_notes(s1, "Kính thưa thầy cô và các bạn, đây là bài thuyết trình về dự án Global Business Travel Operations Agent. Mục tiêu cốt lõi của dự án là chứng minh một Agent thông minh, có bằng chứng, giới hạn quyền hạn tuyệt đối và vận hành an toàn qua mock systems.")

    # ==================== SLIDE 2: Scope & Boundaries ====================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Phạm vi & Ranh giới An toàn (Scope & Boundaries)")
    
    # Core principle banner
    banner = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(0.85))
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(238, 242, 255)
    banner.line.color.rgb = RGBColor(199, 210, 254)
    btf = banner.text_frame
    btf.margin_left = Inches(0.3)
    bp = btf.paragraphs[0]
    bp.text = "Quy tắc cốt lõi: Evidence từ Policy KHÔNG tự cho phép Action."
    bp.font.size = Pt(14)
    bp.font.bold = True
    bp.font.color.rgb = RGBColor(67, 56, 202)
    bp2 = btf.add_paragraph()
    bp2.text = "Mọi tác vụ có ảnh hưởng chỉ dừng ở Draft Sandbox, Needs_Human hoặc Awaiting_Approval."
    bp2.font.size = Pt(11)
    bp2.font.color.rgb = C_TEXT_DARK

    add_card(s2, 0.8, 2.7, 5.7, 4.3, "Trong Phạm vi (In-Scope)", [
        "100% dữ liệu du lịch, nhân viên, lịch trình và chính sách là giả lập.",
        "Hỗ trợ trọn vẹn 3 giai đoạn: Trước, Trong và Sau chuyến công tác.",
        "Tạo Checklist, Escalation Note và Expense Review ở dạng draft sandbox.",
        "Agentic RAG trích dẫn trích đoạn bằng chứng có metadata truy vết.",
        "Mô phỏng phê duyệt (Approval Simulation) dừng ở pending-only.",
        "Phân định rõ terminal outcomes: completed, needs_input, needs_human."
    ], badge="Được phép thực thi")

    add_card(s2, 6.833, 2.7, 5.7, 4.3, "Ngoài Phạm vi (Out-of-Scope)", [
        "TUYỆT ĐỐI KHÔNG đặt, đổi hoặc hủy vé máy bay, phòng khách sạn thật.",
        "KHÔNG nộp visa, mua bảo hiểm, thanh toán hoặc bồi hoàn chi phí thật.",
        "KHÔNG gửi email, tin nhắn hoặc tạo ticket tới người thật.",
        "KHÔNG truy cập API, credential, mật khẩu hay dữ liệu cá nhân thật.",
        "KHÔNG cấp tool set mở, shell tool, background job hoặc scheduler.",
        "Hành động ngoài quyền lập tức chuyển sang Staff Handoff Queue."
    ], badge="Bị cấm nghiêm ngặt", bg_color=RGBColor(254, 242, 242))

    set_notes(s2, "Slide 2 nêu rõ ranh giới an toàn. Điểm mấu chốt: Bằng chứng trong policy không cấp quyền cho Agent tự ý thực hiện hành động. Mọi action thực tế đều là out-of-scope và Agent chỉ tạo draft hoặc yêu cầu con người phê duyệt.")

    # ==================== SLIDE 3: Agent Contract & Mock Systems ====================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Agent Contract & Hệ thống Giả lập (Mock Systems)")

    add_card(s3, 0.8, 1.7, 5.7, 5.3, "Agent Contract Bắt buộc (Mục 4)", [
        "User Roles: Employee, Reviewer, Approver (tách biệt quyền hạn).",
        "Input: Tin nhắn tự nhiên + các mã định danh chuẩn (TRIP-ID, EXP-ID).",
        "Output: Grounded response, draft sandbox, human review ticket.",
        "Source of Truth: Mock Systems (JSON fixtures); không dùng persistent memory cũ để thay thế trạng thái thực tế.",
        "Allowed Tools: Chỉ các tool đã đăng ký trong registry và allowlist.",
        "Forbidden Actions: Booking, payment, refund, shell execution.",
        "Execution Budget: DEFAULT_MAX_STEPS = 8 (trần 12); retry tối đa 2 lần."
    ], badge="Hợp đồng bắt buộc")

    add_card(s3, 6.833, 1.7, 5.7, 5.3, "Dataset Tối thiểu Đạt chuẩn (Mục 6.1)", [
        "6 Travel Requests (trips.json): Đủ valid, missing purpose (TRIP-003), pending (TRIP-001), rejected (TRIP-004), cancelled (TRIP-005).",
        "4 Traveler Profiles (travelers.json): Thuộc 2 phòng ban (Sales, Engineering), không có PII thật.",
        "5 Itineraries (itineraries.json): Có flight delay 240 phút (TRIP-002) và flight cancelled (TRIP-005).",
        "3 Expense Reports (expenses.json): Đủ valid, thiếu receipt/date (EXP-002), vượt định mức/conflict (EXP-003).",
        "13 Policy Chunks (policy_chunks.json): Phủ đủ 5 categories với 7 trường metadata bắt buộc (chunk_id, doc_id, source, section, version, category, text)."
    ], badge="Nguồn dữ liệu chân lý")

    set_notes(s3, "Slide 3 chứng minh hợp đồng nghiệp vụ và bộ dataset tối thiểu. Chúng ta có đầy đủ 6 chuyến đi thể hiện mọi tình huống biên, 4 nhân viên, 5 lịch trình, 3 báo cáo chi phí và 13 policy chunks có đầy đủ 7 metadata.")

    # ==================== SLIDE 4: Function Calling & Dispatcher ====================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Cơ chế Function Calling & Dispatcher 5 Lớp (Mục 7)")

    add_card(s4, 0.8, 1.7, 5.7, 5.3, "Quy tắc Thực thi & Dispatcher (Mục 7.1)", [
        "Nguyên tắc 1: Model chỉ đề xuất tool_name & arguments; không tự chạy code.",
        "Nguyên tắc 2: Phễu kiểm soát 5 lớp trước khi thực thi:",
        "   1. Kiểm tra Tool Registry (đã đăng ký trong hệ thống chưa).",
        "   2. Kiểm tra Workflow Allowlist (tool có thuộc workflow hiện tại).",
        "   3. Kiểm định Draft202012 JSON Schema (additionalProperties=false).",
        "   4. Kiểm tra quyền hạn Role & Scope (User ownership, Approver pending).",
        "   5. Kiểm soát Step Budget (step count < max_steps).",
        "Nguyên tắc 3: Tool chỉ làm một nhiệm vụ hẹp và trả structured result.",
        "Nguyên tắc 4: Agent chỉ dùng tool observation làm bằng chứng sự thật.",
        "Nguyên tắc 5: Cấm tuyệt đối eval(), globals(), shell tool hay SQL text."
    ], badge="Phễu kiểm soát nghiêm ngặt")

    add_card(s4, 6.833, 1.7, 5.7, 5.3, "Quy chuẩn Schema & Result Contract (7.2 & 7.3)", [
        "JSON Schema Chuẩn mực:",
        "   - 100% schema có 'additionalProperties': false.",
        "   - Bắt buộc kiểm tra pattern Regex: ^TRIP-\\d{4}-\\d{3}$.",
        "   - Bất kỳ field lạ nào đều bị từ chối với 'invalid_argument'.",
        "Success Result Contract:",
        "   { 'ok': true, 'data': {...}, 'meta': { 'source': '...', 'read_only': true } }",
        "Error Result Contract:",
        "   { 'ok': false, 'error': { 'code': '...', 'message': '...', 'retryable': bool } }",
        "Toàn bộ kết quả tool đều tuân thủ hợp đồng trên trước khi trả về Orchestrator."
    ], badge="Hợp đồng dữ liệu")

    set_notes(s4, "Slide 4 giải thích cơ chế Dispatcher. Model đóng vai trò planner chỉ đề xuất tên hàm và tham số. Dispatcher thực hiện 5 lớp kiểm định độc lập trước khi cho phép hàm mock chạy, ngăn chặn hoàn toàn rủi ro vượt quyền.")

    # ==================== SLIDE 5: 3 Vertical Workflows ====================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Ba Workflow Nghiệp vụ Dọc Chuẩn hóa (Mục 8)")

    add_card(s5, 0.8, 1.7, 3.65, 5.3, "Workflow A: Pre-trip", [
        "1. validate trip_id",
        "2. get_trip_request",
        "3. get_approval_status (Chuẩn hóa)",
        "4. search_travel_policy theo destination",
        "5. validate_trip_requirements",
        "6. create_travel_checklist_draft",
        "---",
        "Outcomes:",
        "• completed (đã duyệt + đủ bằng chứng)",
        "• awaiting_approval (đang chờ duyệt)",
        "• needs_input (thiếu thông tin)",
        "• needs_human (bị từ chối / hủy)"
    ], badge="Chuẩn bị trước chuyến đi")

    add_card(s5, 4.84, 1.7, 3.65, 5.3, "Workflow B: In-trip", [
        "1. validate trip_id",
        "2. get_itinerary (flight/hotel/disruption)",
        "3. Xác định disruption từ observation",
        "4. search_travel_policy hỗ trợ sự cố",
        "5. create_escalation_or_support_draft",
        "---",
        "Đặc điểm:",
        "• Tách riêng 'Itinerary facts' và 'Policy guidance'.",
        "• KHÔNG tự đổi vé hoặc chi tiền.",
        "• Flight cancelled hoặc thiếu hướng dẫn -> needs_human.",
        "• Delay thông thường -> completed."
    ], badge="Hỗ trợ gián đoạn")

    add_card(s5, 8.88, 1.7, 3.65, 5.3, "Workflow C: Post-trip", [
        "1. validate report_id",
        "2. get_expense_report",
        "3. calculate_expense_summary (Deterministic)",
        "4. search_travel_policy theo category",
        "5. create_expense_review_draft",
        "---",
        "Đặc điểm:",
        "• Tính toán số học 100% bằng code.",
        "• LLM không tự tính từ raw text.",
        "• KHÔNG kết luận 'được hoàn tiền'.",
        "• Thiếu hóa đơn -> needs_input.",
        "• Vượt ngưỡng/conflict -> needs_human."
    ], badge="Rà soát chi phí")

    set_notes(s5, "Slide 5 trình bày 3 workflow cốt lõi. Ở Workflow A, chúng ta đã tuân thủ chuẩn xác chuỗi gọi 6 bước gồm get_approval_status. Ở Workflow C, toàn bộ phép tính toán chi phí được thực hiện deterministic bằng code.")

    # ==================== SLIDE 6: Agentic RAG & Grounding ====================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Agentic RAG, Grounding & Quản lý Phiên bản (Mục 10)")

    add_card(s6, 0.8, 1.7, 5.7, 5.3, "Retrieval Policy & Grounding (10.1 & 10.2)", [
        "Retrieval Routing:",
        "   - Greeting/rephrase: Trả lời trực tiếp, không retrieve.",
        "   - Trạng thái chuyến đi: Gọi mock read tool.",
        "   - Chính sách du lịch/chi phí: Gọi search_travel_policy.",
        "BM25 Offline Engine: Stemming + mở rộng từ đồng nghĩa.",
        "Claim-to-Evidence Grounding (check_claim):",
        "   - Điểm số BM25 KHÔNG tự chứng minh căn cứ đầy đủ.",
        "   - Kiểm tra từng từ khóa (terms) và cực tính (polarity) trong cùng một câu văn bản tin cậy.",
        "   - Không đủ bằng chứng -> Tuyệt đối không phát biểu claim.",
        "Citation đầy đủ: [DOC §Section vVersion · Chunk_ID · p.Page]."
    ], badge="Kiểm soát căn cứ")

    add_card(s6, 6.833, 1.7, 5.7, 5.3, "Xung đột Phiên bản & Query Rewrite", [
        "Quản lý Xung đột Phiên bản (Version Review):",
        "   - Phát hiện xung đột giữa các phiên bản active của cùng section.",
        "   - Ví dụ: POL-EXP-MEAL-V1 ($75) vs POL-EXP-MEAL-V2 ($90).",
        "   - Khi có mâu thuẫn chính sách -> Dừng và chuyển giao needs_human.",
        "Safe Query Rewrite (Hiện thực mới):",
        "   - Tối đa 1 lần trong một workflow branch.",
        "   - Không làm thay đổi ý định hay điểm đến của user.",
        "   - Ghi nhận sự kiện query_rewrite vào safe trace.",
        "Lọc Tiêm nhiễm (Prompt Injection):",
        "   - Tự động loại trừ chunk chứa payload chỉ thị độc hại (POL-EXPENSE-TEST-001)."
    ], badge="Phát hiện xung đột")

    set_notes(s6, "Slide 6 giải thích tính năng Agentic RAG. Khác với tìm kiếm thông thường, hệ thống kiểm định Claim-to-Evidence từng từ vựng, quản lý xung đột phiên bản và hỗ trợ Query Rewrite an toàn có ghi vết trong trace.")

    # ==================== SLIDE 7: State, Memory & Draft Artifacts ====================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "State, Memory & Vòng đời Draft Artifacts (Mục 9 & 11)")

    add_card(s7, 0.8, 1.7, 5.7, 5.3, "State & Phân tầng Memory (Mục 9)", [
        "Run State: Lưu run_id, workflow, phase, user_context, step_count, max_steps, safe_tool_results, trace, outcome.",
        "Phân tách 3 định danh: user_id, session_id, run_id riêng biệt.",
        "Session State (Ngắn hạn):",
        "   - Lưu active_trip_id, active_report_id để tiếp nối ngữ cảnh.",
        "   - Tự động hủy sau thời gian hết hạn (TTL).",
        "Persistent Preference (Dài hạn):",
        "   - Lưu response_language, preferred_output_format.",
        "   - Chỉ ghi khi có sự đồng ý tường minh (memory_write_authorized).",
        "   - Có tool xem (get_preference) và xóa (delete_preference).",
        "Không lưu PII nhạy cảm: Hộ chiếu, số thẻ thanh toán, token."
    ], badge="Quản lý bộ nhớ")

    add_card(s7, 6.833, 1.7, 5.7, 5.3, "Vòng đời Bản nháp Sandbox (Mục 11)", [
        "Idempotent Draft Workspace:",
        "   - draft_id = 'DR-' + SHA256(workflow + source_id)[:20].",
        "   - Thử lại (retry) chỉ cập nhật bản ghi cũ, không tạo duplicate.",
        "Đầy đủ trường quy chuẩn (Mục 11.1):",
        "   - draft_id, source_id, source_ids.",
        "   - status: 'draft_created', draft_status: 'draft_created'.",
        "   - delivery_status: 'not_sent' (intrip) | 'not_published' (pre/post).",
        "Vòng đời Artifact:",
        "   draft_created -> awaiting_approval -> approved -> publish_requested -> published (Trong project không có published thật).",
        "Approval Simulation: request_approval chỉ tạo bản ghi pending."
    ], badge="Bản nháp bất biến")

    set_notes(s7, "Slide 7 trình bày cách quản lý State, Memory và Bản nháp. Bản nháp được sinh với mã SHA-256 duy nhất theo nguồn, đảm bảo tính idempotent tuyệt đối khi retry và không bao giờ tự ý publish ra ngoài.")

    # ==================== SLIDE 8: 9 Layers of Safety ====================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Chín Lớp Kiểm soát An toàn (Safety - Mục 12)")

    # 3x3 Grid of safety layers
    layers = [
        ("1. Input Validation", "Kiểm định định dạng Regex ID (^TRIP-\\d{4}-\\d{3}$), chặn query quá 240 ký tự."),
        ("2. Tool Allowlist", "Per-workflow allowlist; tool nằm ngoài danh mục bị chặn đứng trước execution."),
        ("3. Strict Validation", "Draft202012 JSON Schema validation với additionalProperties=false."),
        ("4. Least Privilege", "Tools chỉ có quyền đọc mock hoặc ghi draft sandbox; tuyệt đối không write ngoài."),
        ("5. Execution Budgets", "Tối đa 8 bước/run, trần 12 bước, tối đa 2 lần retry cho lỗi tạm thời."),
        ("6. Data Boundary", "Phân quyền role; Employee chỉ xem dữ liệu của mình; Approver cần pending scope."),
        ("7. Approval Boundary", "Tool chỉ tạo pending; chỉ có external mock helper mới cập nhật quyết định."),
        ("8. Prompt Injection", "Coi user input và retrieved chunks là Untrusted Data; loại trừ chỉ thị tiêm nhiễm."),
        ("9. Safe Audit Trace", "Ghi safe trace; che số thẻ/token trên file CSV UTF-8 BOM; audit event sạch PII.")
    ]
    
    for idx, (title, desc) in enumerate(layers):
        row = idx // 3
        col = idx % 3
        left = 0.8 + col * 4.0
        top = 1.7 + row * 1.8
        add_card(s8, left, top, 3.75, 1.6, title, [desc])

    set_notes(s8, "Slide 8 tổng hợp 9 lớp kiểm soát an toàn bảo vệ hệ thống từ đầu vào, phân quyền thực thi, ngân sách bước chạy, ranh giới dữ liệu cho đến nhật ký kiểm toán không chứa PII.")

    # ==================== SLIDE 9: Evaluation & Root-Cause ====================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Khung Đánh giá, Chỉ số & Phân loại Lỗi 8 Nhóm (Mục 13)")

    add_card(s9, 0.8, 1.7, 5.7, 5.3, "Kết quả Đo lường Định lượng (Mục 13.2)", [
        "Ma trận 15 Test Cases Bắt buộc (T01 - T15): Đạt 100% pass.",
        "Bộ chỉ số chất lượng chính (Evaluation Metrics):",
        "   • Task completion rate: 1.0 (100% đạt tiêu chí)",
        "   • Tool selection accuracy: 1.0",
        "   • Argument accuracy: 1.0",
        "   • Grounding / Citation accuracy: 1.0",
        "   • Safety-test pass rate: 1.0 (100% an toàn)",
        "Bốn chỉ số Hiệu năng (Efficiency Metrics - Bổ sung đủ):",
        "   • efficiency_average_steps: 5.0",
        "   • efficiency_average_tool_calls: 5.0",
        "   • efficiency_average_retrieval_calls: 2.0",
        "   • efficiency_total_retries_tested: 2"
    ], badge="Đạt 100% chỉ số")

    add_card(s9, 6.833, 1.7, 5.7, 5.3, "Ma trận Phân loại Lỗi 8 Nhóm (Mục 13.3)", [
        "1. Routing: Phân 4 luồng NLU, đưa out-of-scope về Handoff.",
        "2. Argument Extraction: Bắt lỗi format ID và unknown ID.",
        "3. Tool Implementation: Tính toán chi phí xác định bằng code.",
        "4. Observation Handling: Chỉ đối chiếu policy cho category có thực.",
        "5. State/Transition: Ngắt sớm khi trip bị cancelled/rejected.",
        "6. Stopping/Retry: Khống chế 8 bước và retry tối đa 2 lần.",
        "7. Grounding/Citation: Chặn đứng bịa đặt bằng check_claim.",
        "8. Safety/Policy: Loại bỏ chunk injection và rà soát quyền.",
        "Chi tiết được chuẩn hóa tại: eval/reports/root_cause.md"
    ], badge="8 Danh mục bắt buộc")

    set_notes(s9, "Slide 9 chứng minh kết quả đánh giá thực nghiệm. Toàn bộ 15 test cases bắt buộc và 31 evaluation cases đều vượt qua 100%. Báo cáo root cause đã phân loại đầy đủ theo 8 nhóm lỗi của đề bài.")

    # ==================== SLIDE 10: 6 Self-Check Questions ====================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Giải đáp 6 Câu hỏi Tự kiểm tra Trước khi Nộp (Mục 17)")

    q_items = [
        ("1. Bỏ LLM, phần nào vẫn chạy deterministic?", "Toàn bộ: Kiểm định ID, kiểm tra allowlist/schema/role, tính toán chi phí số học, kiểm tra ngưỡng vi phạm, quản lý ngân sách và tạo bản nháp sandbox."),
        ("2. Policy nói 'có thể xem xét', có kết luận 'đã duyệt'?", "TUYỆT ĐỐI KHÔNG. Evidence không tự cho phép action. Quyền duyệt thuộc về con người; Agent chỉ trả về needs_human hoặc awaiting_approval."),
        ("3. Mock API trả itinerary mới khác session summary?", "Nguồn Mock API (Source of Truth) luôn được ưu tiên tuyệt đối. Không dùng persistent memory cũ để thay thế trạng thái thực tế."),
        ("4. Tool request chứa tool name hoặc field lạ?", "Dispatcher lập tức từ chối (Reject) với lỗi not_allowed hoặc invalid_argument nhờ cơ chế additionalProperties=false; không dùng eval()."),
        ("5. Retrieval không tìm thấy evidence, Agent nói gì?", "CẦN NÓI: Không tìm thấy chính sách phù hợp và chuyển giao con người. KHÔNG ĐƯỢC: Bịa đặt điều khoản hoặc suy đoán thiếu căn cứ."),
        ("6. Trace có phân biệt được routing, tool và transition?", "HOÀN TOÀN ĐƯỢC: Thể hiện rõ ràng qua từng trường action, tool, observation_status, transition và phase trong safe trace.")
    ]

    for idx, (q, a) in enumerate(q_items):
        row = idx // 2
        col = idx % 2
        left = 0.8 + col * 6.0
        top = 1.7 + row * 1.8
        add_card(s10, left, top, 5.75, 1.6, q, [a])

    set_notes(s10, "Slide 10 trả lời súc tích 6 câu hỏi tự kiểm tra của Mục 17. Đây là các câu hỏi cốt lõi khẳng định hệ thống hiểu rõ tính deterministic, quyền hạn con người và tính minh bạch của trace.")

    # ==================== SLIDE 11: Demo & Acceptance ====================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Demo Thực tế & Nghiệm thu Tối thiểu (Mục 16)")

    add_card(s11, 0.8, 1.7, 5.7, 5.3, "Phương thức Kiểm thử & Demo", [
        "1. Chạy 54 Automated Unit Tests:",
        "   python -m pytest -v (Tất cả passed trong ~3.2s)",
        "2. Chạy Evaluation Runner 31 Cases:",
        "   python eval/run_eval.py --label after",
        "3. Chạy CLI từng Workflow độc lập:",
        "   python -m travel_agent.app run pretrip --id TRIP-2026-006",
        "   python -m travel_agent.app run intrip --id TRIP-2026-002",
        "   python -m travel_agent.app run posttrip --id EXP-2026-001",
        "4. Giao diện Trực quan Web Demo:",
        "   python -m travel_agent.app web --port 8080",
        "   • Role Selector (Employee, Reviewer, Approver, Admin)",
        "   • Trace & Memory Inspector trực quan",
        "   • Staff Handoff Queue View"
    ], badge="Thao tác kiểm chứng")

    add_card(s11, 6.833, 1.7, 5.7, 5.3, "Đối chiếu 7 Tiêu chí Nghiệm thu (Mục 16)", [
        "✓ Ba workflow chạy thành công với mock data giả lập.",
        "✓ Agent chỉ tương tác với mock systems qua function calling.",
        "✓ Có ít nhất 1 safe failure (T05: failed_validation) và 1 awaiting_approval (TRIP-001) / needs_human (TRIP-004) hợp lệ.",
        "✓ Policy claims có citation truy vết đầy đủ source/section/version.",
        "✓ Không có booking/payment thật; không có production credential.",
        "✓ Đã có test chứng minh input invalid, no-evidence, tool failure, injection và cross-user isolation.",
        "✓ Trace cho phép reviewer xác định rõ ràng Agent đã làm gì, lý do dừng và bằng chứng hỗ trợ."
    ], badge="Đạt 100% tiêu chí")

    set_notes(s11, "Slide 11 minh chứng các kịch bản demo và khẳng định đạt đủ 7/7 tiêu chí nghiệm thu tối thiểu của đề bài.")

    # ==================== SLIDE 12: Summary ====================
    s12 = prs.slides.add_slide(blank_layout)
    bg12 = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg12.fill.solid()
    bg12.fill.fore_color.rgb = C_PRIMARY
    bg12.line.fill.background()

    c_box = s12.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(11.0), Inches(4.5))
    ctf = c_box.text_frame
    ctf.word_wrap = True

    p = ctf.paragraphs[0]
    p.text = "TỔNG KẾT & KẾT LUẬN"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RGBColor(96, 165, 250)

    p = ctf.add_paragraph()
    p.text = "Một Prototype Chuẩn mực về An toàn và Ranh giới AI Agent"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.space_after = Pt(20)

    bullets = [
        "Tuân thủ toàn diện 100% yêu cầu: Đầy đủ 10 Deliverables, 15 Test cases, 6 Metrics và 8 nhóm Root-cause.",
        "Kiến trúc bền vững: Tách biệt tính toán xác định khỏi LLM narrative; phễu Dispatcher 5 lớp bảo vệ chặt chẽ.",
        "Grounding thực thụ: Không ảo tưởng (Zero hallucination); trích dẫn chính sách có đầy đủ metadata.",
        "Tài liệu dẫn chứng hoàn chỉnh: Lưu tại REQUIREMENTS_COMPLIANCE_EVIDENCE.md."
    ]
    for b in bullets:
        p = ctf.add_paragraph()
        p.text = f"✔  {b}"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_before = Pt(8)

    p = ctf.add_paragraph()
    p.text = "\nCẢM ƠN THẦY CÔ VÀ CÁC BẠN ĐÃ THEO DÕI BÀI THUYẾT TRÌNH!"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(52, 211, 153)
    p.alignment = PP_ALIGN.CENTER
    p.space_before = Pt(24)

    set_notes(s12, "Em xin kết thúc bài thuyết trình tại đây. Dự án chứng minh một hướng tiếp cận AI Agent an toàn, có thể kiểm soát và sẵn sàng đáp ứng mọi tiêu chí kiểm thử khắt khe. Xin cảm ơn thầy cô và các bạn.")

    # Save presentation
    output_dir = Path("Presentation")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "Global_Business_Travel_Operations_Agent.pptx"
    prs.save(str(output_path))
    print(f"Presentation saved successfully to: {output_path.resolve()}")

if __name__ == "__main__":
    create_presentation()
