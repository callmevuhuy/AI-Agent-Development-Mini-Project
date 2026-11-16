import math
import re
from collections import Counter
from typing import Any

from travel_agent.rag.citation import citation_fields
from travel_agent.rag.versioning import version_review


_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "the", "to", "with", "what", "how", "can",
}
_INSTRUCTION = re.compile(
    r"ignore\s+(?:all\s+)?previous\s+instructions|"
    r"disregard\s+(?:all\s+)?(?:previous|earlier)\s+(?:instructions|rules)|"
    r"approve\s+all\s+expenses|"
    r"mark\s+all\s+.*\s+approved|"
    r"bypass\s+(?:the\s+)?(?:policy|approval|rules)|"
    r"reveal\s+(?:the\s+)?system\s+prompt|"
    r"override\s+(?:the\s+)?policy",
    re.IGNORECASE,
)
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "hotel": ("lodging", "nightly"),
    "accommodation": ("lodging", "nightly"),
    "room": ("lodging",),
    "food": ("meal", "meals", "allowance"),
    "dinner": ("meal", "meals"),
    "lunch": ("meal", "meals"),
    "breakfast": ("meal", "meals"),
    "meal": ("meals",),
    "late": ("delay", "delays"),
    "postponed": ("delay", "delays"),
    "delayed": ("delay", "delays"),
    "canceled": ("cancel", "cancellation", "cancellations"),
    "cancelled": ("cancel", "cancellation", "cancellations"),
    "invoice": ("receipt", "receipts"),
    "bill": ("receipt", "receipts"),
    "proof": ("receipt", "receipts"),
    "permit": ("visa", "entry"),
    "medical": ("insurance",),
    "health": ("insurance",),
    "limit": ("cap", "capped"),
    "maximum": ("cap", "capped"),
}
_K1, _B = 1.5, 0.75


def _stem(word: str) -> str:
    if len(word) <= 3:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ing") and len(word) > 5:
        return word[:-3]
    if word.endswith("ed") and len(word) > 4:
        base = word[:-2]
        return base[:-1] if len(base) > 2 and base[-1] == base[-2] else base
    if word.endswith("es") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        return word[:-1]
    return word


def _tokens(text: str, *, expand_synonyms: bool = False) -> list[str]:
    base = [t for t in (tok.casefold() for tok in _TOKEN.findall(text)) if t not in _STOPWORDS]
    expanded: list[str] = []
    for tok in base:
        expanded.append(_stem(tok))
        if expand_synonyms and tok in _SYNONYMS:
            expanded.extend(_stem(syn) for syn in _SYNONYMS[tok])
    return expanded


def _bm25_score(
    query_terms: list[str],
    doc_terms: list[str],
    frequencies: Counter[str],
    idf: dict[str, float],
    average_length: float,
) -> float:
    score = 0.0
    for term in query_terms:
        tf = frequencies[term]
        if tf and term in idf:
            denominator = tf + _K1 * (1 - _B + _B * len(doc_terms) / average_length)
            score += idf[term] * tf * (_K1 + 1) / denominator
    return score


# RAG Retriever (Mục 10.1, 12): Tìm kiếm BM25 offline kết hợp stemming, từ đồng nghĩa và loại trừ tiêm nhiễm.
def retrieve(query: str, chunks: list[dict[str, Any]], max_results: int) -> dict[str, Any]:
    """Run offline BM25 retrieval with light stemming, synonym expansion, and injection exclusion."""
    query_terms = list(dict.fromkeys(_tokens(query, expand_synonyms=True)))
    tokenized = [_tokens(chunk["text"], expand_synonyms=False) for chunk in chunks]
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
