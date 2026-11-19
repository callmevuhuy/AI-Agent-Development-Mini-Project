"""Dual-backend LLM abstraction (RuleBased default + optional Gemini API).

Implements:
- Phase 1: Structured-output NLU intent routing with round-1 safety guard and fallback.
- Phase 2: 1-hop RAG query rewrite and grounded narrative synthesis with Post-Generation Guard.
- Phase 3: Gemini Function Calling / tool-use loop routed exclusively through dispatcher.dispatch().
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
import time
from typing import Any

from travel_agent.config import (
    DEFAULT_MAX_STEPS,
    TOTAL_TURN_MAX_STEPS,
    get_gemini_api_key,
    get_gemini_model,
    get_gemini_timeout,
    get_llm_backend,
)
from travel_agent.nlu import (
    RouteDecision,
    _SAFETY_PATTERNS,
    _unaccent,
    extract_date_hint,
    extract_destination,
    extract_record_ids,
    normalize_text,
    route_message_intent,
)
from travel_agent.orchestrator import run_tool
from travel_agent.rag.query_rewrite import rewrite_query
from travel_agent.registry import TOOL_REGISTRY, WORKFLOW_ALLOWLISTS
from travel_agent.state import RunState
from travel_agent.trace import safe_arguments

_ALLOWED_LLM_ROUTES = frozenset({"SELF_SERVE", "CLARIFY", "HANDOFF_STAFF"})
_ALLOWED_LLM_INTENTS = frozenset({
    "pretrip", "intrip", "posttrip", "policy_qa", "mixed",
    "trip_details", "itinerary_read", "handoff_requested", "greeting", "out_of_scope",
})
_ALLOWED_CATEGORIES = frozenset({"travel", "expense", "visa", "insurance", "approval"})
_TRIP_ID_RE = re.compile(r"^TRIP-\d{4}-\d{3}$")
_REPORT_ID_RE = re.compile(r"^EXP-\d{4}-\d{3}$")
_CITATION_TOKEN_RE = re.compile(r"\[([A-Z0-9-]+(?:\s+§[^\s\],·]+)?|CH-[A-Z0-9-]+)")
_APPROVAL_CLAIM_RE = re.compile(
    r"(?<!chưa\s)(?<!không\s)(?<!chờ\s)(?<!not\s)(?<!pending\s)(?<!awaiting\s)"
    r"\b(?:đã\s+(?:được\s+)?phê\s+duyệt|đã\s+duyệt\s+hoàn\s+tiền|approval\s+granted|reimbursement\s+approved)\b",
    re.IGNORECASE,
)

_NLU_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "route": {"type": "string", "enum": ["SELF_SERVE", "CLARIFY", "HANDOFF_STAFF"]},
        "intent": {
            "type": "string",
            "enum": sorted(_ALLOWED_LLM_INTENTS),
        },
        "trip_id": {"type": ["string", "null"]},
        "report_id": {"type": ["string", "null"]},
        "destination": {"type": ["string", "null"]},
        "date_hint": {"type": ["string", "null"]},
        "policy_query": {"type": ["string", "null"]},
        "policy_category": {"type": ["string", "null"]},
        "reason": {"type": "string"},
    },
    "required": ["route", "intent", "reason"],
}


class TurnBudget:
    """Shared step-budget tracker across multi-part turns and auxiliary lookups."""

    def __init__(self, max_total_steps: int = TOTAL_TURN_MAX_STEPS) -> None:
        self.max_total_steps = max(1, max_total_steps)
        self.used_steps = 0

    def remaining(self) -> int:
        return max(0, self.max_total_steps - self.used_steps)

    def allocate(self, desired: int = DEFAULT_MAX_STEPS) -> int:
        rem = self.remaining()
        return max(1, min(desired, rem)) if rem > 0 else 0

    def consume(self, steps: int) -> None:
        if steps > 0:
            self.used_steps += steps


@dataclass
class LLMCallMeta:
    backend: str = "rule"
    model: str | None = None
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    fallback_used: bool = False
    fallback_reason: str | None = None
    query_rewritten: bool = False
    tool_loop_steps: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "model": self.model,
            "latency_ms": round(self.latency_ms, 2),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "query_rewritten": self.query_rewritten,
            "tool_loop_steps": self.tool_loop_steps,
        }


def _extract_usage(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage_metadata", None)
    if not usage:
        return 0, 0
    inp = getattr(usage, "prompt_token_count", 0) or 0
    out = getattr(usage, "candidates_token_count", 0) or 0
    return int(inp), int(out)


def _sanitize_error_reason(exc: Exception) -> str:
    msg = str(exc)
    if "AIza" in msg:
        msg = re.sub(r"AIza[0-9A-Za-z_-]{10,}", "[REDACTED_KEY]", msg)
    low = msg.lower()
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if "429" in low or "quota" in low or "rate" in low:
        return "rate_limited"
    return type(exc).__name__


def _contains_safety_pattern(text: str) -> bool:
    norm = normalize_text(text)
    clean = _unaccent(norm)
    return any(re.search(p, norm) or re.search(p, clean) for p in _SAFETY_PATTERNS)


def _parse_nlu_payload(raw_text: str, message: str) -> RouteDecision | None:
    if not raw_text:
        return None
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        return None
    route = data.get("route")
    intent = data.get("intent")
    if route not in _ALLOWED_LLM_ROUTES or intent not in _ALLOWED_LLM_INTENTS:
        return None
    trip_id = data.get("trip_id")
    if not isinstance(trip_id, str) or not _TRIP_ID_RE.fullmatch(trip_id):
        trip_id = extract_record_ids(message)["trip_id"]
    report_id = data.get("report_id")
    if not isinstance(report_id, str) or not _REPORT_ID_RE.fullmatch(report_id):
        report_id = extract_record_ids(message)["report_id"]
    dest = data.get("destination")
    if not isinstance(dest, str) or not dest.strip():
        dest = extract_destination(normalize_text(message))
    date_hint = data.get("date_hint")
    if not isinstance(date_hint, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date_hint):
        date_hint = extract_date_hint(normalize_text(message))
    pol_query = data.get("policy_query")
    pol_query = pol_query.strip()[:200] if isinstance(pol_query, str) and pol_query.strip() else None
    pol_cat = data.get("policy_category")
    if pol_cat not in _ALLOWED_CATEGORIES:
        pol_cat = "travel" if intent in {"policy_qa", "mixed"} else None
    reason = str(data.get("reason") or "").strip()[:240]
    return RouteDecision(
        route=route,
        intent=intent,
        trip_id=trip_id,
        report_id=report_id,
        destination=dest,
        date_hint=date_hint,
        policy_query=pol_query,
        policy_category=pol_cat,
        reason=reason,
    )


def check_generated_response(
    generated_text: str,
    citations: list[str],
    approval_status: str | None = None,
    *,
    require_all_citations: bool = True,
) -> tuple[bool, str | None]:
    """Post-Generation Guard (Phase 2): verify grounding citations and prevent false approval claims."""
    if not isinstance(generated_text, str) or not generated_text.strip() or len(generated_text) > 4000:
        return False, "empty_or_oversized_response"
    if _contains_safety_pattern(generated_text):
        return False, "unsafe_output_pattern"
    if approval_status != "approved" and _APPROVAL_CLAIM_RE.search(generated_text):
        return False, "unverified_approval_claim"
    tags: list[str] = []
    for cit in citations:
        if not isinstance(cit, str) or not cit.strip():
            continue
        match = _CITATION_TOKEN_RE.search(cit)
        required_tag = match.group(1) if match else cit.strip("[]").split(",")[0].strip()
        if required_tag:
            tags.append(required_tag)
    if tags:
        if require_all_citations:
            for tag in tags:
                if tag not in generated_text:
                    return False, f"missing_citation:{tag}"
        elif not any(tag in generated_text for tag in tags):
            return False, f"missing_citation:{tags[0]}"
    return True, None


def _role_tool_names(role: str, workflow: str | None = None) -> list[str]:
    if role == "Admin":
        return ["admin_list_trips", "admin_get_audit_history"]
    if role == "Approver":
        return ["get_trip_request", "get_itinerary", "get_approval_status", "search_travel_policy", "get_preference"]
    if workflow and workflow in WORKFLOW_ALLOWLISTS:
        allowed = WORKFLOW_ALLOWLISTS[workflow]
    else:
        allowed = (
            WORKFLOW_ALLOWLISTS["pretrip"]
            | WORKFLOW_ALLOWLISTS["intrip"]
            | WORKFLOW_ALLOWLISTS["posttrip"]
        )
    if role == "Reviewer":
        return sorted(name for name in allowed if name != "request_approval")
    return sorted(allowed)


def build_gemini_tools(role: str, workflow: str | None = None) -> list[Any]:
    """Convert contract-verified TOOL_REGISTRY schemas to Gemini FunctionDeclarations."""
    from google.genai import types

    declarations = [
        types.FunctionDeclaration(
            name=name,
            description=TOOL_REGISTRY[name].description,
            parameters_json_schema=TOOL_REGISTRY[name].schema,
        )
        for name in _role_tool_names(role, workflow)
        if name in TOOL_REGISTRY
    ]
    return [types.Tool(function_declarations=declarations)] if declarations else []


class RuleBasedBackend:
    """Offline deterministic backend requiring zero network or API keys."""

    name = "rule"

    def classify_intent(
        self,
        message: str,
        *,
        session_state: dict[str, Any] | None = None,
        role: str = "Employee",
    ) -> tuple[RouteDecision, LLMCallMeta]:
        return route_message_intent(message), LLMCallMeta(backend="rule")

    def rewrite_policy_query(
        self,
        query: str,
        category: str,
        *,
        state: RunState | None = None,
        already_rewritten: bool = False,
    ) -> tuple[str, bool, LLMCallMeta]:
        rewritten, changed = rewrite_query(query, category, state=state, already_rewritten=already_rewritten)
        return rewritten, changed, LLMCallMeta(backend="rule", query_rewritten=changed)

    def synthesize_response(
        self,
        deterministic_text: str,
        facts_payload: dict[str, Any],
        citations: list[str],
        *,
        output_format: str = "concise",
        is_vi: bool = False,
        approval_status: str | None = None,
        state: RunState | None = None,
    ) -> tuple[str, LLMCallMeta]:
        return deterministic_text, LLMCallMeta(backend="rule")

    def run_tool_loop(self, **kwargs: Any) -> tuple[dict[str, Any] | None, LLMCallMeta]:
        return None, LLMCallMeta(backend="rule")


class GeminiBackend:
    """Optional Gemini API backend with fail-safe deterministic fallback."""

    name = "gemini"

    def __init__(
        self,
        *,
        model: str | None = None,
        timeout: float | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = get_gemini_model(model)
        self.timeout = timeout if timeout is not None else get_gemini_timeout()
        self._injected_client = client

    def _get_client(self) -> Any:
        if self._injected_client is not None:
            return self._injected_client
        api_key = get_gemini_api_key()
        if not api_key:
            raise RuntimeError("missing_api_key")
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(self.timeout * 1000)),
        )

    def _generate(self, contents: Any, config: Any) -> Any:
        client = self._get_client()
        return client.models.generate_content(model=self.model, contents=contents, config=config)

    def classify_intent(
        self,
        message: str,
        *,
        session_state: dict[str, Any] | None = None,
        role: str = "Employee",
    ) -> tuple[RouteDecision, LLMCallMeta]:
        # Round-1 deterministic safety, malformed-ID, explicit command & greeting guard runs BEFORE any API call.
        rule_decision = route_message_intent(message)
        if (
            rule_decision.route == "REJECT_SAFETY"
            or rule_decision.intent in {"greeting", "preference", "approval_decision", "admin_overview", "request_approval"}
        ):
            return rule_decision, LLMCallMeta(backend="rule")

        # Keep clear single/explicit routes deterministic; invoke Gemini when rule NLU struggles or is ambiguous/VN follow-up.
        needs_llm = (
            rule_decision.route == "CLARIFY"
            or rule_decision.intent == "out_of_scope"
            or (bool(session_state) and not rule_decision.trip_id and not rule_decision.report_id)
        )
        if not needs_llm:
            return rule_decision, LLMCallMeta(backend="rule")

        started = time.perf_counter()
        try:
            from google.genai import types

            prompt = (
                "You are the NLU router for an enterprise Business Travel Operations Agent.\n"
                f"User role: {role}\n"
                f"Session memory (unverified context): {json.dumps(session_state or {}, ensure_ascii=False)}\n"
                f"User message: {message}\n\n"
                "Map the message to one route/intent:\n"
                "- SELF_SERVE intents: pretrip (checklist/prepare), intrip (flight delay/cancel), posttrip (expense report), "
                "policy_qa (policy rules/caps/visa/insurance), mixed (trip + policy), trip_details, itinerary_read, out_of_scope (unsupported booking/payment/other).\n"
                "- HANDOFF_STAFF intent: handoff_requested (user asks for human/staff assistance in English or Vietnamese).\n"
                "- CLARIFY: missing trip/report ID when no session active_trip_id/active_report_id fits.\n"
                "Rules: Use active_trip_id or active_report_id from session memory for follow-ups like 'chuyến này' or 'it'. "
                "Never change or invent approval/user roles."
            )
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_json_schema=_NLU_RESPONSE_SCHEMA,
            )
            response = self._generate(prompt, config)
            parsed = _parse_nlu_payload(getattr(response, "text", ""), message)
            elapsed = (time.perf_counter() - started) * 1000.0
            in_tok, out_tok = _extract_usage(response)
            if parsed is None:
                return rule_decision, LLMCallMeta(
                    backend="gemini",
                    model=self.model,
                    latency_ms=elapsed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    fallback_used=True,
                    fallback_reason="invalid_nlu_schema",
                )
            return parsed, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - started) * 1000.0
            return rule_decision, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                fallback_used=True,
                fallback_reason=_sanitize_error_reason(exc),
            )

    def rewrite_policy_query(
        self,
        query: str,
        category: str,
        *,
        state: RunState | None = None,
        already_rewritten: bool = False,
    ) -> tuple[str, bool, LLMCallMeta]:
        rewritten, changed = rewrite_query(query, category, state=state, already_rewritten=already_rewritten)
        if changed or already_rewritten or not isinstance(query, str) or not query.strip():
            return rewritten, changed, LLMCallMeta(backend="rule", query_rewritten=changed)

        started = time.perf_counter()
        try:
            from google.genai import types

            prompt = (
                "Convert this travel policy question into concise English search keywords (3-10 words, max 120 chars) "
                "for an offline BM25 policy index. Output ONLY the search keywords, no quotes or instructions.\n"
                f"Category: {category}\n"
                f"Question: {query[:300]}"
            )
            config = types.GenerateContentConfig(temperature=0.0, max_output_tokens=64)
            response = self._generate(prompt, config)
            elapsed = (time.perf_counter() - started) * 1000.0
            in_tok, out_tok = _extract_usage(response)
            candidate = " ".join(str(getattr(response, "text", "") or "").split())[:200]
            if not candidate or _contains_safety_pattern(candidate):
                return query, False, LLMCallMeta(
                    backend="gemini",
                    model=self.model,
                    latency_ms=elapsed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    fallback_used=True,
                    fallback_reason="unsafe_or_empty_rewrite",
                )
            if state is not None:
                state.record_event(
                    "query_rewrite",
                    tool="search_travel_policy",
                    safe_args={
                        "category": category,
                        "original_length": len(query),
                        "rewritten_length": len(candidate),
                        "source": "gemini",
                    },
                    observation_status="ok",
                    transition="query_rewritten",
                )
            return candidate, True, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                input_tokens=in_tok,
                output_tokens=out_tok,
                query_rewritten=True,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - started) * 1000.0
            return query, False, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                fallback_used=True,
                fallback_reason=_sanitize_error_reason(exc),
            )

    def synthesize_response(
        self,
        deterministic_text: str,
        facts_payload: dict[str, Any],
        citations: list[str],
        *,
        output_format: str = "concise",
        is_vi: bool = False,
        approval_status: str | None = None,
        state: RunState | None = None,
    ) -> tuple[str, LLMCallMeta]:
        started = time.perf_counter()
        try:
            from google.genai import types

            lang = "Vietnamese" if is_vi else "English"
            prompt = (
                f"Rewrite the verified travel assistant response naturally in {lang} ({output_format} style).\n"
                "STRICT RULES:\n"
                "1. Use ONLY the verified facts and deterministic draft below. Never invent IDs, amounts, dates, or policy rules.\n"
                "2. Keep EVERY citation tag verbatim (for example: [TRAVEL-APPROVAL §2.1, v1.0]).\n"
                f"3. Current verified trip_approval_status is: {approval_status or 'unknown'}. NEVER claim approved/refunded unless status is 'approved'.\n\n"
                f"Verified facts JSON:\n{json.dumps(facts_payload, ensure_ascii=False)[:3000]}\n\n"
                f"Required citations: {json.dumps(citations, ensure_ascii=False)}\n\n"
                f"Deterministic reference response:\n{deterministic_text}"
            )
            config = types.GenerateContentConfig(temperature=0.2, max_output_tokens=700)
            response = self._generate(prompt, config)
            elapsed = (time.perf_counter() - started) * 1000.0
            in_tok, out_tok = _extract_usage(response)
            candidate = str(getattr(response, "text", "") or "").strip()
            ok, guard_reason = check_generated_response(candidate, citations, approval_status)
            if not ok:
                if state is not None:
                    state.record_event(
                        "llm_post_guard",
                        safe_args={"reason": guard_reason},
                        observation_status="error",
                        transition="fallback_deterministic",
                    )
                return deterministic_text, LLMCallMeta(
                    backend="gemini",
                    model=self.model,
                    latency_ms=elapsed,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    fallback_used=True,
                    fallback_reason=guard_reason,
                )
            return candidate, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - started) * 1000.0
            return deterministic_text, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                fallback_used=True,
                fallback_reason=_sanitize_error_reason(exc),
            )

    def run_tool_loop(
        self,
        *,
        message: str,
        state: RunState,
        session_state: dict[str, Any] | None = None,
        is_vi: bool = False,
        max_rounds: int = 5,
    ) -> tuple[dict[str, Any] | None, LLMCallMeta]:
        """Execute a Gemini Function Calling loop strictly gated by dispatcher.dispatch()."""
        role = state.user_context.get("role", "Employee")
        tools = build_gemini_tools(role, state.workflow)
        if not tools:
            return None, LLMCallMeta(backend="gemini", model=self.model, fallback_used=True, fallback_reason="no_tools")

        started = time.perf_counter()
        total_in = 0
        total_out = 0
        loop_steps = 0
        citations: list[str] = []
        observed_approval: str | None = None
        last_data: dict[str, Any] = {}
        try:
            from google.genai import types

            lang = "Vietnamese" if is_vi else "English"
            system_text = (
                "You are an enterprise Business Travel Operations Agent using verified mock tools.\n"
                f"Respond in {lang}. Use tools to gather facts and policy citations before answering.\n"
                "NEVER invent record IDs, dates, expenses, or policy caps. NEVER fabricate approvals or execute real bookings/payments.\n"
                "Include exact policy citations (e.g. [DOC §SECTION, vX.Y]) in your final reply."
            )
            contents: list[Any] = [
                f"Role: {role}\nSession context: {json.dumps(session_state or {}, ensure_ascii=False)}\nUser message: {message}"
            ]
            config = types.GenerateContentConfig(
                temperature=0.0,
                system_instruction=system_text,
                tools=tools,
            )

            for _ in range(max_rounds):
                if state.outcome is not None or state.step_count >= state.max_steps:
                    break
                response = self._generate(contents, config)
                in_tok, out_tok = _extract_usage(response)
                total_in += in_tok
                total_out += out_tok

                calls = getattr(response, "function_calls", None) or []
                if not calls:
                    final_text = str(getattr(response, "text", "") or "").strip()
                    elapsed = (time.perf_counter() - started) * 1000.0
                    if loop_steps == 0:
                        return None, LLMCallMeta(
                            backend="gemini",
                            model=self.model,
                            latency_ms=elapsed,
                            input_tokens=total_in,
                            output_tokens=total_out,
                            fallback_used=True,
                            fallback_reason="no_tool_proposed",
                        )
                    ok, guard_reason = check_generated_response(
                        final_text,
                        citations,
                        observed_approval,
                        require_all_citations=False,
                    )
                    if not ok:
                        state.record_event(
                            "llm_post_guard",
                            safe_args={"reason": guard_reason},
                            observation_status="error",
                            transition="fallback_deterministic",
                        )
                        return None, LLMCallMeta(
                            backend="gemini",
                            model=self.model,
                            latency_ms=elapsed,
                            input_tokens=total_in,
                            output_tokens=total_out,
                            fallback_used=True,
                            fallback_reason=guard_reason,
                            tool_loop_steps=loop_steps,
                        )
                    return {
                        "bot_response": final_text,
                        "citations": list(dict.fromkeys(citations)),
                        "result": last_data,
                        "approval_status": observed_approval,
                    }, LLMCallMeta(
                        backend="gemini",
                        model=self.model,
                        latency_ms=elapsed,
                        input_tokens=total_in,
                        output_tokens=total_out,
                        tool_loop_steps=loop_steps,
                    )

                candidates = getattr(response, "candidates", None) or []
                if candidates and getattr(candidates[0], "content", None) is not None:
                    contents.append(candidates[0].content)

                fn_parts = []
                for call in calls:
                    tool_name = str(getattr(call, "name", "") or "")
                    raw_args = getattr(call, "args", None)
                    args = dict(raw_args) if isinstance(raw_args, dict) else {}
                    state.record_event(
                        "llm_tool_proposal",
                        tool=tool_name,
                        safe_args=safe_arguments(tool_name, args),
                        observation_status="pending",
                        transition="proposed_by_llm",
                    )
                    obs = run_tool(state, tool_name, args)
                    loop_steps += 1
                    if obs.get("ok") and isinstance(obs.get("data"), dict):
                        data = obs["data"]
                        last_data[tool_name] = data
                        if "trip_approval_status" in data:
                            observed_approval = data.get("trip_approval_status")
                        for row in data.get("results", []) or []:
                            if isinstance(row, dict) and isinstance(row.get("citation"), str):
                                citations.append(row["citation"])
                    fn_parts.append(types.Part.from_function_response(name=tool_name, response=obs))
                    if state.outcome is not None or state.step_count >= state.max_steps:
                        break
                contents.append(types.Content(role="user", parts=fn_parts))

            elapsed = (time.perf_counter() - started) * 1000.0
            return None, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                input_tokens=total_in,
                output_tokens=total_out,
                fallback_used=True,
                fallback_reason="tool_loop_exhausted",
                tool_loop_steps=loop_steps,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - started) * 1000.0
            return None, LLMCallMeta(
                backend="gemini",
                model=self.model,
                latency_ms=elapsed,
                input_tokens=total_in,
                output_tokens=total_out,
                fallback_used=True,
                fallback_reason=_sanitize_error_reason(exc),
                tool_loop_steps=loop_steps,
            )


def get_backend(backend_name: str | None = None, *, client: Any | None = None) -> RuleBasedBackend | GeminiBackend:
    """Resolve active LLM backend instance from argument or environment configuration."""
    resolved = get_llm_backend(backend_name)
    if resolved == "gemini":
        return GeminiBackend(client=client)
    return RuleBasedBackend()
