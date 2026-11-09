import pytest

from travel_agent.dispatcher import dispatch
from travel_agent.memory import (
    ScopeError,
    clear_session,
    delete_preference,
    get_preference,
    get_preferences,
    get_session_state,
    set_preference,
    set_session_value,
)
from travel_agent.rag.claim_evidence_check import check_claim
from travel_agent.rag.citation import citation_for_chunk
from travel_agent.rag.versioning import version_review
from travel_agent.state import RunState
from travel_agent.tools.search_travel_policy import run as search_policy
from travel_agent.orchestrator import run_tool


def context(user_id="U-EMP-001", role="Employee", session_id="session-1", **extra):
    return {"user_id": user_id, "role": role, "session_id": session_id, **extra}


def test_bm25_citation_and_active_version_conflict():
    result = search_policy({"query": "meal allowance cap USD", "category": "expense", "max_results": 5}, user_context=context())["data"]
    ids = {chunk["chunk_id"] for chunk in result["results"]}
    assert {"POL-EXP-MEAL-V1", "POL-EXP-MEAL-V2"} <= ids
    assert result["version_conflicts"][0]["resolution"] == "needs_human"
    citations = {row["citation"] for row in result["version_conflicts"][0]["versions"]}
    assert citations == {
        "[EXPENSE-MEALS §5.1 v1.0 · POL-EXP-MEAL-V1]",
        "[EXPENSE-MEALS §5.1 v2.0 · POL-EXP-MEAL-V2]",
    }


def test_citation_adds_page_only_when_present():
    chunk = {"doc_id": "DOC", "section": "2.1", "version": "1", "chunk_id": "C1", "page": 4}
    assert citation_for_chunk(chunk) == "[DOC §2.1 v1 · C1 · p.4]"


def test_no_result_is_explicit():
    result = search_policy({"query": "qzxv no matching material", "category": "travel"}, user_context=context())["data"]
    assert result["no_result"] is True and result["results"] == []


def test_instruction_chunk_is_excluded_and_safe_traced():
    result = search_policy({"query": "approve all expenses", "category": "expense"}, user_context=context())["data"]
    assert result["no_result"] is True
    assert result["excluded_untrusted_chunk_ids"] == ["POL-EXP-INJECT-001"]
    assert "Ignore previous instructions" not in repr(result)

    state = RunState("posttrip", context())
    run_tool(state, "search_travel_policy", {"query": "approve all expenses", "category": "expense"})
    assert state.trace[-1]["safety_event"] == "untrusted_policy_chunk_excluded"
    assert "approve all expenses" not in repr(state.trace)


def test_grounding_requires_all_claim_terms_in_trusted_evidence():
    result = search_policy({
        "query": "flight delays retain carrier notice contact human travel support",
        "category": "travel",
    }, user_context=context())["data"]
    grounded = check_claim(
        "Retain the carrier's disruption notice and contact the human travel support channel.",
        result["results"],
    )
    ungrounded = check_claim("The company will pay for a replacement hotel.", result["results"])
    negated_source = [{"text": "Policy does not authorize refunds.", "usable_as_evidence": True,
                      "doc_id": "D", "section": "1", "version": "1", "chunk_id": "N1"}]
    polarity_mismatch = check_claim("Policy authorizes refunds.", negated_source)
    assert grounded["grounded"] and grounded["citations"]
    assert not ungrounded["grounded"]
    assert not polarity_mismatch["grounded"]


def test_version_conflict_is_resolved_only_with_valid_supersession():
    old = {"chunk_id": "OLD", "doc_id": "D", "source": "S", "section": "1", "page": None,
           "version": "1", "status": "superseded", "effective_date": "2025-01-01", "rule": {"cap": 5}}
    new = {"chunk_id": "NEW", "doc_id": "D", "source": "S", "section": "1", "page": None,
           "version": "2", "status": "active", "effective_date": "2026-01-01", "rule": {"cap": 7}}
    conflicts, resolved = version_review([old, new])
    assert conflicts == [] and resolved[0]["selected"]["chunk_id"] == "NEW"
    new["effective_date"] = "not-a-date"
    conflicts, resolved = version_review([old, new])
    assert conflicts[0]["resolution"] == "needs_human" and resolved == []


