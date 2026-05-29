#!/usr/bin/env python3
"""
Deterministic calendar analysis confidence (review §1.2, §2.3).

Replaces opaque GPT-only High/Medium/Low → 90/75/60 mapping with a scored,
explainable methodology tied to event data quality, impact, scenario discipline,
and optional macro-scan freshness.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_contract import ANALYSIS_KIND_CALENDAR_EVENT

CALENDAR_CONFIDENCE_PROMPT_RULES = """
CONFIDENCE (two concepts — mandatory):
1) **edge_confidence** (High | Medium | Low): your conviction in the directional trade read for this release.
2) **edge_confidence_reason**: one sentence explaining that edge (e.g. "Hot CPI would extend USD bid if core surprises above 0.3% amid sticky services").
- Also output analysis_confidence with the same High|Medium|Low value (alias for edge_confidence).
- assumptions[]: only for missing data gaps — not a substitute for edge_confidence_reason.
- Do not claim High edge when forecast is missing or scenarios are vague/contradictory.
- The API applies a separate **data quality score** from inputs; your edge_confidence_reason is shown to traders as the edge explanation.
""".strip()

_TIER_FROM_SCORE = (
    (80, "High"),
    (60, "Medium"),
    (0, "Low"),
)


def _tier_label(score: float) -> str:
    for threshold, label in _TIER_FROM_SCORE:
        if score >= threshold:
            return label
    return "Low"


def _parse_forward_scenario_percentages(forward_scenarios: Any) -> Tuple[int, int]:
    """Return (sum_of_ints, count_found)."""
    if not isinstance(forward_scenarios, dict):
        return 0, 0
    total = 0
    count = 0
    for value in forward_scenarios.values():
        text = str(value or "")
        match = re.search(r"\b(\d{1,3})\s*%", text)
        if match:
            total += int(match.group(1))
            count += 1
    return total, count


def _event_field_present(value: Any) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    return s not in ("", "N/A", "TBD", "—", "-")


def _macro_freshness_penalty(freshness_hours: Optional[float]) -> Tuple[int, str]:
    if freshness_hours is None:
        return 0, ""
    try:
        hours = float(freshness_hours)
    except (TypeError, ValueError):
        return 0, ""
    if hours > 24 * 28:
        return 20, f"economy scan ~{int(hours // 24)}d old (−20)"
    if hours > 24 * 14:
        return 12, f"economy scan ~{int(hours // 24)}d old (−12)"
    if hours > 24 * 7:
        return 6, f"economy scan ~{int(hours // 24)}d old (−6)"
    if hours <= 48:
        return 3, "fresh economy scan context (+3)"
    return 0, ""


def compute_calendar_confidence(
    *,
    event: Optional[Dict[str, Any]] = None,
    analysis_type: str = "pre_event",
    payload: Optional[Dict[str, Any]] = None,
    macro_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic confidence score (20–95) with factor breakdown and human reason string.
    """
    payload = payload or {}
    event = event or {}
    factors: List[Dict[str, Any]] = []
    score = 72.0

    impact = str(event.get("impact") or "medium").strip().lower()
    if impact not in ("high", "medium", "low"):
        impact = "medium"
    if impact == "high":
        score += 8
        factors.append({"id": "impact_tier", "delta": 8, "detail": "high-impact release"})
    elif impact == "low":
        score -= 8
        factors.append({"id": "impact_tier", "delta": -8, "detail": "low-impact release"})
    else:
        factors.append({"id": "impact_tier", "delta": 0, "detail": "medium-impact release"})

    has_forecast = _event_field_present(event.get("expected") or event.get("forecast"))
    has_previous = _event_field_present(event.get("previous"))
    has_actual = _event_field_present(event.get("actual"))
    if has_forecast:
        score += 6
        factors.append({"id": "forecast_present", "delta": 6, "detail": "consensus/forecast available"})
    else:
        score -= 18
        factors.append({"id": "forecast_missing", "delta": -18, "detail": "no consensus/forecast on event"})
    if has_previous:
        score += 4
        factors.append({"id": "previous_present", "delta": 4, "detail": "prior print available"})
    else:
        score -= 6
        factors.append({"id": "previous_missing", "delta": -6, "detail": "prior print missing"})

    if analysis_type == "post_event" and has_actual:
        score += 5
        factors.append({"id": "post_actual", "delta": 5, "detail": "post-release with actual print"})
    elif analysis_type == "pre_event":
        factors.append({"id": "pre_event", "delta": 0, "detail": "pre-release conditional scenarios"})

    dq = str(payload.get("data_quality") or "").lower()
    if dq == "validated":
        score += 4
        factors.append({"id": "market_data", "delta": 4, "detail": "live market quotes validated"})
    elif dq in ("stale", "partial"):
        score -= 8
        factors.append({"id": "market_data", "delta": -8, "detail": f"market data {dq}"})
    elif dq in ("failed_validation", "fallback", "cached"):
        score -= 5
        factors.append({"id": "market_data", "delta": -5, "detail": f"market data {dq or 'limited'}"})

    vs = str(payload.get("validation_status") or "").lower()
    if vs == "failed":
        score -= 15
        factors.append({"id": "validation", "delta": -15, "detail": "input validation failed"})

    prob_sum, prob_count = _parse_forward_scenario_percentages(payload.get("forward_scenarios"))
    if prob_count >= 2:
        if prob_sum == 100:
            score += 5
            factors.append({"id": "scenarios_sum", "delta": 5, "detail": "scenario probabilities sum to 100%"})
        else:
            score -= 10
            factors.append(
                {
                    "id": "scenarios_sum",
                    "delta": -10,
                    "detail": f"scenario probabilities sum to {prob_sum}% (expected 100%)",
                }
            )

    macro = macro_snapshot or payload.get("macro_snapshot") or {}
    if isinstance(macro, dict) and macro.get("source") == "holistic_scan":
        penalty, note = _macro_freshness_penalty(macro.get("freshness_hours"))
        if penalty:
            score -= penalty
            factors.append({"id": "macro_freshness", "delta": -penalty, "detail": note})
        elif note:
            score += 3
            factors.append({"id": "macro_freshness", "delta": 3, "detail": note})

    gpt_label = str(payload.get("analysis_confidence") or "").strip().title()
    gpt_map = {"High": 4, "Medium": 0, "Low": -8}
    if gpt_label in gpt_map:
        delta = gpt_map[gpt_label]
        score += delta
        factors.append({"id": "gpt_edge_label", "delta": delta, "detail": f"GPT edge label {gpt_label}"})

    score = max(20.0, min(95.0, round(score, 1)))
    tier = _tier_label(score)
    reason_parts = [f["detail"] for f in factors if f.get("detail")]
    confidence_reason = (
        "Confidence reflects: " + "; ".join(reason_parts[:6]) + ("…" if len(reason_parts) > 6 else "")
        if reason_parts
        else "Confidence based on default event-analysis inputs."
    )

    return {
        "confidence_score": score,
        "confidence_tier": tier.lower(),
        "analysis_confidence": tier,
        "confidence_reason": confidence_reason,
        "confidence_factors": factors,
    }


