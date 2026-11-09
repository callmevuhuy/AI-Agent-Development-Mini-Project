from typing import Any

from travel_agent.rag.retriever import retrieve

from ._storage import load_dataset


def get_policy_chunks(category: str | None = None, role: str | None = None) -> list[dict[str, Any]]:
    chunks = load_dataset("policy_chunks.json")
    if category is not None:
        chunks = [chunk for chunk in chunks if chunk["category"] == category]
    if role is not None:
        chunks = [chunk for chunk in chunks if role in chunk.get("allowed_roles", [])]
    return chunks


def search_policy_chunks(query: str, category: str, max_results: int, role: str) -> dict[str, Any]:
    # ACL filtering happens before BM25 ranking, version checks, and citations.
    return retrieve(query, get_policy_chunks(category, role), max_results)
