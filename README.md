# Global Business Travel Operations Agent

Offline deterministic prototype for business travel operations across pre-trip preparation, in-trip disruption support, and post-trip expense pre-check. All travel, traveler, itinerary, approval, expense, and policy data are synthetic mock fixtures. No live bookings, payments, approvals, email deliveries, or external API calls are performed.

## Requirements and Installation

Requires Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execution

### Local Web Interface

```powershell
python -m travel_agent.app web --port 8080
```

The server listens on `http://127.0.0.1:8080`. It provides an interactive chat view, role selector, trace/memory inspector, Staff Handoff Queue view, Admin CSV download endpoints, and an Admin-only runtime data reset action.

The demo uses Vietnamese descriptions with familiar English labels (Chat, Trips, Drafts, Handoff, Audit log, Memory & Trace). Error messages are always in Vietnamese, including when the request is in English. They explain the reason and next step while retaining stable diagnostic codes such as `unauthorized_scope`. Tool error details are preserved in chat responses, workflow results, and safe traces.

Tab APIs require a selected mock `user_id`: Employees see only their trips and drafts; Reviewers can review all trips and drafts; Approvers use scoped read-only chat instead of browsing trips or drafts; audit logs and CSV exports require Admin. Handoff and chat history are limited to the current user, with Admin able to inspect all records. Switching the demo account clears the previous account's displayed data. This selector remains a local demo mechanism, not production authentication.

### Command-Line Interface

```powershell
# Interactive multi-turn chat
python -m travel_agent.app chat --user U-EMP-002 --session demo-1

# Single conversational request
python -m travel_agent.app message --user U-EMP-002 --text "My flight to Tokyo on Dec 8 is delayed, what should I do?"

# Direct workflow execution
python -m travel_agent.app run pretrip --user U-EMP-002 --id TRIP-2026-006
python -m travel_agent.app run intrip --user U-EMP-002 --id TRIP-2026-002
python -m travel_agent.app run posttrip --user U-EMP-002 --id EXP-2026-001

# Pending-only approval request (Employee trip owner only)
python -m travel_agent.app request-approval --user U-EMP-001 --trip TRIP-2026-001 --action escalation --summary "Please review the disruption details."

# Admin read-only views and CSV log inspection
python -m travel_agent.app admin-trips --user U-ADM-001
python -m travel_agent.app admin-audit --user U-ADM-001 --trip TRIP-2026-004
python -m travel_agent.app handoffs --status open
python -m travel_agent.app logs --limit 20
```

## Environment Configuration

| Variable | Default | Purpose |
|---|---|---|
| `TRAVEL_AGENT_DATA_DIR` | `data/` | Mock JSON fixtures directory |
| `TRAVEL_AGENT_DRAFT_DIR` | `data/drafts/` | Sandbox draft output directory |
| `TRAVEL_AGENT_MEMORY_DIR` | `data/memory/` | Session and preference JSON directory |
| `TRAVEL_AGENT_LOG_DIR` | `data/logs/` | UTF-8 BOM CSV log directory |
| `TRAVEL_AGENT_DEMO_TODAY` | System date | ISO date (`YYYY-MM-DD`) used to resolve `today` and `tomorrow` against mock schedules (`2026-12-01` to `2027-01-07`) |

## Routing Model

Requests are classified in `src/travel_agent/nlu.py` and executed in `src/travel_agent/conversation.py` across four routes:

1. `SELF_SERVE`: Executes authorized workflows (`pretrip`, `intrip`, `posttrip`), standalone policy Q&A with citations, mixed workflow + policy queries, explicit preference commands, or Admin read-only queries.
2. `CLARIFY` (`needs_input`): Requests clarification when a natural date or destination matches zero or multiple records, or when required trip/expense fields or receipts are missing.
3. `HANDOFF_STAFF` (`needs_human` / `awaiting_approval`): Escalates using a fixed template (`[HANDOFF TO STAFF | Ticket: HND-...]`) containing only verified tool facts and citations when evidence is missing or conflicting, approval is pending or rejected, a flight is cancelled, or an out-of-authority action is requested.
4. `REJECT_SAFETY` (`failed_validation` / `unauthorized_scope`): Rejects malformed IDs, prompt-injection or rule-bypass patterns, and unauthorized role or record access prior to side effects.

## Roles and Permissions

User identities and roles are resolved from `data/users.json` (`--user` is a local demo selector, not production authentication). Role-specific scenarios are documented in [`demo/DEMO_SCENARIOS.md`](demo/DEMO_SCENARIOS.md).

| User ID | Role | Permitted Operations | Restrictions |
|---|---|---|---|
| `U-EMP-001`, `U-EMP-002` | Employee | Read/process own trips, itineraries, expenses, checklists, own preferences, and pending `request_approval` for own trips | Denied access to other employees' records and Admin views |
| `U-REV-001` | Reviewer | Read and review all employees' trips, itineraries, expenses, drafts, and allowed policy chunks | Cannot call `request_approval` or Admin audit tools |
| `U-APR-001` | Approver | Read-only access limited to one application-supplied pending `approval_scope` and action-specific policy categories | Cannot browse out-of-scope records, write drafts, or decide approvals via agent tools |
| `U-ADM-001` | Admin | Read-only trip overview, audit history, Staff Handoff Queue view, CSV log downloads, and runtime demo reset (`POST /api/admin/reset`) | Cannot run Employee workflows, search policy RAG, write drafts, or access memory tools |

