import re
from typing import Any

from travel_agent.orchestrator import run_tool
from travel_agent.state import RunState


_REPORT_ID = re.compile(r"^EXP-\d{4}-\d{3}$")
_CATEGORY_QUERY = {"meals": "meal", "ground_transport": "transport", "lodging": "lodging"}


# Workflow State (Mục 9.1): Chốt trạng thái dừng và ghi nhận terminal outcome.
def _stop(state: RunState, outcome: str, message: str, **details: Any) -> dict[str, Any]:
    if details.get("error_code"):
        for observation in reversed(state.safe_tool_results):
            if observation.get("error_code") == details["error_code"]:
                details["error"] = {
                    "code": observation["error_code"],
                    "message": observation["error_message"],
                    "retryable": observation["retryable"],
                }
                message = observation["error_message"]
                break
    state.finish(outcome)
    return {"outcome": outcome, "message": message, **details}


# Workflow C (Mục 8.3): Rà soát báo cáo chi phí sau chuyến đi trước khi nộp theo chuỗi 6 bước chuẩn.
def run_posttrip(state: RunState, report_id: str | None) -> dict[str, Any]:
    """Create a deterministic, read-only expense pre-check for a mock report."""
    state.set_phase("posttrip_validation")
    if not isinstance(report_id, str) or not report_id:
        return _stop(state, "needs_input", "Vui lòng cung cấp mã báo cáo chi phí theo định dạng EXP-YYYY-NNN.")
    if not _REPORT_ID.fullmatch(report_id):
        return _stop(state, "failed_validation", "Mã báo cáo chi phí không hợp lệ. Hãy dùng định dạng EXP-YYYY-NNN.")

    state.set_phase("posttrip_report_lookup")
    report_result = run_tool(state, "get_expense_report", {"report_id": report_id})
    if not report_result["ok"]:
        error = report_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else (
            "failed_validation" if error["code"] == "not_found" else "partial"
        )
        return _stop(state, outcome, "Không tải được báo cáo chi phí. Hãy thử lại hoặc nhờ Reviewer hỗ trợ.", error_code=error["code"])
    report = report_result["data"]

    state.set_phase("posttrip_calculation")
    summary_result = run_tool(state, "calculate_expense_summary", {"report_id": report_id})
    if not summary_result["ok"]:
        error = summary_result["error"]
        outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, outcome, "Không tổng hợp được chi phí. Hãy nhờ Reviewer kiểm tra dữ liệu báo cáo.", error_code=error["code"])
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
        return _stop(state, outcome, "Tra cứu chính sách chi phí chưa hoàn tất. Hãy nhờ Reviewer hỗ trợ.", error_code=error["code"], summary=summary)
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

    has_policy_issue = bool(
        summary["threshold_conflicts"]
        or any(flag.get("status") != "within_all_active_versions" for flag in summary["threshold_flags"])
    )
    has_missing_data = bool(summary["missing_fields"] or summary["missing_receipts"] or summary["invalid_items"])
    if policy_result["data"]["no_result"] or not evidence:
        outcome, message = "needs_human", "Không tìm thấy căn cứ chính sách chi phí phù hợp. Cần Reviewer kiểm tra trước khi kết luận."
    elif has_policy_issue:
        outcome, message = "needs_human", "Có khoản chi chạm hạn mức hoặc xung đột giữa các phiên bản chính sách. Cần Reviewer rà soát."
    elif has_missing_data:
        outcome, message = "needs_input", "Báo cáo thiếu thông tin hoặc chứng từ. Vui lòng bổ sung các mục được liệt kê."
    else:
        outcome, message = "completed", "The deterministic expense pre-check is ready for human review."

    state.set_phase("posttrip_draft")
    draft_result = run_tool(state, "create_expense_review_draft", {
        "report_id": report_id, "review_preview": review_preview,
    })
    if not draft_result["ok"]:
        error = draft_result["error"]
        draft_outcome = "failed_budget" if error["code"] == "budget_exceeded" else "partial"
        return _stop(state, draft_outcome, "Đã chuẩn bị nội dung rà soát chi phí nhưng chưa lưu được bản nháp. Hãy thử lại hoặc nhờ người quản trị kiểm tra.", error_code=error["code"], report=report, review_preview=review_preview)
    return _stop(state, outcome, message, report=report, review_preview=review_preview, draft=draft_result["data"])
