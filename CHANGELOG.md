# Changelog

Project-level history. Dates are recorded when known; earlier milestone dates were not retained in the handoff context.

## 2026-11-16 — Documentation sync, requirements update, and clean release state

- Updated `requirements.txt` to include `jsonschema>=4.23`, `pytest>=8.0`, and `-e .` for single-step installation.
- Rewrote `README.md` with a neutral technical tone and `pip install -r requirements.txt` setup flow.
- Synchronized `Given Docs/` (`README.md`, `TOOL_CARDS.md`, `WORKFLOWS.md`, `MEMORY_AND_SAFETY.md`, `PLAN.md`, `TEST_MATRIX.md`) with the 19 registered tools, 4-flow routing, TTL session state, CSV logging, and Web Demo Admin controls.
- Restored `data/audit_events.json` to clean seed records prior to commit.

## 2026-11-16 — Issue fixes: Traveler details across all replies & detailed missing-checklist status breakdown

- Added `get_traveler_profile` to `intrip` and `posttrip` workflow allowlists (`src/travel_agent/registry.py`) and enriched authorized responses in `src/travel_agent/conversation.py` (`_enrich_trip_and_traveler`, `_trip_details_block`, `_format_trip_choice`, `_verified_facts`) so `Traveler: <Name> (<EMP-ID> · <Department>)` is displayed consistently across pre-trip, in-trip, post-trip, Reviewer lists, and Staff Handoff summaries (while preserving Approver/Admin profile boundaries).
- Added `_format_clarify_workflow` in `src/travel_agent/conversation.py` (with `validation` returned on missing-field stop in `a_pretrip.py` and `report` returned in `c_posttrip.py`) so `needs_input` replies explicitly report current checklist/review status, approval status, destination policy config, and exact missing fields/receipts.
- Expanded `tests/test_conversational_and_fixes.py` to cover both fixes.

## 2026-11-16 — Bugfix: Flight/departure date validation during natural-language lookup

- Investigated `data/logs/chat_history.csv`: asking `"My flight to Tokyo on Dec 9 is delayed..."` incorrectly matched `TRIP-2026-002` because `list_my_trips` checked `start_date <= date <= end_date` (`2026-12-08..2026-12-12`), ignoring that flight `MOCK-202` only flies on `2026-12-08`.
- Fixed `src/travel_agent/conversation.py` (`_resolve_natural_record`) to verify actual `flight.departure` / `flight.arrival` dates via `get_itinerary` for `intrip` flight queries and `trip.start_date` for `pretrip` queries, returning a `CLARIFY` prompt with exact recorded dates when mismatched.
- Extended `src/travel_agent/nlu.py` to also parse `YYYY/MM/DD` and `DD Month [YYYY]` (e.g. `9 Dec`) formats.
- Added regression assertions in `tests/test_conversational_and_fixes.py`.

## 2026-11-16 — Stage 5: Natural-language lookup (no raw IDs required), rich formatting, role showcase, Admin reset/export guard, and rewritten README

- Added scoped read-only lookup tools `list_my_trips` and `list_my_expenses` (Employee own-only, Reviewer all-records, Admin/Approver denied) with JSON schemas, dispatcher/registry/trace integration.
- Upgraded `src/travel_agent/nlu.py` and `src/travel_agent/conversation.py` to resolve natural English prompts without raw IDs via destination aliases, explicit dates, and relative dates (`today`/`tomorrow` using `config.get_demo_today()`), clarifying cleanly when multiple or zero trips match.
- Improved answer formatting with readable line breaks, corpus `source` labels alongside citations, and natural-language trip/flight details (Route, Departure/Arrival times, Airport, and Flight/Trip Status).
- Upgraded `src/travel_agent/web_demo.py`: added `U-APR-001` (Approver) scope support, role-specific sample prompts, automatic chat reset when switching users, Admin-only visibility and server-side `403` enforcement for CSV exports and the **Reset Trace, Memory & Logs** button (`POST /api/admin/reset`).
- Added `demo/DEMO_SCENARIOS.md`, updated `demo/run_demo.ps1`, and rewrote `README.md` for straightforward third-party setup and reproduction.
- Expanded `tests/test_conversational_and_fixes.py` (53 total pytest cases) and `eval/run_eval.py`. No commit or push performed.

## 2026-11-16 — Stage 4: Zero-dependency Web Demo UI, expanded test/eval suite, and documentation sync

