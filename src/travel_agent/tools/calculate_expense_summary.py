import math
from collections import defaultdict
from typing import Any

from travel_agent.mock_systems.expense import get_expense_report
from travel_agent.mock_systems.policy_kb import get_policy_chunks
from travel_agent.tools._result import failure, success


def run(arguments: dict[str, Any], *, user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(user_context, dict):
        return failure("unauthorized_scope", "Application role context is required.")
    report = get_expense_report(arguments["report_id"])
    if report is None:
        return failure("not_found", "The requested mock record was not found.")

    currency = report["currency"]
    totals: dict[str, float] = defaultdict(float)
    daily_meals: dict[str, float] = defaultdict(float)
    missing_fields = []
    missing_receipts = []
    invalid_items = []
    all_policy_chunks = get_policy_chunks("expense")
    policy_chunks = get_policy_chunks("expense", role=user_context.get("role"))
    categories_with_rules = {chunk["rule"]["category"] for chunk in all_policy_chunks if isinstance(chunk.get("rule"), dict)}
    visible_rule_categories = {chunk["rule"]["category"] for chunk in policy_chunks if isinstance(chunk.get("rule"), dict)}
    report_categories = {item.get("category") for item in report["line_items"] if isinstance(item.get("category"), str)}
    if (report_categories & categories_with_rules) - visible_rule_categories:
        return failure("policy_access_required", "Applicable policy evidence is not available to this role.")

    rules: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for chunk in policy_chunks:
        rule = chunk.get("rule")
        if chunk.get("status") == "active" and isinstance(rule, dict):
            rules[(rule["category"], rule["measure"])].append({**rule, "chunk_id": chunk["chunk_id"]})

    for item in report["line_items"]:
        item_id = item.get("item_id", "unknown")
        missing = [field for field in ("item_id", "category", "amount", "date", "receipt_attached") if field not in item]
        if missing:
            missing_fields.append({"item_id": item_id, "fields": missing})
        if item.get("receipt_attached") is not True:
            missing_receipts.append(item_id)
        amount = item.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            invalid_items.append(item_id)
            continue
        category = item.get("category")
        if not isinstance(category, str):
            invalid_items.append(item_id)
            continue
        totals[category] += amount
        if category == "meals" and isinstance(item.get("date"), str):
            daily_meals[item["date"]] += amount

    total = sum(totals.values())
    conflicts = []
    for (category, measure), candidates in rules.items():
        if category not in totals:
            continue
        caps = sorted({candidate["cap"] for candidate in candidates if candidate["currency"] == currency})
        if len(caps) > 1:
            conflicts.append({
                "category": category,
                "measure": measure,
                "caps": caps,
                "policy_refs": [candidate["chunk_id"] for candidate in candidates if candidate["currency"] == currency],
            })

    threshold_flags = []
    for date, amount in sorted(daily_meals.items()):
        candidates = [c for c in rules.get(("meals", "per_traveler_per_day"), []) if c["currency"] == currency]
        caps = [c["cap"] for c in candidates]
        if caps:
            status = "exceeds_all_active_versions" if amount > max(caps) else (
                "exceeds_some_active_versions" if amount > min(caps) else "within_all_active_versions"
            )
            threshold_flags.append({
                "category": "meals",
                "measure": "per_traveler_per_day",
                "date": date,
                "amount": round(amount, 2),
                "currency": currency,
                "status": status,
                "policy_refs": [c["chunk_id"] for c in candidates],
            })

    lodging_rules = [c for c in rules.get(("lodging", "per_night"), []) if c["currency"] == currency]
    for item in report["line_items"]:
        amount = item.get("amount")
        if item.get("category") == "lodging" and lodging_rules and isinstance(amount, (int, float)) and not isinstance(amount, bool):
            cap = min(rule["cap"] for rule in lodging_rules)
            if amount > cap:
                threshold_flags.append({
                    "category": "lodging",
                    "measure": "per_night",
                    "item_id": item.get("item_id"),
                    "amount": round(amount, 2),
                    "currency": currency,
                    "status": "exceeds_all_active_versions",
                    "policy_refs": [rule["chunk_id"] for rule in lodging_rules],
                })

    data = {
        "report_id": report["report_id"],
        "currency": currency,
        "total": round(total, 2),
        "category_totals": {key: round(value, 2) for key, value in sorted(totals.items())},
        "category_ratios": {key: round(value / total, 4) if total else 0 for key, value in sorted(totals.items())},
        "missing_fields": missing_fields,
        "missing_receipts": missing_receipts,
        "invalid_items": invalid_items,
        "threshold_conflicts": conflicts,
        "threshold_flags": threshold_flags,
    }
    return success(data, "mock_expense_system+mock_policy_knowledge_base")
