import json
import re
from collections import defaultdict
from datetime import date
from typing import Any

from travel_agent.rag.citation import citation_fields


def _version_key(version: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", version)
    return tuple(map(int, parts)) if parts else ()


def version_review(chunks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        groups[(chunk["doc_id"], chunk["section"])].append(chunk)

    conflicts, resolved = [], []
    for (doc_id, section), versions in groups.items():
        if len({chunk["version"] for chunk in versions}) < 2:
            continue
        active = [chunk for chunk in versions if chunk.get("status") == "active"]
        superseded = [chunk for chunk in versions if chunk.get("status") == "superseded"]
        if not active:
            continue
        signatures = {
            json.dumps(chunk.get("rule", chunk.get("text", "")), sort_keys=True, ensure_ascii=False)
            for chunk in versions
        }
        if len(signatures) < 2:
            continue
        newer_active = []
        for chunk in active:
            try:
                effective = date.fromisoformat(chunk["effective_date"])
            except (KeyError, TypeError, ValueError):
                continue
            if superseded and _version_key(chunk["version"]) and all(
                _version_key(chunk["version"]) > _version_key(old["version"])
                for old in superseded
            ):
                newer_active.append((effective, chunk))
        if len(newer_active) == len(active) == 1 and superseded:
            effective, selected = newer_active[0]
            resolved.append({
                "doc_id": doc_id,
                "section": section,
                "selected": citation_fields(selected),
                "superseded": [citation_fields(chunk) for chunk in superseded],
                "effective_date": effective.isoformat(),
            })
        else:
            conflicts.append({
                "doc_id": doc_id,
                "section": section,
                "versions": [citation_fields(chunk) for chunk in sorted(versions, key=lambda item: item["version"])],
                "resolution": "needs_human",
            })
    return conflicts, resolved
