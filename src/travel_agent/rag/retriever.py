import math
import re
from collections import Counter
from typing import Any

from travel_agent.rag.citation import citation_fields
from travel_agent.rag.versioning import version_review


_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to", "with"}
_INSTRUCTION = re.compile(
    r"ignore\s+(?:all\s+)?previous\s+instructions|approve\s+all\s+expenses|"
    r"reveal\s+(?:the\s+)?system\s+prompt|override\s+(?:the\s+)?policy",
    re.IGNORECASE,
)
_K1, _B = 1.5, 0.75


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN.findall(text)]


def _bm25_score(query_terms: list[str], doc_terms: list[str], frequencies: Counter[str], idf: dict[str, float], average_length: float) -> float:
    score = 0.0
    for term in query_terms:
        tf = frequencies[term]
        if tf:
            denominator = tf + _K1 * (1 - _B + _B * len(doc_terms) / average_length)
            score += idf[term] * tf * (_K1 + 1) / denominator
    return score


def retrieve(query: str, chunks: list[dict[str, Any]], max_results: int) -> dict[str, Any]:
    query_terms = [term for term in dict.fromkeys(_tokens(query)) if term not in _STOPWORDS]
    tokenized = [_tokens(chunk["text"]) for chunk in chunks]
    document_frequency = Counter(term for terms in tokenized for term in set(terms))
    count = len(chunks)
    idf = {
        term: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
        for term, frequency in document_frequency.items()
    }
    average_length = sum(map(len, tokenized)) / count if count and any(tokenized) else 1
    ranked = []
    excluded = []
    for chunk, terms in zip(chunks, tokenized):
        score = _bm25_score(query_terms, terms, Counter(terms), idf, average_length)
        if score <= 0:
            continue
        if _INSTRUCTION.search(chunk["text"]):
            excluded.append(chunk["chunk_id"])
            continue
        ranked.append({**chunk, "score": round(score, 4), "usable_as_evidence": chunk.get("status") == "active"})
    ranked.sort(key=lambda item: (-item["score"], item["chunk_id"]))
    conflicts, resolved = version_review(ranked)
    candidates = [chunk for chunk in ranked if chunk["usable_as_evidence"]]
    results = [{**chunk, **citation_fields(chunk)} for chunk in candidates[:max_results]]
    return {
        "results": results,
        "no_result": not results,
        "version_conflicts": conflicts,
        "resolved_versions": resolved,
        "excluded_untrusted_chunk_ids": sorted(excluded),
    }
