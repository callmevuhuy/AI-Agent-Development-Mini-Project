# Demo Scenarios — Global Business Travel Operations Agent

Use these scenarios in the Web Demo (`python -m travel_agent.app web --port 8080`) or CLI (`python -m travel_agent.app chat --user <USER_ID>`) to demonstrate natural-language handling, 4-flow routing, role boundaries, memory, and CSV logging.

> Note on dates: Synthetic trips in `data/trips.json` are scheduled between `2026-12-01` and `2027-01-07`. To test `"tomorrow"` against Tokyo (`2026-12-08`), set `$env:TRAVEL_AGENT_DEMO_TODAY="2026-12-07"` before starting the app.

---

## 1. Employee (`U-EMP-002` — Jamie Tran, Engineering)
*Unique role scope:* Own trips & expenses only, personal preferences, pending approval requests for own trips.

1. **Natural Pre-trip (no raw ID required):**
   * Prompt: `I am traveling to Sydney on Dec 31 for a workshop, what do I need to prepare?`
   * Expected: `SELF_SERVE` · `completed` — resolves `TRIP-2026-006`, shows natural trip details (route, dates, status) + policy sources + citations + sandbox draft ID.
2. **Natural In-trip Delay (no raw ID required):**
   * Prompt: `My flight to Tokyo on Dec 8 is delayed, what should I do?`
   * Expected: `SELF_SERVE` · `completed` — resolves `TRIP-2026-002` (`MOCK-202`, `Postponed / Delayed (+240 mins)`), separates flight facts from grounded policy guidance.
3. **Natural Post-trip Clean Expense:**
   * Prompt: `Please review my Tokyo trip expenses`
   * Expected: `SELF_SERVE` · `completed` — resolves `EXP-2026-001`, deterministic totals & citations.
4. **Unmatched Date Clarification:**
   * Prompt: `My flight tomorrow is delayed, what should I do?` (with default today = `2026-11-16`)
   * Expected: `CLARIFY` · `needs_input` — does not guess; informs user no trip exists on `2026-11-17` and lists Jamie's real Dec 2026 trips.
5. **Mixed Query (Workflow + Policy):**
   * Prompt: `Check my Sydney trip and what is the lodging cap?`
   * Expected: `SELF_SERVE` · `completed` — executes `pretrip` + answers lodging cap (`USD 250/night`).
6. **Strict Staff Handoff (Forbidden Action):**
   * Prompt: `Can you book a new hotel in Tokyo for me?`
   * Expected: `HANDOFF_STAFF` · `needs_human` — strict `[HANDOFF TO STAFF | Ticket: HND-...]` template with zero speculative claims, logged in `handoff_queue.csv`.
7. **Long-Term Preference + Cross-User Isolation:**
   * Prompt A: `Remember I prefer detailed answers` -> updates `data/memory/preferences/U-EMP-002.json`.
   * Prompt B: `Prepare checklist for TRIP-2026-001` (Alex's trip) -> `REJECT_SAFETY` (denied outside Employee scope).

---

## 2. Employee (`U-EMP-001` — Alex Nguyen, Sales)
1. **Ambiguous Upcoming Trip -> Multi-turn Clarification:**
   * Prompt 1: `Check my upcoming trip` -> `CLARIFY` listing `TRIP-2026-001` (Singapore) and `TRIP-2026-004` (London).
   * Prompt 2: `Singapore` -> resolves `TRIP-2026-001`, returns `HANDOFF_STAFF` (`awaiting_approval`, checklist preview drafted).
2. **Rejected Trip Blocking:**
   * Prompt: `Check my London trip status` -> `HANDOFF_STAFF` (`approval_rejected`).
3. **Meal Cap / Active Version Conflict:**
   * Prompt: `Review my Singapore trip expenses` -> `HANDOFF_STAFF` citing both `EXPENSE-MEALS` v1.0 (`USD 70`) and v2.0 (`USD 85`).

---

## 3. Reviewer (`U-REV-001` — Travel Operations Reviewer)
*Unique role capability:* Cross-employee inspection across **all** employees' trips, itineraries, expenses, and drafts; **cannot** call `request_approval` or `admin_*` tools.

1. `List all trips` -> shows all 6 employee trips (`EMP-001`..`EMP-004`).
2. `Review expense report EXP-2026-003` -> Reviewer can inspect Alex's expense report (unlike Jamie) and escalate conflict to Staff.
3. `Prepare checklist for TRIP-2026-003` -> inspects Taylor's Berlin draft missing `purpose` (`CLARIFY` · `needs_input`).

---

## 4. Approver (`U-APR-001` — Scoped Pending Reviewer)
*Unique role capability:* Strictly limited to one application-supplied pending `approval_scope` (`(trip_id, action_type)`) and action-specific RAG categories. Cannot create drafts, request approvals, or decide approvals via agent tools.

1. Select scope `TRIP-2026-001 · checklist_review`:
   * `Check trip TRIP-2026-001` -> `SELF_SERVE` (reads trip + approval status).
   * `What is the approval policy?` -> `SELF_SERVE` (`approval` category allowed).
   * `What is the meal allowance cap?` -> `REJECT_SAFETY` (`expense` category denied for Approver).
   * `Check flight delay on TRIP-2026-002` -> `REJECT_SAFETY` (outside `TRIP-2026-001` scope).

---

## 5. Admin (`U-ADM-001` — Governance & Audit Admin)
*Unique role capability:* Read-only all-trip overview, read-only audit history, CSV log downloads (`chat_history.csv`, `handoff_queue.csv`), and **Admin-only Reset button** (`POST /api/admin/reset`). Cannot run workflows or policy RAG.

1. `List all company trips` -> `SELF_SERVE` (`admin_list_trips`).
2. `Show audit log for TRIP-2026-004` -> `SELF_SERVE` (`admin_get_audit_history`).
3. `What is the meal allowance cap?` -> `REJECT_SAFETY` (Admin has no RAG access).
4. Click **Download chat_history.csv** / **Download handoff_queue.csv** (buttons visible only to Admin).
5. Click **Reset Trace, Memory & Logs** -> wipes runtime CSV logs, memory, drafts, non-seed audit events, and clears UI.
