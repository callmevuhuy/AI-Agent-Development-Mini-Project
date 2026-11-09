import re
from typing import Any

from travel_agent.rag.citation import citation_for_chunk


_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from",
    "has", "have", "in", "is", "it", "of", "on", "or", "that", "the", "their",
    "this", "to", "was", "were", "will", "with", "you", "your",
}
_NEGATION = {"no", "not", "never", "cannot", "without", "neither", "nor"}


def _terms(text: str) -> set[str]:
    terms = set()
    for word in _TOKEN.findall(text.casefold()):
        if len(word) <= 1 or word in _STOPWORDS:
            continue
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("ed") and len(word) > 4:
            word = word[:-2]
            if len(word) > 2 and word[-1] == word[-2]:
                word = word[:-1]
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]
        terms.add(word)
    return terms


def check_claim(claim: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Require every non-stopword claim term to occur in trusted retrieved text."""
    claim_terms = _terms(claim)
    supported = []
    for chunk in chunks:
        if chunk.get("usable_as_evidence") is not True or not isinstance(chunk.get("text"), str):
            continue
        for sentence in re.split(r"(?<=[.!?;])\s+", chunk["text"]):
            sentence_terms = _terms(sentence)
            same_polarity = bool(claim_terms & _NEGATION) == bool(sentence_terms & _NEGATION)
            if claim_terms and claim_terms <= sentence_terms and same_polarity:
                supported.append(citation_for_chunk(chunk))
                break
    return {
        "grounded": bool(claim_terms and supported),
        "citations": supported,
        "unsupported_terms": sorted(claim_terms) if not supported else [],
    }
