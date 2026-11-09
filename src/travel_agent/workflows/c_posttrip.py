import re
from typing import Any

from travel_agent.orchestrator import run_tool
from travel_agent.state import RunState


_REPORT_ID = re.compile(r"^EXP-\d{4}-\d{3}$")
_CATEGORY_QUERY = {"meals": "meal", "ground_transport": "transport", "lodging": "lodging"}


def _stop(state: RunState, outcome: str, message: str, **details: Any) -> dict[str, Any]:
    state.finish(outcome)
    return {"outcome": outcome, "message": message, **details}


def run_posttrip(state: RunState, report_id: str | None) -> dict[str, Any]:
    """Create a deterministic, read-only expense pre-check for a mock report."""
    state.set_phase("posttrip_validation")
    if not isinstance(report_id, str) or not report_id:
        return _stop(state, "needs_input", "Please provide an expense report ID.")
    if not _REPORT_ID.fullmatch(report_id):
        return _stop(state, "failed_validation", "The expense report ID format is invalid.")

    state.set_phase("posttrip_report_lookup")
    report_result = run_tool(state, "get_expense_report", {"report_id": report_id})
    if not report_result["ok"]:
        error = report_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else (
            "failed_validation" if error["code"] == "not_found" else "partial"
        )
        return _stop(state, outcome, "Could not load the expense report.", error_code=error["code"])

    state.set_phase("posttrip_calculation")
    summary_result = run_tool(state, "calculate_expense_summary", {"report_id": report_id})
    if not summary_result["ok"]:
        error = summary_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Could not calculate the expense summary.", error_code=error["code"])
    summary = summary_result["data"]

    state.set_phase("posttrip_policy_retrieval")
    categories = [_CATEGORY_QUERY.get(category, category) for category in sorted(summary["category_totals"])]
    policy_result = run_tool(state, "search_travel_policy", {
        "query": f"expense {' '.join(categories)} receipt policy",
        "category": "expense",
        "max_results": 5,
    })
    if not policy_result["ok"]:
        error = policy_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Expense policy retrieval did not complete.", error_code=error["code"], summary=summary)
    evidence = [
        {
            "chunk_id": chunk["chunk_id"], "doc_id": chunk["doc_id"],
            "source": chunk["source"], "section": chunk["section"],
            "page": chunk.get("page"), "version": chunk["version"],
            "citation": chunk["citation"],
        }
        for chunk in policy_result["data"]["results"]
    ]
    review_preview = {
        "report_id": report_id,
        "summary": summary,
        "policy_evidence": evidence,
        "version_conflicts": policy_result["data"]["version_conflicts"],
        "resolved_versions": policy_result["data"]["resolved_versions"],
        "delivery_status": "not_published",
        "decision": "review_required",
    }

    has_policy_issue = bool(summary["threshold_conflicts"] or summary["threshold_flags"])
    has_missing_data = bool(summary["missing_fields"] or summary["missing_receipts"] or summary["invalid_items"])
    if policy_result["data"]["no_result"] or not evidence:
        outcome, message = "needs_human", "No usable expense policy evidence was retrieved."
    elif has_policy_issue:
        outcome, message = "needs_human", "Policy limits or conflicting active versions require reviewer assessment."
    elif has_missing_data:
        outcome, message = "needs_input", "The report is missing fields or receipts and needs follow-up."
    else:
        outcome, message = "completed", "The deterministic expense pre-check is ready for human review."

    state.set_phase("posttrip_draft")
    draft_result = run_tool(state, "create_expense_review_draft", {
        "report_id": report_id, "review_preview": review_preview,
    })
    if not draft_result["ok"]:
        error = draft_result["error"]
        draft_outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, draft_outcome, "The expense preview is ready, but the review draft was not saved.", error_code=error["code"], review_preview=review_preview)
    return _stop(state, outcome, message, review_preview=review_preview, draft=draft_result["data"])