def _fetch_macro_snapshot_for_currency(
    currency: str,
    token_user_info: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not token_user_info:
        return None
    country_map = {"USD": "US", "EUR": "EUR", "GBP": "GBP", "JPY": "JPY", "AUD": "AUD", "CAD": "CAD", "CHF": "CHF", "NZD": "NZD"}
    country = country_map.get((currency or "").upper())
    if not country:
        return None
    try:
        from services.analysis_context_pack import extract_macro_snapshot_from_scan
        from services.economy_holistic_scan_store import economy_holistic_scan_store

        recent = economy_holistic_scan_store.get_recent_holistic_scans(
            user_info=token_user_info,
            limit=1,
            country_code=country,
        )
        if not recent:
            return None
        snap = (recent[0] or {}).get("scan_snapshot") or {}
        macro = extract_macro_snapshot_from_scan(snap)
        macro["source"] = "holistic_scan"
        return macro
    except Exception:
        return None


def apply_calendar_confidence_to_response(
    payload: Dict[str, Any],
    *,
    event: Optional[Dict[str, Any]] = None,
    analysis_type: Optional[str] = None,
    token_user_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(payload)
    ev = event or {}
    currency = str(ev.get("currency") or "USD").upper()
    macro = out.get("macro_snapshot")
    if not isinstance(macro, dict):
        macro = _fetch_macro_snapshot_for_currency(currency, token_user_info)

    computed = compute_calendar_confidence(
        event=ev,
        analysis_type=analysis_type or str(out.get("analysis_type") or "pre_event"),
        payload=out,
        macro_snapshot=macro if isinstance(macro, dict) else None,
    )

    out["data_confidence_score"] = computed["confidence_score"]
    out["confidence_score"] = computed["confidence_score"]
    out["confidence_reason"] = computed["confidence_reason"]
    out["confidence_tier"] = computed["confidence_tier"]

    gpt_edge = str(payload.get("analysis_confidence") or payload.get("edge_confidence") or "").strip().title()
    if gpt_edge not in ("High", "Medium", "Low"):
        gpt_edge = computed["analysis_confidence"]
    edge_reason = str(payload.get("edge_confidence_reason") or "").strip()
    if not edge_reason:
        assumptions = payload.get("assumptions")
        if isinstance(assumptions, list) and assumptions:
            edge_reason = str(assumptions[0])[:320]
    out["edge_confidence"] = gpt_edge
    out["edge_confidence_reason"] = edge_reason
    out["analysis_confidence"] = gpt_edge
    if isinstance(macro, dict):
        out["macro_snapshot"] = macro
    out["confidence_methodology_applied"] = {
        "surface": "economic_calendar",
        "methodology": "deterministic_v1",
        "factors": computed["confidence_factors"],
        "final_score": computed["confidence_score"],
        "tier": computed["confidence_tier"],
    }
    return out


def apply_calendar_confidence_if_calendar(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    event: Optional[Dict[str, Any]] = None,
    analysis_type: Optional[str] = None,
    token_user_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_CALENDAR_EVENT:
        return dict(payload)
    return apply_calendar_confidence_to_response(
        payload,
        event=event,
        analysis_type=analysis_type,
        token_user_info=token_user_info,
    )
