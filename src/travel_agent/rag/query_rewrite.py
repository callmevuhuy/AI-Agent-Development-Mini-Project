"""Safe deterministic query rewrite for Agentic RAG (Mục 10.2)."""
from __future__ import annotations

import re
from typing import Any

# Synonyms and domain canonical term replacements that preserve user intent
_REWRITE_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bper\s+diem\b", re.IGNORECASE), "daily meal allowance cap"),
    (re.compile(r"\bhotel\s+(?:limit|ceiling)\b", re.IGNORECASE), "lodging nightly cap rate"),
    (re.compile(r"\bflight\s+postponed\b", re.IGNORECASE), "flight delay notice policy"),
    (re.compile(r"\bentry\s+permit\b", re.IGNORECASE), "visa requirements entry authorization"),
    (re.compile(r"\bhealth\s+coverage\b", re.IGNORECASE), "business travel medical insurance policy"),
    (re.compile(r"\b(?:an\s+uong|bua\s+an|tien\s+an)\b", re.IGNORECASE), "meals daily allowance cap"),
    (re.compile(r"\b(?:khach\s+san|tien\s+phong)\b", re.IGNORECASE), "lodging nightly cap rate"),
    (re.compile(r"\b(?:tre\s+chuyen|hoan\s+chuyen|huy\s+chuyen)\b", re.IGNORECASE), "flight delay notice policy"),
    (re.compile(r"\b(?:thi\s+thuc|nhap\s+canh)\b", re.IGNORECASE), "visa requirements entry authorization"),
    (re.compile(r"\b(?:bao\s+hiem|y\s+te)\b", re.IGNORECASE), "business travel medical insurance policy"),
]


# RAG Query Rewrite (Mục 10.2): Chuẩn hóa truy vấn chính sách tối đa 1 lần/branch có ghi trace an toàn.
def rewrite_query(
    query: str,
    category: str,
    *,
    state: Any | None = None,
    already_rewritten: bool = False,
) -> tuple[str, bool]:
    """Rewrite search query at most once per branch without changing meaning or injecting instructions."""
    if already_rewritten or not isinstance(query, str) or not query.strip():
        return query, False

    from travel_agent.nlu import _unaccent
    rewritten = query
    unaccented = _unaccent(rewritten)
    for pattern, replacement in _REWRITE_MAP:
        if pattern.search(rewritten):
            rewritten = pattern.sub(replacement, rewritten)
        elif pattern.search(unaccented):
            # Substitute matching segment or append canonical terms
            rewritten = f"{rewritten} {replacement}"
            break

    if rewritten != query:
        if state is not None and hasattr(state, "record_event"):
            state.record_event(
                "query_rewrite",
                tool="search_travel_policy",
                safe_args={
                    "category": category,
                    "original_length": len(query),
                    "rewritten_length": len(rewritten),
                },
                observation_status="ok",
                transition="query_rewritten",
            )
        return rewritten, True

    return query, False
