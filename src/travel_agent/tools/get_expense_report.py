from typing import Any

from travel_agent.mock_systems.expense import get_expense_report as read_expense_report
from travel_agent.tools._result import record_result


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    return record_result(read_expense_report(arguments["report_id"]), "mock_expense_system")
