#!/usr/bin/env python3
"""
Detect and enforce trader-facing "If X → then Y" conditionals across analysis surfaces.

Prompts steer GPT; this module measures compliance and appends a deterministic trigger
when prose is purely observational (monitor/watch/vigilant) with no conditional.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
)

# Matches review §1.1 examples: passive watch-language without a trigger.
PASSIVE_ONLY_PATTERNS = (
    r"\bmonitor\b",
    r"\bremain vigilant\b",
    r"\bwatch closely\b",
    r"\bwatch for opportunities\b",
    r"\bconsider swing\b",
    r"\btraders should\b",
    r"\bpay attention\b",
)

CONDITIONAL_PATTERNS = (
    re.compile(
        r"\bif\b[^.!?]{4,220}?\b(then|→|->|expect|likely|should|target|break|fade|reprice|extend|watch for|lead to|implies)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwhen\b[^.!?]{4,160}?\b(then|expect|likely|should)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\binvalidated if\b", re.IGNORECASE),
    re.compile(r"\[ABOVE\]|\[BELOW\]|\[ON\]", re.IGNORECASE),
)

ACTIONABLE_PROMPT_RULES = """
ACTIONABLE TRIGGERS (mandatory — cross-cutting):
- Include at least one explicit conditional per major section you write: "If [trigger] → then [market outcome / level / bias]."
- Replace passive filler ("monitor", "watch closely", "remain vigilant", "consider strategies") with a concrete trigger.
- Calendar: each forward_scenarios entry must read as a conditional surprise path (beat/miss/inline), not generic regime copy.
- News: trading_implications must contain at least one If→then with instrument + level or session timing.
- Tie conditionals to supplied data (forecast, actual, yields, scan bias) — no orphan generics.
""".strip()


def _flatten_text(value: Any, depth: int = 0) -> str:
    if depth > 6:
        return ""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_flatten_text(v, depth + 1) for v in value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(v, depth + 1) for v in value.values())
    return ""


def count_conditionals(text: str) -> int:
    if not text:
        return 0
    total = 0
    for pattern in CONDITIONAL_PATTERNS:
        total += len(pattern.findall(text))
    return total


def has_actionable_conditional(text: str) -> bool:
    return count_conditionals(text) >= 1


def is_mostly_passive_language(text: str) -> bool:
    lowered = (text or "").lower()
    if not lowered.strip():
        return True
    if has_actionable_conditional(lowered):
        return False
    return any(re.search(p, lowered) for p in PASSIVE_ONLY_PATTERNS)


def _check_record(check_id: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"id": check_id, "passed": bool(passed), "detail": detail}


def _compliance_score(checks: List[Dict[str, Any]]) -> int:
    if not checks:
        return 100
    passed = sum(1 for c in checks if c.get("passed"))
    return int(round(100 * passed / len(checks)))


def build_actionable_metadata(
    *,
    surface: str,
    checks: List[Dict[str, Any]],
    conditional_count: int,
    enforcement_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "surface": surface,
        "conditional_count": conditional_count,
        "checks": checks,
        "compliance_score": _compliance_score(checks),
        "enforcement_actions": enforcement_actions or [],
    }


def _append_sentence(existing: str, sentence: str) -> str:
    base = (existing or "").strip()
    if not base:
        return sentence
    if sentence.lower() in base.lower():
        return base
    return f"{base.rstrip('.')}. {sentence}"


def _calendar_fallback_conditional(
    event: Optional[Dict[str, Any]],
    analysis_type: Optional[str],
) -> str:
    ev = event or {}
    currency = str(ev.get("currency") or "USD").upper()
    title = str(ev.get("title") or "this release").strip()
    forecast = ev.get("forecast") or ev.get("expected") or "consensus"
    is_pre = (analysis_type or "pre_event") == "pre_event"
    if is_pre:
        return (
            f"If {title} prints above {forecast}, expect near-term {currency} strength and FX volatility in the first session; "
            f"if it misses, fade the initial spike and reassess whether the move aligns with the latest economy scan bias."
        )
    return (
        f"If the {currency} print confirms a hawkish surprise vs {forecast}, extend bullish follow-through in affected pairs; "
        f"if inline or soft, expect range conditions until the next catalyst reprices yields."
    )


def _news_fallback_conditional(news_item: Optional[Dict[str, Any]]) -> str:
    title = str((news_item or {}).get("title") or "this headline").strip()
    pairs = (news_item or {}).get("currency_pairs") or []
    instrument = str(pairs[0]) if pairs else "the primary pair"
    return (
        f"If follow-through holds after '{title[:80]}', expect {instrument} to extend in the headline direction over the next session; "
        f"if price rejects the move within 2–4 hours, treat it as a fade and wait for London/NY confirmation."
    )


def _holistic_fallback_conditional(scan: Dict[str, Any]) -> str:
    short = scan.get("short_term") or {}
    bias = str(short.get("bias") or "neutral")
    score = short.get("score")
    score_txt = f" (score {score})" if score is not None else ""
    return (
        f"If the short-term regime stays **{bias}**{score_txt} and yields extend today's impulse, expect mapped FX pairs to follow the scan bias; "
        f"if yields reverse or event risk spikes, reduce size and wait for the next data refresh before adding risk."
    )


def validate_and_enforce_calendar(
    payload: Dict[str, Any],
    *,
    event: Optional[Dict[str, Any]] = None,
    analysis_type: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(payload)
    checks: List[Dict[str, Any]] = []
    enforcement: List[str] = []

    corpus = _flatten_text(
        {
            "headline": out.get("headline"),
            "key_takeaway": out.get("key_takeaway"),
            "forward_scenarios": out.get("forward_scenarios"),
            "market_reaction": out.get("market_reaction"),
            "implications": out.get("implications_takeaways"),
            "trading_plan": out.get("trading_plan"),
            "big_picture": out.get("big_picture"),
        }
    )
    total = count_conditionals(corpus)
    checks.append(
        _check_record(
            "global_conditional_present",
            total >= 1,
            "At least one If→then (or [ABOVE]/[BELOW]/[ON] scenario path) required in calendar body.",
        )
    )

    scenarios = out.get("forward_scenarios")
    scenario_conditional = False
    if isinstance(scenarios, dict):
        scenario_conditional = any(has_actionable_conditional(str(v)) for v in scenarios.values())
    checks.append(
        _check_record(
            "forward_scenarios_conditional",
            scenario_conditional,
            "Each forward_scenarios path should be framed as a conditional surprise outcome.",
        )
    )

    trading_plan = out.get("trading_plan")
    if not isinstance(trading_plan, dict):
        trading_plan = {}
        out["trading_plan"] = trading_plan
    plan_text = _flatten_text(trading_plan)
    if not has_actionable_conditional(plan_text):
        fallback = _calendar_fallback_conditional(event, analysis_type)
        trading_plan["best_approach"] = _append_sentence(
            str(trading_plan.get("best_approach") or ""),
            fallback,
        )
        out["trading_plan"] = trading_plan
        enforcement.append("appended_trading_plan.best_approach_conditional")
        total = count_conditionals(_flatten_text(out))

    meta = build_actionable_metadata(
        surface="economic_calendar",
        checks=checks,
        conditional_count=total,
        enforcement_actions=enforcement,
    )
    return out, meta


def validate_and_enforce_news(
    payload: Dict[str, Any],
    *,
    news_item: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(payload)
    checks: List[Dict[str, Any]] = []
    enforcement: List[str] = []

    corpus = _flatten_text(
        {
            "news_impact": out.get("news_impact"),
            "trading_implications": out.get("trading_implications"),
        }
    )
    total = count_conditionals(corpus)
    checks.append(
        _check_record(
            "global_conditional_present",
            total >= 1,
            "At least one If→then required across news_impact and trading_implications.",
        )
    )

    implications = str(out.get("trading_implications") or "")
    checks.append(
        _check_record(
            "trading_implications_conditional",
            has_actionable_conditional(implications),
            "trading_implications must include an explicit If→then trigger.",
        )
    )

    if not has_actionable_conditional(implications):
        out["trading_implications"] = _append_sentence(
            implications,
            _news_fallback_conditional(news_item),
        )
        enforcement.append("appended_trading_implications_conditional")
        total = count_conditionals(_flatten_text(out))

    if is_mostly_passive_language(str(out.get("news_impact") or "")) and not has_actionable_conditional(
        str(out.get("news_impact") or "")
    ):
        out["news_impact"] = _append_sentence(
            str(out.get("news_impact") or ""),
            "If the headline narrative holds into the next liquid session, expect the primary pair to drift with the stated USD lean.",
        )
        enforcement.append("appended_news_impact_conditional")

    meta = build_actionable_metadata(
        surface="live_news",
        checks=checks,
        conditional_count=total,
        enforcement_actions=enforcement,
    )
    return out, meta


def validate_and_enforce_holistic_scan(
    scan: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(scan)
    checks: List[Dict[str, Any]] = []
    enforcement: List[str] = []

    narrative = out.get("narrative") if isinstance(out.get("narrative"), dict) else {}
    corpus = _flatten_text(
        {
            "narrative": narrative,
            "pair_setups": out.get("pair_setups"),
            "trader_brief": out.get("trader_brief"),
        }
    )
    total = count_conditionals(corpus)
    checks.append(
        _check_record(
            "global_conditional_present",
            total >= 1,
            "At least one If→then (or pair invalidation trigger) required in holistic narrative/setups.",
        )
    )

    short_text = str(narrative.get("short_term") or "")
    if not has_actionable_conditional(short_text):
        narrative = dict(narrative)
        narrative["short_term"] = _append_sentence(short_text, _holistic_fallback_conditional(out))
        out["narrative"] = narrative
        enforcement.append("appended_narrative.short_term_conditional")
        total = count_conditionals(_flatten_text(out))

    meta = build_actionable_metadata(
        surface="holistic_scan",
        checks=checks,
        conditional_count=total,
        enforcement_actions=enforcement,
    )
    return out, meta


def apply_actionable_conditionals_to_response(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    event: Optional[Dict[str, Any]] = None,
    analysis_type: Optional[str] = None,
    news_item: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run surface validators; attach actionable_triggers_applied metadata."""
    out = dict(payload)

    if analysis_kind == ANALYSIS_KIND_CALENDAR_EVENT:
        body, meta = validate_and_enforce_calendar(
            out,
            event=event,
            analysis_type=analysis_type,
        )
        body["actionable_triggers_applied"] = meta
        return body

    if analysis_kind == ANALYSIS_KIND_LIVE_NEWS:
        body, meta = validate_and_enforce_news(out, news_item=news_item)
        body["actionable_triggers_applied"] = meta
        return body

    if analysis_kind == ANALYSIS_KIND_ECONOMY_SCAN:
        scan = out.get("scan")
        if isinstance(scan, dict):
            scan_body, meta = validate_and_enforce_holistic_scan(scan)
            out = dict(out)
            out["scan"] = scan_body
            out["actionable_triggers_applied"] = meta
        return out

    return out
