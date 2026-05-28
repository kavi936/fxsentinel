#!/usr/bin/env python3
"""
Post-parse personalization compliance checks and lightweight enforcement.

Prompts steer GPT; this module measures whether responses reflect trader profile
(swing vs day structure, preferred pairs) and attaches QA metadata for the API.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
)
from services.analysis_personalization import normalize_pair_symbol, prioritize_instruments

SWING_HORIZON_PATTERNS = (
    r"\bmulti[- ]?week",
    r"\bweeks?\b",
    r"\bmedium[- ]?term\b",
    r"\blonger[- ]?term\b",
    r"\bfollow[- ]?through\b",
    r"\bpositioning horizon\b",
)

DAY_TRIGGER_PATTERNS = (
    r"\btrigger\b",
    r"\binvalidation\b",
    r"\bsession\b",
    r"\bnext\s+\d",
    r"\b\d+\s*[-–]?\s*\d+\s*hours?\b",
    r"\blondon\b|\bnew york\b|\basia\b",
    r"\bintraday\b",
    r"\bimmediate\b",
)

PAIR_IN_TEXT = re.compile(
    r"\b([A-Z]{3})\s*/\s*([A-Z]{3})\b|\b([A-Z]{6})\b",
    re.IGNORECASE,
)


def normalize_pair(symbol: Any) -> str:
    return normalize_pair_symbol(symbol)


def _matches_any(text: str, patterns: Tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(re.search(p, lowered) for p in patterns)


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


def _pairs_in_text(text: str) -> List[str]:
    found: List[str] = []
    seen = set()
    for match in PAIR_IN_TEXT.finditer(text or ""):
        if match.group(1) and match.group(2):
            norm = f"{match.group(1).upper()}{match.group(2).upper()}"
        elif match.group(3):
            norm = match.group(3).upper()
        else:
            continue
        if norm not in seen:
            seen.add(norm)
            found.append(norm)
    return found


def _check_record(check_id: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"id": check_id, "passed": bool(passed), "detail": detail}


def _compliance_score(checks: List[Dict[str, Any]]) -> int:
    if not checks:
        return 100
    passed = sum(1 for c in checks if c.get("passed"))
    return int(round(100 * passed / len(checks)))


def build_personalization_applied(
    *,
    personalization: Optional[Dict[str, Any]],
    surface: str,
    checks: List[Dict[str, Any]],
    preferred_pairs_used: Optional[List[str]] = None,
    relevance_notes: Optional[List[str]] = None,
    enforcement_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    p = personalization or {}
    return {
        "surface": surface,
        "profile_available": bool(p.get("profile_available")),
        "trading_style": p.get("trading_style", "unsure"),
        "experience_level": p.get("experience_level", "intermediate"),
        "preferred_pairs": list(p.get("primary_pairs") or [])[:8],
        "preferred_pairs_used": preferred_pairs_used or [],
        "relevance_notes": relevance_notes or [],
        "checks": checks,
        "compliance_score": _compliance_score(checks),
        "enforcement_actions": enforcement_actions or [],
    }


def validate_and_enforce_calendar(
    payload: Dict[str, Any],
    personalization: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Measure calendar output against swing/day and preferred-pair rules."""
    out = dict(payload)
    p = personalization or {}
    style = str(p.get("trading_style") or "unsure").lower()
    preferred = [normalize_pair(x) for x in (p.get("primary_pairs") or []) if normalize_pair(x)]

    corpus = " ".join(
        [
            _flatten_text(out.get("headline")),
            _flatten_text(out.get("key_takeaway")),
            _flatten_text(out.get("forward_scenarios")),
            _flatten_text(out.get("big_picture")),
            _flatten_text(out.get("trading_plan")),
            _flatten_text(out.get("market_reaction")),
            _flatten_text(out.get("implications_takeaways")),
        ]
    )
    text_pairs = _pairs_in_text(corpus)
    preferred_used = [pair for pair in preferred if pair in text_pairs or pair in corpus.upper().replace("/", "")]

    checks: List[Dict[str, Any]] = []
    relevance_notes: List[str] = []
    enforcement: List[str] = []

    if not p.get("profile_available"):
        meta = build_personalization_applied(
            personalization=p,
            surface="economic_calendar",
            checks=[_check_record("profile_available", False, "No onboarding profile; skipped style checks.")],
            preferred_pairs_used=preferred_used,
        )
        return out, meta

    big_picture_text = _flatten_text(out.get("big_picture"))
    trading_plan_text = _flatten_text(out.get("trading_plan"))
    market_reaction_text = _flatten_text(out.get("market_reaction"))

    if style in {"swing", "both"}:
        swing_ok = _matches_any(big_picture_text, SWING_HORIZON_PATTERNS) or _matches_any(
            _flatten_text(out.get("forward_scenarios")), SWING_HORIZON_PATTERNS
        )
        checks.append(
            _check_record(
                "swing_horizon_framing",
                swing_ok,
                "Multi-week / medium-term framing expected in big_picture or forward_scenarios.",
            )
        )
    if style in {"day", "both"}:
        day_ok = _matches_any(trading_plan_text, DAY_TRIGGER_PATTERNS) or _matches_any(
            market_reaction_text, DAY_TRIGGER_PATTERNS
        )
        checks.append(
            _check_record(
                "day_trigger_framing",
                day_ok,
                "Session/trigger/invalidation framing expected in trading_plan or market_reaction.",
            )
        )

    if preferred:
        referenced = [pair for pair in preferred if pair in text_pairs or pair.replace("/", "") in corpus.upper()]
        checks.append(
            _check_record(
                "preferred_pairs_referenced",
                bool(referenced),
                f"At least one preferred pair should appear in narrative ({', '.join(preferred[:4])}).",
            )
        )
        missing = [pair for pair in preferred[:4] if pair not in referenced]
        for pair in missing:
            relevance_notes.append(f"{pair} not referenced; weak relevance to this release should be stated explicitly.")

        trading_plan = out.get("trading_plan")
        if isinstance(trading_plan, dict):
            for key in ("pairs", "instruments", "key_pairs"):
                raw_list = trading_plan.get(key)
                if isinstance(raw_list, list) and raw_list:
                    reordered = prioritize_instruments(
                        [str(x) for x in raw_list],
                        p.get("primary_pairs") or [],
                        limit=max(len(raw_list), 4),
                    )
                    if reordered != raw_list:
                        trading_plan = dict(trading_plan)
                        trading_plan[key] = reordered
                        out["trading_plan"] = trading_plan
                        enforcement.append(f"reordered_trading_plan.{key}")
                    first_norm = normalize_pair(reordered[0]) if reordered else ""
                    checks.append(
                        _check_record(
                            "preferred_pair_primary_in_plan",
                            not preferred or first_norm in preferred,
                            "First instrument in trading_plan should be a user-preferred pair when relevant.",
                        )
                    )
                    break
    else:
        checks.append(
            _check_record("preferred_pairs_configured", True, "No preferred pairs on profile; pair checks skipped.")
        )

    meta = build_personalization_applied(
        personalization=p,
        surface="economic_calendar",
        checks=checks,
        preferred_pairs_used=preferred_used or [pair for pair in preferred if pair in text_pairs],
        relevance_notes=relevance_notes,
        enforcement_actions=enforcement,
    )
    return out, meta


