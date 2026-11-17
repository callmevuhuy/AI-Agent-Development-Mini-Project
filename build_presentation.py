"""
Script to generate an enhanced, comprehensive 14-slide presentation
for the Global Business Travel Operations Agent Mini-Project,
fully aligned with Global_Business_Travel_Operations_Agent_Mini_Project.pdf
and the actual repository implementation.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# --- COLOR PALETTE (Modern Clean Tech / Pitch & Stripe Style) ---
COLOR_BG_LIGHT = RGBColor(248, 250, 252)       # Slate 50 (#F8FAFC)
COLOR_BG_DARK = RGBColor(15, 23, 42)           # Slate 900 (#0F172A)
COLOR_CARD_DARK = RGBColor(30, 41, 59)         # Slate 800 (#1E293B)
COLOR_CARD_LIGHT = RGBColor(255, 255, 255)     # Pure White
COLOR_BORDER_LIGHT = RGBColor(226, 232, 240)   # Slate 200 (#E2E8F0)
COLOR_BORDER_DARK = RGBColor(51, 65, 85)       # Slate 700 (#334155)

COLOR_TEXT_DARK = RGBColor(15, 23, 42)         # Slate 900
COLOR_TEXT_BODY = RGBColor(51, 65, 85)         # Slate 700
COLOR_TEXT_MUTED = RGBColor(100, 116, 139)     # Slate 500
COLOR_TEXT_LIGHT = RGBColor(241, 245, 249)     # Slate 100
COLOR_TEXT_MUTED_LIGHT = RGBColor(148, 163, 184) # Slate 400

# Accents
COLOR_BLUE = RGBColor(37, 99, 235)             # Blue 600 (#2563EB)
COLOR_BLUE_LIGHT = RGBColor(239, 246, 255)     # Blue 50
COLOR_EMERALD = RGBColor(16, 185, 129)         # Emerald 500 (#10B981)
COLOR_EMERALD_LIGHT = RGBColor(236, 253, 245) # Emerald 50
COLOR_AMBER = RGBColor(245, 158, 11)           # Amber 500 (#F59E0B)
COLOR_AMBER_LIGHT = RGBColor(254, 243, 199)   # Amber 50
COLOR_PURPLE = RGBColor(139, 92, 246)          # Purple 500 (#8B5CF6)
COLOR_PURPLE_LIGHT = RGBColor(245, 243, 255)  # Purple 50
COLOR_ROSE = RGBColor(244, 63, 94)             # Rose 500 (#F43F5E)
COLOR_ROSE_LIGHT = RGBColor(255, 241, 242)    # Rose 50

FONT_NAME = "Segoe UI"

def set_slide_bg(slide, prs, color):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg

def add_header(slide, badge_text, title_text, subtitle_text, dark_mode=False):
    # Badge Pill
    badge_bg = COLOR_CARD_DARK if dark_mode else COLOR_BLUE_LIGHT
    badge_color = COLOR_BLUE if not dark_mode else RGBColor(147, 197, 253)
    
    badge_shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.8), Inches(0.42), Inches(3.4), Inches(0.32)
    )
    badge_shape.fill.solid()
    badge_shape.fill.fore_color.rgb = badge_bg
    badge_shape.line.fill.background()
    
    tf = badge_shape.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = badge_text.upper()
    p.font.name = FONT_NAME
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = badge_color
    p.alignment = PP_ALIGN.CENTER

    # Title & Subtitle
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.733), Inches(0.95))
    tf2 = tx_box.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    
    p_title = tf2.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_NAME
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_TEXT_LIGHT if dark_mode else COLOR_TEXT_DARK
    p_title.space_after = Pt(2)

    p_sub = tf2.add_paragraph()
    p_sub.text = subtitle_text
    p_sub.font.name = FONT_NAME
    p_sub.font.size = Pt(11.5)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED_LIGHT if dark_mode else COLOR_TEXT_MUTED

def add_footer(slide, current_idx, total_slides=14, dark_mode=False):
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.95), Inches(11.733), Inches(0.35))
    tf = tx_box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p = tf.paragraphs[0]
    p.text = f"Global Business Travel Operations Agent  |  Báo cáo Nghiệm thu Mini-Project"
    p.font.name = FONT_NAME
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_MUTED_LIGHT if dark_mode else COLOR_TEXT_MUTED
    
    tx_box2 = slide.shapes.add_textbox(Inches(10.5), Inches(6.95), Inches(2.0), Inches(0.35))
    tf2 = tx_box2.text_frame
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = f"Trang {current_idx} / {total_slides}"
    p2.font.name = FONT_NAME
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = COLOR_TEXT_MUTED_LIGHT if dark_mode else COLOR_TEXT_MUTED
    p2.alignment = PP_ALIGN.RIGHT

def create_card(slide, left, top, width, height, bg_color=COLOR_CARD_LIGHT, border_color=COLOR_BORDER_LIGHT, border_width=1):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
    else:
        card.line.fill.background()
    return card

def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    total_slides = 14

    # ==========================================
    # SLIDE 1: TRANG BÌA (HERO COVER)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1, prs, COLOR_BG_DARK)

    top_line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.1), Inches(1.2), Inches(0.06))
    top_line.fill.solid()
    top_line.fill.fore_color.rgb = COLOR_BLUE
    top_line.line.fill.background()

    tag = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.35), Inches(3.6), Inches(0.36))
    tag.fill.solid()
    tag.fill.fore_color.rgb = COLOR_CARD_DARK
    tag.line.fill.background()
    tf_tag = tag.text_frame
    tf_tag.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = "AI AGENT DEVELOPMENT  •  MINI PROJECT"
    p_tag.font.name = FONT_NAME
    p_tag.font.size = Pt(9.5)
    p_tag.font.bold = True
    p_tag.font.color.rgb = RGBColor(147, 197, 253)
    p_tag.alignment = PP_ALIGN.CENTER

    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.9), Inches(11.7), Inches(2.5))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = 0
    p1 = tf_t.paragraphs[0]
    p1.text = "Global Business Travel Operations Agent"
    p1.font.name = FONT_NAME
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_LIGHT
    p1.space_after = Pt(8)

    p2 = tf_t.add_paragraph()
    p2.text = "Hệ thống AI Agent Điều phối Hoạt động Công tác Doanh nghiệp"
    p2.font.name = FONT_NAME
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_after = Pt(10)

    p3 = tf_t.add_paragraph()
    p3.text = "Báo cáo Đồ án Tuân thủ Toàn diện Đặc tả Yêu cầu (Requirements Compliance) • Vận hành Offline trên Mock Systems • 9 Lớp An toàn Đa tầng"
    p3.font.name = FONT_NAME
    p3.font.size = Pt(12)
    p3.font.color.rgb = COLOR_TEXT_MUTED_LIGHT

    # 3 Summary Cards at Bottom
    cards_data = [
        ("MÔ HÌNH HỌC TẬP CÓ GIỚI HẠN", "Offline Deterministic Prototype", "Chỉ làm việc với mock systems qua function calling, không có quyền tự trị cấp production hay live action."),
        ("ĐIỀU PHỐI ĐA GIAI ĐOẠN KHÉP KÍN", "3 Workflows & Terminal Outcomes", "Hỗ trợ Pre-trip, In-trip và Post-trip; kết thúc rõ ràng ở completed, needs_input, needs_human, awaiting_approval."),
        ("MINH BẠCH & BẢO VỆ ĐA LỚP", "Grounded RAG & 9 Lớp Guardrails", "Mọi khẳng định chính sách đều trích dẫn đầy đủ 4 trường; tính toán số học xác định 100% ngoài LLM.")
    ]
    card_w = Inches(3.64)
    card_gap = Inches(0.4)
    card_top = Inches(4.7)
    card_h = Inches(1.95)

    for i, (head, sub, desc) in enumerate(cards_data):
        c_left = Inches(0.8) + i * (card_w + card_gap)
        c = create_card(s1, c_left, card_top, card_w, card_h, bg_color=COLOR_CARD_DARK, border_color=COLOR_BORDER_DARK)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = Inches(0.2)
        
        p = tf.paragraphs[0]
        p.text = head
        p.font.name = FONT_NAME
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_BLUE if i == 0 else (COLOR_EMERALD if i == 1 else RGBColor(168, 85, 247))
        p.space_after = Pt(3)

        p = tf.add_paragraph()
        p.text = sub
        p.font.name = FONT_NAME
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_LIGHT
        p.space_after = Pt(4)

        p = tf.add_paragraph()
        p.text = desc
        p.font.name = FONT_NAME
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_MUTED_LIGHT

    # ==========================================
    # SLIDE 2: BỐI CẢNH, MỤC TIÊU & PHẠM VI (Mục 1, 2, 3)
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2, prs, COLOR_BG_LIGHT)
    add_header(s2, "MỤC 1, 2 & 3: TỔNG QUAN", "Bối cảnh, Mục tiêu Học tập & Phạm vi Dự án", "Chứng minh năng lực xây dựng Agent hướng mục tiêu, có ranh giới an toàn và kiểm soát quyền hạn")
    add_footer(s2, 2, total_slides)

    col_w = Inches(5.66)
    col_gap = Inches(0.4)
    col_top = Inches(1.95)
    col_h = Inches(4.75)

    # Left: Mục tiêu học tập & Bối cảnh
    c_l = create_card(s2, Inches(0.8), col_top, col_w, col_h)
    tf_l = c_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = tf_l.margin_right = tf_l.margin_bottom = Inches(0.25)

    p = tf_l.paragraphs[0]
    p.text = "BỐI CẢNH & 7 MỤC TIÊU HỌC TẬP CỐT LÕI"
    p.font.name = FONT_NAME
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    goals = [
        ("Thiết kế Agent hướng mục tiêu", "Ràng buộc tools, state, guardrails và terminal outcomes tường minh."),
        ("Xây dựng Mock Systems & Function Calling", "Tương tác chỉ qua công cụ kiểm định, tạo artifact sandbox."),
        ("Điều phối Workflow nhiều bước", "Xử lý dependency, validation, retry limit, step budget và human handoff."),
        ("Agentic RAG & Policy Grounding", "Corpus có metadata, trích dẫn chính xác và kiểm tra đối chiếu từ vựng."),
        ("Phân tầng State & Source of Truth", "Tách bạch run state, session context, persistent preference và mock data."),
        ("Automation Draft-Only & Tách tính toán", "100% tính toán số học xác định do code xử lý, tách rời khỏi LLM."),
        ("Đánh giá Định lượng Toàn diện", "Kiểm chứng qua 15 test cases, safe traces, metrics và root-cause analysis.")
    ]
    for title, desc in goals:
        pt = tf_l.add_paragraph()
        pt.text = f"•  {title}: {desc}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.color.rgb = COLOR_TEXT_BODY
        pt.space_after = Pt(4)

    # Right: Phạm vi In-scope & Out-of-scope (Mục 3)
    c_r = create_card(s2, Inches(0.8) + col_w + col_gap, col_top, col_w, col_h)
    tf_r = c_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = Inches(0.25)

    p = tf_r.paragraphs[0]
    p.text = "RANH GIỚI VẬN HÀNH & NGUYÊN TẮC CỐT LÕI (MỤC 3)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_after = Pt(8)

    p_in = tf_r.add_paragraph()
    p_in.text = "✔  TRONG PHẠM VI (IN-SCOPE):"
    p_in.font.name = FONT_NAME
    p_in.font.size = Pt(10.5)
    p_in.font.bold = True
    p_in.font.color.rgb = COLOR_EMERALD
    p_in.space_after = Pt(2)

    in_items = [
        "100% dữ liệu chuyến đi, nhân viên, itinerary, approval, expense và policy là giả lập.",
        "Hỗ trợ trọn vẹn 3 giai đoạn: Trước chuyến đi, Trong chuyến đi và Sau chuyến đi.",
        "Tạo các bản nháp: Checklist, Support note, Expense review dạng sandbox draft.",
        "Dùng RAG trả lời câu hỏi chính sách kèm citation; yêu cầu duyệt mô phỏng pending."
    ]
    for it in in_items:
        pi = tf_r.add_paragraph()
        pi.text = f"   - {it}"
        pi.font.name = FONT_NAME
        pi.font.size = Pt(9.5)
        pi.font.color.rgb = COLOR_TEXT_BODY
        pi.space_after = Pt(2)

    p_out = tf_r.add_paragraph()
    p_out.text = "✖  NGOÀI PHẠM VI (OUT-OF-SCOPE):"
    p_out.font.name = FONT_NAME
    p_out.font.size = Pt(10.5)
    p_out.font.bold = True
    p_out.font.color.rgb = COLOR_ROSE
    p_out.space_after = Pt(2)

    out_items = [
        "Tuyệt đối không đặt, đổi, hủy vé máy bay/khách sạn thật.",
        "Không nộp visa, mua bảo hiểm, thanh toán, hoàn tiền hay phê duyệt chi phí thật.",
        "Không gửi email/tin nhắn tới người thật; không dùng production API/credential.",
        "Không dùng autonomous agent có tool set mở, scheduler hay background job."
    ]
    for it in out_items:
        po = tf_r.add_paragraph()
        po.text = f"   - {it}"
        po.font.name = FONT_NAME
        po.font.size = Pt(9.5)
        po.font.color.rgb = COLOR_TEXT_BODY
        po.space_after = Pt(2)

    # Core Rule Banner inside card
    p_rule = tf_r.add_paragraph()
    p_rule.text = "⚡ QUY TẮC CỐT LÕI: Evidence từ policy không tự cho phép action. Mọi action có tác động chỉ dừng ở draft sandbox, needs_human hoặc awaiting_approval."
    p_rule.font.name = FONT_NAME
    p_rule.font.size = Pt(9.5)
    p_rule.font.bold = True
    p_rule.font.color.rgb = COLOR_TEXT_DARK
    p_rule.space_before = Pt(6)

    # ==========================================
    # SLIDE 3: AGENT CONTRACT BẮT BUỘC & ROLES (Mục 4)
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3, prs, COLOR_BG_LIGHT)
    add_header(s3, "MỤC 4: CONTRACT & ROLES", "Hợp đồng Ràng buộc của Agent (Agent Contract)", "Cam kết cụ thể về quyền hạn, đầu vào, đầu ra, ngân sách và nguồn chân lý (Source of Truth)")
    add_footer(s3, 3, total_slides)

    # Top Contract Table Card
    c_top = create_card(s3, Inches(0.8), Inches(1.95), Inches(11.733), Inches(2.95))
    tf_top = c_top.text_frame
    tf_top.word_wrap = True
    tf_top.margin_left = tf_top.margin_top = tf_top.margin_right = tf_top.margin_bottom = Inches(0.2)

    p = tf_top.paragraphs[0]
    p.text = "BẢNG ĐẶC TẢ AGENT CONTRACT BẮT BUỘC (MỤC 4)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(6)

    contract_rows = [
        ("User roles", "Employee (U-EMP-001..004), Travel Operations Reviewer (U-REV-001), Approver (U-APR-001), Admin (U-ADM-001)."),
        ("Goal", "Hỗ trợ chuẩn bị, theo dõi và rà soát chuyến công tác quốc tế bằng dữ liệu/policy giả lập an toàn."),
        ("Input & Output", "Input: User message, trip_id, report_id, traveler_id | Output: Grounded response kèm citation, draft artifact, terminal outcome."),
        ("Allowed / Forbidden", "Allowed: Chỉ 19 tools trong registry và per-workflow allowlist | Forbidden: Booking, payment, refund, email, shell/SQL."),
        ("Source of Truth", "Mock systems luôn là nguồn chân lý; không dùng memory cũ để thay thế trạng thái chuyến đi, duyệt hay chi phí."),
        ("Budgets & Evidence", "Budget: default max 8 steps, trần cứng 12 steps, tối đa 2 lần retry cho lỗi tạm | Evidence: Safe trace, tool observation, citation.")
    ]
    for field, detail in contract_rows:
        pf = tf_top.add_paragraph()
        pf.text = f"•  {field}: {detail}"
        pf.font.name = FONT_NAME
        pf.font.size = Pt(10)
        pf.font.color.rgb = COLOR_TEXT_BODY
        pf.space_after = Pt(3)

    # Bottom Role Cards (4 Roles)
    roles_data = [
        ("EMPLOYEE", COLOR_BLUE, "U-EMP-001..004", "Quyền hạn: Xem/xử lý chuyến đi, lịch trình, chi phí của chính mình; tạo draft và yêu cầu duyệt pending.\nBị chặn: Xem dữ liệu nhân viên khác, Admin audit."),
        ("REVIEWER", COLOR_PURPLE, "U-REV-001", "Quyền hạn: Đọc và rà soát toàn bộ chuyến đi, chi phí, bản nháp của mọi nhân viên; tra cứu policy RAG.\nBị chặn: Gọi request_approval, Admin audit."),
        ("APPROVER", COLOR_AMBER, "U-APR-001", "Quyền hạn: Chỉ xem xét hồ sơ nằm trong approval_scope được cấp kèm danh mục policy tương ứng.\nBị chặn: Duyệt/từ chối trực tiếp qua tool, ghi draft."),
        ("ADMIN", COLOR_ROSE, "U-ADM-001", "Quyền hạn: Xem tổng quan chuyến đi, audit logs, Staff Handoff Queue, tải CSV và Reset demo runtime.\nBị chặn: Chạy Employee workflows, RAG, ghi memory.")
    ]
    r_w = Inches(2.72)
    r_gap = Inches(0.28)
    r_top = Inches(5.05)
    r_h = Inches(1.75)

    for i, (role_name, col, user_ids, role_desc) in enumerate(roles_data):
        cur_l = Inches(0.8) + i * (r_w + r_gap)
        c_role = create_card(s3, cur_l, r_top, r_w, r_h)
        tf_r = c_role.text_frame
        tf_r.word_wrap = True
        tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = Inches(0.18)

        p = tf_r.paragraphs[0]
        p.text = f"{role_name} ({user_ids})"
        p.font.name = FONT_NAME
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_after = Pt(3)

        p_desc = tf_r.add_paragraph()
        p_desc.text = role_desc
        p_desc.font.name = FONT_NAME
        p_desc.font.size = Pt(9)
        p_desc.font.color.rgb = COLOR_TEXT_BODY

    # ==========================================
    # SLIDE 4: KIẾN TRÚC PROTOTYPE & DISPATCHER (Mục 5 & 7)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4, prs, COLOR_BG_LIGHT)
    add_header(s4, "MỤC 5 & 7: ARCHITECTURE", "Kiến trúc Prototype & Kiểm soát Function Calling", "Luồng điều phối trung tâm với Dispatcher kiểm định nghiêm ngặt trước khi thực thi")
    add_footer(s4, 4, total_slides)

    # 4 Pipeline Stages
    stages = [
        ("TẦNG 1: INPUT & NLU ROUTER", COLOR_BLUE, [
            "Chuẩn hóa văn bản Unicode NFKC.",
            "Trích xuất Regex ID (TRIP-YYYY-NNN, EXP-YYYY-NNN).",
            "Tách câu truy vấn phức hợp (Clause splitting).",
            "Phân loại 4 luồng: SELF_SERVE, CLARIFY, HANDOFF, REJECT."
        ]),
        ("TẦNG 2: DISPATCHER & SAFETY", COLOR_PURPLE, [
            "Kiểm tra Registry & Workflow Allowlist.",
            "Draft202012 JSON Schema (additionalProperties: false).",
            "Kiểm tra quyền hạn Application Context Scope & Role ACL.",
            "Giám sát ngân sách thực thi: max_steps (8-12), retry limit (2)."
        ]),
        ("TẦNG 3: MOCK SYSTEMS & DRAFT", COLOR_AMBER, [
            "19 công cụ mock chuyên biệt có trách nhiệm hẹp.",
            "Tính toán số học 100% xác định ngoài LLM.",
            "Offline BM25 RAG có Stemming & Synonym expansion.",
            "Draft Workspace: Tạo bản nháp Idempotent bằng SHA-256."
        ]),
        ("TẦNG 4: TERMINAL OUTCOMES", COLOR_EMERALD, [
            "completed: Hoàn thành có kèm draft & citation.",
            "needs_input: Yêu cầu người dùng bổ sung dữ kiện thiếu.",
            "needs_human / awaiting_approval: Chuyển giao Staff Ticket.",
            "Ghi nhận Safe Trace và Audit Log CSV UTF-8 BOM."
        ])
    ]
    p_w = Inches(2.72)
    p_gap = Inches(0.28)
    p_top = Inches(1.95)
    p_h = Inches(3.2)

    for i, (st_title, accent, bullets) in enumerate(stages):
        cur_l = Inches(0.8) + i * (p_w + p_gap)
        c_st = create_card(s4, cur_l, p_top, p_w, p_h)
        tf_s = c_st.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = Inches(0.18)

        p = tf_s.paragraphs[0]
        p.text = st_title
        p.font.name = FONT_NAME
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = accent
        p.space_after = Pt(6)

        for b in bullets:
            pb = tf_s.add_paragraph()
            pb.text = f"• {b}"
            pb.font.name = FONT_NAME
            pb.font.size = Pt(9.5)
            pb.font.color.rgb = COLOR_TEXT_BODY
            pb.space_after = Pt(4)

    # Bottom Banner: 5 Nguyên tắc Function Calling (Mục 7.1)
    b_bot = create_card(s4, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.5), bg_color=COLOR_BLUE_LIGHT, border_color=RGBColor(191, 219, 254))
    tf_b = b_bot.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = Inches(0.2)

    p = tf_b.paragraphs[0]
    p.text = "QUY TẮC THỰC THI FUNCTION CALLING & HỢP ĐỒNG KẾT QUẢ (MỤC 7.1 & 7.3)"
    p.font.name = FONT_NAME
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(3)

    p_r1 = tf_b.add_paragraph()
    p_r1.text = "1. Model chỉ đề xuất tool name và arguments; Dispatcher kiểm định Schema + Allowlist + ACL trước khi gọi hàm."
    p_r1.font.name = FONT_NAME
    p_r1.font.size = Pt(9.5)
    p_r1.font.color.rgb = COLOR_TEXT_DARK

    p_r2 = tf_b.add_paragraph()
    p_r2.text = "2. Tuyệt đối không dùng eval, globals()[tool_name], arbitrary path/URL, shell tool hay câu SQL do model tự tạo."
    p_r2.font.name = FONT_NAME
    p_r2.font.size = Pt(9.5)
    p_r2.font.color.rgb = COLOR_TEXT_DARK

    p_r3 = tf_b.add_paragraph()
    p_r3.text = "3. Result Contract chuẩn: Thành công trả {ok: True, data: ..., meta: {source, read_only}}; Lỗi trả {ok: False, error: {code, message, retryable}}."
    p_r3.font.name = FONT_NAME
    p_r3.font.size = Pt(9.5)
    p_r3.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================
    # SLIDE 5: HỆ THỐNG MOCK & DATASET TỐI THIỂU (Mục 6 & 6.1)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5, prs, COLOR_BG_LIGHT)
    add_header(s5, "MỤC 6 & 6.1: MOCK SYSTEMS", "Hệ thống Giả lập & Dữ liệu Thử nghiệm Tối thiểu", "Được xây dựng bằng JSON/file hệ thống độc lập, không hardcode facts vào prompt")
    add_footer(s5, 5, total_slides)

    # 2 Big Columns
    m_col_w = Inches(5.66)
    m_col_gap = Inches(0.4)
    m_top = Inches(1.95)
    m_h = Inches(4.75)

    # Left: 6 Mock Systems & Tools (Mục 6)
    c_m1 = create_card(s5, Inches(0.8), m_top, m_col_w, m_h)
    tf_m1 = c_m1.text_frame
    tf_m1.word_wrap = True
    tf_m1.margin_left = tf_m1.margin_top = tf_m1.margin_right = tf_m1.margin_bottom = Inches(0.25)

    p = tf_m1.paragraphs[0]
    p.text = "6 HỆ THỐNG GIẢ LẬP & TOOLS BẮT BUỘC (MỤC 6)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    mock_systems = [
        ("Travel Request System", "get_trip_request(trip_id)", "Đọc chuyến đi (destination, dates, purpose, status)."),
        ("Traveler Profile System", "get_traveler_profile(traveler_id)", "Đọc thông tin nhân viên, department, không chứa PII nhạy cảm."),
        ("Itinerary System", "get_itinerary(trip_id)", "Đọc dữ liệu chuyến bay, khách sạn và thông tin sự cố (disruption)."),
        ("Approval System", "get_approval_status(trip_id), request_approval(action...)", "Đọc trạng thái duyệt; chỉ tạo pending, không tự duyệt."),
        ("Policy Knowledge Base", "search_travel_policy(query, category, max_results)", "Truy xuất offline BM25 policy chunks có metadata đầy đủ."),
        ("Expense System", "get_expense_report, calculate_expense_summary", "Đọc báo cáo chi phí; code tính toán xác định tổng & tỷ lệ."),
        ("Draft Workspace", "3 tools tạo draft: checklist, support_note, expense_review", "Lưu trữ bản nháp sandbox idempotent vào data/drafts/.")
    ]
    for sys_name, tool_sig, desc in mock_systems:
        ps = tf_m1.add_paragraph()
        ps.text = f"• {sys_name}: {tool_sig}"
        ps.font.name = FONT_NAME
        ps.font.size = Pt(10)
        ps.font.bold = True
        ps.font.color.rgb = COLOR_TEXT_DARK
        ps.space_after = Pt(1)

        pd = tf_m1.add_paragraph()
        pd.text = f"   {desc}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(4)

    # Right: Dataset tối thiểu (Mục 6.1)
    c_m2 = create_card(s5, Inches(0.8) + m_col_w + m_col_gap, m_top, m_col_w, m_h)
    tf_m2 = c_m2.text_frame
    tf_m2.word_wrap = True
    tf_m2.margin_left = tf_m2.margin_top = tf_m2.margin_right = tf_m2.margin_bottom = Inches(0.25)

    p = tf_m2.paragraphs[0]
    p.text = "DẪN CHỨNG ĐẠT CHUẨN DATASET TỐI THIỂU (MỤC 6.1)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_after = Pt(8)

    datasets = [
        ("6 Travel Requests (data/trips.json)", [
            "TRIP-001 (Singapore): Pending approval",
            "TRIP-002 (Tokyo): Confirmed / Approved",
            "TRIP-003 (Berlin): Missing field (purpose)",
            "TRIP-004 (London): Rejected approval",
            "TRIP-005 (Bangkok): Cancelled mock case",
            "TRIP-006 (Sydney): Valid / Happy path"
        ]),
        ("4 Traveler Profiles (data/travelers.json)", [
            "4 nhân viên thuộc 2 phòng ban (Sales, Engineering).",
            "Không lưu PII nhạy cảm (passport, thẻ tín dụng)."
        ]),
        ("5 Itineraries (data/itineraries.json)", [
            "Bao gồm TRIP-002 (delay 240 phút) và TRIP-005 (flight cancelled)."
        ]),
        ("3 Expense Reports (data/expenses.json)", [
            "EXP-001 (Valid 3 items), EXP-002 (thiếu receipt/date), EXP-003 (vượt định mức meal $90.00 và xung đột policy v1/v2)."
        ]),
        ("13 Policy Chunks (data/policy_chunks.json)", [
            "Phủ đủ 5 categories: travel, expense, visa, insurance, approval.",
            "Chuẩn 7 metadata: chunk_id, doc_id, source, section, version, category, text."
        ])
    ]
    for d_title, d_items in datasets:
        p_dt = tf_m2.add_paragraph()
        p_dt.text = f"✔  {d_title}:"
        p_dt.font.name = FONT_NAME
        p_dt.font.size = Pt(10)
        p_dt.font.bold = True
        p_dt.font.color.rgb = COLOR_TEXT_DARK
        p_dt.space_after = Pt(1)

        for it in d_items:
            p_di = tf_m2.add_paragraph()
            p_di.text = f"   - {it}"
            p_di.font.name = FONT_NAME
            p_di.font.size = Pt(9)
            p_di.font.color.rgb = COLOR_TEXT_BODY
            p_di.space_after = Pt(1)

    # ==========================================
    # SLIDE 6: WORKFLOW A — PRE-TRIP PLANNING (Mục 8.1)
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6, prs, COLOR_BG_LIGHT)
    add_header(s6, "MỤC 8.1: WORKFLOW A", "Quy trình Pre-trip Planning & Compliance", "Chuẩn bị và rà soát tuân thủ chuyến công tác trước khi khởi hành")
    add_footer(s6, 6, total_slides)

    # 3 Section Cards
    c1 = create_card(s6, Inches(0.8), Inches(1.95), Inches(3.64), Inches(4.75))
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = Inches(0.2)

    p = tf1.paragraphs[0]
    p.text = "1. CHUỖI BƯỚC THỰC THI CHUẨN"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    steps_a = [
        ("Bước 1: validate trip_id", "Kiểm tra Regex ^TRIP-\\d{4}-\\d{3}$."),
        ("Bước 2: get_trip_request", "Đọc thông tin điểm đến, ngày đi, mục đích."),
        ("Bước 3: get_approval_status", "Đọc trạng thái duyệt; nếu rejected dừng ngay needs_human."),
        ("Bước 4: search_travel_policy", "Tìm chính sách visa, bảo hiểm theo điểm đến."),
        ("Bước 5: validate_requirements", "Đối chiếu facts + approval + policy evidence."),
        ("Bước 6: create_checklist_draft", "Lưu bản nháp checklist chuẩn bị vào sandbox.")
    ]
    for st, sd in steps_a:
        pt = tf1.add_paragraph()
        pt.text = f"• {st}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf1.add_paragraph()
        pd.text = f"  {sd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(5)

    c2 = create_card(s6, Inches(4.84), Inches(1.95), Inches(3.64), Inches(4.75))
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.2)

    p = tf2.paragraphs[0]
    p.text = "2. RÀNG BUỘC NGHIỆP VỤ BẮT BUỘC"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_after = Pt(8)

    rules_a = [
        ("Chỉ claim khi có evidence", "Mọi thông báo về visa, bảo hiểm bắt buộc trích dẫn chunk policy xác thực."),
        ("Không suy diễn phê duyệt", "Tuyệt đối không kết luận chuyến đi đã duyệt nếu hệ thống mock chưa trả status: 'approved'."),
        ("Xử lý thiếu thông tin", "Nếu chuyến đi thiếu mục đích hoặc thiếu bằng chứng, Agent dừng lại trả needs_input hoặc needs_human thay vì suy đoán.")
    ]
    for rt, rd in rules_a:
        pt = tf2.add_paragraph()
        pt.text = f"✔ {rt}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf2.add_paragraph()
        pd.text = f"  {rd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(8)

    c3 = create_card(s6, Inches(8.88), Inches(1.95), Inches(3.65), Inches(4.75))
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = tf3.margin_right = tf3.margin_bottom = Inches(0.2)

    p = tf3.paragraphs[0]
    p.text = "3. KẾT QUẢ & TERMINAL OUTCOMES"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_after = Pt(8)

    outcomes_a = [
        ("completed", "Checklist draft được tạo thành công kèm trích dẫn quy định visa/bảo hiểm đầy đủ (Ví dụ case TRIP-2026-006)."),
        ("awaiting_approval", "Chuyến đi có trạng thái pending; Agent giữ nguyên trạng thái chờ duyệt (Ví dụ case TRIP-2026-001)."),
        ("needs_human", "Chuyến đi bị rejected; Agent từ chối tiếp tục và chuyển con người giải quyết (Case TRIP-2026-004)."),
        ("needs_input", "Chuyến đi thiếu trường bắt buộc purpose (Case TRIP-2026-003).")
    ]
    for ot, od in outcomes_a:
        pt = tf3.add_paragraph()
        pt.text = f"➔ {ot}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf3.add_paragraph()
        pd.text = f"  {od}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(6)

    # ==========================================
    # SLIDE 7: WORKFLOW B — IN-TRIP DISRUPTION (Mục 8.2)
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7, prs, COLOR_BG_LIGHT)
    add_header(s7, "MỤC 8.2: WORKFLOW B", "Quy trình In-trip Disruption Support", "Hỗ trợ và xử lý sự cố phát sinh trong hành trình (trễ chuyến, hủy chuyến)")
    add_footer(s7, 7, total_slides)

    # 3 Section Cards
    c1 = create_card(s7, Inches(0.8), Inches(1.95), Inches(3.64), Inches(4.75))
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = Inches(0.2)

    p = tf1.paragraphs[0]
    p.text = "1. CHUỖI BƯỚC THỰC THI CHUẨN"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_AMBER
    p.space_after = Pt(8)

    steps_b = [
        ("Bước 1: validate trip_id", "Kiểm định mã chuyến đi hợp lệ."),
        ("Bước 2: get_itinerary", "Đọc chuyến bay và trạng thái hành trình."),
        ("Bước 3: Xác định Disruption", "Bắt sự kiện trễ (delay) hoặc hủy (cancelled) khách quan từ mock API."),
        ("Bước 4: search_travel_policy", "Tra cứu chính sách hỗ trợ sự cố khẩn cấp."),
        ("Bước 5: create_support_draft", "Tạo bản nháp Support / Escalation Note.")
    ]
    for st, sd in steps_b:
        pt = tf1.add_paragraph()
        pt.text = f"• {st}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf1.add_paragraph()
        pd.text = f"  {sd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(6)

    c2 = create_card(s7, Inches(4.84), Inches(1.95), Inches(3.64), Inches(4.75))
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.2)

    p = tf2.paragraphs[0]
    p.text = "2. RANH GIỚI BẢO VỆ TUYỆT ĐỐI"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_ROSE
    p.space_after = Pt(8)

    rules_b = [
        ("Tuyệt đối KHÔNG tự hành động", "Agent không được tự ý đổi vé, đặt phòng khách sạn, hoàn tiền hay chi tiền cứu trợ."),
        ("Tách rời Fact và Policy", "Bản nháp phân biệt rõ: Đâu là dữ kiện lịch trình thực tế, đâu là điều khoản chính sách tham chiếu."),
        ("Xử lý khi thiếu thông tin", "Nếu chính sách không nêu chi tiết, Agent phải dừng trả needs_human kèm phiếu chuyển giao.")
    ]
    for rt, rd in rules_b:
        pt = tf2.add_paragraph()
        pt.text = f"✖ {rt}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf2.add_paragraph()
        pd.text = f"  {rd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(8)

    c3 = create_card(s7, Inches(8.88), Inches(1.95), Inches(3.65), Inches(4.75))
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = tf3.margin_right = tf3.margin_bottom = Inches(0.2)

    p = tf3.paragraphs[0]
    p.text = "3. MINH HỌA CASE DELAY VS CANCEL"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    cases_b = [
        ("Case Hoãn chuyến (TRIP-2026-002)", "Flight MOCK-202 trễ 240 phút. Agent tra cứu policy POL-TRAVEL-DISRUPT-001, cung cấp định mức ăn uống và khách sạn, tạo Support Note Draft an toàn."),
        ("Case Hủy chuyến (TRIP-2026-005)", "Flight MOCK-505 bị cancelled. Agent nhận định tình huống vượt thẩm quyền, dừng tự động hóa và xuất Ticket: [HANDOFF TO STAFF | HND-XXXXXXXX], kết thúc ở needs_human.")
    ]
    for ct, cd in cases_b:
        pt = tf3.add_paragraph()
        pt.text = f"➔ {ct}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(2)

        pd = tf3.add_paragraph()
        pd.text = f"  {cd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(8)

    # ==========================================
    # SLIDE 8: WORKFLOW C — POST-TRIP EXPENSE (Mục 8.3)
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8, prs, COLOR_BG_LIGHT)
    add_header(s8, "MỤC 8.3: WORKFLOW C", "Quy trình Post-trip Expense Pre-check", "Rà soát báo cáo chi phí, đối chiếu định mức và kiểm tra tính hợp lệ trước khi nộp")
    add_footer(s8, 8, total_slides)

    # 3 Section Cards
    c1 = create_card(s8, Inches(0.8), Inches(1.95), Inches(3.64), Inches(4.75))
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = Inches(0.2)

    p = tf1.paragraphs[0]
    p.text = "1. CHUỖI BƯỚC THỰC THI CHUẨN"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_after = Pt(8)

    steps_c = [
        ("Bước 1: validate report_id", "Kiểm tra định dạng EXP-YYYY-NNN."),
        ("Bước 2: get_expense_report", "Đọc các line items chi phí và trạng thái hóa đơn."),
        ("Bước 3: calculate_expense_summary", "Thực hiện tính toán số học xác định 100% bằng code."),
        ("Bước 4: search_travel_policy", "Tra cứu định mức chi phí bữa ăn, khách sạn."),
        ("Bước 5: create_expense_review_draft", "Khởi tạo bản nháp rà soát chi phí chi tiết.")
    ]
    for st, sd in steps_c:
        pt = tf1.add_paragraph()
        pt.text = f"• {st}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf1.add_paragraph()
        pd.text = f"  {sd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(6)

    c2 = create_card(s8, Inches(4.84), Inches(1.95), Inches(3.64), Inches(4.75))
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.2)

    p = tf2.paragraphs[0]
    p.text = "2. NGUYÊN TẮC TÍNH TOÁN XÁC ĐỊNH"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    rules_c = [
        ("Tách tính toán khỏi LLM", "Mọi phép cộng dồn tổng tiền, tính tỷ lệ hóa đơn và cờ vượt ngưỡng do calculate_expense_summary.py tính toán; LLM không tự tính nhẩm."),
        ("Không tự ý duyệt chi phí", "Agent tuyệt đối không được tự ý kết luận 'được hoàn tiền' hoặc 'đã phê duyệt'."),
        ("Bản nháp trung thực", "Draft chỉ nêu facts, evidence policy và danh sách các mục cảnh báo cần Reviewer kiểm tra lại.")
    ]
    for rt, rd in rules_c:
        pt = tf2.add_paragraph()
        pt.text = f"✔ {rt}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(1)

        pd = tf2.add_paragraph()
        pd.text = f"  {rd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(8)

    c3 = create_card(s8, Inches(8.88), Inches(1.95), Inches(3.65), Inches(4.75))
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = tf3.margin_right = tf3.margin_bottom = Inches(0.2)

    p = tf3.paragraphs[0]
    p.text = "3. BA KỊCH BẢN KIỂM THỬ THỰC TẾ"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_after = Pt(8)

    cases_c = [
        ("EXP-2026-001 (Happy Path)", "Hợp lệ 100%: 3 line items có đầy đủ ngày tháng và receipt_attached: true. Tạo Expense Review Draft thành công (completed)."),
        ("EXP-2026-002 (Thiếu chứng từ)", "Phát hiện mục thiếu receipt_attached và mục thiếu ngày (date). Agent dừng trả needs_input yêu cầu bổ sung."),
        ("EXP-2026-003 (Vượt ngưỡng / Conflict)", "Chi bữa ăn $90.00 vượt định mức $75.00 của v1.0. Phát hiện xung đột policy v1/v2, gắn cờ cảnh báo Reviewer (completed/flagged).")
    ]
    for ct, cd in cases_c:
        pt = tf3.add_paragraph()
        pt.text = f"➔ {ct}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(2)

        pd = tf3.add_paragraph()
        pd.text = f"  {cd}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(6)

    # ==========================================
    # SLIDE 9: STATE, MEMORY & DRAFT ARTIFACTS (Mục 9 & 11)
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s9, prs, COLOR_BG_LIGHT)
    add_header(s9, "MỤC 9 & 11: STATE & MEMORY", "Quản lý Trạng thái, Bộ nhớ & Bản nháp Idempotent", "Phân tầng bộ nhớ nghiêm ngặt, cách ly dữ liệu người dùng và tạo bản nháp sandbox an toàn")
    add_footer(s9, 9, total_slides)

    # 3 Section Columns
    col3_w = Inches(3.64)
    col3_gap = Inches(0.4)
    col3_top = Inches(1.95)
    col3_h = Inches(4.75)

    # Col 1: State bắt buộc
    c1 = create_card(s9, Inches(0.8), col3_top, col3_w, col3_h)
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = Inches(0.2)

    p = tf1.paragraphs[0]
    p.text = "1. RUN STATE BẮT BUỘC (MỤC 9.1)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    state_items = [
        ("run_id & workflow", "Định danh từng phiên chạy và quy trình tương ứng (pretrip, intrip, posttrip)."),
        ("phase & step_count", "Giám sát từng bước thực thi so với trần max_steps (8-12 bước)."),
        ("user_context", "Phân định rõ scope và vai trò application-owned; không nhận từ model args."),
        ("safe_tool_results", "Lưu trữ observation sạch sẽ, phục vụ tạo bằng chứng."),
        ("safe trace & outcome", "Ghi vết sự kiện đầy đủ, kết thúc bằng terminal outcome chuẩn.")
    ]
    for st, sd in state_items:
        pt = tf1.add_paragraph()
        pt.text = f"• {st}: {sd}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(9.5)
        pt.font.color.rgb = COLOR_TEXT_BODY
        pt.space_after = Pt(5)

    # Col 2: Memory Policy
    c2 = create_card(s9, Inches(4.84), col3_top, col3_w, col3_h)
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.2)

    p = tf2.paragraphs[0]
    p.text = "2. CHÍNH SÁCH BỘ NHỚ (MỤC 9.2)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_after = Pt(8)

    mem_items = [
        ("Session State (Ngắn hạn)", "Lưu active_trip_id, active_report_id có cơ chế hết hạn TTL theo session."),
        ("Persistent Preference (Dài hạn)", "Lưu response_language, preferred_output_format CHỈ KHI có cờ memory_write_authorized=True."),
        ("Cách ly tuyệt đối", "Tách bạch user_id, session_id, run_id. Người dùng này không thấy memory người khác."),
        ("Không lưu PII nhạy cảm", "Cấm tuyệt đối lưu hộ chiếu, visa, thẻ tín dụng, token hay raw prompt."),
        ("Source of Truth", "Dữ liệu nghiệp vụ luôn lấy lại từ Mock system; memory không được ghi đè fact.")
    ]
    for mt, md in mem_items:
        pt = tf2.add_paragraph()
        pt.text = f"✔ {mt}: {md}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(9.5)
        pt.font.color.rgb = COLOR_TEXT_BODY
        pt.space_after = Pt(4)

    # Col 3: Idempotent Draft & Approval
    c3 = create_card(s9, Inches(8.88), col3_top, col3_w, col3_h)
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = tf3.margin_right = tf3.margin_bottom = Inches(0.2)

    p = tf3.paragraphs[0]
    p.text = "3. BẢN NHÁP SANDBOX (MỤC 11)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_after = Pt(8)

    draft_items = [
        ("Idempotency qua SHA-256", "draft_id được sinh từ hash cố định của (workflow, source_id); gọi lại nhiều lần không tạo rác/duplicate file."),
        ("Trạng thái Delivery trung thực", "Artifacts lưu trong data/drafts/ luôn có delivery_status: 'not_sent' hoặc 'not_published'."),
        ("Approval Simulation", "request_approval chỉ tạo bản ghi pending; agent tuyệt đối không tự phê duyệt hay từ chối."),
        ("Partial Failure Handling", "Khi bước sau gặp lỗi, trả về partial hoặc failed_validation; không báo success giả lập.")
    ]
    for dt, dd in draft_items:
        pt = tf3.add_paragraph()
        pt.text = f"➔ {dt}: {dd}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(9.5)
        pt.font.color.rgb = COLOR_TEXT_BODY
        pt.space_after = Pt(5)

    # ==========================================
    # SLIDE 10: AGENTIC RAG & POLICY GROUNDING (Mục 10)
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10, prs, COLOR_BG_LIGHT)
    add_header(s10, "MỤC 10: RAG & GROUNDING", "Agentic RAG, Dẫn chứng & Xử lý Xung đột Chính sách", "Truy xuất tri thức có cấu trúc, gắn citation 4 trường bắt buộc và loại bỏ hoàn toàn ảo giác")
    add_footer(s10, 10, total_slides)

    # 3 Horizontal Cards
    r_top = Inches(1.95)
    r_h = Inches(1.45)
    r_gap = Inches(0.2)
    r_w = Inches(11.733)

    rag_blocks = [
        ("1. CHÍNH SÁCH TRUY XUẤT PHÂN TẦNG (RETRIEVAL POLICY - MỤC 10.1)", COLOR_BLUE, [
            "Chào hỏi (Greeting) / Viết lại text: Trả lời trực tiếp, tuyệt đối không gọi công cụ RAG thừa thãi.",
            "Trạng thái chuyến đi / Chi phí live: Gọi Mock API đọc dữ liệu thật trước; không suy đoán từ policy.",
            "Câu hỏi kết hợp (Mixed Query): Đọc dữ liệu lịch trình trước, sau đó mới gọi RAG có điều kiện theo destination."
        ]),
        ("2. TRÍCH DẪN DẪN CHỨNG CHUẨN 4 TRƯỜNG & GROUNDING (MỤC 10.2)", COLOR_PURPLE, [
            "Bắt buộc gắn Citation đầy đủ: [source/doc_id | section/page | version | chunk_id] từ search result đến phản hồi cuối.",
            "Kiểm tra Claim-to-Evidence: Đối chiếu từ vựng và cực tính; điểm retrieval score cao không tự coi là bằng chứng hợp lệ.",
            "Query rewrite có kiểm soát: Tối đa 1 lần/branch, ghi log trace rõ ràng và không được làm biến đổi ý định người dùng."
        ]),
        ("3. XỬ LÝ XUNG ĐỘT PHIÊN BẢN & PHÒNG CHỐNG TIÊM NHIỄM", COLOR_AMBER, [
            "Phát hiện xung đột phiên bản: Nhận diện mâu thuẫn giữa Meal Policy v1.0 ($75/ngày) và v2.0 ($90/ngày); chủ động cảnh báo.",
            "Loại trừ Chunk độc hại: Tự động phát hiện và loại bỏ chunk POL-EXPENSE-TEST-001 chứa chỉ thị ghi đè prompt.",
            "Retrieved text là untrusted data: Dữ liệu văn bản lấy về chỉ là dữ liệu tham khảo, không được coi là system instruction."
        ])
    ]
    for i, (title, accent, bullets) in enumerate(rag_blocks):
        top = r_top + i * (r_h + r_gap)
        c_r = create_card(s10, Inches(0.8), top, r_w, r_h)
        tf_r = c_r.text_frame
        tf_r.word_wrap = True
        tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = Inches(0.2)

        p = tf_r.paragraphs[0]
        p.text = title
        p.font.name = FONT_NAME
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = accent
        p.space_after = Pt(4)

        for b in bullets:
            pb = tf_r.add_paragraph()
            pb.text = f"• {b}"
            pb.font.name = FONT_NAME
            pb.font.size = Pt(9.5)
            pb.font.color.rgb = COLOR_TEXT_BODY
            pb.space_after = Pt(2)

    # ==========================================
    # SLIDE 11: 9 LỚP BẢO VỆ AN TOÀN (Mục 12)
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s11, prs, COLOR_BG_LIGHT)
    add_header(s11, "MỤC 12: SAFETY GUARDRAILS", "9 Lớp Kiểm soát An toàn Đa tầng (Defense-in-Depth)", "Kiến trúc phòng thủ toàn diện từ kiểm định đầu vào, phân quyền đến nhật ký kiểm toán")
    add_footer(s11, 11, total_slides)

    # 3 Columns for 9 layers
    s_col_w = Inches(3.64)
    s_col_gap = Inches(0.4)
    s_top = Inches(1.95)
    s_h = Inches(4.75)

    safety_layers = [
        ("NHÓM 1: KIỂM SOÁT ĐẦU VÀO & SCHEMA", COLOR_BLUE, [
            ("1. Input Validation", "Regex ID nghiêm ngặt (^TRIP-\\d{4}-\\d{3}$, ^EXP-\\d{4}-\\d{3}$); giới hạn độ dài câu truy vấn <= 240 ký tự."),
            ("2. Tool Allowlist", "Tách biệt allowlist cho từng workflow (pretrip, intrip, posttrip); chặn mọi công cụ ngoài danh mục trước execution."),
            ("3. Schema Validation", "Kiểm định Draft202012 JSON Schema với additionalProperties: false; từ chối tham số lạ.")
        ]),
        ("NHÓM 2: QUYỀN HẠN & NGÂN SÁCH", COLOR_PURPLE, [
            ("4. Least Privilege", "Công cụ chỉ có quyền đọc dữ liệu mock hoặc tạo draft sandbox; không có lệnh ghi hay gọi network bên ngoài."),
            ("5. Execution Budgets", "Giới hạn tối đa 8 bước mặc định (trần cứng 12 bước), tối đa 2 lần retry cho lỗi tạm thời (retryable: True)."),
            ("6. Data Boundary & Role ACL", "Phân quyền theo vai trò (Employee, Approver, Reviewer, Admin); cách ly bộ nhớ giữa các người dùng.")
        ]),
        ("NHÓM 3: RANH GIỚI HÀNH ĐỘNG & AUDIT", COLOR_EMERALD, [
            ("7. Approval Boundary", "Yêu cầu duyệt chỉ tạo trạng thái pending; quyết định phê duyệt thực tế chỉ do con người thực hiện ngoài hệ thống."),
            ("8. Prompt Injection Defense", "Chặn đứng các mẫu tiêm nhiễm chỉ thị trong câu hỏi người dùng và lọc bỏ policy chunk độc hại."),
            ("9. Safe Audit Trail", "Ghi nhận safe trace không chứa PII; xuất nhật ký CSV UTF-8 BOM tự động che số thẻ ngân hàng và token.")
        ])
    ]
    for i, (g_title, accent, items) in enumerate(safety_layers):
        cur_l = Inches(0.8) + i * (s_col_w + s_col_gap)
        c_s = create_card(s11, cur_l, s_top, s_col_w, s_h)
        tf_s = c_s.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = Inches(0.2)

        p = tf_s.paragraphs[0]
        p.text = g_title
        p.font.name = FONT_NAME
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = accent
        p.space_after = Pt(10)

        for l_num, l_desc in items:
            pt = tf_s.add_paragraph()
            pt.text = l_num
            pt.font.name = FONT_NAME
            pt.font.size = Pt(10)
            pt.font.bold = True
            pt.font.color.rgb = COLOR_TEXT_DARK
            pt.space_after = Pt(2)

            pd = tf_s.add_paragraph()
            pd.text = f"• {l_desc}"
            pd.font.name = FONT_NAME
            pd.font.size = Pt(9.5)
            pd.font.color.rgb = COLOR_TEXT_BODY
            pd.space_after = Pt(8)

    # ==========================================
    # SLIDE 12: ĐÁNH GIÁ THỰC NGHIỆM & 15 TEST CASES (Mục 13)
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s12, prs, COLOR_BG_LIGHT)
    add_header(s12, "MỤC 13: EVALUATION & METRICS", "Đánh giá Thực nghiệm & Bộ 15 Test Cases Bắt buộc", "Đạt kết quả tối đa 100% trên bộ test suite tự động và kiểm soát hồi quy hoàn toàn")
    add_footer(s12, 12, total_slides)

    # 4 Metric Cards
    metrics = [
        ("100%", "Task Completion", "31/31 kịch bản kiểm thử đánh giá hoàn thành chính xác", COLOR_BLUE),
        ("100%", "Tool & Argument", "Chọn đúng công cụ và tham số chuẩn JSON Schema", COLOR_PURPLE),
        ("100%", "Grounding & Safety", "Dẫn chứng trích dẫn chính xác, vượt qua toàn bộ safety test", COLOR_EMERALD),
        ("54/54", "Pytest Suite", "Bộ unit test và integration test vượt qua tuyệt đối", COLOR_AMBER)
    ]
    m_w = Inches(2.72)
    m_gap = Inches(0.28)
    m_top = Inches(1.95)
    m_h = Inches(1.7)

    for i, (val, title, desc, col) in enumerate(metrics):
        cur_l = Inches(0.8) + i * (m_w + m_gap)
        c_m = create_card(s12, cur_l, m_top, m_w, m_h)
        tf_m = c_m.text_frame
        tf_m.word_wrap = True
        tf_m.margin_left = tf_m.margin_top = tf_m.margin_right = tf_m.margin_bottom = Inches(0.18)

        p = tf_m.paragraphs[0]
        p.text = val
        p.font.name = FONT_NAME
        p.font.size = Pt(30)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_after = Pt(1)

        p = tf_m.add_paragraph()
        p.text = title
        p.font.name = FONT_NAME
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(2)

        p = tf_m.add_paragraph()
        p.text = desc
        p.font.name = FONT_NAME
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_BODY

    # Bottom Split: 15 Test Cases & 8-Root-Cause Matrix
    b_left_w = Inches(6.8)
    b_right_w = Inches(4.533)
    b_gap = Inches(0.4)
    b_top = Inches(3.85)
    b_h = Inches(2.85)

    c_bl = create_card(s12, Inches(0.8), b_top, b_left_w, b_h)
    tf_bl = c_bl.text_frame
    tf_bl.word_wrap = True
    tf_bl.margin_left = tf_bl.margin_top = tf_bl.margin_right = tf_bl.margin_bottom = Inches(0.2)

    p = tf_bl.paragraphs[0]
    p.text = "DANH MỤC 15 TEST CASES BẮT BUỘC ĐÃ ĐƯỢC KIỂM CHỨNG (MỤC 13.1)"
    p.font.name = FONT_NAME
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(4)

    test_lines = [
        "T01 Pre-trip happy path  •  T02 In-trip delay mock  •  T03 Expense happy path",
        "T04 Missing trip ID  •  T05 Invalid ID format  •  T06 Unknown trip/report ID",
        "T07 Pending approval  •  T07 Rejected approval  •  T08 Policy no-result/thiếu evidence",
        "T09 Policy version conflict  •  T10 Tool timeout có retry limit  •  T11 Budget exceeded",
        "T12 Prompt injection user  •  T13 Chunk injection text  •  T14 Cross-user memory isolation",
        "T15 Retry draft với cùng ID (Idempotency, không sinh duplicate file)"
    ]
    for tl in test_lines:
        pt = tf_bl.add_paragraph()
        pt.text = f"✔  {tl}"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(9.5)
        pt.font.color.rgb = COLOR_TEXT_BODY
        pt.space_after = Pt(2)

    c_br = create_card(s12, Inches(0.8) + b_left_w + b_gap, b_top, b_right_w, b_h)
    tf_br = c_br.text_frame
    tf_br.word_wrap = True
    tf_br.margin_left = tf_br.margin_top = tf_br.margin_right = tf_br.margin_bottom = Inches(0.2)

    p = tf_br.paragraphs[0]
    p.text = "MA TRẬN 8 NHÓM ROOT-CAUSE (MỤC 13.3)"
    p.font.name = FONT_NAME
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PURPLE
    p.space_after = Pt(4)

    root_causes = [
        "1. routing: Sai luồng NLU router.",
        "2. argument_extraction: Lỗi trích xuất ID/ngày.",
        "3. tool_implementation: Lỗi logic trong mock tool.",
        "4. observation_handling: Xử lý observation sai lệch.",
        "5. state/transition: Lỗi chuyển trạng thái RunState.",
        "6. stopping/retry: Vượt quá budget hoặc retry cap.",
        "7. grounding/citation: Sai lệch đối chiếu evidence.",
        "8. safety/policy: Vi phạm quyền hạn hoặc injection."
    ]
    for rc in root_causes:
        pr = tf_br.add_paragraph()
        pr.text = f"• {rc}"
        pr.font.name = FONT_NAME
        pr.font.size = Pt(9)
        pr.font.color.rgb = COLOR_TEXT_BODY
        pr.space_after = Pt(1)

    # ==========================================
    # SLIDE 13: GIAO DIỆN & 10 DELIVERABLES (Mục 14 & 16)
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s13, prs, COLOR_BG_LIGHT)
    add_header(s13, "MỤC 14 & 16: DELIVERABLES", "Giao diện Sản phẩm & Danh mục 10 Sản phẩm Bàn giao", "Đầy đủ 10 deliverables theo yêu cầu, giao diện trực quan và đáp ứng tiêu chí nghiệm thu")
    add_footer(s13, 13, total_slides)

    col_w = Inches(5.66)
    col_gap = Inches(0.4)
    col_top = Inches(1.95)
    col_h = Inches(4.75)

    # Left: Giao diện Web UI & CLI
    c_l = create_card(s13, Inches(0.8), col_top, col_w, col_h)
    tf_l = c_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = tf_l.margin_right = tf_l.margin_bottom = Inches(0.25)

    p = tf_l.paragraphs[0]
    p.text = "GIAO DIỆN SẢN PHẨM & TRẢI NGHIỆM THỰC TẾ"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE
    p.space_after = Pt(8)

    ui_points = [
        ("Web UI Tương tác Đa năng (http://127.0.0.1:8080)", [
            "Role Selector: Chuyển đổi linh hoạt giữa Employee, Reviewer, Approver, Admin.",
            "Trace & Memory Inspector: Quan sát run state, session context và reasoning theo thời gian thực.",
            "Staff Handoff Queue View: Xem danh sách ticket chuyển giao nhân sự minh bạch.",
            "Admin Controls: Nút Reset runtime dữ liệu demo và download CSV logs."
        ]),
        ("Giao diện Dòng lệnh CLI Tinh gọn", [
            "python -m travel_agent.app chat: Trò chuyện đa lượt tương tác.",
            "python -m travel_agent.app run <wf>: Chạy độc lập từng workflow Pre-trip, In-trip, Post-trip.",
            "python -m travel_agent.app logs: Kiểm tra trực tiếp file log CSV UTF-8 BOM."
        ])
    ]
    for head, subpts in ui_points:
        pt = tf_l.add_paragraph()
        pt.text = f"✔ {head}:"
        pt.font.name = FONT_NAME
        pt.font.size = Pt(10)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_DARK
        pt.space_after = Pt(2)

        for sp in subpts:
            ps = tf_l.add_paragraph()
            ps.text = f"   - {sp}"
            ps.font.name = FONT_NAME
            ps.font.size = Pt(9.5)
            ps.font.color.rgb = COLOR_TEXT_BODY
            ps.space_after = Pt(2)

    # Right: 10 Deliverables (Mục 14)
    c_r = create_card(s13, Inches(0.8) + col_w + col_gap, col_top, col_w, col_h)
    tf_r = c_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = Inches(0.25)

    p = tf_r.paragraphs[0]
    p.text = "ĐỐI CHIẾU 10 SẢN PHẨM BÀN GIAO (MỤC 14)"
    p.font.name = FONT_NAME
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.space_after = Pt(8)

    delivs = [
        "1. Source code hoàn chỉnh tại src/travel_agent/ (19 tools, NLU, dispatcher).",
        "2. README.md: Hướng dẫn chi tiết cài đặt môi trường và lệnh chạy.",
        "3. Mock datasets & Policy corpus trong thư mục data/ đầy đủ metadata.",
        "4. Agent contract, tool cards, JSON Schemas (thư mục schemas/).",
        "5. Sơ đồ kiến trúc & ba workflow theo chiều dọc (Given Docs/ARCHITECTURE.md).",
        "6. Memory policy & Data boundaries (Given Docs/MEMORY_AND_SAFETY.md).",
        "7. Test matrix, traces tiêu biểu, metric report & root-cause analysis (eval/).",
        "8. Báo cáo cải tiến baseline, after và regression không phát sinh lỗi.",
        "9. Demo walkthrough ngắn: demo/DEMO_SCENARIOS.md và web UI.",
        "10. Mục giới hạn an toàn & các hành động tuyệt đối không triển khai."
    ]
    for d in delivs:
        pd = tf_r.add_paragraph()
        pd.text = f"✔ {d}"
        pd.font.name = FONT_NAME
        pd.font.size = Pt(9)
        pd.font.color.rgb = COLOR_TEXT_BODY
        pd.space_after = Pt(2)

    # ==========================================
    # SLIDE 14: 6 CÂU HỎI TỰ KIỂM TRA TRƯỚC KHI NỘP (Mục 17)
    # ==========================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s14, prs, COLOR_BG_DARK)

    # Top accent line
    top_line14 = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.65), Inches(1.2), Inches(0.06))
    top_line14.fill.solid()
    top_line14.fill.fore_color.rgb = COLOR_BLUE
    top_line14.line.fill.background()

    tag14 = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.85), Inches(3.6), Inches(0.32))
    tag14.fill.solid()
    tag14.fill.fore_color.rgb = COLOR_CARD_DARK
    tag14.line.fill.background()
    tf_tag14 = tag14.text_frame
    tf_tag14.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_tag14 = tf_tag14.paragraphs[0]
    p_tag14.text = "MỤC 17: TỰ KIỂM TRA TRƯỚC KHI NỘP BÀI"
    p_tag14.font.name = FONT_NAME
    p_tag14.font.size = Pt(9.5)
    p_tag14.font.bold = True
    p_tag14.font.color.rgb = RGBColor(147, 197, 253)
    p_tag14.alignment = PP_ALIGN.CENTER

    t_box14 = s14.shapes.add_textbox(Inches(0.8), Inches(1.25), Inches(11.7), Inches(0.85))
    tf14 = t_box14.text_frame
    tf14.margin_left = tf14.margin_top = 0
    p = tf14.paragraphs[0]
    p.text = "Giải đáp Chi tiết 6 Câu hỏi Nghiệm thu Dự án"
    p.font.name = FONT_NAME
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_LIGHT
    p.space_after = Pt(2)

    p_sub = tf14.add_paragraph()
    p_sub.text = "Chứng minh tính vững chắc, xác định và tuân thủ tuyệt đối các nguyên tắc an toàn cốt lõi"
    p_sub.font.name = FONT_NAME
    p_sub.font.size = Pt(11.5)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED_LIGHT

    add_footer(s14, 14, total_slides, dark_mode=True)

    # 6 Questions Grid (2 columns x 3 rows)
    q_w = Inches(5.66)
    q_h = Inches(1.42)
    q_gap_x = Inches(0.4)
    q_gap_y = Inches(0.18)
    q_top = Inches(2.25)

    questions = [
        ("CÂU 1: BỎ LLM, PHẦN NÀO CHẠY DETERMINISTIC?",
         "Toàn bộ lõi nghiệp vụ chạy 100% code thuần: Regex ID, Dispatcher allowlist & schema check, tính toán số học chi phí (calculate_expense_summary), quản lý ngân sách bước và sinh draft ID bằng SHA-256."),
        ("CÂU 2: POLICY GHI 'CÓ THỂ XEM XÉT', AGENT ĐƯỢC NÓI 'ĐÃ DUYỆT'?",
         "Tuyệt đối KHÔNG. Quyền phê duyệt chỉ thuộc về người thẩm quyền ngoài hệ thống. Agent chỉ trích dẫn điều khoản tham chiếu và dừng ở needs_human hoặc awaiting_approval."),
        ("CÂU 3: API MOCK KHÁC SESSION CŨ, SOURCE NÀO ƯU TIÊN?",
         "API MOCK (Source of Truth) luôn được ưu tiên tuyệt đối. Session memory chỉ đóng vai trò ngữ cảnh ngắn hạn, không bao giờ được dùng để thay thế trạng thái thực tế từ Mock system."),
        ("CÂU 4: TOOL REQUEST CÓ TÊN/FIELD LẠ, DISPATCHER LÀM GÌ?",
         "Dispatcher lập tức TỪ CHỐI (Reject) với mã lỗi có cấu trúc: not_allowed nếu sai tool, hoặc invalid_argument nếu vi phạm Schema (additionalProperties: false). Tuyệt đối không eval()."),
        ("CÂU 5: RAG KHÔNG TÌM THẤY EVIDENCE, AGENT NÓI GÌ & TRÁNH GÌ?",
         "CẦN NÓI: Thông báo trung thực không tìm thấy chính sách và chuyển tiếp Staff Ticket. TRÁNH NÓI: Tuyệt đối không tự suy đoán định mức hoặc bịa đặt quy định (Hallucination)."),
        ("CÂU 6: TRACE CÓ ĐỦ PHÂN BIỆT CÁC NHÓM LỖI KHÔNG?",
         "ĐẦY ĐỦ 100%. Safe trace ghi nhận case_id, run_id, phase, tool, safe arguments, observation status, transition và budget; phân biệt rõ 8 nhóm nguyên nhân lỗi chuẩn.")
    ]
    for i, (q_title, q_ans) in enumerate(questions):
        row = i // 2
        col = i % 2
        left = Inches(0.8) + col * (q_w + q_gap_x)
        top = q_top + row * (q_h + q_gap_y)

        c_q = create_card(s14, left, top, q_w, q_h, bg_color=COLOR_CARD_DARK, border_color=COLOR_BORDER_DARK)
        tf_q = c_q.text_frame
        tf_q.word_wrap = True
        tf_q.margin_left = tf_q.margin_top = tf_q.margin_right = tf_q.margin_bottom = Inches(0.18)

        p = tf_q.paragraphs[0]
        p.text = q_title
        p.font.name = FONT_NAME
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = RGBColor(147, 197, 253) if col == 0 else COLOR_EMERALD
        p.space_after = Pt(2)

        p_ans = tf_q.add_paragraph()
        p_ans.text = q_ans
        p_ans.font.name = FONT_NAME
        p_ans.font.size = Pt(9)
        p_ans.font.color.rgb = COLOR_TEXT_LIGHT

    out_dir = os.path.join(os.path.dirname(__file__), "Presentation")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "Global_Business_Travel_Operations_Agent.pptx")
    prs.save(out_file)
    print(f"Enhanced 14-slide presentation saved successfully: {out_file}")

if __name__ == "__main__":
    main()
