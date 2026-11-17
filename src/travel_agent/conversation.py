"""4-flow conversational orchestrator with natural entity lookup, memory, strict handoff, and CSV logging."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from travel_agent.errors import ERROR_MESSAGES, error_text, role_error
from travel_agent.logging_utils import log_chat_turn
from travel_agent.memory import (
    delete_session_value,
    get_preferences,
    get_session_state,
    set_session_value,
)
from travel_agent.mock_systems.approval import record_audit_event
from travel_agent.mock_systems.user import get_user
from travel_agent.nlu import RouteDecision, normalize_text, route_message_intent
from travel_agent.orchestrator import run_tool
from travel_agent.rag.query_rewrite import rewrite_query
from travel_agent.state import RunState
from travel_agent.workflows.a_pretrip import run_pretrip
from travel_agent.workflows.b_intrip import run_intrip
from travel_agent.workflows.c_posttrip import run_posttrip


_WORKFLOWS = {"pretrip": run_pretrip, "intrip": run_intrip, "posttrip": run_posttrip}
_CONTEXT_PRONOUNS = re.compile(r"\b(?:it|this|that|the trip|my trip|this trip|this report|my report|same trip)\b", re.IGNORECASE)
_FLIGHT_STATUS_LABELS = {
    "scheduled": "Scheduled",
    "departed": "Departed",
    "arrived": "Arrived",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "delayed": "Postponed / Delayed",
    "postponed": "Postponed / Delayed",
}
_TRIP_STATUS_LABELS = {
    "draft": "Draft (Incomplete)",
    "submitted": "Submitted",
    "confirmed": "Confirmed",
    "cancelled": "Cancelled",
}


def _human_flight_status(status: str | None, disruption: dict[str, Any] | None = None) -> str:
    label = _FLIGHT_STATUS_LABELS.get(str(status or "").casefold(), str(status or "Unknown").title())
    if isinstance(disruption, dict) and disruption.get("delay_minutes"):
        return f"{label} (+{disruption['delay_minutes']} mins)"
    return label


def _human_trip_status(status: str | None) -> str:
    return _TRIP_STATUS_LABELS.get(str(status or "").casefold(), str(status or "Unknown").title())


def _fmt_iso_dt(raw: str | None) -> str:
    if not isinstance(raw, str) or "T" not in raw:
        return raw or "N/A"
    date_part, time_part = raw.split("T", 1)
    return f"{date_part} {time_part}"


def _extract_citations(result: dict[str, Any]) -> list[str]:
    citations: list[str] = []
    for key in ("checklist", "support_draft", "review_preview"):
        container = result.get(key)
        if not isinstance(container, dict):
            continue
        for item in container.get("evidence", []) + container.get("policy_evidence", []):
            if isinstance(item, dict) and isinstance(item.get("citation"), str):
                citations.append(item["citation"])
        for conflict in container.get("version_conflicts", []):
            for ver in conflict.get("versions", []):
                if isinstance(ver, dict) and isinstance(ver.get("citation"), str):
                    citations.append(ver["citation"])
        grounding = container.get("grounding")
        if isinstance(grounding, dict):
            citations.extend(c for c in grounding.get("citations", []) if isinstance(c, str))
    return list(dict.fromkeys(citations))


def _format_evidence_lines(result: dict[str, Any], max_items: int | None = None) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for key in ("checklist", "support_draft", "review_preview"):
        container = result.get(key)
        if not isinstance(container, dict):
            continue
        for item in container.get("evidence", []) + container.get("policy_evidence", []):
            if not isinstance(item, dict):
                continue
            cit = item.get("citation")
            if not isinstance(cit, str) or cit in seen:
                continue
            seen.add(cit)
            src = item.get("source", "Policy Corpus")
            sec = item.get("section", "")
            ver = item.get("version", "")
            lines.append(f"  - {src} (§{sec}, v{ver}) {cit}")
    if max_items is not None:
        return lines[:max_items]
    return lines


def _traveler_label(traveler: dict[str, Any] | None, fallback_id: str | None = None) -> str | None:
    if isinstance(traveler, dict) and traveler.get("traveler_id"):
        name = traveler.get("display_name")
        dept = traveler.get("department")
        tid = traveler["traveler_id"]
        if name and dept:
            return f"{name} ({tid} · {dept})"
        if name:
            return f"{name} ({tid})"
        return tid
    return fallback_id


def _lookup_traveler(user: dict[str, Any], user_context: dict[str, Any], traveler_id: str | None) -> dict[str, Any] | None:
    if not traveler_id or user.get("role") not in {"Employee", "Reviewer"}:
        return None
    res = run_tool(
        RunState("pretrip", user_context, phase="traveler_lookup"),
        "get_traveler_profile",
        {"traveler_id": traveler_id},
    )
    return res["data"] if res.get("ok") and isinstance(res.get("data"), dict) else None


def _enrich_trip_and_traveler(
    result: dict[str, Any],
    user: dict[str, Any],
    user_context: dict[str, Any],
    resolved_trip: str | None,
) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("error_code") == "unauthorized_scope" or result.get("outcome") == "failed_validation":
        return result
    if user.get("role") not in {"Employee", "Reviewer"}:
        return result

    trip = result.get("trip")
    trip_id = resolved_trip or (result.get("report") or {}).get("trip_id") or (result.get("support_draft") or {}).get("trip_id")
    if not isinstance(trip, dict) and trip_id:
        trip_res = run_tool(
            RunState("pretrip", user_context, phase="trip_context_lookup"),
            "get_trip_request",
            {"trip_id": trip_id},
        )
        if trip_res.get("ok") and isinstance(trip_res.get("data"), dict):
            trip = trip_res["data"]
            result["trip"] = trip

    traveler_id = (
        (trip.get("traveler_id") if isinstance(trip, dict) else None)
        or ((result.get("report") or {}).get("traveler_id"))
    )
    traveler = _lookup_traveler(user, user_context, traveler_id)
    if traveler:
        result["traveler"] = traveler
    return result


def _is_vietnamese(text: str, user_context: dict[str, Any]) -> bool:
    """Detect whether user input or preference requires Vietnamese response formatting."""
    if user_context.get("role") in {"Employee", "Reviewer", "Approver"}:
        pref = get_preferences(user_context)
        if pref.get("response_language") == "vi":
            return True
        if pref.get("response_language") == "en":
            return False
    vn_chars = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    if any(c in text.lower() for c in vn_chars):
        return True
    from travel_agent.nlu import _unaccent
    vn_keywords = {
        "chuyen", "bay", "di", "toi", "cua", "bi", "tre", "hoan", "chuan", "bi", "chi",
        "phi", "khach", "san", "han", "muc", "duyet", "liet", "ke", "nhat", "ky", "kiem", "toan"
    }
    tokens = set(re.findall(r"\w+", _unaccent(text.lower())))
    return len(tokens & vn_keywords) >= 2


def _trip_details_block(result: dict[str, Any], is_vi: bool = False) -> list[str]:
    lines: list[str] = []
    trip = result.get("trip")
    traveler = result.get("traveler")
    traveler_line = _traveler_label(
        traveler,
        (trip.get("traveler_id") if isinstance(trip, dict) else None)
        or (result.get("report") or {}).get("traveler_id"),
    )
    if isinstance(trip, dict):
        origin = trip.get("origin", "Unknown")
        ap = f" ({trip['origin_airport']})" if trip.get("origin_airport") else ""
        dest = trip.get("destination", "Unknown")
        purpose = trip.get("purpose")
        lines.append("Thông tin chuyến đi (Trip Details):" if is_vi else "Trip Details:")
        if traveler_line:
            lines.append(f"  - Traveler: {traveler_line}")
        if is_vi:
            lines.extend([
                f"  - Tuyến đi (Route): {origin}{ap} -> {dest}",
                f"  - Lịch trình (Dates): {trip.get('start_date', 'N/A')} đến {trip.get('end_date', 'N/A')}",
                f"  - Mục đích (Purpose): {purpose if isinstance(purpose, str) and purpose.strip() else '[MISSING — required]'}",
                f"  - Trạng thái chuyến đi (Trip Status): {_human_trip_status(trip.get('travel_status'))}",
            ])
        else:
            lines.extend([
                f"  - Route: {origin}{ap} -> {dest}",
                f"  - Dates: {trip.get('start_date', 'N/A')} to {trip.get('end_date', 'N/A')}",
                f"  - Purpose: {purpose if isinstance(purpose, str) and purpose.strip() else '[MISSING — required]'}",
                f"  - Trip Status: {_human_trip_status(trip.get('travel_status'))}",
            ])
    elif traveler_line:
        lines.extend(["Thông tin người đi (Traveler Details):" if is_vi else "Traveler Details:", f"  - Traveler: {traveler_line}"])
    flight = result.get("flight_facts") or (result.get("support_draft") or {}).get("flight_facts")
    disruption = (result.get("support_draft") or {}).get("disruption")
    if isinstance(flight, dict) and flight:
        o_ap = f" ({flight['origin_airport']})" if flight.get("origin_airport") else ""
        d_ap = f" ({flight['destination_airport']})" if flight.get("destination_airport") else ""
        if lines:
            lines.append("")
        header = f"Thông tin chuyến bay (Flight Details - {flight.get('flight_id', 'N/A')}):" if is_vi else f"Flight Details ({flight.get('flight_id', 'N/A')}):"
        if is_vi:
            lines.extend([
                header,
                f"  - Khởi hành: {flight.get('origin', 'Unknown')}{o_ap} lúc {_fmt_iso_dt(flight.get('departure'))}",
                f"  - Đến nơi: {flight.get('destination', 'Unknown')}{d_ap} lúc {_fmt_iso_dt(flight.get('arrival'))}",
                f"  - Trạng thái chuyến bay (Flight Status): {_human_flight_status(flight.get('status'), disruption)}",
            ])
        else:
            lines.extend([
                header,
                f"  - Departure: {flight.get('origin', 'Unknown')}{o_ap} at {_fmt_iso_dt(flight.get('departure'))}",
                f"  - Arrival: {flight.get('destination', 'Unknown')}{d_ap} at {_fmt_iso_dt(flight.get('arrival'))}",
                f"  - Flight Status: {_human_flight_status(flight.get('status'), disruption)}",
            ])
    hotel = result.get("hotel")
    if isinstance(hotel, dict) and hotel.get("name"):
        lines.append(f"  - Khách sạn (Hotel): {hotel['name']} ({hotel.get('check_in', '')} đến {hotel.get('check_out', '')})" if is_vi else f"  - Hotel: {hotel['name']} ({hotel.get('check_in', '')} to {hotel.get('check_out', '')})")
    return lines


def _verified_facts(result: dict[str, Any], trip_id: str | None, report_id: str | None) -> str:
    facts: list[str] = []
    if trip_id:
        facts.append(f"trip_id={trip_id}")
    if report_id:
        facts.append(f"report_id={report_id}")
    trip = result.get("trip")
    traveler_line = _traveler_label(
        result.get("traveler"),
        (trip.get("traveler_id") if isinstance(trip, dict) else None) or (result.get("report") or {}).get("traveler_id"),
    )
    if traveler_line:
        facts.append(f"traveler={traveler_line}")
    if isinstance(trip, dict):
        facts.append(f"route={trip.get('origin')} -> {trip.get('destination')} ({trip.get('start_date')}..{trip.get('end_date')})")
        facts.append(f"trip_status={_human_trip_status(trip.get('travel_status'))}")
    flight = result.get("flight_facts") or (result.get("support_draft") or {}).get("flight_facts")
    disruption = (result.get("support_draft") or {}).get("disruption")
    if isinstance(flight, dict) and flight:
        facts.append(f"flight={flight.get('flight_id')} ({_human_flight_status(flight.get('status'), disruption)})")
    if isinstance(result.get("draft"), dict):
        draft = result["draft"]
        facts.append(f"draft_id={draft.get('draft_id')} ({draft.get('delivery_status')})")
    validation = result.get("validation")
    if isinstance(validation, dict):
        if validation.get("trip_approval_status"):
            facts.append(f"approval_status={validation['trip_approval_status']}")
        if validation.get("blocking"):
            facts.append(f"blocking={','.join(validation['blocking'])}")
        if validation.get("missing_policy_categories"):
            facts.append(f"missing_categories={','.join(validation['missing_policy_categories'])}")
    review = result.get("review_preview")
    if isinstance(review, dict):
        summary = review.get("summary", {})
        if isinstance(summary, dict):
            if summary.get("total") is not None:
                facts.append(f"total={summary['total']} {summary.get('currency', '')}".strip())
            if summary.get("threshold_flags"):
                facts.append(f"threshold_flags={len(summary['threshold_flags'])}")
            if summary.get("threshold_conflicts"):
                facts.append(f"threshold_conflicts={len(summary['threshold_conflicts'])}")
    return "; ".join(facts)


def _format_handoff_response(
    handoff_id: str,
    reason: str,
    facts_summary: str,
    citations: list[str],
    output_format: str,
    result: dict[str, Any] | None = None,
    is_vi: bool = False,
) -> str:
    """Strictly deterministic handoff message: clean layout, verified facts only, zero improvised claims."""
    lines = [
        f"[HANDOFF TO STAFF | Ticket: {handoff_id}]",
        "",
        f"Lý do chuyển tiếp (Reason): {reason}" if is_vi else f"Reason: {reason}",
    ]
    detail_lines = _trip_details_block(result or {}, is_vi=is_vi)
    if detail_lines:
        lines.append("")
        lines.extend(detail_lines)
    if facts_summary:
        lines.extend(["", f"Tóm tắt dữ kiện xác thực (Verified Summary): {facts_summary}" if is_vi else f"Verified Summary: {facts_summary}"])
    ev_lines = _format_evidence_lines(result or {}, max_items=3 if output_format == "concise" else None)
    if ev_lines:
        lines.extend(["", "Căn cứ chính sách tham chiếu (Policy Sources Referenced):" if is_vi else "Policy Sources Referenced:"])
        lines.extend(ev_lines)
    elif citations:
        limit = 3 if output_format == "concise" else len(citations)
        lines.extend(["", f"Trích dẫn đã ghi nhận (Recorded Citations): {' ; '.join(citations[:limit])}" if is_vi else f"Recorded Citations: {' ; '.join(citations[:limit])}"])
    lines.extend([
        "",
        "Bước tiếp theo: Yêu cầu được lưu trong hàng đợi demo để Travel Operations xem xét."
        if is_vi
        else "Next Step: This case is queued for Travel Operations Staff.",
    ])
    return "\n".join(lines)


def _format_workflow_success(
    workflow: str,
    result: dict[str, Any],
    citations: list[str],
    output_format: str,
    policy_note: str | None = None,
    is_vi: bool = False,
) -> str:
    draft = result.get("draft", {})
    draft_info = f"Draft {draft.get('draft_id')} ({draft.get('delivery_status')})" if isinstance(draft, dict) and draft.get("draft_id") else "No draft created"
    
    msg = result.get("message", "")
    if is_vi:
        if workflow == "pretrip":
            msg = "Checklist chuẩn bị chuyến công tác đã sẵn sàng."
        elif workflow == "intrip":
            msg = "Hướng dẫn xử lý sự cố chuyến bay đã sẵn sàng."
        elif workflow == "posttrip":
            msg = "Kiểm toán báo cáo chi phí hoàn tất đối chiếu với các định mức chính sách doanh nghiệp."

    lines = [f"[{workflow.upper()} | COMPLETED]", msg]

    detail_lines = _trip_details_block(result, is_vi=is_vi)
    if detail_lines:
        lines.append("")
        lines.extend(detail_lines)

    if workflow == "intrip" and isinstance(result.get("support_draft"), dict):
        follow_up = result["support_draft"].get("recommended_follow_up")
        if follow_up:
            lines.extend(["", "Hướng dẫn có căn cứ (Grounded Guidance):" if is_vi else "Grounded Guidance:", f"  - {follow_up}"])

    if workflow == "posttrip" and isinstance(result.get("review_preview"), dict):
        summary = result["review_preview"].get("summary", {})
        if isinstance(summary, dict) and summary:
            lines.extend([
                "",
                "Tóm tắt chi phí (Expense Summary):" if is_vi else "Expense Summary (Deterministic):",
                f"  - Report ID: {summary.get('report_id')} | Total: {summary.get('total')} {summary.get('currency', '')}",
                f"  - Category Totals: {summary.get('category_totals')}",
            ])

    ev_lines = _format_evidence_lines(result, max_items=3 if output_format == "concise" else None)
    if ev_lines:
        lines.extend(["", "Căn cứ chính sách trích dẫn (Policy Sources Cited):" if is_vi else "Policy Sources Cited:"])
        lines.extend(ev_lines)
    elif citations:
        lines.extend(["", f"Trích dẫn (Citations): {' ; '.join(citations[:3] if output_format == 'concise' else citations)}" if is_vi else f"Citations: {' ; '.join(citations[:3] if output_format == 'concise' else citations)}"])

    if policy_note:
        lines.extend(["", "Giải đáp chính sách bổ sung (Policy Q&A):" if is_vi else "Additional Policy Q&A:", f"  {policy_note}"])

    if output_format == "detailed":
        lines.extend(["", f"Sản phẩm Sandbox (Sandbox Artifact): {draft_info}" if is_vi else f"Sandbox Artifact: {draft_info}"])
    else:
        lines.extend(["", f"Sản phẩm (Artifact): {draft_info}" if is_vi else f"Artifact: {draft_info}"])
    return "\n".join(lines)


def _format_clarify_workflow(workflow: str, result: dict[str, Any], output_format: str, is_vi: bool = False) -> str:
    """Format a structured breakdown of current checklist/review status and exact missing items."""
    msg = "Cần bổ sung thêm thông tin." if is_vi else "More information is required."
    lines = [f"[{workflow.upper()} | NEEDS INPUT]", result.get("message", msg)]

    detail_lines = _trip_details_block(result, is_vi=is_vi)
    if detail_lines:
        lines.append("")
        lines.extend(detail_lines)

    if workflow == "pretrip":
        validation = result.get("validation") or {}
        missing_fields = result.get("missing_fields") or validation.get("missing_fields") or []
        approval_status = validation.get("trip_approval_status")
        dest = (result.get("trip") or {}).get("destination", "this destination")
        if validation.get("unknown_destination_requirements"):
            dest_note = f"Chưa cấu hình chính sách cho {dest} (cần nhân sự xem xét khi đủ trường)" if is_vi else f"No configured policy requirements for {dest} (staff review needed once fields are complete)"
        elif validation.get("required_policy_categories"):
            dest_note = f"Danh mục chính sách bắt buộc: {', '.join(validation['required_policy_categories'])}" if is_vi else f"Required policy categories: {', '.join(validation['required_policy_categories'])}"
        else:
            dest_note = "Chưa đánh giá" if is_vi else "Not evaluated yet"

        lines.extend([
            "",
            "Trạng thái danh sách kiểm tra (Current Checklist Status):" if is_vi else "Current Checklist Status:",
            "  - Checklist Draft: Chưa tạo do thiếu các trường bắt buộc" if is_vi else "  - Checklist Draft: Not created yet (blocked by missing required trip fields)",
            f"  - Trạng thái phê duyệt (Approval Status): {approval_status or 'Chưa nộp (chưa có bản ghi duyệt)'}" if is_vi else f"  - Approval Status: {approval_status or 'Not submitted (no approval record)'}",
            f"  - Cấu hình chính sách điểm đến: {dest_note}" if is_vi else f"  - Destination Policy Config: {dest_note}",
            "",
            "Các trường thiếu / Cần làm rõ (Missing / Needs Clarification):" if is_vi else "Missing / Needs Clarification:",
        ])
        for field in missing_fields:
            lines.append(f"  - Missing required field: `{field}` (vui lòng cung cấp thông tin này để tiếp tục)" if is_vi else f"  - Missing required field: `{field}` (please provide this information to continue)")
        if not missing_fields:
            lines.append("  - Thông tin chuyến đi chưa đầy đủ." if is_vi else "  - Required trip details are incomplete.")
        return "\n".join(lines)

    if workflow == "posttrip":
        review = result.get("review_preview") or {}
        summary = review.get("summary") or {}
        draft = result.get("draft") or {}
        draft_info = f"Draft {draft.get('draft_id')} ({draft.get('delivery_status')})" if draft.get("draft_id") else "Not created"
        lines.extend([
            "",
            "Trạng thái kiểm toán chi phí (Current Expense Review Status):" if is_vi else "Current Expense Review Status:",
            f"  - Report ID: {summary.get('report_id', 'N/A')} | Tổng tính toán: {summary.get('total', 'N/A')} {summary.get('currency', '')}".strip() if is_vi else f"  - Report ID: {summary.get('report_id', 'N/A')} | Calculated Total: {summary.get('total', 'N/A')} {summary.get('currency', '')}".strip(),
            f"  - Category Totals: {summary.get('category_totals', {})}",
            f"  - Sandbox Artifact: {draft_info}",
        ])
        ev_lines = _format_evidence_lines(result, max_items=3 if output_format == "concise" else None)
        if ev_lines:
            lines.extend(["", "Căn cứ chính sách trích dẫn (Policy Sources Cited):" if is_vi else "Policy Sources Cited:"])
            lines.extend(ev_lines)

        lines.extend(["", "Các mục thiếu / Cần làm rõ (Missing / Needs Clarification):" if is_vi else "Missing / Needs Clarification:"])
        for item_id in summary.get("missing_receipts", []):
            lines.append(f"  - Missing receipt attachment for item `{item_id}`")
        for mf in summary.get("missing_fields", []):
            lines.append(f"  - Thiếu trường dữ liệu trên `{mf.get('item_id')}`: {', '.join(mf.get('fields', []))}" if is_vi else f"  - Missing field(s) on `{mf.get('item_id')}`: {', '.join(mf.get('fields', []))}")
        for inv in summary.get("invalid_items", []):
            lines.append(f"  - Mục không hợp lệ `{inv}`" if is_vi else f"  - Invalid or incomplete item `{inv}`")
        return "\n".join(lines)

    return "\n".join(lines)


def _format_policy_qa(data: dict[str, Any], output_format: str, is_vi: bool = False) -> tuple[str, list[str]]:
    chunks = data.get("results", [])
    citations = [chunk["citation"] for chunk in chunks if isinstance(chunk.get("citation"), str)]
    if output_format == "concise":
        top = chunks[0]
        text = f"Nguồn (Source): {top['source']} (§{top['section']}, v{top['version']})\n{top['text']}\nTrích dẫn (Citation): {top['citation']}" if is_vi else f"Source: {top['source']} (§{top['section']}, v{top['version']})\n{top['text']}\nCitation: {top['citation']}"
        return text, citations
    lines = ["Căn cứ chính sách đã xác thực (Grounded Policy Evidence):" if is_vi else "Grounded Policy Evidence:"]
    for chunk in chunks:
        lines.append(f"\n- Nguồn (Source): {chunk['source']} (§{chunk['section']}, v{chunk['version']})" if is_vi else f"\n- Source: {chunk['source']} (§{chunk['section']}, v{chunk['version']})")
        lines.append(f"  {chunk['text']}")
        lines.append(f"  Trích dẫn (Citation): {chunk['citation']}" if is_vi else f"  Citation: {chunk['citation']}")
    return "\n".join(lines), citations


def _audit_chat_event(user: dict[str, Any], state: RunState, trip_id: str | None, report_id: str | None, reason_code: str) -> None:
    record_audit_event({
        "event_id": f"EVT-{state.run_id}",
        "event_type": "workflow_run",
        "actor_id": user["user_id"],
        "role": user["role"],
        "action": state.workflow,
        "trip_id": trip_id,
        "report_id": report_id,
        "outcome": state.outcome,
        "reason_code": reason_code,
        "reason": "Conversational turn completed with recorded outcome.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": state.run_id,
    })


def _format_trip_choice(trip: dict[str, Any], traveler_label: str | None = None) -> str:
    ap = f" ({trip['origin_airport']})" if trip.get("origin_airport") else ""
    who = traveler_label or trip.get("traveler_id") or "Unknown"
    return (
        f"  - {trip['trip_id']} ({who}): {trip.get('origin', '')}{ap} -> {trip.get('destination', '')} "
        f"| {trip.get('start_date', '')} to {trip.get('end_date', '')} "
        f"| Status: {_human_trip_status(trip.get('travel_status'))}"
    )


def _resolve_natural_record(
    decision: RouteDecision,
    wf: str,
    user_context: dict[str, Any],
    is_vi: bool = False,
) -> tuple[str | None, str | None, str | None]:
    """Resolve trip_id / report_id via scoped list_my_trips / list_my_expenses when ID is omitted."""
    target_trip = decision.trip_id
    target_report = decision.report_id
    if (wf in {"pretrip", "intrip"} and target_trip) or (wf == "posttrip" and target_report):
        return target_trip, target_report, None

    if wf == "posttrip" and not target_trip:
        temp = RunState("posttrip", user_context, phase="record_lookup")
        exp_res = run_tool(temp, "list_my_expenses", {})
        reports = exp_res.get("data", []) if exp_res.get("ok") else []
        if not decision.destination and not decision.date_hint:
            if len(reports) == 1:
                return reports[0]["trip_id"], reports[0]["report_id"], None
            if len(reports) > 1:
                opts = "\n".join(f"  - {r['report_id']} (Trip {r['trip_id']}, {len(r.get('line_items', []))} items)" for r in reports)
                msg = (
                    f"Bạn có nhiều báo cáo chi phí. Bạn muốn tôi kiểm tra báo cáo nào?\n{opts}"
                    if is_vi
                    else f"You have multiple expense reports. Which one should I review?\n{opts}"
                )
                return None, None, msg
            msg = (
                "Không tìm thấy báo cáo chi phí nào cho tài khoản của bạn. Vui lòng cung cấp mã EXP-YYYY-NNN."
                if is_vi
                else "No expense reports were found for your account. Please specify an EXP-YYYY-NNN ID."
            )
            return None, None, msg

    if not target_trip:
        temp = RunState(wf if wf in _WORKFLOWS else "pretrip", user_context, phase="record_lookup")
        args: dict[str, Any] = {}
        if decision.destination:
            args["destination"] = decision.destination
        if decision.date_hint:
            args["date"] = decision.date_hint
        res = run_tool(temp, "list_my_trips", args)
        matches = res.get("data", []) if res.get("ok") else []

        if len(matches) == 1:
            candidate = matches[0]
            if decision.date_hint and wf == "intrip":
                itin_res = run_tool(RunState("intrip", user_context, phase="flight_date_check"), "get_itinerary", {"trip_id": candidate["trip_id"]})
                flight = itin_res.get("data", {}).get("flight", {}) if itin_res.get("ok") else {}
                flight_dates = {
                    str(flight.get("departure", ""))[:10],
                    str(flight.get("arrival", ""))[:10],
                } - {""}
                if flight_dates and decision.date_hint not in flight_dates:
                    disruption = itin_res.get("data", {}).get("disruption") if itin_res.get("ok") else None
                    if is_vi:
                        msg = (
                            f"Không tìm thấy chuyến bay nào được lên lịch vào ngày {decision.date_hint}.\n"
                            f"Chuyến đi {candidate.get('destination')} của bạn ({candidate['trip_id']}, "
                            f"{candidate.get('start_date')} đến {candidate.get('end_date')}) có chuyến bay "
                            f"{flight.get('flight_id', 'N/A')} vào ngày {', '.join(sorted(flight_dates))} "
                            f"(Status: {_human_flight_status(flight.get('status'), disruption)}).\n\n"
                            f"Vui lòng trả lời bằng `{candidate['trip_id']}` nếu bạn muốn kiểm tra chuyến bay đó, hoặc xác nhận lại ngày."
                        )
                    else:
                        msg = (
                            f"I could not find a flight scheduled on {decision.date_hint}.\n"
                            f"Your recorded {candidate.get('destination')} trip ({candidate['trip_id']}, "
                            f"{candidate.get('start_date')} to {candidate.get('end_date')}) has flight "
                            f"{flight.get('flight_id', 'N/A')} on {', '.join(sorted(flight_dates))} "
                            f"(Status: {_human_flight_status(flight.get('status'), disruption)}).\n\n"
                            f"Please reply with `{candidate['trip_id']}` if you meant that flight, or confirm the date."
                        )
                    return None, None, msg
            elif decision.date_hint and wf == "pretrip" and candidate.get("start_date") != decision.date_hint:
                if is_vi:
                    msg = (
                        f"Không có chuyến đi nào khởi hành vào ngày {decision.date_hint}.\n"
                        f"Chuyến đi {candidate.get('destination')} của bạn ({candidate['trip_id']}) được lên lịch từ "
                        f"{candidate.get('start_date')} đến {candidate.get('end_date')}.\n\n"
                        f"Vui lòng trả lời bằng `{candidate['trip_id']}` nếu bạn muốn kiểm tra chuyến đi này."
                    )
                else:
                    msg = (
                        f"No trip departs on {decision.date_hint}.\n"
                        f"Your recorded {candidate.get('destination')} trip ({candidate['trip_id']}) is scheduled from "
                        f"{candidate.get('start_date')} to {candidate.get('end_date')}.\n\n"
                        f"Please reply with `{candidate['trip_id']}` if you meant this trip."
                    )
                return None, None, msg
            target_trip = candidate["trip_id"]
        elif len(matches) > 1:
            opts = "\n".join(_format_trip_choice(t) for t in matches)
            msg = (
                f"Tìm thấy nhiều chuyến đi phù hợp với yêu cầu của bạn. Bạn muốn chọn chuyến nào?\n{opts}"
                if is_vi
                else f"I found multiple trips matching your request. Which trip do you mean?\n{opts}"
            )
            return None, None, msg
        else:
            # No match for the specified date/destination -> list available trips cleanly for clarification.
            all_res = run_tool(RunState(wf if wf in _WORKFLOWS else "pretrip", user_context, phase="record_lookup"), "list_my_trips", {})
            all_trips = all_res.get("data", []) if all_res.get("ok") else []
            if not all_trips:
                msg = (
                    "Không tìm thấy chuyến đi nào trong tài khoản của bạn. Vui lòng cung cấp mã TRIP-YYYY-NNN hợp lệ."
                    if is_vi
                    else "No trips were found for your account. Please provide a valid TRIP-YYYY-NNN ID."
                )
                return None, None, msg
            if is_vi:
                detail = f"vào ngày {decision.date_hint}" if decision.date_hint else (f"đến {decision.destination}" if decision.destination else "phù hợp với yêu cầu")
                opts = "\n".join(_format_trip_choice(t) for t in all_trips)
                msg = f"Không tìm thấy chuyến đi nào đã ghi nhận {detail}. Các chuyến đi đã ghi nhận của bạn:\n{opts}\n\nVui lòng trả lời với điểm đến, ngày hoặc trip_id."
            else:
                detail = f"on {decision.date_hint}" if decision.date_hint else (f"to {decision.destination}" if decision.destination else "matching your request")
                opts = "\n".join(_format_trip_choice(t) for t in all_trips)
                msg = f"I could not find a recorded trip {detail}. Your recorded trips are:\n{opts}\n\nPlease reply with the destination, date, or trip ID."
            return None, None, msg

    if wf == "posttrip" and target_trip and not target_report:
        temp = RunState("posttrip", user_context, phase="record_lookup")
        exp_res = run_tool(temp, "list_my_expenses", {"trip_id": target_trip})
        reports = exp_res.get("data", []) if exp_res.get("ok") else []
        if len(reports) == 1:
            target_report = reports[0]["report_id"]
        elif len(reports) > 1:
            opts = "\n".join(f"  - {r['report_id']} (Trip {r['trip_id']})" for r in reports)
            msg = (
                f"Có nhiều báo cáo chi phí cho chuyến {target_trip}. Bạn muốn tôi kiểm tra báo cáo nào?\n{opts}"
                if is_vi
                else f"Multiple expense reports exist for {target_trip}. Which one should I review?\n{opts}"
            )
            return target_trip, None, msg
        else:
            msg = (
                f"Không tìm thấy báo cáo chi phí nào liên kết với chuyến {target_trip}. Vui lòng cung cấp mã EXP-YYYY-NNN."
                if is_vi
                else f"No expense report was found linked to {target_trip}. Please specify an EXP-YYYY-NNN ID."
            )
            return target_trip, None, msg

    return target_trip, target_report, None


def _resolve_with_session(decision: RouteDecision, user_context: dict[str, Any], message: str) -> RouteDecision:
    if user_context["role"] not in {"Employee", "Reviewer", "Approver"}:
        return decision
    session = get_session_state(user_context)
    if decision.intent == "clarify_id":
        last_wf = session.get("last_workflow")
        wf = last_wf if last_wf in {"pretrip", "intrip", "posttrip"} else "pretrip"
        if decision.report_id:
            return RouteDecision("SELF_SERVE", "posttrip", report_id=decision.report_id)
        if decision.trip_id:
            return RouteDecision("SELF_SERVE", "pretrip" if wf not in {"pretrip", "intrip"} else wf, trip_id=decision.trip_id)
        if decision.destination or decision.date_hint:
            return RouteDecision("SELF_SERVE", wf, destination=decision.destination, date_hint=decision.date_hint)

    if (
        decision.route == "SELF_SERVE"
        and decision.intent in {"pretrip", "intrip", "posttrip"}
        and not decision.trip_id
        and not decision.report_id
        and not decision.destination
        and not decision.date_hint
        and _CONTEXT_PRONOUNS.search(message)
    ):
        if decision.intent == "posttrip" and session.get("active_report_id"):
            return RouteDecision("SELF_SERVE", "posttrip", report_id=session["active_report_id"])
        if decision.intent in {"pretrip", "intrip"} and session.get("active_trip_id"):
            return RouteDecision("SELF_SERVE", decision.intent, trip_id=session["active_trip_id"])
    return decision


def _handle_preference(user_context: dict[str, Any], cmd: dict[str, Any], is_vi: bool = False) -> tuple[str, RunState]:
    auth_ctx = {**user_context, "memory_write_authorized": True}
    state = RunState("pretrip", auth_ctx, phase="preference_management")
    action = cmd["action"]
    key = cmd.get("key")
    if action == "get":
        if key:
            res = run_tool(state, "get_preference", {"key": key})
            state.finish("completed" if res.get("ok") else "failed_validation")
            val = res.get("data")
            if is_vi:
                msg = f"Tùy chọn đã lưu `{key}` của bạn là `{val}`." if val else f"Không tìm thấy tùy chọn đã lưu cho `{key}`."
            else:
                msg = f"Your saved preference `{key}` is `{val}`." if val else f"No saved preference found for `{key}`."
            return msg, state
        prefs = get_preferences(user_context)
        state.finish("completed")
        if is_vi:
            msg = f"Tùy chọn đã lưu (Saved preferences): {prefs}" if prefs else "Bạn hiện chưa có tùy chọn cá nhân nào được lưu."
        else:
            msg = f"Saved preferences: {prefs}" if prefs else "You currently have no saved persistent preferences."
        return msg, state
    if action == "set":
        res = run_tool(state, "set_preference", {"key": key, "value": cmd["value"]})
        state.finish("completed" if res.get("ok") else "failed_validation")
        if res.get("ok"):
            msg = f"Đã lưu tùy chọn `{key}` = `{cmd['value']}` (Saved preference)." if is_vi else f"Saved preference `{key}` = `{cmd['value']}`."
            return msg, state
        msg = "Không thể cập nhật tùy chọn do tham số hoặc quyền không hợp lệ." if is_vi else "Could not update preference due to invalid arguments or permissions."
        return msg, state
    res = run_tool(state, "delete_preference", {"key": key})
    state.finish("completed" if res.get("ok") else "failed_validation")
    if res.get("ok"):
        existed = res.get("data")
        if is_vi:
            msg = f"Đã xóa tùy chọn `{key}`." if existed else f"Không có tùy chọn `{key}` nào được lưu."
        else:
            msg = f"Deleted preference `{key}`." if existed else f"No `{key}` preference was saved."
        return msg, state
    msg = "Không thể xóa tùy chọn do tham số hoặc quyền không hợp lệ." if is_vi else "Could not delete preference due to invalid arguments or permissions."
    return msg, state


def _handle_admin_overview(
    user: dict[str, Any],
    user_context: dict[str, Any],
    decision: RouteDecision,
    is_vi: bool = False,
) -> tuple[str, str, RunState]:
    if user["role"] in {"Employee", "Reviewer"} and decision.admin_action == "trips":
        state = RunState("pretrip", user_context, phase="reviewer_trip_list")
        args = {"destination": decision.destination} if decision.destination else {}
        res = run_tool(state, "list_my_trips", args)
        state.finish("completed" if res.get("ok") else "failed_validation")
        if not res.get("ok"):
            return "REJECT_SAFETY", "", state
        rows = res.get("data", []) if res.get("ok") else []
        cache: dict[str, str] = {}
        label = "CHUYẾN ĐI CỦA BẠN" if user["role"] == "Employee" else "TOÀN BỘ CHUYẾN ĐI CỦA NHÂN VIÊN"
        header = f"[{user['role'].upper()} | {label} ({len(rows)})]"
        lines = [header, ""]
        for t in rows:
            tid = t.get("traveler_id")
            if tid and tid not in cache:
                cache[tid] = _traveler_label(_lookup_traveler(user, user_context, tid), tid) or tid
            lines.append(_format_trip_choice(t, cache.get(tid)))
        return "SELF_SERVE", "\n".join(lines), state

    state = RunState("admin", user_context, phase="admin_read")
    if decision.admin_action == "audit":
        args: dict[str, Any] = {}
        if decision.trip_id:
            args["trip_id"] = decision.trip_id
        if decision.report_id:
            args["report_id"] = decision.report_id
        res = run_tool(state, "admin_get_audit_history", args)
        if not res.get("ok"):
            state.finish("failed_validation")
            err = "Không có quyền: Chỉ tài khoản Admin mới có thể kiểm tra lịch sử kiểm toán." if is_vi else "Unauthorized: only Admin accounts can inspect audit history."
            return "REJECT_SAFETY", err, state
        state.finish("completed")
        events = res["data"]
        header = f"[ADMIN | LỊCH SỬ KIỂM TOÁN ({len(events)} sự kiện)]" if is_vi else f"[ADMIN | AUDIT HISTORY ({len(events)} events)]"
        lines = [header, ""]
        for ev in events[-10:]:
            lines.append(
                f"  - {ev.get('event_id')} | {ev.get('timestamp')} | {ev.get('event_type')} | Actor: {ev.get('actor_id')} ({ev.get('role')}) "
                f"| Trip/Report: {ev.get('trip_id') or ev.get('report_id') or '-'} | Outcome: {ev.get('outcome')} | Reason: {ev.get('reason_code')}"
            )
        if not events:
            lines.append("  Không có sự kiện kiểm toán nào phù hợp." if is_vi else "  No audit events match this filter.")
        return "SELF_SERVE", "\n".join(lines), state

    res = run_tool(state, "admin_list_trips", {})
    if not res.get("ok"):
        state.finish("failed_validation")
        err = "Không có quyền: Chỉ tài khoản Admin mới có thể xem tổng quan chuyến đi." if is_vi else "Unauthorized: only Admin accounts can run admin trip overview."
        return "REJECT_SAFETY", err, state
    state.finish("completed")
    trips = res["data"]
    header = f"[ADMIN | TỔNG QUAN CHUYẾN ĐI (CHỈ ĐỌC) ({len(trips)} chuyến)]" if is_vi else f"[ADMIN | READ-ONLY TRIP OVERVIEW ({len(trips)} trips)]"
    lines = [header, ""]
    lines.extend(_format_trip_choice(t) for t in trips)
    return "SELF_SERVE", "\n".join(lines), state


def _handle_approver_turn(
    user: dict[str, Any],
    user_context: dict[str, Any],
    decision: RouteDecision,
    approval_scope: dict[str, str] | None,
    is_vi: bool = False,
) -> tuple[str, str, str, list[str], str, RunState]:
    if decision.intent in {"posttrip", "admin_overview", "request_approval"} or decision.report_id or decision.draft_requested:
        state = RunState("pretrip", user_context, phase="approver_role_boundary")
        state.finish("failed_validation")
        return "REJECT_SAFETY", "failed_validation", "", [], "", state
    if not isinstance(approval_scope, dict) or not approval_scope.get("trip_id") or not approval_scope.get("action_type"):
        state = RunState("pretrip", user_context, phase="approver_scope_missing")
        state.finish("needs_human")
        err = "Tài khoản Approver yêu cầu phạm vi phê duyệt đang chờ xử lý từ ứng dụng." if is_vi else "Approver accounts require an application-supplied pending approval scope."
        return (
            "HANDOFF_STAFF",
            "needs_human",
            "",
            [],
            err,
            state,
        )
    scoped_ctx = {**user_context, "approval_scope": approval_scope}
    trip_id = decision.trip_id or approval_scope["trip_id"]
    action_type = approval_scope["action_type"]
    wf = "intrip" if action_type == "escalation" or decision.intent == "intrip" else "pretrip"
    state = RunState(wf, scoped_ctx, phase="approver_scoped_review")

    if decision.intent == "policy_qa":
        res = run_tool(state, "search_travel_policy", {
            "query": decision.policy_query or "travel policy",
            "category": decision.policy_category or ("travel" if action_type == "escalation" else "approval"),
            "max_results": 5,
        })
        if not res.get("ok"):
            state.finish("failed_validation")
            err = "Danh mục chính sách yêu cầu nằm ngoài phạm vi phê duyệt của bạn." if is_vi else "Requested policy category is outside your Approver scope."
            return "REJECT_SAFETY", "failed_validation", "", [], err, state
        data = res["data"]
        if data.get("no_result") or not data.get("results") or data.get("version_conflicts"):
            state.finish("needs_human")
            cits = [v["citation"] for c in data.get("version_conflicts", []) for v in c.get("versions", []) if v.get("citation")]
            reason = "Căn cứ chính sách thiếu hoặc có xung đột phiên bản. Cần Travel Operations xem xét."
            return "HANDOFF_STAFF", "needs_human", "", cits, reason, state
        state.finish("completed")
        text, cits = _format_policy_qa(res["data"], "detailed", is_vi=is_vi)
        return "SELF_SERVE", "completed", text, cits, "", state

    read_tool = "get_itinerary" if action_type == "escalation" or decision.intent == "intrip" else "get_trip_request"
    res = run_tool(state, read_tool, {"trip_id": trip_id})
    if not res.get("ok"):
        state.finish("failed_validation")
        err = "Chuyến đi yêu cầu nằm ngoài phạm vi phê duyệt đang chờ của bạn." if is_vi else "Requested trip is outside your active pending approval scope."
        return "REJECT_SAFETY", "failed_validation", "", [], err, state

    header = f"[APPROVER XEM XÉT THEO PHẠM VI | {trip_id} ({action_type})]" if is_vi else f"[APPROVER SCOPED REVIEW | {trip_id} ({action_type})]"
    facts_title = "Dữ kiện chỉ đọc theo phạm vi (Scoped Read-Only Facts):" if is_vi else "Scoped Read-Only Facts:"
    lines = [
        header,
        "",
        facts_title,
    ]
    data = res["data"]
    if read_tool == "get_trip_request":
        if is_vi:
            lines.extend([
                f"  - Traveler: {data.get('traveler_id', 'Unknown')}",
                f"  - Route: {data.get('origin')} ({data.get('origin_airport', 'HAN')}) -> {data.get('destination')}",
                f"  - Dates: {data.get('start_date')} đến {data.get('end_date')}",
                f"  - Purpose: {data.get('purpose')}",
                f"  - Trip Status: {_human_trip_status(data.get('travel_status'))}",
            ])
        else:
            lines.extend([
                f"  - Traveler: {data.get('traveler_id', 'Unknown')}",
                f"  - Route: {data.get('origin')} ({data.get('origin_airport', 'HAN')}) -> {data.get('destination')}",
                f"  - Dates: {data.get('start_date')} to {data.get('end_date')}",
                f"  - Purpose: {data.get('purpose')}",
                f"  - Trip Status: {_human_trip_status(data.get('travel_status'))}",
            ])
        app_res = run_tool(state, "get_approval_status", {"trip_id": trip_id})
        if app_res.get("ok"):
            lines.append(f"  - Trạng thái phê duyệt (Approval Status): {app_res['data'].get('trip_approval_status')}" if is_vi else f"  - Approval Status: {app_res['data'].get('trip_approval_status')}")
    else:
        flight = data.get("flight", {})
        disruption = data.get("disruption")
        if is_vi:
            lines.extend([
                f"  - Flight: {flight.get('flight_id')} | {flight.get('origin')} -> {flight.get('destination')}",
                f"  - Schedule: {_fmt_iso_dt(flight.get('departure'))} đến {_fmt_iso_dt(flight.get('arrival'))}",
                f"  - Flight Status: {_human_flight_status(flight.get('status'), disruption)}",
            ])
        else:
            lines.extend([
                f"  - Flight: {flight.get('flight_id')} | {flight.get('origin')} -> {flight.get('destination')}",
                f"  - Schedule: {_fmt_iso_dt(flight.get('departure'))} to {_fmt_iso_dt(flight.get('arrival'))}",
                f"  - Flight Status: {_human_flight_status(flight.get('status'), disruption)}",
            ])
    state.finish("completed")
    return "SELF_SERVE", "completed", "\n".join(lines), [], "", state


def _handoff_reason_for_workflow(outcome: str, result: dict[str, Any], is_vi: bool = False) -> str:
    if outcome == "awaiting_approval":
        return "Chuyến đi đang chờ phê duyệt; cần có sự phê duyệt của con người." if is_vi else "Trip approval is pending; human approval is required."
    if outcome == "failed_budget":
        return "Thực thi đạt giới hạn ngân sách bước (step budget limit); chuyển tiếp nhân viên xem xét." if is_vi else "Execution reached step budget limit; escalated for staff review."
    if outcome == "partial":
        return result.get("message", "Quy trình chưa hoàn tất. Cần Travel Operations kiểm tra trước khi thử lại.")
    validation = result.get("validation")
    if isinstance(validation, dict):
        if validation.get("blocking"):
            return f"Trạng thái chuyến đi / phê duyệt bị chặn (blocking): {', '.join(validation['blocking'])}." if is_vi else f"Blocking travel/approval status: {', '.join(validation['blocking'])}."
        if validation.get("missing_policy_categories"):
            return f"Thiếu căn cứ chính sách bắt buộc cho các danh mục: {', '.join(validation['missing_policy_categories'])}." if is_vi else f"Missing required policy evidence for categories: {', '.join(validation['missing_policy_categories'])}."
    review = result.get("review_preview")
    if isinstance(review, dict):
        if review.get("version_conflicts"):
            return "Xung đột phiên bản chính sách hiệu lực cần nhân viên giải quyết." if is_vi else "Active policy version conflict requires staff reviewer resolution."
        summary = review.get("summary", {})
        if isinstance(summary, dict) and summary.get("threshold_flags"):
            return "Các khoản chi phí vượt quá hoặc xung đột với giới hạn chính sách." if is_vi else "Expense items exceed or conflict with active policy limits."
    return result.get("message", "Cần nhân viên Vận hành Du lịch xem xét." if is_vi else "Human Travel Operations staff review is required.")


# Conversational Orchestrator (Mục 5, 8, 9, 11): Điều phối phiên thoại đa lượt qua 4 luồng nghiệp vụ chuẩn.
def handle_turn(
    message: str,
    user_id: str,
    *,
    session_id: str = "demo-session",
    approval_scope: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Process one conversational turn across 4 strict routes and log to UTF-8 CSV."""
    user = get_user(user_id)
    if not user:
        raise ValueError("Không tìm thấy tài khoản demo. Hãy chọn một người dùng trong danh sách.")

    user_context = {"user_id": user["user_id"], "role": user["role"], "session_id": session_id}
    output_format = "concise"
    if user["role"] in {"Employee", "Reviewer", "Approver"}:
        output_format = get_preferences(user_context).get("preferred_output_format", "concise")

    is_vi = _is_vietnamese(message, user_context)

    decision = _resolve_with_session(route_message_intent(message), user_context, message)

    route = decision.route
    intent = decision.intent
    workflow_name: str | None = None
    log_trip_id = decision.trip_id
    log_report_id = decision.report_id
    record_id = log_report_id or log_trip_id
    citations: list[str] = []
    facts_summary = ""
    handoff_required = False
    handoff_id: str | None = None
    handoff_reason = ""
    result_payload: dict[str, Any] = {}
    state: RunState

    # Role-specific routing for Admin & Approver before Employee/Reviewer workflows.
    if intent == "approval_decision":
        route = "REJECT_SAFETY"
        state = RunState("pretrip", user_context, phase="approval_decision_boundary")
        state.finish("failed_validation")
        outcome = "failed_validation"
        bot_response = ""
        _audit_chat_event(user, state, decision.trip_id, decision.report_id, "approval_decision_denied")
    elif user["role"] == "Admin" and route != "REJECT_SAFETY" and intent not in {"greeting", "handoff_requested", "out_of_scope", "admin_overview"}:
        route = "REJECT_SAFETY"
        state = RunState("admin", user_context, phase="admin_boundary")
        state.finish("failed_validation")
        outcome = "failed_validation"
        bot_response = (
            "Từ chối quyền đối với vai trò Admin: Admin chỉ có quyền xem tổng quan chuyến đi chỉ đọc (`danh sách chuyến đi`) "
            "và lịch sử kiểm toán (`nhật ký kiểm toán`), không được phép chạy quy trình hoặc tìm kiếm chính sách."
            if is_vi
            else (
                "Unauthorized for Admin role: Admin only has read-only trip overview (`list all trips`) "
                "and audit history (`show audit log`), and cannot run workflows or search policy."
            )
        )
        _audit_chat_event(user, state, decision.trip_id, decision.report_id, "admin_boundary_enforced")
    elif user["role"] == "Approver" and route != "REJECT_SAFETY" and intent not in {"greeting", "handoff_requested", "out_of_scope", "preference"}:
        route, outcome, bot_response, citations, handoff_reason, state = _handle_approver_turn(
            user, user_context, decision, approval_scope, is_vi=is_vi
        )
        if route == "HANDOFF_STAFF":
            handoff_required = True
            handoff_id = f"HND-{uuid4().hex[:8].upper()}"
            bot_response = _format_handoff_response(handoff_id, handoff_reason, "", citations, output_format, is_vi=is_vi)
        _audit_chat_event(user, state, decision.trip_id, decision.report_id, "approver_scoped_turn")
    elif route == "REJECT_SAFETY":
        state = RunState("pretrip", user_context, phase="safety_guard")
        outcome = "failed_validation" if intent == "invalid_id" else "needs_input"
        state.trace.append({
            "run_id": state.run_id,
            "phase": "safety_guard",
            "action": "route_rejected",
            "tool": None,
            "safe_args": {},
            "observation_status": "not_applicable",
            "transition": "rejected_before_tool_call",
            "budget": {"step": 0, "max": state.max_steps},
            "outcome": None,
            "safety_event": "unsafe_or_invalid_user_input",
        })
        state.finish(outcome)
        if intent == "invalid_id":
            bot_response = (
                "Định dạng ID không hợp lệ. Kỳ vọng TRIP-YYYY-NNN hoặc EXP-YYYY-NNN."
                if is_vi
                else "Invalid ID format. Expected TRIP-YYYY-NNN or EXP-YYYY-NNN."
            )
        else:
            bot_response = (
                "Yêu cầu bị từ chối bởi chính sách an toàn: Không cho phép hành vi vượt quyền quy tắc (rule-bypass), ghi đè hàng loạt (bulk-override) hoặc chỉ thị bị cấm."
                if is_vi
                else "Request rejected by safety policy: rule-bypass, bulk-override, or forbidden instruction patterns are not allowed."
            )
        _audit_chat_event(user, state, decision.trip_id, decision.report_id, "safety_guard_rejected")

    elif route == "SELF_SERVE" and intent == "admin_overview":
        workflow_name = "admin"
        route, bot_response, state = _handle_admin_overview(user, user_context, decision, is_vi=is_vi)
        outcome = state.outcome or "completed"
        _audit_chat_event(user, state, decision.trip_id, decision.report_id, "admin_overview")

    elif route == "CLARIFY":
        state = RunState(intent if intent in _WORKFLOWS else "pretrip", user_context, phase="clarification")
        state.finish("needs_input")
        outcome = "needs_input"
        if user["role"] in {"Employee", "Reviewer", "Approver"} and intent in {"pretrip", "intrip", "posttrip"}:
            set_session_value(user_context, "last_workflow", intent)
            set_session_value(user_context, "pending_slot", "report_id" if intent == "posttrip" else "trip_id")
        if intent == "posttrip":
            bot_response = (
                "Vui lòng cung cấp mã báo cáo chi phí (EXP-YYYY-NNN) hoặc điểm đến/ngày để tôi kiểm tra."
                if is_vi
                else "Please provide the expense report ID (EXP-YYYY-NNN) or destination/date so I can review it."
            )
        else:
            bot_response = (
                "Vui lòng cung cấp mã chuyến đi (TRIP-YYYY-NNN), điểm đến hoặc ngày khởi hành để tôi hỗ trợ."
                if is_vi
                else "Please provide the trip ID (TRIP-YYYY-NNN), destination, or travel date so I can assist you."
            )
        _audit_chat_event(user, state, None, None, "clarification_requested")

    elif route == "SELF_SERVE" and intent == "request_approval":
        workflow_name = "request_approval"
        state = RunState("intrip" if decision.approval_action == "escalation" else "pretrip", user_context, phase="approval_request")
        if user["role"] != "Employee":
            state.finish("failed_validation")
            route, outcome = "REJECT_SAFETY", "failed_validation"
            result_payload = {"outcome": outcome, "error": role_error(user["role"], "request_approval")["error"]}
            bot_response = ""
        elif not decision.trip_id:
            state.finish("needs_input")
            route, outcome = "CLARIFY", "needs_input"
            bot_response = "Hãy cung cấp mã chuyến đi TRIP-YYYY-NNN cần tạo yêu cầu phê duyệt."
        else:
            res = run_tool(state, "request_approval", {
                "trip_id": decision.trip_id, "action_type": decision.approval_action or "checklist_review",
                "action_summary": f"Yêu cầu xem xét {decision.approval_action or 'checklist_review'} cho {decision.trip_id}.",
            })
            outcome = "awaiting_approval" if res.get("ok") else "failed_validation"
            state.finish(outcome)
            if res.get("ok"):
                result_payload = {"outcome": outcome, "approval_request": res["data"]}
                bot_response = f"Yêu cầu phê duyệt cho {decision.trip_id} ({decision.approval_action}) đang chờ người phụ trách xem xét."
            else:
                route = "REJECT_SAFETY"
                result_payload = {"outcome": outcome, "error": res["error"]}
                bot_response = ""
        _audit_chat_event(user, state, decision.trip_id, None, "approval_request")

    elif route == "SELF_SERVE" and intent == "greeting":
        state = RunState("pretrip", user_context, phase="direct_reply")
        state.finish("completed")
        outcome = "completed"
        if user["role"] in {"Admin", "Approver"}:
            capabilities = (
                "Xem danh sách chuyến đi, audit log và tải log CSV."
                if user["role"] == "Admin" else
                "Xem hồ sơ và chính sách trong phạm vi phê duyệt đang chờ; quản lý tùy chọn cá nhân."
            )
            bot_response = f"Xin chào ({user['user_id']} · {user['role']})!\n\n{capabilities}"
        elif is_vi:
            bot_response = (
                f"Xin chào ({user['user_id']} · {user['role']})!\n\n"
                "Tôi có thể hỗ trợ bạn:\n"
                "  - Danh sách checklist & tuân thủ trước chuyến đi (Pre-trip: nhập điểm đến, ngày hoặc TRIP-ID)\n"
                "  - Hướng dẫn xử lý hoãn / hủy chuyến bay trong chuyến đi (In-trip)\n"
                "  - Kiểm toán và rà soát báo cáo chi phí sau chuyến đi (Post-trip)\n"
                "  - Tra cứu chính sách công tác có trích dẫn nguồn xác thực (Policy Q&A)\n"
                "  - Tùy chỉnh định dạng phản hồi (ngắn gọn / chi tiết)"
            )
        else:
            bot_response = (
                f"Hello ({user['user_id']} · {user['role']})!\n\n"
                "I can help with:\n"
                "  - Pre-trip checklists & compliance (mention a destination, date, or TRIP-ID)\n"
                "  - In-trip flight delay / cancellation guidance\n"
                "  - Post-trip expense report pre-checks\n"
                "  - Grounded travel policy Q&A with corpus citations\n"
                "  - Your output preferences (concise / detailed)"
            )

    elif route == "SELF_SERVE" and intent == "preference" and decision.preference_cmd:
        bot_response, state = _handle_preference(user_context, decision.preference_cmd, is_vi=is_vi)
        outcome = state.outcome or "completed"
        workflow_name = "preference"
        _audit_chat_event(user, state, None, None, "preference_operation")

    elif route == "SELF_SERVE" and intent == "policy_qa":
        workflow_name = "policy_qa"
        state = RunState("pretrip", user_context, phase="policy_qa")
        pol_cat = decision.policy_category or "travel"
        rewritten_q, _ = rewrite_query(decision.policy_query or message, pol_cat, state=state)
        res = run_tool(state, "search_travel_policy", {
            "query": rewritten_q,
            "category": pol_cat,
            "max_results": 5,
        })
        data = res.get("data", {}) if res.get("ok") else {}
        results = data.get("results", [])
        conflicting_docs = {c.get("doc_id") for c in data.get("version_conflicts", [])}
        top_has_conflict = bool(results and results[0].get("doc_id") in conflicting_docs)
        if not res.get("ok") or data.get("no_result") or not results or top_has_conflict:
            state.finish("needs_human")
            outcome = "needs_human"
            route = "HANDOFF_STAFF"
            handoff_required = True
            handoff_id = f"HND-{uuid4().hex[:8].upper()}"
            if not res.get("ok"):
                handoff_reason = (
                    f"Tìm kiếm chính sách thất bại hoặc ngoài phạm vi vai trò ({res.get('error', {}).get('code', 'error')})."
                    if is_vi
                    else f"Policy search failed or is outside role scope ({res.get('error', {}).get('code', 'error')})."
                )
            elif top_has_conflict:
                handoff_reason = (
                    "Phát hiện xung đột phiên bản chính sách; cần quyết định của nhân viên."
                    if is_vi
                    else "Active policy version conflict detected; requires human staff decision."
                )
                for conflict in data["version_conflicts"]:
                    if conflict.get("doc_id") == results[0].get("doc_id"):
                        citations.extend(v["citation"] for v in conflict.get("versions", []) if isinstance(v.get("citation"), str))
            else:
                handoff_reason = (
                    "Không tìm thấy căn cứ chính sách phù hợp trong kho dữ liệu."
                    if is_vi
                    else "No matching policy evidence found in the corpus."
                )
            bot_response = _format_handoff_response(handoff_id, handoff_reason, "", citations, output_format, is_vi=is_vi)
        else:
            state.finish("completed")
            outcome = "completed"
            bot_response, citations = _format_policy_qa(data, output_format, is_vi=is_vi)
            if user["role"] in {"Employee", "Reviewer", "Approver"}:
                set_session_value(user_context, "last_workflow", "policy_qa")
        _audit_chat_event(user, state, None, None, "policy_qa")

    elif route == "SELF_SERVE" and intent in {"pretrip", "intrip", "posttrip", "mixed"}:
        wf = (
            "posttrip" if (intent == "mixed" and (decision.report_id or "expense" in normalize_text(message)))
            else ("intrip" if (intent == "mixed" and any(k in normalize_text(message) for k in ("delay", "cancel", "disruption", "itinerary")))
                  else ("pretrip" if intent == "mixed" else intent))
        )
        workflow_name = wf
        resolved_trip, resolved_report, clarify_msg = _resolve_natural_record(decision, wf, user_context, is_vi=is_vi)
        if clarify_msg:
            route = "CLARIFY"
            outcome = "needs_input"
            state = RunState(wf, user_context, phase="clarification")
            state.finish("needs_input")
            set_session_value(user_context, "last_workflow", wf)
            set_session_value(user_context, "pending_slot", "report_id" if wf == "posttrip" else "trip_id")
            if resolved_trip:
                set_session_value(user_context, "active_trip_id", resolved_trip)
            bot_response = clarify_msg
            _audit_chat_event(user, state, resolved_trip, resolved_report, "clarification_requested")
        else:
            log_trip_id = resolved_trip
            log_report_id = resolved_report
            record_id = resolved_report if wf == "posttrip" else resolved_trip
            max_steps = 10 if (intent == "mixed" or wf == "pretrip") else 8
            state = RunState(wf, user_context, max_steps=max_steps)
            result_payload = _WORKFLOWS[wf](state, record_id)
            _enrich_trip_and_traveler(result_payload, user, user_context, resolved_trip)
            outcome = result_payload["outcome"]
            citations = _extract_citations(result_payload)
            facts_summary = _verified_facts(result_payload, resolved_trip, resolved_report)

            policy_note: str | None = None
            policy_handoff_reason: str | None = None
            if intent == "mixed" and decision.policy_query and state.step_count < state.max_steps and not result_payload.get("error_code"):
                temp_state = RunState(wf, user_context, max_steps=state.max_steps, run_id=state.run_id)
                temp_state.set_phase("mixed_policy_qa")
                temp_state.step_count = state.step_count
                mixed_cat = decision.policy_category or "travel"
                rewritten_mixed_q, _ = rewrite_query(decision.policy_query, mixed_cat, state=temp_state)
                p_res = run_tool(temp_state, "search_travel_policy", {
                    "query": rewritten_mixed_q,
                    "category": mixed_cat,
                    "max_results": 5,
                })
                state.step_count = temp_state.step_count
                for ev in temp_state.trace[1:]:
                    ev["outcome"] = state.outcome
                    state.trace.append(ev)
                p_data = p_res.get("data", {}) if p_res.get("ok") else {}
                p_results = p_data.get("results", [])
                p_conflicts = {c.get("doc_id") for c in p_data.get("version_conflicts", [])}
                p_top_conflict = bool(p_results and p_results[0].get("doc_id") in p_conflicts)
                if not p_res.get("ok") or p_data.get("no_result") or not p_results or p_top_conflict:
                    policy_handoff_reason = (
                        "Câu hỏi chính sách phụ có bằng chứng xung đột hoặc thiếu dữ liệu trong kho."
                        if is_vi
                        else "Secondary policy question has conflicting or missing corpus evidence."
                    )
                    for conflict in p_data.get("version_conflicts", []):
                        if not p_results or conflict.get("doc_id") == p_results[0].get("doc_id"):
                            citations.extend(v["citation"] for v in conflict.get("versions", []) if isinstance(v.get("citation"), str))
                else:
                    p_text, p_cits = _format_policy_qa(p_data, "concise", is_vi=is_vi)
                    policy_note = p_text
                    citations = list(dict.fromkeys([*citations, *p_cits]))

            if (
                user["role"] in {"Employee", "Reviewer", "Approver"}
                and outcome != "failed_validation"
                and result_payload.get("error_code") != "unauthorized_scope"
            ):
                set_session_value(user_context, "last_workflow", wf)
                delete_session_value(user_context, "pending_slot")
                if resolved_trip:
                    set_session_value(user_context, "active_trip_id", resolved_trip)
                if resolved_report:
                    set_session_value(user_context, "active_report_id", resolved_report)

            if result_payload.get("error_code") == "unauthorized_scope":
                route = "REJECT_SAFETY"
                bot_response = (
                    "Yêu cầu bị từ chối: Bản ghi được yêu cầu nằm ngoài phạm vi ủy quyền của bạn."
                    if is_vi
                    else "Request denied: the requested record is outside your authorized scope."
                )
            elif outcome == "completed" and not policy_handoff_reason:
                bot_response = _format_workflow_success(wf, result_payload, citations, output_format, policy_note=policy_note, is_vi=is_vi)
            elif outcome == "needs_input":
                route = "CLARIFY"
                bot_response = _format_clarify_workflow(wf, result_payload, output_format, is_vi=is_vi)
            elif outcome == "failed_validation":
                route = "REJECT_SAFETY"
                bot_response = result_payload.get("message", "Validation failed.")
            else:
                route = "HANDOFF_STAFF"
                handoff_required = True
                handoff_id = f"HND-{uuid4().hex[:8].upper()}"
                handoff_reason = policy_handoff_reason or _handoff_reason_for_workflow(outcome, result_payload, is_vi=is_vi)
                bot_response = _format_handoff_response(
                    handoff_id, handoff_reason, facts_summary, citations, output_format, result=result_payload, is_vi=is_vi
                )
            _audit_chat_event(user, state, resolved_trip, resolved_report, "workflow_terminal_outcome")

    else:
        route = "HANDOFF_STAFF"
        handoff_required = True
        handoff_id = f"HND-{uuid4().hex[:8].upper()}"
        handoff_reason = decision.reason or ("Chuyển tiếp đến nhân viên Vận hành Du lịch (Travel Operations Staff)." if is_vi else "Escalated to Travel Operations Staff.")
        state = RunState("pretrip", user_context, phase="staff_handoff")
        state.finish("needs_human")
        outcome = "needs_human"
        handoff_ctx_result: dict[str, Any] = {}
        if decision.trip_id:
            _enrich_trip_and_traveler(handoff_ctx_result, user, user_context, decision.trip_id)
        facts_summary = _verified_facts(handoff_ctx_result, decision.trip_id, decision.report_id)
        bot_response = _format_handoff_response(
            handoff_id, handoff_reason, facts_summary, citations, output_format, result=handoff_ctx_result, is_vi=is_vi
        )
        _audit_chat_event(user, state, decision.trip_id, decision.report_id, "staff_handoff")

    # Failures always use Vietnamese, independently of the input/preferred language.
    # Only expose messages produced by validated tools, never raw exceptions.
    response_error = result_payload.get("error")
    if not response_error and result_payload.get("error_code"):
        code = result_payload["error_code"]
        response_error = {"code": code, "message": ERROR_MESSAGES.get(code, ERROR_MESSAGES["unavailable"]), "retryable": False}
    last_observation = state.safe_tool_results[-1] if state.safe_tool_results else {}
    if (not response_error and last_observation.get("ok") is False
            and (route == "REJECT_SAFETY" or outcome in {"partial", "failed_budget", "failed_delivery", "failed_validation"}
                 or workflow_name in {"policy_qa", "preference"})):
        response_error = {
            "code": last_observation["error_code"],
            "message": last_observation["error_message"],
            "retryable": last_observation["retryable"],
        }
    if not response_error and route == "REJECT_SAFETY":
        if intent == "invalid_id":
            code, detail = "invalid_argument", "Mã không đúng định dạng. Hãy dùng TRIP-YYYY-NNN hoặc EXP-YYYY-NNN."
        elif intent == "safety_adversarial":
            code, detail = "not_allowed", "Yêu cầu chứa chỉ thị bỏ qua quy tắc an toàn hoặc vượt quyền. Hãy gửi lại tác vụ công tác trong phạm vi được cấp."
        elif state.phase == "admin_boundary":
            action = intent if intent in {"pretrip", "intrip", "posttrip", "policy_qa", "preference", "request_approval"} else "pretrip"
            code, detail = "unauthorized_scope", role_error("Admin", action)["error"]["message"]
        elif state.phase == "approver_role_boundary":
            action = ("audit" if decision.admin_action == "audit" else "trip_list") if intent == "admin_overview" else intent
            code, detail = "unauthorized_scope", role_error("Approver", action)["error"]["message"]
        elif state.phase == "approval_decision_boundary":
            code, detail = "unauthorized_scope", role_error(user["role"], "approval_decision")["error"]["message"]
        else:
            code = result_payload.get("error_code", "invalid_argument")
            detail = ERROR_MESSAGES.get(code, ERROR_MESSAGES["unavailable"])
        response_error = {"code": code, "message": detail, "retryable": False}
    if not response_error and state.phase == "approver_scope_missing":
        response_error = {
            "code": "unauthorized_scope", "retryable": False,
            "message": "Approver chưa được cấp phạm vi phê duyệt (approval scope). Hãy chọn yêu cầu đang chờ trong mục Phạm vi phê duyệt.",
        }
    if not response_error and outcome in {"partial", "failed_budget", "failed_delivery"}:
        code = "budget_exceeded" if outcome == "failed_budget" else "unavailable"
        response_error = {"code": code, "message": result_payload.get("message") or ERROR_MESSAGES[code], "retryable": False}
    if response_error:
        detail = error_text(response_error)
        if route == "HANDOFF_STAFF":
            handoff_reason = detail
            bot_response = _format_handoff_response(
                handoff_id, detail, facts_summary, citations, output_format, result=result_payload, is_vi=True
            )
        else:
            bot_response = detail

    log_chat_turn(
        session_id=session_id,
        user_id=user["user_id"],
        role=user["role"],
        route=route,
        intent=intent,
        workflow=workflow_name,
        record_id=record_id,
        outcome=outcome,
        handoff_required=handoff_required,
        handoff_id=handoff_id,
        handoff_reason=handoff_reason,
        user_message=message,
        bot_response=bot_response,
        citations=citations,
        run_id=state.run_id,
        step_count=state.step_count,
        verified_facts_summary=facts_summary,
        trip_id=log_trip_id,
        report_id=log_report_id,
    )

    return {
        "route": route,
        "intent": intent,
        "outcome": outcome,
        "bot_response": bot_response,
        "handoff_required": handoff_required,
        "handoff_id": handoff_id,
        "handoff_reason": handoff_reason,
        "citations": citations,
        "workflow": workflow_name,
        "record_id": record_id,
        "result": result_payload,
        "error": response_error,
        "run_id": state.run_id,
        "step_count": state.step_count,
        "trace": state.trace,
    }