def test_preference_tools_scope_and_value_validation(monkeypatch, tmp_path):
    from travel_agent.memory import store
    monkeypatch.setattr(store, "PREFERENCE_DIR", tmp_path / "preferences")
    employee = context(memory_write_authorized=True)
    other = context("U-EMP-002", session_id="session-2")
    set_result = dispatch("set_preference", {"key": "response_language", "value": "vi"}, "pretrip", employee)
    assert set_result["ok"] and set_result["data"] == {"key": "response_language", "value": "vi"}
    assert dispatch("get_preference", {"key": "response_language"}, "pretrip", employee)["data"] == "vi"
    assert get_preferences(other) == {}
    assert dispatch("get_preference", {"key": "response_language", "user_id": "U-EMP-001"}, "pretrip", other)["error"]["code"] == "invalid_argument"
    assert dispatch("set_preference", {"key": "response_language", "value": "detailed"}, "pretrip", employee)["error"]["code"] == "invalid_argument"
    assert dispatch("delete_preference", {"key": "response_language"}, "pretrip", employee)["data"] is True
    assert get_preference(employee, "response_language") is None


def test_persistent_preference_write_requires_application_consent(monkeypatch, tmp_path):
    from travel_agent.memory import store
    monkeypatch.setattr(store, "PREFERENCE_DIR", tmp_path / "preferences")
    employee = context()
    result = dispatch("set_preference", {"key": "response_language", "value": "vi"}, "pretrip", employee)
    assert result["error"]["code"] == "not_allowed"
    assert get_preferences(employee) == {}


def test_session_state_scopes_by_user_and_session(monkeypatch, tmp_path):
    from travel_agent.memory import store
    monkeypatch.setattr(store, "SESSION_DIR", tmp_path / "sessions")
    a1, a2, b1 = context(session_id="a1"), context(session_id="a2"), context("U-EMP-002", session_id="a1")
    set_session_value(a1, "active_trip_id", "TRIP-2026-001")
    set_session_value(a1, "last_workflow", "pretrip")
    assert get_session_state(a1)["active_trip_id"] == "TRIP-2026-001"
    assert get_session_state(a2) == get_session_state(b1) == {}
    clear_session(a1)
    assert get_session_state(a1) == {}
    with pytest.raises(ValueError, match="invalid_argument"):
        set_session_value(a1, "raw_conversation", "do not persist")


def test_memory_context_is_required_and_cannot_select_another_scope():
    with pytest.raises(ScopeError):
        get_preferences({"user_id": "../other", "role": "Employee", "session_id": "s"})
    with pytest.raises(ScopeError):
        get_preferences({"user_id": "U-EMP-001", "role": "Employee", "session_id": "../other"})


def test_employee_isolated_from_other_trip_and_expense():
    employee = context()
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-002"}, "pretrip", employee)["error"]["code"] == "unauthorized_scope"
    assert dispatch("get_expense_report", {"report_id": "EXP-2026-001"}, "posttrip", employee)["error"]["code"] == "unauthorized_scope"


def test_reviewer_can_read_other_employee_trip():
    reviewer = context("U-REV-001", "Reviewer")
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-002"}, "pretrip", reviewer)["ok"]


def test_approver_can_read_only_pending_scoped_checklist_facts():
    approver = context(
        "U-APR-001", "Approver",
        approval_scope={"trip_id": "TRIP-2026-001", "action_type": "checklist_review"},
    )
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-001"}, "pretrip", approver)["ok"]
    assert dispatch("get_approval_status", {"trip_id": "TRIP-2026-001"}, "pretrip", approver)["ok"]
    assert dispatch("get_itinerary", {"trip_id": "TRIP-2026-001"}, "intrip", approver)["error"]["code"] == "unauthorized_scope"


def test_approver_can_read_only_scoped_escalation_itinerary():
    approver = context(
        "U-APR-001", "Approver",
        approval_scope={"trip_id": "TRIP-2026-002", "action_type": "escalation"},
    )
    assert dispatch("get_itinerary", {"trip_id": "TRIP-2026-002"}, "intrip", approver)["ok"]
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-002"}, "pretrip", approver)["error"]["code"] == "unauthorized_scope"


