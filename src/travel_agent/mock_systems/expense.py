from typing import Any

from ._storage import find_record, load_dataset


def get_expense_report(report_id: str) -> dict[str, Any] | None:
    return find_record("expenses.json", "report_id", report_id)


def list_expense_reports(traveler_id: str | None = None) -> list[dict[str, Any]]:
    rows = load_dataset("expenses.json")
    if traveler_id is not None:
        return [row for row in rows if row.get("traveler_id") == traveler_id]
    return rows
