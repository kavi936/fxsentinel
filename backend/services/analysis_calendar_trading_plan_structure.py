#!/usr/bin/env python3
"""
Calendar trading-plan structure enforcement (review §2.4).

Builds a deterministic structured plan from GPT prose so the API always exposes:
- scenario_trigger
- direction
- entry_condition
- target_zone
- invalidation
- sizing_note
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from services.analysis_contract import ANALYSIS_KIND_CALENDAR_EVENT

TRADING_PLAN_STRUCTURE_PROMPT_RULES = """
TRADING PLAN STRUCTURE (mandatory):
- trading_plan.best_approach must include an explicit conditional trigger (If X -> then Y).
- Also provide a practical plan with these elements:
  1) scenario_trigger
  2) direction (pair + long/short bias)
  3) entry_condition (confirmation / break / reaction condition)
  4) target_zone (approximate level/range with basis if available)
  5) invalidation (what kills the thesis)
  6) sizing_note (volatility-adjusted risk guidance)
- If exact levels are unavailable, use conditional zones and clearly label assumptions.
""".strip()


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _sanitize_emphasis_markers(text: str) -> str:
    """Drop orphan ** pairs left by clause extraction slicing through GPT emphasis."""
    s = str(text or "")
    if "**" not in s:
        return s
    # Balanced markdown: splitting on ** yields an odd number of segments.
    if len(s.split("**")) % 2 == 0:
        return s.replace("**", "")
    return s


def _extract_if_clause(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"\bif\b", text, flags=re.IGNORECASE)
    if not match:
        return ""
    chunk = text[match.end() :]
    end = len(chunk)
    for i, ch in enumerate(chunk):
        if ch in "!?":
            end = i
            break
        if ch == ".":
            # Do not treat decimal points inside levels (e.g. 1.0850) as sentence ends.
            prev_digit = i > 0 and chunk[i - 1].isdigit()
            next_digit = i + 1 < len(chunk) and chunk[i + 1].isdigit()
            if prev_digit and next_digit:
                continue
            end = i
            break
    clause = chunk[:end].strip(" ,;")
    if len(clause) >= 6:
        return _sanitize_emphasis_markers(f"If {clause}")
    return ""


def _infer_direction(best_approach: str, market_bias: str, currency: str) -> str:
    source = f"{best_approach} {market_bias}".lower()
    ccy = (currency or "USD").upper()
    if "eur/usd" in source or "eurusd" in source:
        if "usd strength" in source or "bullish for usd" in source or "short eur" in source:
            return "Short EUR/USD (USD strength path)"
        if "usd weakness" in source or "bearish for usd" in source or "long eur" in source:
            return "Long EUR/USD (USD weakness path)"
    if "usd/jpy" in source or "usdjpy" in source:
        if "usd strength" in source or "bullish for usd" in source:
            return "Long USD/JPY (USD strength path)"
        if "usd weakness" in source or "bearish for usd" in source:
            return "Short USD/JPY (USD weakness path)"

    if "bullish" in source and ccy == "USD":
        return "Long USD vs weaker counterpart (pair selected by liquidity/session)"
    if "bearish" in source and ccy == "USD":
        return "Short USD vs stronger counterpart (pair selected by liquidity/session)"
    if "bullish" in source:
        return f"Long {ccy} crosses aligned with scenario"
    if "bearish" in source:
        return f"Short {ccy} crosses aligned with scenario"
    return f"Directional expression in liquid {ccy} pair once trigger confirms"


def _extract_level_hint(text: str) -> str:
    if not text:
        return ""
    # captures simple levels/ranges like 1.0850, 159.40, 1.08-1.09
    range_match = re.search(r"(\d{1,3}\.\d{2,5}\s*[-–]\s*\d{1,3}\.\d{2,5})", text)
    if range_match:
        return range_match.group(1)
    one = re.search(r"\b(\d{1,3}\.\d{2,5})\b", text)
    if one:
        return one.group(1)
    return ""


def build_structured_calendar_trading_plan(
    payload: Dict[str, Any],
    *,
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    trading_plan = payload.get("trading_plan") if isinstance(payload.get("trading_plan"), dict) else {}
    best_approach = str((trading_plan or {}).get("best_approach") or "")
    avoid = str((trading_plan or {}).get("avoid_strategies") or "")
    key_levels = str((trading_plan or {}).get("key_levels") or "")
    sizing = str((trading_plan or {}).get("position_sizing") or (trading_plan or {}).get("position_sizing_risk") or "")
    market_bias = str(((payload.get("implications_takeaways") or {}).get("market_bias") or ""))
    scenarios = payload.get("forward_scenarios") if isinstance(payload.get("forward_scenarios"), dict) else {}

    currency = str((event or {}).get("currency") or "USD").upper()
    neutral_zone = ((payload.get("market_scenarios") or {}).get("neutral_zone") or {}).get("definition")

    scenario_trigger = _first_nonempty(
        _extract_if_clause(best_approach),
        _extract_if_clause(str(scenarios.get("bullish") or "")),
        _extract_if_clause(str(scenarios.get("bearish") or "")),
        f"If the release materially deviates from consensus for {currency}",
    )
    direction = _infer_direction(best_approach, market_bias, currency)
    entry_condition = _first_nonempty(
        _extract_if_clause(best_approach).replace("If ", "Confirm "),
        "Confirm initial post-release direction holds through the next liquid session candle.",
    )

    lvl = _extract_level_hint(key_levels) or _extract_level_hint(best_approach)
    target_zone = (
        f"Target retest/extension toward {lvl} (per provided level context)."
        if lvl
        else "Target incremental extension only after trigger confirmation; avoid pre-positioning."
    )
    invalidation = _first_nonempty(
        _extract_if_clause(avoid).replace("If ", "Invalidated if "),
        "Invalidated if the initial move fully retraces and yields fail to confirm direction.",
    )
    sizing_note = _first_nonempty(
        sizing,
        "Use conservative sizing around release volatility; scale only after confirmation.",
    )

    if neutral_zone:
        scenario_trigger = f"{scenario_trigger}; inline zone: {neutral_zone}"

    return {
        "scenario_trigger": _sanitize_emphasis_markers(scenario_trigger),
        "direction": _sanitize_emphasis_markers(direction),
        "entry_condition": _sanitize_emphasis_markers(entry_condition),
        "target_zone": _sanitize_emphasis_markers(target_zone),
        "invalidation": _sanitize_emphasis_markers(invalidation),
        "sizing_note": _sanitize_emphasis_markers(sizing_note),
    }


def apply_calendar_trading_plan_structure(
    payload: Dict[str, Any],
    *,
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(payload)
    structured = build_structured_calendar_trading_plan(out, event=event)
    out["trading_plan_structured"] = structured
    out["trading_plan_structure_applied"] = {
        "surface": "economic_calendar",
        "template_version": "v1",
        "fields_present": [k for k, v in structured.items() if str(v or "").strip()],
    }
    return out


def apply_calendar_trading_plan_structure_if_calendar(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_CALENDAR_EVENT:
        return dict(payload)
    return apply_calendar_trading_plan_structure(payload, event=event)

