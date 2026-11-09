# Global Business Travel Operations Agent

Offline training prototype for employee business travel operations. All business records are synthetic mock data. There are no real bookings, payments, approvals, email delivery, or third-party API calls.

## Setup

Requires Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run the demo

Run a supported message through the deterministic planner:

```powershell
python -m travel_agent.app message --user U-EMP-002 --text "Prepare checklist for TRIP-2026-006"
```

Or call a workflow explicitly:

```powershell
python -m travel_agent.app run pretrip --user U-EMP-002 --id TRIP-2026-006
python -m travel_agent.app run intrip --user U-EMP-002 --id TRIP-2026-002
python -m travel_agent.app run posttrip --user U-EMP-002 --id EXP-2026-001
```

Create a pending-only approval request (Employee must own the trip):

```powershell
python -m travel_agent.app request-approval --user U-EMP-001 --trip TRIP-2026-001 --action escalation --summary "Please review the disruption details."
```

Admin has read-only mock trip and audit views:

```powershell
python -m travel_agent.app admin-trips --user U-ADM-001
python -m travel_agent.app admin-audit --user U-ADM-001 --trip TRIP-2026-004
```

The CLI resolves roles from `data/users.json`; do not treat the local `--user` selector as production authentication. Approval requests and audit events persist in local JSON fixtures. Use a disposable copy of the project for demos that create new records.

## Checks and evaluation

```powershell
python -m pytest -q
python eval/run_eval.py --label baseline
python eval/run_eval.py --label after
```

Evaluation case results and metrics are stored under `eval/reports/`. The evaluator uses temporary copies of mock fixtures and does not alter project data.
For a short guided run of all three workflows and the Admin views, execute `./demo/run_demo.ps1` from the project root.

## Permission model

- Employee: own trip/expense data, policy RAG allowed by chunk ACL, own preference, and pending-only approval requests for own trips.
- Reviewer: read/review all mock travel data and allowed policy chunks; may create sandbox drafts.
- Approver: reads only facts needed for one application-supplied pending approval scope; RAG categories are limited by action; no decision or draft tools.
- Admin: read-only trip overview and audit history; no policy RAG, approval, draft, or business-write permissions.

Chunks are filtered by `allowed_roles` before retrieval ranking and citation. The Admin extension and audit log are still mock-only; the audit file has no automatic retention/deletion mechanism.

## Project documents

- `Given Docs/PLAN.md` — phases and status
- `Given Docs/ARCHITECTURE.md` — application, dispatcher, workflows, and data boundary
- `Given Docs/MEMORY_AND_SAFETY.md` — roles, scopes, memory, and safety rules
- `Given Docs/TEST_MATRIX.md` — acceptance cases and evaluation metrics
- `HANDOFF.md` / `CHANGELOG.md` / `TODO.md` — working agreement, history, and remaining work

## Known limitations

- The planner uses a small deterministic keyword/ID router; it is not an LLM and does not understand arbitrary requests.
- BM25 retrieval is lexical and offline. Grounding is a conservative lexical check, not semantic entailment.
- Fixtures model a single local training tenant and one mock Approver identity. They are not a production authorization or immutable audit service.
- No live employee data, identity provider, external integrations, scheduler, deployment, or production credential support.
