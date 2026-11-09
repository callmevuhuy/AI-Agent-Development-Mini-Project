# Changelog

Project-level history. Dates are recorded when known; earlier milestone dates were not retained in the handoff context.

## 2026-11-09 — Phase 6 and remaining TODOs completed

- Added deterministic application/planner entry points and a CLI demo for all three workflows, pending-only approval requests, and Admin read views.
- Registered idempotent Employee-owned `request_approval`; added external mock decision helper with Approver validation and append-only workflow/request/decision audit events.
- Added Admin read-only trip/audit tools. Added per-chunk `allowed_roles`, role/scope checks before RAG retrieval, and pre-ranking corpus filtering.
- Expanded synthetic datasets for Admin, audit history, role ACL and distinct expense outcomes. Fixed irrelevant policy conflicts blocking expense reports without affected categories.
- Added acceptance/authorization tests and deterministic evaluator. Final checks: 43 pytest cases passed; 25/25 evaluation cases passed; sample traces and metrics saved under `eval/`; compile and diff checks passed.
- No commit or push performed.

## 2026-11-09 — A–Z status audit and TODO

- Added `TODO.md` with remaining acceptance work and separate Admin/RAG role-authorization extensions.
- Compared assignment requirements, project docs, implementation, mock data and current tests. Confirmed the mock dataset minimum counts are present (6 trips, 4 travelers, 5 itineraries, 3 expenses, 13 policy chunks).
- Audit confirmed `request_approval` remains documented but is not registered; there is no planner/application entry point, eval runner/report or demo artifact. Existing 19 tests are focused RAG/memory/Approver tests, not the full acceptance matrix.
- No source behavior changed; no commit or push performed.

## 2026-11-09 — Section 3 completed

- Added `HANDOFF.md` with milestone plan, working agreement, progress-report requirements, current status, and handoff template.
- Added `data/drafts/` mock workspace with atomic JSON upsert and stable SHA-256 draft IDs derived from `(workflow, source_id)`.
- Added dispatcher-registered draft tools for pre-trip checklist, in-trip support, and post-trip expense review; employee draft access is checked against ownership.
- Connected all three workflows to saved drafts. Pre-trip uses validator-provided approval status to keep the Sydney workflow within the 8-step budget.
- Added in-trip disruption handling for delay, cancellation, missing disruption details, and no-disruption cases. No booking, spend, send, approval, or publish action is performed.
- Updated workflow/data/agent docs and ignored generated draft JSON artifacts.
- Checks: assert-based workflow and draft idempotency/access smoke checks, Python compilation, and `git diff --check` passed. Pytest/evaluation were not run.

## 2026-11-09 — Sections 4 and 5 completed for the prototype

- Replaced token overlap with dependency-free offline BM25 retrieval and added citation rendering that preserves doc/section/version/chunk/page metadata.
- Added explicit no-result output, instruction-like chunk exclusion with safe trace events, lexical claim grounding with sentence and polarity checks, and version conflict/supersession review.
- Connected grounding and citation evidence to the in-trip workflow; connected conflict metadata to pre-trip and expense review drafts.
- Added user-scoped preference and session stores. Preference values are whitelisted; persistent preference writes/deletes require an application-owned explicit-request flag. Tool arguments cannot select another user or session.
- Added a separate pending `approval_requests.json` fixture. Approver dispatcher access now requires an exact application-owned scope backed by a pending fixture row and applies action-specific read allowlists.
- Added 19 focused pytest cases covering RAG, citations, grounding, no-result, injection, version conflict, memory isolation, reviewer access, and Approver allow/deny paths.
- Checks: `pytest -q` passed (19); Python compilation and `git diff --check` passed. Full project eval/baseline/demo remain for milestone 6.

## Earlier project milestones — date not recorded

- Added synthetic Hanoi (HAN) travel, traveler, itinerary, approval, expense, requirements, and policy fixtures with mock-system readers.
- Added JSON Schema-backed tools, registry, per-workflow allowlists, dispatcher authorization, structured errors, and step budget checks.
- Added run state, safe trace with redaction, retry cap, and terminal outcomes.
- Implemented pre-trip checklist preview and post-trip expense pre-check preview. At this point neither persisted a draft, and in-trip workflow was not implemented.
- Smoke checks were used during development; pytest/evaluation suite had not yet been run.
