#!/usr/bin/env python3
"""
Live news impact horizon + pair-focus metadata (V2 Tier 2: N3, N4).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.analysis_contract import ANALYSIS_KIND_LIVE_NEWS
from services.analysis_personalization import prioritize_instruments
from services.analysis_personalization_validation import normalize_pair

NEWS_HORIZON_PROMPT_RULES = """
NEWS IMPACT HORIZON (mandatory):
- impact_horizon: exactly one of "intraday" | "multi_day" | "structural"
  - intraday: headline-driven tape reaction (hours)
  - multi_day: policy repricing / data cycle (days to weeks)
  - structural: regime/theme shift (weeks+)
- timeframe_immediate: reaction window (e.g. "next 2-4 hours", "London session")
- timeframe_positioning: positioning horizon (e.g. "through June ECB meetings", "multi-week")
- Do NOT use a 2-4 hour immediate window alone when impact_horizon is multi_day or structural.
""".strip()

_VALID_HORIZONS = frozenset({"intraday", "multi_day", "structural"})

_POLICY_KEYWORDS = re.compile(
    r"\b(ecb|fed|fomc|boe|boj|rate\s+hike|rate\s+cut|policy\s+signal|terminal\s+rate|"
    r"forward\s+guidance|tightening\s+bias|dovish\s+pivot)\b",
    re.IGNORECASE,
)


def _normalize_horizon(value: Any, timeframe: str, implications: str) -> str:
    raw = str(value or "").strip().lower()
    if raw in _VALID_HORIZONS:
        return raw
    combined = f"{timeframe} {implications}".lower()
    if _POLICY_KEYWORDS.search(combined) or any(
        token in combined for token in ("week", "month", "june", "july", "quarter")
    ):
        return "multi_day"
    if any(token in combined for token in ("structural", "regime", "years", "long-term")):
        return "structural"
    return "intraday"


def _infer_positioning_timeframe(horizon: str, timeframe: str, implications: str) -> str:
    if horizon == "intraday":
        return str(timeframe or "next 2-4 hours")
    if horizon == "structural":
        return "multi-week to multi-month positioning window"
    if _POLICY_KEYWORDS.search(implications):
        return "multi-week policy repricing window"
    return "multi-day follow-through window"


def build_pairs_focus_metadata(
    payload: Dict[str, Any],
    personalization: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    p = personalization or {}
    preferred = [normalize_pair(x) for x in (p.get("primary_pairs") or []) if normalize_pair(x)]
    key_pairs_raw = payload.get("key_pairs") if isinstance(payload.get("key_pairs"), list) else []
    key_pairs = prioritize_instruments([str(x) for x in key_pairs_raw], p.get("primary_pairs") or [], limit=4)

    focused = [normalize_pair(x) for x in key_pairs if normalize_pair(x)]
    deemphasized = [pair for pair in preferred if pair not in focused]

    display = ""
    if focused and deemphasized:
        display = (
            f"Focused on {', '.join(focused[:3])}; "
            f"lower relevance for this headline: {', '.join(deemphasized[:3])}."
        )
    elif focused:
        display = f"Focused on {', '.join(focused[:3])} for this headline."
    elif preferred:
        display = f"Profile pairs ({', '.join(preferred[:3])}) — headline did not map cleanly to a single cross."

    return {
        "pairs_focus": focused,
        "pairs_deemphasized": deemphasized,
        "pairs_focus_display": display,
        "preferred_pairs_configured": preferred,
    }


def apply_news_horizon_and_pairs_focus(
    payload: Dict[str, Any],
    *,
    personalization: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(payload)
    implications = str(out.get("trading_implications") or "")
    timeframe = str(out.get("timeframe") or "")

    horizon = _normalize_horizon(
        out.get("impact_horizon"),
        timeframe,
        implications,
    )
    out["impact_horizon"] = horizon
    out["impact_horizon_display"] = {
        "intraday": "Intraday reaction",
        "multi_day": "Multi-day repricing",
        "structural": "Structural / theme",
    }.get(horizon, horizon)

    immediate = str(out.get("timeframe_immediate") or timeframe or "").strip()
    if not immediate:
        immediate = "next 2-4 hours" if horizon == "intraday" else "near-term sessions"
    out["timeframe_immediate"] = immediate

    positioning = str(out.get("timeframe_positioning") or "").strip()
    if not positioning:
        positioning = _infer_positioning_timeframe(horizon, timeframe, implications)
    out["timeframe_positioning"] = positioning

    pairs_meta = build_pairs_focus_metadata(out, personalization)
    out.update(pairs_meta)

    out["news_horizon_applied"] = {
        "surface": "live_news",
        "impact_horizon": horizon,
        "has_pairs_focus_display": bool(pairs_meta.get("pairs_focus_display")),
    }
    return out


def apply_news_horizon_if_news(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    personalization: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_LIVE_NEWS:
        return dict(payload)
    return apply_news_horizon_and_pairs_focus(payload, personalization=personalization)