## Project Structure

```text
data/                     Mock JSON fixtures (trips, travelers, itineraries, approvals, expenses, policy_chunks, users)
  drafts/                 Idempotent sandbox draft JSON artifacts
  logs/                   UTF-8 BOM CSV files (chat_history.csv, handoff_queue.csv)
  memory/                 User-scoped preference and TTL session JSON files
demo/
  DEMO_SCENARIOS.md       Role-based scenario scripts
  run_demo.ps1            PowerShell demo sequence
  web_demo.py             Web UI entrypoint
src/travel_agent/
  app.py                  CLI and application boundary
  config.py               Centralized paths, budgets, and reference date
  nlu.py                  English normalizer, ID/date/destination extraction, clause splitter, 4-route classifier
  conversation.py         4-flow orchestrator, scoped lookup resolution, response formatting, handoff guard
  dispatcher.py           Allowlist, JSON Schema, role/scope authorization, and budget enforcement
  registry.py             19 registered tools and per-workflow allowlists
  logging_utils.py        Thread-safe UTF-8 BOM CSV logger with token/number redaction
  web_demo.py             Stdlib HTTP server and browser UI
  memory/                 Short-term session store (with TTL) and long-term preference store
  rag/                    Offline BM25, stemming, synonym expansion, version review, and lexical grounding
  workflows/              Pre-trip (A), In-trip (B), and Post-trip (C) modules
tests/                    Automated pytest suite
eval/                     Deterministic evaluation runner (31 cases) and reports
```

## Logging, Memory, and Verification

* Conversation turns are appended to `data/logs/chat_history.csv` and staff escalations to `data/logs/handoff_queue.csv` in UTF-8 BOM format with card/token redaction. Technical `data/audit_events.json` excludes raw user messages.
* Both `pytest` and `eval/run_eval.py` execute against temporary copies of `data/` and do not modify repository fixtures.

```powershell
python -m pytest -v
python eval/run_eval.py --label after
python -m compileall -q src tests eval demo
```

## Deliverables Index (Section 14 Compliance)

Full mapping with concrete evidence against the assignment specification is documented in [REQUIREMENTS_COMPLIANCE_EVIDENCE.md](REQUIREMENTS_COMPLIANCE_EVIDENCE.md).

| Deliverable | Specification Reference | Repository Location |
|---|---|---|
| **1. Source Code & CLI** | Section 14.1 | [src/travel_agent/](src/travel_agent/) |
| **2. Setup & Execution Guide** | Section 14.2 | [README.md](README.md) |
| **3. Mock Datasets & Policy Corpus** | Section 14.3 | [data/](data/) (`trips`, `travelers`, `itineraries`, `expenses`, `policy_chunks`) |
| **4. Agent Contract & Tool Cards** | Section 14.4 | [Given Docs/AGENTS.md](Given%20Docs/AGENTS.md), [Given Docs/TOOL_CARDS.md](Given%20Docs/TOOL_CARDS.md), [src/travel_agent/schemas/](src/travel_agent/schemas/) |
| **5. Architecture & Vertical Workflows** | Section 14.5 | [Given Docs/ARCHITECTURE.md](Given%20Docs/ARCHITECTURE.md) |
| **6. Memory Policy & Data Boundaries** | Section 14.6 | [Given Docs/MEMORY_AND_SAFETY.md](Given%20Docs/MEMORY_AND_SAFETY.md) |
| **7. Test Matrix & Root-Cause Taxonomy** | Section 14.7 | [Given Docs/TEST_MATRIX.md](Given%20Docs/TEST_MATRIX.md), [eval/reports/root_cause.md](eval/reports/root_cause.md) |
| **8. Baseline / After / Regression Report** | Section 14.8 | [eval/reports/baseline.md](eval/reports/baseline.md), [eval/reports/after.md](eval/reports/after.md), [eval/reports/regression.md](eval/reports/regression.md) |
| **9. Demo & Walkthrough** | Section 14.9 | [demo/DEMO_SCENARIOS.md](demo/DEMO_SCENARIOS.md), [demo/run_demo.ps1](demo/run_demo.ps1), [demo/web_demo.py](demo/web_demo.py) |
| **10. Limitations & Safety Boundaries** | Section 14.10 | [README.md](README.md#known-limitations) & [Given Docs/AGENTS.md](Given%20Docs/AGENTS.md) |
| **Bonus: Section 17 Self-Check Answers** | Section 17 | [REQUIREMENTS_COMPLIANCE_EVIDENCE.md#mục-17-giải-đáp-chi-tiết-6-câu-hỏi-tự-kiểm-tra-trước-khi-nộp-bài](REQUIREMENTS_COMPLIANCE_EVIDENCE.md#mục-17-giải-đáp-chi-tiết-6-câu-hỏi-tự-kiểm-tra-trước-khi-nộp-bài) |

## Known Limitations

* Intent routing (`nlu.py`) and BM25 retrieval (`rag/retriever.py`) are deterministic, offline, and English-only; no external LLM or semantic NLI model is used.
* Grounding (`rag/claim_evidence_check.py`) uses conservative lexical sentence and polarity matching.
* Local JSON and CSV files model a single training tenant and are not a production database, identity provider, or immutable audit store.
* No external travel booking, payment, email, or background scheduling integrations exist.