def validate_and_enforce_news(
    payload: Dict[str, Any],
    personalization: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(payload)
    p = personalization or {}
    style = str(p.get("trading_style") or "unsure").lower()
    preferred = [normalize_pair(x) for x in (p.get("primary_pairs") or []) if normalize_pair(x)]

    enforcement: List[str] = []
    raw_pairs = out.get("key_pairs")
    if isinstance(raw_pairs, list) and raw_pairs:
        reordered = prioritize_instruments([str(x) for x in raw_pairs], p.get("primary_pairs") or [], limit=4)
        if reordered != raw_pairs:
            out["key_pairs"] = reordered
            enforcement.append("reordered_key_pairs")

    corpus = " ".join(
        [
            _flatten_text(out.get("news_impact")),
            _flatten_text(out.get("trading_implications")),
            _flatten_text(out.get("key_pairs")),
        ]
    )
    text_pairs = _pairs_in_text(corpus)
    preferred_used = [pair for pair in preferred if pair in text_pairs]

    checks: List[Dict[str, Any]] = []
    relevance_notes: List[str] = []

    if not p.get("profile_available"):
        meta = build_personalization_applied(
            personalization=p,
            surface="live_news",
            checks=[_check_record("profile_available", False, "No onboarding profile; skipped style checks.")],
            preferred_pairs_used=preferred_used,
        )
        return out, meta

    implications = _flatten_text(out.get("trading_implications"))
    timeframe = str(out.get("timeframe") or "").lower()

    if style in {"swing", "both"}:
        swing_ok = _matches_any(implications, SWING_HORIZON_PATTERNS) or any(
            token in timeframe for token in ("week", "session", "multi", "days")
        )
        checks.append(
            _check_record(
                "swing_horizon_framing",
                swing_ok,
                "Swing profile expects multi-session/week framing in trading_implications or timeframe.",
            )
        )
    if style in {"day", "both"}:
        day_ok = _matches_any(implications, DAY_TRIGGER_PATTERNS) or any(
            token in timeframe for token in ("hour", "session", "immediate", "intraday")
        )
        checks.append(
            _check_record(
                "day_trigger_framing",
                day_ok,
                "Day profile expects trigger/session timing in trading_implications or timeframe.",
            )
        )

    if preferred:
        key_pairs = out.get("key_pairs") if isinstance(out.get("key_pairs"), list) else []
        first_norm = normalize_pair(key_pairs[0]) if key_pairs else ""
        checks.append(
            _check_record(
                "preferred_pair_listed_first",
                not key_pairs or first_norm in preferred,
                "Primary key_pairs entry should be a user-preferred instrument when relevant.",
            )
        )
        checks.append(
            _check_record(
                "preferred_pairs_referenced",
                bool(preferred_used),
                f"Preferred pair should appear in narrative ({', '.join(preferred[:4])}).",
            )
        )
        for pair in preferred[:4]:
            if pair not in preferred_used:
                relevance_notes.append(f"{pair} not referenced in news body; mark weak relevance if not applicable.")

    meta = build_personalization_applied(
        personalization=p,
        surface="live_news",
        checks=checks,
        preferred_pairs_used=preferred_used,
        relevance_notes=relevance_notes,
        enforcement_actions=enforcement,
    )
    return out, meta


def validate_holistic_scan(
    scan: Dict[str, Any],
    personalization: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Measure holistic narrative against personalization cascade (no score changes)."""
    out = dict(scan)
    p = personalization or {}
    style = str(p.get("trading_style") or "unsure").lower()
    preferred = [normalize_pair(x) for x in (p.get("primary_pairs") or []) if normalize_pair(x)]

    narrative = out.get("narrative") if isinstance(out.get("narrative"), dict) else {}
    short_text = _flatten_text(narrative.get("short_term"))
    long_text = _flatten_text(narrative.get("long_term"))
    fx_text = _flatten_text(narrative.get("fx"))
    brief_text = _flatten_text(out.get("trader_brief"))
    setups_text = _flatten_text(out.get("pair_setups"))
    corpus = " ".join([short_text, long_text, fx_text, brief_text, setups_text])
    text_pairs = _pairs_in_text(corpus)
    preferred_used = [pair for pair in preferred if pair in text_pairs]

    checks: List[Dict[str, Any]] = []
    relevance_notes: List[str] = []
    enforcement: List[str] = []

    pair_setups = out.get("pair_setups")
    if isinstance(pair_setups, list) and pair_setups and preferred:
        ordered: List[Dict[str, Any]] = []
        seen_pairs = set()
        pref_set = set(preferred)
        for row in pair_setups:
            if not isinstance(row, dict):
                continue
            pair_norm = normalize_pair(row.get("pair"))
            if pair_norm in pref_set and pair_norm not in seen_pairs:
                ordered.append(row)
                seen_pairs.add(pair_norm)
        for row in pair_setups:
            if not isinstance(row, dict):
                continue
            pair_norm = normalize_pair(row.get("pair"))
            if pair_norm not in seen_pairs:
                ordered.append(row)
                seen_pairs.add(pair_norm)
        if ordered and ordered != pair_setups:
            out["pair_setups"] = ordered
            enforcement.append("reordered_pair_setups")

    if not p.get("profile_available"):
        meta = build_personalization_applied(
            personalization=p,
            surface="holistic_scan",
            checks=[_check_record("profile_available", False, "No onboarding profile; skipped style checks.")],
            preferred_pairs_used=preferred_used,
        )
        return out, meta

    if style in {"swing", "both"}:
        long_words = len(long_text.split())
        short_words = len(short_text.split()) or 1
        swing_ok = _matches_any(long_text, SWING_HORIZON_PATTERNS) or long_words >= max(short_words, 40)
        checks.append(
            _check_record(
                "swing_long_term_primary",
                swing_ok,
                "Swing profile expects narrative.long_term to carry the primary multi-week thesis.",
            )
        )
    if style in {"day", "both"}:
        day_ok = _matches_any(short_text, DAY_TRIGGER_PATTERNS) or _matches_any(brief_text, DAY_TRIGGER_PATTERNS)
        checks.append(
            _check_record(
                "day_short_term_triggers",
                day_ok,
                "Day profile expects actionable triggers in narrative.short_term or trader_brief.",
            )
        )

    if preferred:
        checks.append(
            _check_record(
                "preferred_pairs_in_setups",
                bool(preferred_used),
                "Preferred pairs should appear in pair_setups or narrative.",
            )
        )
        setup_pairs = [
            normalize_pair(row.get("pair"))
            for row in (out.get("pair_setups") or [])
            if isinstance(row, dict) and row.get("pair")
        ]
        if setup_pairs and setup_pairs[0] not in preferred:
            relevance_notes.append("Top pair_setup is not a user-preferred pair; consider de-emphasizing in UI.")
        for pair in preferred[:4]:
            if pair not in preferred_used:
                relevance_notes.append(f"{pair} not referenced in holistic narrative.")

    meta = build_personalization_applied(
        personalization=p,
        surface="holistic_scan",
        checks=checks,
        preferred_pairs_used=preferred_used,
        relevance_notes=relevance_notes,
        enforcement_actions=enforcement,
    )
    return out, meta


def apply_personalization_to_response(
    payload: Dict[str, Any],
    analysis_kind: str,
    personalization: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run surface-specific validators and attach personalization_applied metadata.
    """
    if not personalization:
        return dict(payload)

    out = dict(payload)
    if analysis_kind == ANALYSIS_KIND_CALENDAR_EVENT:
        body, meta = validate_and_enforce_calendar(out, personalization)
        body["personalization_applied"] = meta
        return body

    if analysis_kind == ANALYSIS_KIND_LIVE_NEWS:
        body, meta = validate_and_enforce_news(out, personalization)
        body["personalization_applied"] = meta
        return body

    if analysis_kind == ANALYSIS_KIND_ECONOMY_SCAN:
        scan = out.get("scan")
        if isinstance(scan, dict):
            scan_body, meta = validate_holistic_scan(scan, personalization)
            out = dict(out)
            out["scan"] = scan_body
            out["personalization_applied"] = meta
        return out

    return out
