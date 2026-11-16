"""Deterministic English NLU: text normalization, ID/date/destination extraction, clause splitting, and intent routing."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from travel_agent.config import get_demo_today


_TRIP_CANONICAL = re.compile(r"\bTRIP[-\s_]?(\d{4})[-\s_]?(\d{3})\b", re.IGNORECASE)
_EXP_CANONICAL = re.compile(r"\bEXP[-\s_]?(\d{4})[-\s_]?(\d{3})\b", re.IGNORECASE)
_ANY_ID_LIKE = re.compile(r"\b(TRIP|EXP)[-_]\d{1,5}[-_]\d{1,5}\b", re.IGNORECASE)

_DESTINATION_ALIASES: dict[str, str] = {
    "singapore": "Singapore",
    "tokyo": "Tokyo",
    "japan": "Tokyo",
    "berlin": "Berlin",
    "germany": "Berlin",
    "london": "London",
    "uk": "London",
    "england": "London",
    "bangkok": "Bangkok",
    "thailand": "Bangkok",
    "sydney": "Sydney",
    "australia": "Sydney",
}

_MONTHS: dict[str, int] = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_ISO_DATE = re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b")
_SLASH_DATE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b")
_MONTH_DATE = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(20\d{2}))?\b",
    re.IGNORECASE,
)
_DAY_MONTH_DATE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:,?\s*(20\d{2}))?\b",
    re.IGNORECASE,
)

_SAFETY_PATTERNS = [
    r"\bignore\s+(?:all\s+)?(?:previous\s+)?(?:rules|instructions|policies|policy)\b",
    r"\bdisregard\s+(?:all\s+)?(?:previous\s+|earlier\s+)?(?:rules|instructions|policies|policy)\b",
    r"\bbypass\s+(?:all\s+)?(?:rules|policy|policies|checks|approval|security)\b",
    r"\boverride\s+(?:the\s+)?(?:policy|rules|system)\b",
    r"\breveal\s+(?:the\s+)?(?:system\s+prompt|secret|api\s+key|credentials)\b",
    r"\bapprove\s+all\s+expenses\b",
    r"\bdelete\s+all\b",
    r"\bjailbreak\b",
]

_FORBIDDEN_COMMAND_PATTERNS = [
    r"(?:^|\b(?:can|could|would|will)\s+you\s+|please\s+)(?:book|reserve|purchase|buy|rebook|cancel|approve|reject|pay|refund|reimburse|charge|send)\b",
    r"\b(?:book|reserve|rebook|purchase)\s+(?:a\s+|the\s+|my\s+)?(?:flight|ticket|hotel|room)\b",
    r"\b(?:approve|reject|sign\s+off|pay|refund|reimburse)\s+(?:my\s+|this\s+|the\s+)?(?:trip|expense|report|request|claim)\s*(?:now|immediately|already|for\s+me)?\b",
    r"\bcharge\s+(?:my\s+|the\s+)?(?:card|credit\s+card|account)\b",
    r"\bsend\s+(?:an?\s+)?email\b",
]

_HANDOFF_PATTERNS = [
    r"\bspeak\s+(?:to|with)\s+(?:a\s+)?(?:human|staff|manager|agent|person|reviewer|representative)\b",
    r"\btalk\s+(?:to|with)\s+(?:a\s+)?(?:human|staff|manager|agent|person|reviewer)\b",
    r"\b(?:human\s+support|human\s+agent|human\s+staff|live\s+agent|customer\s+support|travel\s+ops\s+staff)\b",
    r"\bescalate\s+(?:to\s+)?(?:staff|manager|human|support)\b",
    r"\bfile\s+(?:a\s+)?complaint\b",
]

_GREETING_PATTERNS = [
    r"^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|greetings)[!.\s]*$",
    r"^(?:what\s+can\s+you\s+do|help|how\s+do\s+you\s+work)[?!.\s]*$",
]

_INTRIP_KEYWORDS = (
    "delay", "delayed", "cancel", "cancelled", "canceled", "disruption",
    "stranded", "missed flight", "itinerary", "flight status", "in-trip", "intrip",
)
_PRETRIP_KEYWORDS = (
    "prepare", "pre-trip", "pretrip", "checklist", "compliance", "requirement",
    "requirements", "ready", "before departure", "trip status", "approval status",
    "traveling to", "travelling to", "going to", "upcoming trip",
)
_POLICY_TOPIC_NOUNS = (
    "policy", "policies", "rule", "rules", "cap", "limit", "allowance", "visa",
    "insurance", "coverage", "eligible", "eligibility", "meal", "meals", "food",
    "lodging", "hotel", "room", "receipt", "receipts", "rebooking", "disruption",
    "approval", "per day", "per night",
)
_POLICY_QA_HINTS = (
    *_POLICY_TOPIC_NOUNS,
    "allowed", "what is", "what are", "how much", "how many", "can i", "do i need", "should i",
)


@dataclass(frozen=True)
class RouteDecision:
    route: str  # "SELF_SERVE" | "CLARIFY" | "HANDOFF_STAFF" | "REJECT_SAFETY"
    intent: str
    trip_id: str | None = None
    report_id: str | None = None
    malformed_id: str | None = None
    destination: str | None = None
    date_hint: str | None = None
    policy_query: str | None = None
    policy_category: str | None = None
    preference_cmd: dict[str, Any] | None = None
    admin_action: str | None = None
    reason: str = ""


# NLU Input Normalization (Mục 12): Chuẩn hóa chuỗi văn bản đầu vào theo chuẩn NFKC và loại bỏ ký tự lạ.
def normalize_text(text: str) -> str:
    """Normalize English text (NFKC, lowercase, collapsed whitespace) for deterministic matching."""
    if not isinstance(text, str):
        return ""
    norm = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(norm.split())


# NLU Input Validation (Mục 12): Trích xuất và kiểm định mã TRIP-ID hoặc EXP-ID từ thông điệp người dùng.
def extract_record_ids(text: str) -> dict[str, str | None]:
    """Extract canonical TRIP/EXP IDs and detect malformed ID attempts."""
    trip_match = _TRIP_CANONICAL.search(text)
    report_match = _EXP_CANONICAL.search(text)
    trip_id = f"TRIP-{trip_match.group(1)}-{trip_match.group(2)}" if trip_match else None
    report_id = f"EXP-{report_match.group(1)}-{report_match.group(2)}" if report_match else None

    malformed_id = None
    for match in _ANY_ID_LIKE.finditer(text):
        token = match.group(0).upper()
        prefix = match.group(1).upper()
        if prefix == "TRIP" and not re.fullmatch(r"TRIP-\d{4}-\d{3}", token):
            malformed_id = token
            break
        if prefix == "EXP" and not re.fullmatch(r"EXP-\d{4}-\d{3}", token):
            malformed_id = token
            break
    return {"trip_id": trip_id, "report_id": report_id, "malformed_id": malformed_id}


def extract_destination(norm: str) -> str | None:
    """Extract a known destination city from a normalized English message."""
    for alias, canonical in _DESTINATION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", norm):
            return canonical
    return None


def extract_date_hint(norm: str) -> str | None:
    """Extract an ISO date from explicit dates (YYYY-MM-DD, DD/MM/YYYY, 'Dec 8') or 'today'/'tomorrow'."""
    iso = _ISO_DATE.search(norm)
    if iso:
        try:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3))).isoformat()
        except ValueError:
            pass
    slash = _SLASH_DATE.search(norm)
    if slash:
        day, month, year = int(slash.group(1)), int(slash.group(2)), int(slash.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass
    m_match = _MONTH_DATE.search(norm)
    if m_match:
        month = _MONTHS[m_match.group(1).casefold()]
        day = int(m_match.group(2))
        year = int(m_match.group(3)) if m_match.group(3) else (2027 if month == 1 else get_demo_today().year)
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass
    dm_match = _DAY_MONTH_DATE.search(norm)
    if dm_match:
        day = int(dm_match.group(1))
        month = _MONTHS[dm_match.group(2).casefold()]
        year = int(dm_match.group(3)) if dm_match.group(3) else (2027 if month == 1 else get_demo_today().year)
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass
    if re.search(r"\btomorrow\b", norm):
        return (get_demo_today() + timedelta(days=1)).isoformat()
    if re.search(r"\btoday\b", norm):
        return get_demo_today().isoformat()
    return None


def detect_preference_command(norm: str) -> dict[str, Any] | None:
    """Detect explicit user preference read/set/delete requests."""
    if any(phrase in norm for phrase in ("show my preference", "my preferences", "get preference", "what are my preferences")):
        key = "response_language" if "language" in norm else ("preferred_output_format" if "format" in norm else None)
        return {"action": "get", "key": key}
    if any(word in norm for word in ("delete", "remove", "clear", "forget", "reset")) and any(
        word in norm for word in ("preference", "preferences", "format", "language")
    ):
        key = "response_language" if "language" in norm else "preferred_output_format"
        return {"action": "delete", "key": key}
    if any(word in norm for word in ("prefer", "set", "remember", "save", "change", "use")) and any(
        word in norm for word in ("concise", "detailed", "format", "language")
    ):
        if "concise" in norm:
            return {"action": "set", "key": "preferred_output_format", "value": "concise"}
        if "detailed" in norm:
            return {"action": "set", "key": "preferred_output_format", "value": "detailed"}
        lang_match = re.search(r"\b(?:language|lang)\s+(?:to\s+)?(en|vi|english|vietnamese)\b", norm)
        if lang_match:
            raw = lang_match.group(1)
            val = "vi" if raw in {"vi", "vietnamese"} else "en"
            return {"action": "set", "key": "response_language", "value": val}
    return None


def detect_policy_category(norm: str) -> str:
    """Infer the policy category for a knowledge query."""
    if any(k in norm for k in ("visa", "entry", "passport", "immigration")):
        return "visa"
    if any(k in norm for k in ("insurance", "medical", "health", "coverage")):
        return "insurance"
    if any(k in norm for k in ("meal", "meals", "food", "dinner", "lunch", "lodging", "hotel", "room", "receipt", "expense", "reimburse")):
        return "expense"
    if any(k in norm for k in ("approval", "approve", "pre-approval")):
        return "approval"
    return "travel"


def _has_any(norm: str, keywords: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(kw)}\b", norm) for kw in keywords)


def _split_clauses(text: str) -> list[str]:
    parts = re.split(r"[,;?!]+|\b(?:and\s+also|and|also|then|plus)\b", text, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part and part.strip()]


def _infer_workflow_intent(norm: str, trip_id: str | None, report_id: str | None, dest: str | None, date_hint: str | None) -> str | None:
    if report_id or _has_any(norm, ("expense", "expenses", "receipt", "reimburse", "reimbursement", "post-trip", "posttrip")):
        return "posttrip"
    if _has_any(norm, _INTRIP_KEYWORDS):
        return "intrip"
    if _has_any(norm, _PRETRIP_KEYWORDS):
        return "pretrip"
    if (trip_id or dest or date_hint) and any(w in norm for w in ("trip", "travel", "flight", "check", "review", "status")):
        return "pretrip"
    return None


# NLU Routing (Mục 5, 10.1, 12): Phân loại yêu cầu người dùng vào một trong 4 luồng xử lý nghiêm ngặt.
def route_message_intent(message: str) -> RouteDecision:
    """Classify an English user message into one of four deterministic routes."""
    if not isinstance(message, str) or not message.strip():
        return RouteDecision("CLARIFY", "clarify_id", reason="Empty user message.")
    if len(message) > 1000:
        return RouteDecision("REJECT_SAFETY", "safety_adversarial", reason="Message exceeds maximum allowed length.")

    norm = normalize_text(message)

    # 1. Safety / prompt-injection checks come first.
    if any(re.search(p, norm) for p in _SAFETY_PATTERNS):
        return RouteDecision("REJECT_SAFETY", "safety_adversarial", reason="Adversarial or rule-bypass phrasing detected.")

    # 2. Explicit forbidden-action commands (must hand off, never execute or fabricate).
    is_policy_question = bool(
        re.search(r"\b(?:can\s+i|am\s+i|may\s+i|do\s+i|should\s+i|is\s+it\s+allowed|what\s+is\s+the\s+policy|policy\s+on)\b", norm)
    )
    if not is_policy_question and any(re.search(p, norm) for p in _FORBIDDEN_COMMAND_PATTERNS):
        ids = extract_record_ids(message)
        return RouteDecision(
            "HANDOFF_STAFF",
            "out_of_scope",
            trip_id=ids["trip_id"],
            report_id=ids["report_id"],
            destination=extract_destination(norm),
            date_hint=extract_date_hint(norm),
            reason="Requested action (booking, payment, refund, approval decision, or external email) is outside agent authority.",
        )

    # 3. Explicit user request for human staff.
    if any(re.search(p, norm) for p in _HANDOFF_PATTERNS):
        ids = extract_record_ids(message)
        return RouteDecision(
            "HANDOFF_STAFF",
            "handoff_requested",
            trip_id=ids["trip_id"],
            report_id=ids["report_id"],
            destination=extract_destination(norm),
            date_hint=extract_date_hint(norm),
            reason="User explicitly requested human Travel Operations staff assistance.",
        )

    ids = extract_record_ids(message)
    trip_id, report_id, malformed_id = ids["trip_id"], ids["report_id"], ids["malformed_id"]
    if malformed_id:
        return RouteDecision("REJECT_SAFETY", "invalid_id", malformed_id=malformed_id, reason="Malformed trip or expense ID format.")

    dest = extract_destination(norm)
    date_hint = extract_date_hint(norm)

    # 4. Admin / Reviewer overview intents.
    if re.search(r"\b(?:audit\s+(?:log|history|events?))\b", norm):
        return RouteDecision("SELF_SERVE", "admin_overview", trip_id=trip_id, report_id=report_id, admin_action="audit")
    if re.search(r"\b(?:list|show|view|all)\s+(?:company\s+|employee\s+|all\s+)?trips\b", norm):
        return RouteDecision("SELF_SERVE", "admin_overview", trip_id=trip_id, destination=dest, admin_action="trips")

    # 5. Explicit preference commands.
    pref_cmd = detect_preference_command(norm)
    if pref_cmd:
        return RouteDecision("SELF_SERVE", "preference", preference_cmd=pref_cmd)

    # 6. Pure greetings / help.
    if any(re.search(p, norm) for p in _GREETING_PATTERNS):
        return RouteDecision("SELF_SERVE", "greeting")

    # 7. Bare ID or bare destination/date reply (multi-turn clarification).
    if re.fullmatch(r"\s*(?:TRIP|EXP)[-\s_]?\d{4}[-\s_]?\d{3}\s*[.!?]?\s*", message, re.IGNORECASE):
        return RouteDecision("SELF_SERVE", "clarify_id", trip_id=trip_id, report_id=report_id)
    if dest and len(norm.split()) <= 3 and not _has_any(norm, _POLICY_QA_HINTS):
        return RouteDecision("SELF_SERVE", "clarify_id", destination=dest, date_hint=date_hint)

    # 8. Mixed query detection via clause splitting.
    clauses = _split_clauses(message)
    if len(clauses) >= 2 and (trip_id or report_id or dest or date_hint):
        wf_intent: str | None = None
        policy_clauses: list[str] = []
        for clause in clauses:
            c_norm = normalize_text(clause)
            c_ids = extract_record_ids(clause)
            c_dest = extract_destination(c_norm)
            c_date = extract_date_hint(c_norm)
            c_wf = _infer_workflow_intent(c_norm, c_ids["trip_id"], c_ids["report_id"], c_dest, c_date)
            c_policy = _has_any(c_norm, _POLICY_TOPIC_NOUNS) and not c_ids["trip_id"] and not c_ids["report_id"] and not c_wf
            if c_wf and not wf_intent:
                wf_intent = c_wf
            elif c_policy:
                policy_clauses.append(clause)
        if wf_intent and policy_clauses:
            policy_q = " ".join(policy_clauses)
            return RouteDecision(
                route="SELF_SERVE",
                intent="mixed",
                trip_id=trip_id,
                report_id=report_id,
                destination=dest,
                date_hint=date_hint,
                policy_query=policy_q,
                policy_category=detect_policy_category(normalize_text(policy_q)),
            )

    # 9. Single workflow intent (supports natural destination/date resolution without raw IDs).
    wf = _infer_workflow_intent(norm, trip_id, report_id, dest, date_hint)
    if wf:
        return RouteDecision(
            route="SELF_SERVE",
            intent=wf,
            trip_id=trip_id,
            report_id=report_id,
            destination=dest,
            date_hint=date_hint,
        )

    # 10. Standalone Policy Q&A.
    if _has_any(norm, _POLICY_QA_HINTS):
        return RouteDecision(
            route="SELF_SERVE",
            intent="policy_qa",
            destination=dest,
            policy_query=message.strip(),
            policy_category=detect_policy_category(norm),
        )

    # 11. Ambiguous / out-of-domain -> hand off cleanly without guessing.
    return RouteDecision(
        route="HANDOFF_STAFF",
        intent="out_of_scope",
        destination=dest,
        date_hint=date_hint,
        reason="Request could not be mapped confidently to a supported travel operations workflow or policy query.",
    )
