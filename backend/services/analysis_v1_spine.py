"""
V1 unified analysis spine (see AI_ANALYSIS_V1_UNIFIED_SPEC.md).

Additive fields only: callers merge into existing response dicts so legacy
clients keep working. Toggle with env ANALYSIS_V1_SPINE_ENABLED (default: on).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from services.calendar_scenario_engine import (
    attach_canonical_calendar_scenarios,
    build_market_scenarios,
    calendar_scenario_alignment_warnings,
    forward_scenarios_by_outcome,
)

ANALYSIS_FORMAT_VERSION = "v1"


def is_analysis_v1_enabled() -> bool:
    """
    Master switch for V1 spine + pipeline envelope (default: off).

    Set ANALYSIS_V1_ENABLED=true to re-enable. ANALYSIS_V1_SPINE_ENABLED is
    still read as a fallback for older env files.
    """
    for key in ("ANALYSIS_V1_ENABLED", "ANALYSIS_V1_SPINE_ENABLED"):
        raw = os.environ.get(key)
        if raw is not None:
            return raw.strip().lower() in ("1", "true", "yes", "on")
    return False


def is_analysis_v1_spine_enabled() -> bool:
    return is_analysis_v1_enabled()


def _confidence_reason_calendar(data_quality: str, validation_status: str) -> str:
    parts = []
    if data_quality and data_quality != "unknown":
        parts.append(f"data_quality={data_quality}")
    if validation_status and validation_status != "unknown":
        parts.append(f"validation={validation_status}")
    return "; ".join(parts) if parts else "Model synthesis; verify against live prices before execution."


def _bias_from_market_bias_text(market_bias: Optional[str]) -> str:
    if not market_bias:
        return "neutral"
    lower = market_bias.lower()
    bull = "bullish" in lower
    bear = "bearish" in lower
    if bull and not bear:
        return "bullish"
    if bear and not bull:
        return "bearish"
    return "neutral"


def _levels_context_note(payload: Dict[str, Any]) -> Optional[str]:
    """
    Explain whether levels are explicitly anchored to live context or likely illustrative.
    """
    tp = payload.get("trading_plan") or {}
    mr = payload.get("market_reaction") or {}
    key_levels = str(tp.get("key_levels") or "")
    price_action = str(mr.get("price_action") or "")
    joined = f"{key_levels} {price_action}".lower()
    if not joined.strip():
        return None
    anchored_tokens = (
        "current",
        "spot",
        "last close",
        "live",
        "currently",
        "trading at",
    )
    if any(tok in joined for tok in anchored_tokens):
        return "Levels appear anchored to current context."
    return "Levels may be illustrative unless explicitly anchored to current spot or last close."


def build_spine_calendar(
    payload: Dict[str, Any],
    *,
    event_title: str,
    currency: str,
    analysis_type: str,
) -> Dict[str, Any]:
    implications = payload.get("implications_takeaways") or {}
    market_bias = implications.get("market_bias") or ""
    bias = _bias_from_market_bias_text(market_bias)
    cc = (currency or "USD").upper()
    bias_subject = f"{cc} around this release"

    horizon = "post-release" if "post" in (analysis_type or "").lower() else "into the release"

    conf = payload.get("confidence_score")
    try:
        conf_int = int(round(float(conf))) if conf is not None else 70
    except (TypeError, ValueError):
        conf_int = 70

    dq = str(payload.get("data_quality") or "unknown")
    vs = str(payload.get("validation_status") or "unknown")
    conf_reason = _confidence_reason_calendar(dq, vs)

    tp = payload.get("trading_plan") or {}
    invalidation = (
        (tp.get("avoid_strategies") or "").strip()
        or (tp.get("key_levels") or "").strip()[:240]
        or "Stale if actual print deviates sharply from scenario assumptions."
    )

    mr = payload.get("market_reaction") or {}
    pa = str(mr.get("price_action") or "")
    instruments: List[str] = []
    for pair in ("EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD"):
        if pair.replace("/", "") in pa.replace(" ", "").upper():
            instruments.append(pair)
    if not instruments:
        instruments = ["EUR/USD", "USD/JPY"] if cc == "USD" else [f"{cc}/USD" if cc != "USD" else "EUR/USD"]

    summary_line = (payload.get("headline") or payload.get("key_takeaway") or "").strip()
    if len(summary_line) > 220:
        summary_line = summary_line[:217] + "..."

    return {
        "summary_line": summary_line or f"{event_title}: macro event analysis ({horizon}).",
        "bias": bias,
        "bias_subject": bias_subject,
        "time_horizon": horizon,
        "confidence": conf_int,
        "confidence_reason": conf_reason,
        "invalidation": invalidation[:500],
        "primary_instruments": instruments[:8],
    }


def build_spine_news(analysis: Dict[str, Any], news_item: Dict[str, Any]) -> Dict[str, Any]:
    reaction = str(analysis.get("immediate_reaction") or "").lower()
    if reaction == "bullish_usd":
        bias, subj = "bullish", "USD"
    elif reaction == "bearish_usd":
        bias, subj = "bearish", "USD"
    else:
        bias, subj = "neutral", "USD / risk (headline context)"

    tf = str(analysis.get("timeframe") or "next session")
    try:
        conf_int = int(analysis.get("confidence"))
    except (TypeError, ValueError):
        conf_int = 70

    vol = str(analysis.get("volatility") or "unknown")
    risk = analysis.get("risk_assessment") or {}
    liq = str(risk.get("liquidity_impact") or "unknown")
    conf_reason = (
        f"Headline-first synthesis; volatility={vol}, liquidity_impact={liq}. "
        "Re-check if a larger macro theme starts dominating flow."
    )

    pairs = analysis.get("key_pairs") or []
    instruments = [str(p) for p in pairs][:8]
    if not instruments:
        instruments = ["EUR/USD", "USD/JPY"]

    title = (news_item.get("title") or "").strip()
    summary_line = (analysis.get("news_impact") or title or "Live news analysis.")[:220]

    inv = "Stale if the headline is denied, superseded, or a larger macro story dominates the session."

    return {
        "summary_line": summary_line,
        "bias": bias,
        "bias_subject": subj,
        "time_horizon": tf,
        "confidence": conf_int,
        "confidence_reason": conf_reason,
        "invalidation": inv,
        "primary_instruments": instruments,
    }


def build_spine_holistic(scan: Dict[str, Any], country_code: str) -> Dict[str, Any]:
    st = scan.get("short_term") or {}
    lt = scan.get("long_term") or {}
    tb = scan.get("trader_brief") or {}
    pair_setups: List[Dict[str, Any]] = list(scan.get("pair_setups") or [])

    bias = str(st.get("bias") or "neutral").lower()
    if bias not in ("bullish", "bearish", "neutral"):
        bias = "neutral"

    cc = (country_code or "").upper()
    economy = scan.get("economy") or cc
    bias_subject = f"{economy} short-term regime (2–6w)"

    try:
        conf_int = int(st.get("confidence") or 0)
    except (TypeError, ValueError):
        conf_int = 70

    qo = scan.get("quality_overrides") or {}
    missing = "incomplete signals" if qo.get("incomplete") else "full signal set"
    freshness = "stale inputs" if qo.get("stale") else "fresh-enough inputs"
    conf_reason = (
        f"Deterministic regime blend with {missing} and {freshness}; "
        f"model={scan.get('model_version', 'economy_scan')}."
    )

    inv = (pair_setups[0].get("invalidation") if pair_setups else None) or tb.get("key_risk")
    if not inv:
        inv = "Regime reprices if incoming data contradicts drivers or event risk spikes."

    instruments = [str(p.get("pair")) for p in pair_setups if p.get("pair")][:8]

    summary_line = (tb.get("short_term_line") or lt.get("display_bias") or bias).strip()
    if isinstance(summary_line, str) and len(summary_line) > 220:
        summary_line = summary_line[:217] + "..."

    return {
        "summary_line": summary_line or f"{economy}: macro regime scan.",
        "bias": bias,
        "bias_subject": bias_subject,
        "time_horizon": "2–6 weeks (short-term strip); see scan for long-term horizon.",
        "confidence": conf_int,
        "confidence_reason": conf_reason[:400],
        "invalidation": str(inv)[:500],
        "primary_instruments": instruments or ["EUR/USD", "USD/JPY"],
    }


def merge_v1_calendar_response(
    enhanced_analysis: Dict[str, Any],
    *,
    validated_event: Dict[str, Any],
    analysis_type: str,
) -> Dict[str, Any]:
    out = dict(enhanced_analysis)
    title = str(validated_event.get("title") or "")
    currency = str(validated_event.get("currency") or "USD")

    out, market_scenarios = attach_canonical_calendar_scenarios(
        out, event_title=title, currency=currency
    )
    if not market_scenarios and validated_event.get("expected") not in (None, "", "N/A"):
        market_scenarios = build_market_scenarios(
            event_title=title,
            currency=currency,
            expected=validated_event.get("expected"),
            expected_display=validated_event.get("expected"),
        )
        if market_scenarios:
            out["market_scenarios"] = market_scenarios
            fs_dict = out.get("forward_scenarios")
            if isinstance(fs_dict, dict):
                out["forward_scenarios_by_outcome"] = forward_scenarios_by_outcome(fs_dict)

    fs = out.get("forward_scenarios")
    warnings = calendar_scenario_alignment_warnings(
        title,
        currency,
        fs if isinstance(fs, dict) else None,
        market_scenarios=market_scenarios,
    )

    level_context_note = _levels_context_note(out)
    out["analysis_format_version"] = ANALYSIS_FORMAT_VERSION
    out["spine"] = build_spine_calendar(
        out,
        event_title=title,
        currency=currency,
        analysis_type=analysis_type,
    )
    if level_context_note:
        out["level_context_note"] = level_context_note
        out["spine"]["confidence_reason"] = (
            f"{out['spine'].get('confidence_reason', '')} {level_context_note}".strip()
        )
    out["scenario_alignment_status"] = "warning" if warnings else "aligned"
    if warnings:
        out["scenario_alignment_warnings"] = warnings
    return out


def merge_v1_news_response(analysis_result: Dict[str, Any], news_item: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(analysis_result)
    out["analysis_format_version"] = ANALYSIS_FORMAT_VERSION
    out["spine"] = build_spine_news(out, news_item)
    return out


def merge_v1_economy_scan_response(
    response_body: Dict[str, Any],
    country_code: str,
) -> Dict[str, Any]:
    out = dict(response_body)
    scan = out.get("scan")
    if not isinstance(scan, dict):
        return out
    out["analysis_format_version"] = ANALYSIS_FORMAT_VERSION
    out["spine"] = build_spine_holistic(scan, country_code)
    return out


def build_spine_legacy_local_calendar(event: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Spine for generate_ai_analysis() shape (local analyzer / mock)."""
    title = str(event.get("title") or "Economic event")
    currency = str(event.get("currency") or "USD")
    summary = str(analysis.get("news_impact") or title)[:220]
    bias = str(analysis.get("immediate_reaction") or "neutral").lower()
    if bias not in ("bullish", "bearish", "neutral"):
        bias = "neutral"
    try:
        conf_int = int(analysis.get("confidence") or 70)
    except (TypeError, ValueError):
        conf_int = 70
    pairs = analysis.get("key_pairs") or ["EUR/USD", "USD/JPY"]
    return {
        "summary_line": summary,
        "bias": bias,
        "bias_subject": f"{currency.upper()} around this release (local analyzer)",
        "time_horizon": "into the release",
        "confidence": conf_int,
        "confidence_reason": "Local / template analysis; upgrade path uses enhanced-analysis for full context.",
        "invalidation": (analysis.get("trading_implications") or "")[:400] or "Stale after actual vs expected is known.",
        "primary_instruments": [str(p) for p in pairs][:8],
    }


def merge_v1_legacy_local_calendar_response(
    analysis: Dict[str, Any],
    *,
    event: Dict[str, Any],
) -> Dict[str, Any]:
    out = dict(analysis)
    out["analysis_format_version"] = ANALYSIS_FORMAT_VERSION
    out["spine"] = build_spine_legacy_local_calendar(event, out)
    return out