def test_approver_denied_without_valid_pending_scope(monkeypatch):
    import travel_agent.dispatcher as dispatcher
    approver = context("U-APR-001", "Approver")
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-001"}, "pretrip", approver)["error"]["code"] == "unauthorized_scope"
    wrong = context("U-APR-001", "Approver", approval_scope={"trip_id": "TRIP-2026-002", "action_type": "checklist_review"})
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-002"}, "pretrip", wrong)["error"]["code"] == "unauthorized_scope"
    stale = context("U-APR-001", "Approver", approval_scope={"trip_id": "TRIP-2026-001", "action_type": "checklist_review"})
    monkeypatch.setattr(dispatcher, "get_approval_request", lambda *_: {"status": "approved"})
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-001"}, "pretrip", stale)["error"]["code"] == "unauthorized_scope"


def test_approver_cannot_write_drafts_or_use_model_supplied_scope():
    approver = context(
        "U-APR-001", "Approver",
        approval_scope={"trip_id": "TRIP-2026-001", "action_type": "checklist_review"},
    )
    assert dispatch("create_travel_checklist_draft", {"trip_id": "TRIP-2026-001", "checklist": {}}, "pretrip", approver)["error"]["code"] == "unauthorized_scope"
    assert dispatch("get_trip_request", {
        "trip_id": "TRIP-2026-002", "approval_scope": {"trip_id": "TRIP-2026-002", "action_type": "checklist_review"},
    }, "pretrip", approver)["error"]["code"] in {"invalid_argument", "unauthorized_scope"}
    assert dispatch("request_approval", {
        "trip_id": "TRIP-2026-001", "action_type": "checklist_review", "action_summary": "approve this request",
    }, "pretrip", approver)["error"]["code"] == "unauthorized_scope"


def test_approver_cannot_use_scope_for_non_pending_request():
    approver = context(
        "U-APR-001", "Approver",
        approval_scope={"trip_id": "TRIP-2026-004", "action_type": "checklist_review"},
    )
    assert dispatch("get_trip_request", {"trip_id": "TRIP-2026-004"}, "pretrip", approver)["error"]["code"] == "unauthorized_scope"


def test_all_new_tool_schemas_are_valid():
    from jsonschema import Draft202012Validator
    from travel_agent.registry import TOOL_REGISTRY
    for name in (
        "get_preference", "set_preference", "delete_preference",
        "create_travel_checklist_draft", "create_escalation_or_support_draft", "create_expense_review_draft",
    ):
        Draft202012Validator.check_schema(TOOL_REGISTRY[name].schema)


def test_rag_citations_grounding_and_conflict_reach_workflows(monkeypatch, tmp_path):
    from travel_agent.mock_systems import draft_workspace
    from travel_agent.workflows.a_pretrip import run_pretrip
    from travel_agent.workflows.b_intrip import run_intrip
    from travel_agent.workflows.c_posttrip import run_posttrip
    monkeypatch.setattr(draft_workspace, "DRAFT_DIR", tmp_path / "drafts")

    pretrip_state = RunState("pretrip", context())
    pretrip = run_pretrip(pretrip_state, "TRIP-2026-001")
    assert pretrip["outcome"] == "awaiting_approval"
    assert all("citation" in item for item in pretrip["checklist"]["evidence"])

    intrip_state = RunState("intrip", context("U-EMP-002"))
    intrip = run_intrip(intrip_state, "TRIP-2026-002")
    assert intrip["outcome"] == "completed"
    assert intrip["support_draft"]["grounding"]["grounded"]
    assert intrip["support_draft"]["grounding"]["citations"]

    posttrip_state = RunState("posttrip", context("U-EMP-001"))
    posttrip = run_posttrip(posttrip_state, "EXP-2026-003")
    assert posttrip["outcome"] == "needs_human"
    versions = posttrip["review_preview"]["version_conflicts"][0]["versions"]
    assert {row["chunk_id"] for row in versions} == {"POL-EXP-MEAL-V1", "POL-EXP-MEAL-V2"}