- Added `src/travel_agent/web_demo.py` and `demo/web_demo.py` (plus `python -m travel_agent.app web`) providing an interactive browser UI using Python stdlib `http.server` (Chat, Role/User Switcher, Trace & Memory Inspector, Staff Handoff Queue, and UTF-8 CSV export downloads).
- Updated `demo/run_demo.ps1` to demonstrate all workflows, strict Staff Handoff, and CSV queue viewing.
- Added `tests/test_conversational_and_fixes.py` (8 comprehensive test cases covering Stage 1–4 fixes, English NLU, mixed queries, synonym RAG, short/long-term memory + TTL, strict handoff template, UTF-8 BOM CSV logging, and Web Demo HTTP endpoints).
- Expanded `eval/run_eval.py` from 25 to 29 cases and verified `after` evaluation (29/29 passed, 0 regressions).
- Updated `.gitignore`, `README.md`, `HANDOFF.md`, `TODO.md`, and `Given Docs/` (`ARCHITECTURE.md`, `WORKFLOWS.md`, `MEMORY_AND_SAFETY.md`, `TEST_MATRIX.md`).
- Verified: `pytest -v` (51 passed), `eval/run_eval.py --label after` (29/29 passed), `compileall`, and `git diff --check`. No commit or push performed.

## 2026-11-16 — Stage 3: Memory optimization, 4-flow orchestrator, strict handoff guard, and UTF-8 CSV logger

- Enhanced `src/travel_agent/memory/store.py` with `active_report_id`, `pending_slot`, `delete_session_value`, and session TTL (`_expires_at`), plus automatic test/temp directory isolation via `_storage._DATA_DIR`.
- Added `src/travel_agent/logging_utils.py` to log every turn to `data/logs/chat_history.csv` (UTF-8 BOM for Excel) and escalated cases to `data/logs/handoff_queue.csv` with sensitive-token redaction while keeping `audit_events.json` raw-message free.
- Added `src/travel_agent/conversation.py` implementing the 4-flow engine (`SELF_SERVE`, `CLARIFY`, `HANDOFF_STAFF`, `REJECT_SAFETY`), multi-turn session resolution, `preferred_output_format` response formatting, explicit preference management, and strict deterministic Staff Handoff templates (zero speculative explanations).
- Updated `src/travel_agent/app.py` with `chat_turn()`, interactive `chat` CLI, `handoffs`, `logs`, and updated `message` CLI command.
- Verified: `pytest -q` (43 passed). No commit or push performed.

## 2026-11-16 — Stage 2: English NLU router and enhanced offline RAG

- Added `src/travel_agent/nlu.py` with NFKC normalization, canonical & malformed ID detection, explicit preference command parsing, clause splitting for mixed workflow + policy queries, safety/adversarial detection, and 4-route classification (`SELF_SERVE`, `CLARIFY`, `HANDOFF_STAFF`, `REJECT_SAFETY`).
- Refactored `src/travel_agent/planner.py` to delegate to `nlu.route_message_intent` while keeping deterministic `plan()` compatibility.
- Upgraded `src/travel_agent/rag/retriever.py` with light English stemming, curated English domain synonym expansion (`hotel->lodging`, `food->meals`, `late->delay`, etc.), and expanded prompt-injection exclusion patterns.
- Verified: `pytest -q` (43 passed). No commit or push performed.

## 2026-11-16 — Stage 1: Core bug fixes, config centralization, and hardening

- Added `src/travel_agent/config.py` to centralize `DATA_DIR`, `DRAFT_DIR`, `MEMORY_DIR`, `LOG_DIR`, and budget/TTL defaults with env-var overrides.
- Fixed `calculate_expense_summary.py` and `workflows/c_posttrip.py` so `within_all_active_versions` meal items remain in `threshold_evaluations` without falsely triggering `threshold_flags` / `needs_human`.
- Fixed `workflows/a_pretrip.py` to evaluate blocking travel/approval statuses (`cancelled`/`rejected`) before stopping on `unknown_destination_requirements`, and raised `MAX_ALLOWED_STEPS` to 12 (default remains 8).
- Hardened `tools/_draft.py` (verify source trip/expense exists before creating drafts), `schemas/validate_trip_requirements.json` (`trip_id` required inside `trip_facts`), `trace.py` (`safe_arguments` for all 3 draft tools), `dispatcher.py` (unused import removed), and `mock_systems/approval.py` (`_REQUEST_LOCK` on `record_external_decision`).
- Fixed duplicate `U-ADM-001` row in `Given Docs/DATA_SPEC.md`.
- Verified: `pytest -q` (43 passed). No commit or push performed.

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
