from typing import Any

from travel_agent.mock_systems._storage import load_dataset
from travel_agent.tools._result import success


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    events = load_dataset("audit_events.json")
    trip_id = arguments.get("trip_id")
    if trip_id:
        events = [event for event in events if event.get("trip_id") == trip_id]
    report_id = arguments.get("report_id")
    if report_id:
        events = [event for event in events if event.get("report_id") == report_id]
    return success(events, "mock_audit_log")
