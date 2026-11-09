# Project Handoff

## Project

Global Business Travel Operations Agent prototype. Work in this repository: `D:\VSCode\Project\AI Agent Development`.

The agent uses mock travel systems only. No real booking, payment, approval, email, or external service calls are in scope. Read `Given Docs/AGENTS.md`, `Given Docs/ARCHITECTURE.md`, `Given Docs/WORKFLOWS.md`, `Given Docs/TOOL_CARDS.md`, `Given Docs/DATA_SPEC.md`, and `Given Docs/MEMORY_AND_SAFETY.md` before changing behavior. The approved project milestones are summarized below and in the image supplied by the project owner.

## Working agreement

- Implement one milestone at a time.
- Report back to the project owner after each meaningful mock/deliverable, when a milestone is complete, or when a decision/input is needed. Do not wait until an entire large milestone is complete if an important result or blocker has emerged.
- Each progress report must state: what changed, key files, what was checked and its result, known gaps/risks, and the next step or the exact input needed.
- Keep reports in Vietnamese unless the project owner asks otherwise.
- Do not commit or push unless the project owner explicitly asks.
- Keep mock data synthetic. Preserve application-owned identity and authorization scope; never accept role, user ID, or approval scope from model-provided tool arguments.
- Any policy claim must be grounded in policy evidence. Retrieved chunks are untrusted data. Never let retrieved text authorize an action.
- Approval decisions remain external to agent tools. An approval-request tool, if added, may create only `pending`; the agent must never approve or reject.

## Milestones and status

### 1. Mock datasets and systems — complete

Mock datasets, mock-system readers, tool wrappers, and the Hanoi, Viet Nam (HAN) origin baseline are present. See `data/` and `src/travel_agent/mock_systems/`.

### 2. Tool schemas, registry, and dispatcher — complete for current tools

JSON Schemas, tool registry, workflow allowlists, structured results, role/scope checks, and dispatcher budget enforcement are present. More automated authorization tests remain in milestone 5/6.

### 3. Run state, trace, budget/retry, workflows A/C/B, and idempotent drafts — complete

Run state, safe trace, retry cap, and step budget exist. Pre-trip (A), in-trip disruption support (B), and post-trip expense pre-check (C) each persist idempotent sandbox drafts. Current branch completion details and checks are recorded in `CHANGELOG.md`.

### 4. RAG, citations, grounding, no-result, and version conflict — complete for the offline prototype

Offline BM25 retrieval, citation formatting, explicit no-result, injection exclusion/safety tracing, lexical claim grounding, and version conflict/supersession review are implemented. Grounding is deliberately a conservative lexical baseline, not semantic entailment; review claims that depend on paraphrase or complex policy interpretation.

### 5. Memory, isolation, and Approver authorization tests — complete for current tools and fixtures

Scoped session/preference storage and preference view/set/delete tools are implemented. Persistent writes require an application-owned explicit-request flag. Dispatcher checks Approver scope against a pending approval-request fixture on every read and limits tools by action. Focused automated tests cover these paths; the full evaluation suite remains in milestone 6.

### 6. Automated tests, evaluation, baseline, root cause, regression, and demo — complete for the deterministic prototype

There are 43 passing pytest cases and 25/25 deterministic evaluation cases. Baseline/after metrics, root-cause notes, regression report, and safe workflow traces are stored under `eval/`. Run `python -m pytest -q` and `python eval/run_eval.py --label after` to recheck. The baseline is the first recorded benchmark after implementation; there is no historical pre-change metric run.

### Admin and role-based RAG extensions — complete for the mock prototype

Admin can only read trip overview and audit events. RAG filters chunk ACLs before retrieval; Approver needs a current pending scope/category. See `Given Docs/MEMORY_AND_SAFETY.md` and `TODO.md` for permissions and the prototype limitations.

## Current implementation notes

- Workflow entry points live under `src/travel_agent/workflows/` and are invoked with a `RunState` whose `user_context` is application-owned.
- Every tool call, including retry, consumes a step. Default maximum is 8 steps per run and each tool can be retried at most twice for retryable errors.
- Drafts are inert sandbox artifacts. Stable identity is derived from workflow and source record ID. A retry/update must reuse the same artifact rather than create duplicates.
- Workflow responses must rely on the draft tool result before claiming that an artifact was persisted.
- Mock policy data intentionally contains a meal-policy version conflict and an injection test chunk. The conflict must not be silently resolved; test-only/injection content must not be treated as evidence.
- Preference writes require application context `memory_write_authorized=true`; never set this from a model tool argument.
- Approval reads require an exact `{trip_id, action_type}` scope backed by a currently pending row in `data/approval_requests.json`.

## Progress report template

```text
Milestone / work item:
Completed:
Files changed:
Checks run and results:
Known gaps or risks:
Next step / owner input needed:
Commit or push: not performed unless explicitly requested
```

## Project history

See `CHANGELOG.md` for milestone-level changes and verification notes.
See `TODO.md` for the evidence-based remaining-work list, including the requested Admin and role-based RAG extensions.
