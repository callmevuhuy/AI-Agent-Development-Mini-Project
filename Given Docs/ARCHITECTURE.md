# ARCHITECTURE

## 1. Kiến trúc tổng thể
Model chỉ đề xuất tool call. Dispatcher (code) kiểm tra và thực thi. Agent chỉ thấy mock systems qua tool.

```mermaid
flowchart TD
    U["User (Employee / Reviewer / Approver)<br/>message + IDs"] --> APP["Application layer<br/>gắn user_context (user_id, role, session_id)"]
    APP --> ORCH["Orchestrator<br/>state machine + budget + workflow phase"]
    ORCH <--> LLM["Planner<br/>RuleBased (mặc định) | LLM tùy chọn<br/>chỉ đề xuất tool_name + args"]
    ORCH --> DISP["Dispatcher<br/>registry → allowlist → JSON Schema →<br/>domain validation → role/scope → budget"]
    DISP -->|reject| REJ["failed_validation / unauthorized_scope<br/>(trace, không execute)"]
    DISP --> TOOLS["Tool wrappers (hẹp, structured result)"]
    TOOLS --> M1["Mock Travel Request"]
    TOOLS --> M2["Mock Traveler Profile"]
    TOOLS --> M3["Mock Itinerary"]
    TOOLS --> M4["Mock Approval (fixture)"]
    TOOLS --> M5["Mock Expense"]
    TOOLS --> RAG["Policy KB + RAG<br/>retriever → claim-evidence check → citation"]
    TOOLS --> DW["Draft Workspace (sandbox)<br/>idempotent draft_id"]
    ORCH --> MEM["Memory<br/>session state | preference (user yêu cầu)"]
    ORCH --> TR["Safe trace + eval record"]
    ORCH --> OUT{"Evidence đủ<br/>và trong scope?"}
    OUT -->|đủ| DONE["completed + draft<br/>not_sent / not_published"]
    OUT -->|thiếu input| NI["needs_input"]
    OUT -->|thiếu evidence / rủi ro| NH["needs_human"]
    OUT -->|approval pending thật| AA["awaiting_approval"]
```

## 2. Workflow A — Pre-trip (dọc)
```mermaid
flowchart TD
    A0["validate trip_id"] -->|sai format| F["failed_validation"]
    A0 -->|thiếu| NI["needs_input"]
    A0 --> A1["get_trip_request"]
    A1 -->|not_found| F
    A1 --> A2["get_approval_status"]
    A2 --> A3["search_travel_policy<br/>(<=1 rewrite, top_k<=5)"]
    A3 --> A4["validate_trip_requirements<br/>(requirements.json)"]
    A4 --> A5["create_travel_checklist_draft<br/>(idempotent)"]
    A5 --> A6{"Outcome"}
    A6 -->|field thiếu| NI
    A6 -->|approval pending| AA["awaiting_approval"]
    A6 -->|rejected / cancelled / thiếu evidence| NH["needs_human"]
    A6 -->|approved + evidence đủ| C["completed"]
```

## 3. Workflow B — In-trip disruption (dọc)
```mermaid
flowchart TD
    B0["validate trip_id"] --> B1["get_itinerary"]
    B1 --> B2["xác định disruption<br/>từ observation"]
    B2 -->|không có disruption| C0["completed: không phát hiện gián đoạn"]
    B2 --> B3["search_travel_policy<br/>disruption / emergency"]
    B3 --> B4["create_escalation_or_support_draft<br/>(tách Itinerary fact | Policy guidance)"]
    B4 --> B5{"Guidance đủ<br/>và không cần chi tiền / đổi vé?"}
    B5 -->|có| C["completed"]
    B5 -->|không| NH["needs_human<br/>(tùy chọn request_approval → pending)"]
```

## 4. Workflow C — Post-trip expense (dọc)
```mermaid
flowchart TD
    C0["validate report_id"] --> C1["get_expense_report"]
    C1 --> C2["deterministic validation<br/>+ calculate_expense_summary"]
    C2 --> C3["search_travel_policy<br/>theo category liên quan"]
    C3 --> C4["create_expense_review_draft<br/>(facts + evidence + items cần kiểm tra)"]
    C4 --> C5{"Outcome"}
    C5 -->|thiếu receipt / field| NI["needs_input"]
    C5 -->|vượt ngưỡng / policy conflict| NH["needs_human"]
    C5 -->|sạch| C["completed"]
```

## 5. Data boundary
- Agent code không import trực tiếp `mock_systems/`; chỉ `tools/` được gọi vào đó.
- `user_context` đến từ application. Source of truth của trip/itinerary/approval/expense luôn là mock systems.
- Retrieved text là untrusted; không thay đổi allowlist, role hay outcome.
