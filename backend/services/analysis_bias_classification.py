#!/usr/bin/env python3
"""
NEUTRAL sub-classifications for analysis outputs (review priority #9).

When composite bias is neutral, distinguish true balance vs bullish/bearish lean
using score band position or narrative signals — without changing core bullish/bearish
labels outside the neutral band.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
)

# Align with economy_holistic_scan_service score bands
NEUTRAL_BAND_MIN = -20
NEUTRAL_BAND_MAX = 20
LEAN_THRESHOLD = 5
BIAS_BULLISH_MIN = 21
BIAS_BEARISH_MAX = -21

BIAS_CLASS_BULLISH = "bullish"
BIAS_CLASS_BEARISH = "bearish"
BIAS_CLASS_TRUE_NEUTRAL = "true_neutral"
BIAS_CLASS_NEUTRAL_BULLISH_LEAN = "neutral_bullish_lean"
BIAS_CLASS_NEUTRAL_BEARISH_LEAN = "neutral_bearish_lean"

DISPLAY_LABELS: Dict[str, str] = {
    BIAS_CLASS_BULLISH: "BULLISH",
    BIAS_CLASS_BEARISH: "BEARISH",
    BIAS_CLASS_TRUE_NEUTRAL: "TRUE NEUTRAL",
    BIAS_CLASS_NEUTRAL_BULLISH_LEAN: "NEUTRAL · BULLISH LEAN",
    BIAS_CLASS_NEUTRAL_BEARISH_LEAN: "NEUTRAL · BEARISH LEAN",
}

BIAS_PROMPT_RULES = """
NEUTRAL SUB-CLASSIFICATION (mandatory when bias is in the neutral score band):
- Use TRUE NEUTRAL only when drivers are genuinely balanced with no readable lean.
- Use NEUTRAL · BULLISH LEAN or NEUTRAL · BEARISH LEAN when bias stays neutral but narrative/score tilts one way.
- Do not label plain NEUTRAL when the body clearly implies a directional lean — match label to narrative.
- Strong conviction outside the neutral band: keep BULLISH or BEARISH (no lean suffix).
""".strip()


def score_to_base_bias(score: float) -> str:
    if score >= BIAS_BULLISH_MIN:
        return BIAS_CLASS_BULLISH
    if score <= BIAS_BEARISH_MAX:
        return BIAS_CLASS_BEARISH
    return "neutral"


def classify_from_score(
    score: float,
    *,
    incomplete: bool = False,
) -> Dict[str, Any]:
    """
    Map a composite score to base bias + fine-grained classification + display label.
    """
    base = score_to_base_bias(score)
    if base != "neutral":
        classification = base
    elif score > LEAN_THRESHOLD:
        classification = BIAS_CLASS_NEUTRAL_BULLISH_LEAN
    elif score < -LEAN_THRESHOLD:
        classification = BIAS_CLASS_NEUTRAL_BEARISH_LEAN
    else:
        classification = BIAS_CLASS_TRUE_NEUTRAL

    display = DISPLAY_LABELS.get(classification, classification.upper().replace("_", " "))
    if incomplete:
        display = f"{display} (incomplete)"

    return {
        "bias": base,
        "bias_classification": classification,
        "display_bias": display,
    }


def _format_display_label(classification: str, *, incomplete: bool = False, usd_suffix: bool = False) -> str:
    label = DISPLAY_LABELS.get(classification, classification.upper().replace("_", " "))
    if usd_suffix and classification in (BIAS_CLASS_BULLISH, BIAS_CLASS_BEARISH):
        label = f"{label} USD"
    if classification in (BIAS_CLASS_NEUTRAL_BULLISH_LEAN, BIAS_CLASS_NEUTRAL_BEARISH_LEAN):
        label = f"{label} (USD)" if usd_suffix else label
    if incomplete:
        label = f"{label} (incomplete)"
    return label


def infer_text_directional_lean(text: str) -> Optional[str]:
    """Return neutral_bullish_lean / neutral_bearish_lean when text tilts but is not decisive."""
    combined = (text or "").upper()
    bullish_hits = (
        "BULLISH",
        "HAWKISH",
        "STRENGTHEN",
        "RALLY",
        "HIGHER",
        "UPSIDE",
        "SUPPORTS USD",
        "USD STRENGTH",
        "USD FIRMS",
        "USD BID",
    )
    bearish_hits = (
        "BEARISH",
        "DOVISH",
        "WEAKEN",
        "SELLOFF",
        "LOWER",
        "DRIFT LOWER",
        "DOWNSIDE",
        "DOWNWARD",
        "PRESSURE ON",
        "PRESSURE ON USD",
        "USD WEAK",
        "USD SLIPS",
        "USD FALLS",
        "DOWNTURN",
        "EURO RALLY",
        "WEIGHS ON USD",
    )
    bull = sum(1 for t in bullish_hits if t in combined)
    bear = sum(1 for t in bearish_hits if t in combined)
    if bull > bear and bull >= 1:
        return BIAS_CLASS_NEUTRAL_BULLISH_LEAN
    if bear > bull and bear >= 1:
        return BIAS_CLASS_NEUTRAL_BEARISH_LEAN
    return None


def classify_usd_reaction(
    immediate_reaction: str,
    news_impact: str = "",
    trading_implications: str = "",
) -> Dict[str, Any]:
    """
    Classify live-news immediate_reaction with optional lean when reaction is neutral.
    """
    reaction = str(immediate_reaction or "neutral").strip().lower()
    corpus = f"{news_impact}\n{trading_implications}"

    if reaction == "bullish_usd":
        return {
            "immediate_reaction": reaction,
            "bias_classification": BIAS_CLASS_BULLISH,
            "reaction_display": _format_display_label(BIAS_CLASS_BULLISH, usd_suffix=True),
        }
    if reaction == "bearish_usd":
        return {
            "immediate_reaction": reaction,
            "bias_classification": BIAS_CLASS_BEARISH,
            "reaction_display": _format_display_label(BIAS_CLASS_BEARISH, usd_suffix=True),
        }

    lean = infer_text_directional_lean(corpus)
    if lean == BIAS_CLASS_NEUTRAL_BULLISH_LEAN:
        classification = lean
    elif lean == BIAS_CLASS_NEUTRAL_BEARISH_LEAN:
        classification = lean
    else:
        classification = BIAS_CLASS_TRUE_NEUTRAL

    return {
        "immediate_reaction": reaction,
        "bias_classification": classification,
        "reaction_display": _format_display_label(classification, usd_suffix=True),
    }


_SCENARIO_PROB_RE = re.compile(r"\[?(ABOVE|ON|BELOW)\]?\s*(\d{1,3})\s*%", re.IGNORECASE)


def infer_lean_from_forward_scenarios(forward_scenarios: Any) -> Optional[str]:
    """If neutral label but scenario mass skews, return a lean classification."""
    if not isinstance(forward_scenarios, dict):
        return None
    above = on = below = 0
    for key, text in forward_scenarios.items():
        blob = str(text or "")
        for match in _SCENARIO_PROB_RE.finditer(blob):
            bucket = match.group(1).upper()
            pct = int(match.group(2))
            if bucket == "ABOVE":
                above += pct
            elif bucket == "ON":
                on += pct
            elif bucket == "BELOW":
                below += pct
        key_lower = str(key).lower()
        if above == on == below == 0:
            nums = re.findall(r"\b(\d{1,3})\s*%", blob)
            if nums and key_lower in ("bullish", "higher", "above"):
                above += int(nums[0])
            elif nums and key_lower in ("bearish", "lower", "below"):
                below += int(nums[0])
            elif nums and key_lower == "neutral":
                on += int(nums[0])
    if above > on and above > below and above >= 55:
        return BIAS_CLASS_NEUTRAL_BULLISH_LEAN
    if below > on and below > above and below >= 55:
        return BIAS_CLASS_NEUTRAL_BEARISH_LEAN
    return None


def parse_calendar_market_bias(market_bias: str) -> Tuple[str, str]:
    """
    Parse leading BULLISH|BEARISH|NEUTRAL from market_bias line.
    Returns (base_bias, remainder_text).
    """
    raw = str(market_bias or "").strip()
    upper = raw.upper()
    for token in ("BULLISH", "BEARISH", "NEUTRAL"):
        if upper.startswith(token):
            rest = raw[len(token) :].lstrip(" :,-")
            return token.lower(), rest
    return "neutral", raw


def classify_calendar_bias(
    implications_takeaways: Dict[str, Any],
    forward_scenarios: Any,
) -> Dict[str, Any]:
    """Derive bias_classification for calendar from market_bias + scenario skew."""
    impl = implications_takeaways if isinstance(implications_takeaways, dict) else {}
    market_bias = str(impl.get("market_bias") or "")
    base, remainder = parse_calendar_market_bias(market_bias)

    if base in (BIAS_CLASS_BULLISH, BIAS_CLASS_BEARISH):
        classification = base
    else:
        lean = infer_lean_from_forward_scenarios(forward_scenarios)
        lean = lean or infer_text_directional_lean(f"{market_bias}\n{remainder}")
        classification = lean or BIAS_CLASS_TRUE_NEUTRAL

    display = _format_display_label(classification)
    return {
        "bias": base if base in (BIAS_CLASS_BULLISH, BIAS_CLASS_BEARISH) else "neutral",
        "bias_classification": classification,
        "display_bias": display,
        "market_bias_display": f"{display}: {remainder}".strip(": ") if remainder else display,
    }


def _check_record(check_id: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"id": check_id, "passed": bool(passed), "detail": detail}


def _compliance_score(checks: List[Dict[str, Any]]) -> int:
    if not checks:
        return 100
    passed = sum(1 for c in checks if c.get("passed"))
    return int(round(100 * passed / len(checks)))


def build_bias_classification_metadata(
    *,
    surface: str,
    checks: List[Dict[str, Any]],
    enforcement_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "surface": surface,
        "checks": checks,
        "compliance_score": _compliance_score(checks),
        "enforcement_actions": enforcement_actions or [],
    }


def validate_and_enforce_calendar(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(payload)
    enforcement: List[str] = []
    impl = out.get("implications_takeaways")
    if not isinstance(impl, dict):
        impl = {}
        out["implications_takeaways"] = impl

    classified = classify_calendar_bias(impl, out.get("forward_scenarios"))
    impl["bias_classification"] = classified["bias_classification"]
    impl["display_bias"] = classified["display_bias"]
    if classified.get("market_bias_display"):
        impl["market_bias_display"] = classified["market_bias_display"]
    out["implications_takeaways"] = impl

    base = classified["bias"]
    lean = classified["bias_classification"]
    corpus = f"{impl.get('market_bias', '')}"
    checks = [
        _check_record(
            "market_bias_classified",
            bool(lean),
            "bias_classification and display_bias attached to implications_takeaways.",
        ),
    ]
    if base == "neutral" and lean == BIAS_CLASS_TRUE_NEUTRAL:
        text_lean = infer_text_directional_lean(corpus)
        checks.append(
            _check_record(
                "neutral_not_contradicted_by_narrative",
                text_lean is None,
                "TRUE NEUTRAL should not coexist with clear directional narrative.",
            )
        )
        if text_lean:
            impl["bias_classification"] = text_lean
            impl["display_bias"] = _format_display_label(text_lean)
            enforcement.append("upgraded_neutral_to_lean_from_narrative")

    meta = build_bias_classification_metadata(
        surface="economic_calendar",
        checks=checks,
        enforcement_actions=enforcement,
    )
    return out, meta


def validate_and_enforce_news(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(payload)
    enforcement: List[str] = []
    classified = classify_usd_reaction(
        str(out.get("immediate_reaction") or "neutral"),
        str(out.get("news_impact") or ""),
        str(out.get("trading_implications") or ""),
    )
    out["bias_classification"] = classified["bias_classification"]
    out["reaction_display"] = classified["reaction_display"]

    reaction = str(out.get("immediate_reaction") or "neutral").lower()
    checks = [
        _check_record(
            "reaction_classified",
            bool(classified.get("bias_classification")),
            "bias_classification and reaction_display attached.",
        ),
    ]
    if reaction == "neutral" and classified["bias_classification"] == BIAS_CLASS_TRUE_NEUTRAL:
        lean = infer_text_directional_lean(
            f"{out.get('news_impact', '')}\n{out.get('trading_implications', '')}"
        )
        if lean:
            out["bias_classification"] = lean
            out["reaction_display"] = _format_display_label(lean, usd_suffix=True)
            enforcement.append("upgraded_neutral_reaction_to_lean")
            checks.append(
                _check_record("neutral_narrative_lean_applied", True, "Lean derived from narrative."),
            )

    meta = build_bias_classification_metadata(
        surface="live_news",
        checks=checks,
        enforcement_actions=enforcement,
    )
    return out, meta


def validate_and_enforce_holistic_scan(scan: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(scan)
    enforcement: List[str] = []
    checks: List[Dict[str, Any]] = []

    for key in ("short_term", "long_term"):
        regime = out.get(key)
        if not isinstance(regime, dict):
            continue
        score = regime.get("score")
        if not isinstance(score, (int, float)):
            score = regime.get("score_precise")
        if not isinstance(score, (int, float)):
            continue
        incomplete = "(incomplete)" in str(regime.get("display_bias") or "").lower()
        classified = classify_from_score(float(score), incomplete=incomplete)
        if regime.get("bias_classification") != classified["bias_classification"]:
            regime = dict(regime)
            regime["bias_classification"] = classified["bias_classification"]
            regime["display_bias"] = classified["display_bias"]
            out[key] = regime
            enforcement.append(f"refreshed_{key}_bias_classification")

        checks.append(
            _check_record(
                f"{key}_classification_present",
                bool(regime.get("bias_classification")),
                f"{key} exposes bias_classification and display_bias.",
            )
        )

    meta = build_bias_classification_metadata(
        surface="holistic_scan",
        checks=checks,
        enforcement_actions=enforcement,
    )
    return out, meta


def apply_bias_classification_to_response(
    payload: Dict[str, Any],
    analysis_kind: str,
) -> Dict[str, Any]:
    if analysis_kind == ANALYSIS_KIND_CALENDAR_EVENT:
        body, meta = validate_and_enforce_calendar(payload)
        body["bias_classification_applied"] = meta
        return body
    if analysis_kind == ANALYSIS_KIND_LIVE_NEWS:
        body, meta = validate_and_enforce_news(payload)
        body["bias_classification_applied"] = meta
        return body
    if analysis_kind == ANALYSIS_KIND_ECONOMY_SCAN:
        scan = payload.get("scan")
        if isinstance(scan, dict):
            scan_body, meta = validate_and_enforce_holistic_scan(scan)
            out = dict(payload)
            out["scan"] = scan_body
            out["bias_classification_applied"] = meta
            return out
    return dict(payload)
