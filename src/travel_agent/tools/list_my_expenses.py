from typing import Any

from travel_agent.mock_systems.expense import list_expense_reports
from travel_agent.mock_systems.user import get_user
from travel_agent.tools._result import failure, success


def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(user_context, dict):
        return failure("unauthorized_scope", "Application role context is required.")
    user = get_user(user_context.get("user_id", ""))
    if not user or user.get("role") not in {"Employee", "Reviewer"}:
        return failure("unauthorized_scope", "This user cannot list scoped expense reports.")
    traveler_id = user.get("traveler_id") if user["role"] == "Employee" else None
    reports = list_expense_reports(traveler_id=traveler_id)

    trip_id = arguments.get("trip_id")
    if isinstance(trip_id, str) and trip_id:
        reports = [r for r in reports if r.get("trip_id") == trip_id]
    return success(reports, "mock_expense_system")
