from typing import Any

from ._storage import find_record


def get_expense_report(report_id: str) -> dict[str, Any] | None:
    return find_record("expenses.json", "report_id", report_id)
