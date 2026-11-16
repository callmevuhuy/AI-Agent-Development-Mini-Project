"""Deterministic planner compatibility wrapper backed by the English NLU router."""
from travel_agent.nlu import route_message_intent


# Planner (Mục 7.1): Phân tích thông điệp người dùng để đề xuất workflow và ID đối tượng tương ứng.
def plan(message: str) -> dict[str, str] | None:
    """Return {workflow, record_id} for supported single-turn workflow requests, else None."""
    decision = route_message_intent(message)
    if decision.route != "SELF_SERVE":
        return None
    if decision.intent == "posttrip" and decision.report_id:
        return {"workflow": "posttrip", "record_id": decision.report_id}
    if decision.intent in {"pretrip", "intrip"} and decision.trip_id:
        return {"workflow": decision.intent, "record_id": decision.trip_id}
    if decision.intent == "mixed":
        if decision.report_id:
            return {"workflow": "posttrip", "record_id": decision.report_id}
        if decision.trip_id:
            wf = "intrip" if "delay" in message.casefold() or "cancel" in message.casefold() else "pretrip"
            return {"workflow": wf, "record_id": decision.trip_id}
    return None
