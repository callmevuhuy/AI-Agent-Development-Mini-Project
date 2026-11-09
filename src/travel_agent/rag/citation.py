from typing import Any


def citation_for_chunk(chunk: dict[str, Any]) -> str:
    citation = f"[{chunk['doc_id']} §{chunk['section']} v{chunk['version']} · {chunk['chunk_id']}"
    if chunk.get("page") is not None:
        citation += f" · p.{chunk['page']}"
    return citation + "]"


def citation_fields(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": chunk["chunk_id"],
        "doc_id": chunk["doc_id"],
        "source": chunk["source"],
        "section": chunk["section"],
        "page": chunk.get("page"),
        "version": chunk["version"],
        "citation": citation_for_chunk(chunk),
    }
