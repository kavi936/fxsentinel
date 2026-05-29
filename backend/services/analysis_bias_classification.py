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
from services.analysis_score_bands import (
    BIAS_BEARISH_MAX,
    BIAS_BULLISH_MIN,
    BIAS_CLASS_BEARISH,
    BIAS_CLASS_BULLISH,
    BIAS_CLASS_NEUTRAL_BEARISH_LEAN,
    BIAS_CLASS_NEUTRAL_BULLISH_LEAN,
    BIAS_CLASS_TRUE_NEUTRAL,
    DISPLAY_LABELS,
    HEADLINE_LABELS,
    LEAN_THRESHOLD,
    NEUTRAL_BAND_MAX,
    NEUTRAL_BAND_MIN,
    score_to_base_bias,
)

BIAS_PROMPT_RULES = """
NEUTRAL SUB-CLASSIFICATION (mandatory when bias is in the neutral score band):
- Use TRUE NEUTRAL only when drivers are genuinely balanced with no readable lean.
- Use NEUTRAL · BULLISH LEAN or NEUTRAL · BEARISH LEAN when bias stays neutral but narrative/score tilts one way.
- Do not label plain NEUTRAL when the body clearly implies a directional lean — match label to narrative.
- Strong conviction outside the neutral band: keep BULLISH or BEARISH (no lean suffix).
""".strip()


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
    headline = HEADLINE_LABELS.get(classification, display)
    if incomplete:
        display = f"{display} (incomplete)"
        headline = f"{headline} (incomplete)"

    return {
        "bias": base,
        "bias_classification": classification,
        "display_bias": display,
        "headline_bias": headline,
    }


def _format_display_label(
    classification: str,
    *,
    incomplete: bool = False,
    currency_code: Optional[str] = None,
    usd_suffix: bool = False,
) -> str:
    """Format bias/reaction label; append (CCY) when lean applies to a specific currency."""
    label = DISPLAY_LABELS.get(classification, classification.upper().replace("_", " "))
    ccy = (currency_code or ("USD" if usd_suffix else "")).upper()
    if ccy and classification in (BIAS_CLASS_BULLISH, BIAS_CLASS_BEARISH):
        label = f"{label} {ccy}"
    if ccy and classification in (BIAS_CLASS_NEUTRAL_BULLISH_LEAN, BIAS_CLASS_NEUTRAL_BEARISH_LEAN):
        label = f"{label} ({ccy})"
    if incomplete:
        label = f"{label} (incomplete)"
    return label


_CURRENCY_SIGNAL_PATTERNS: Dict[str, Tuple[str, ...]] = {
    "EUR": (
        r"\bECB\b",
        r"\beuro\b",
        r"euro[- ]?area",
        r"\bEUR\b",
        r"european central bank",
        r"lagarde",
    ),
    "GBP": (
        r"\bBOE\b",
        r"\bGBP\b",
        r"bank of england",
        r"sterling",
        r"\bpound\b",
    ),
    "JPY": (
        r"\bBOJ\b",
        r"\bJPY\b",
        r"bank of japan",
        r"\byen\b",
    ),
    "AUD": (r"\bRBA\b", r"\bAUD\b", r"reserve bank of australia"),
    "USD": (
        r"\bFED\b",
        r"federal reserve",
        r"\bFOMC\b",
        r"\bUSD\b",
        r"\bdollar\b",
        r"greenback",
    ),
}


def detect_news_primary_currency(
    *,
    title: str = "",
    news_impact: str = "",
    trading_implications: str = "",
    key_pairs: Optional[List[str]] = None,
) -> str:
    """Infer which currency the headline primarily concerns (for reaction labels)."""
    blob = f"{title}\n{news_impact}\n{trading_implications}"
    scores: Dict[str, int] = {}
    for ccy, patterns in _CURRENCY_SIGNAL_PATTERNS.items():
        scores[ccy] = sum(1 for pat in patterns if re.search(pat, blob, re.IGNORECASE))

    pairs = key_pairs or []
    for pair in pairs:
        p = str(pair or "").upper().replace("/", "").replace(" ", "")
        if p.startswith("EUR"):
            scores["EUR"] = scores.get("EUR", 0) + 2
        if p.startswith("GBP"):
            scores["GBP"] = scores.get("GBP", 0) + 2
        if p.startswith("JPY") and "USDJPY" in p:
            scores["JPY"] = scores.get("JPY", 0) + 1
            scores["USD"] = scores.get("USD", 0) + 1

    if re.search(r"\b(bearish|bullish|weak|strong|pressure on)\s+usd\b", blob, re.IGNORECASE):
        scores["USD"] = scores.get("USD", 0) + 4
    if re.search(r"\b(bearish|bullish|weak|strong|pressure on)\s+(eur|euro)\b", blob, re.IGNORECASE):
        scores["EUR"] = scores.get("EUR", 0) + 4

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if not ranked or ranked[0][1] <= 0:
        return "USD"
    top_score = ranked[0][1]
    leaders = [ccy for ccy, score in ranked if score == top_score]
    if "USD" in leaders and len(leaders) > 1:
        non_usd = [c for c in leaders if c != "USD"]
        if non_usd:
            return non_usd[0]
    return ranked[0][0]


def infer_text_directional_lean(text: str, primary_currency: str = "USD") -> Optional[str]:
    """Return neutral_bullish_lean / neutral_bearish_lean when text tilts but is not decisive."""
    combined = (text or "").upper()
    cur = (primary_currency or "USD").upper()

    currency_bullish: Tuple[str, ...]
    currency_bearish: Tuple[str, ...]
    if cur == "EUR":
        currency_bullish = (
            "STRONGER EURO",
            "EURO STRENGTHENS",
            "EUR RALLY",
            "EUR BULLISH",
            "ECB HAWKISH",
            "SUPPORTS A STRONGER EURO",
            "EURO GAINS",
        )
        currency_bearish = (
            "WEAKER EURO",
            "EUR WEAK",
            "EUR SLIPS",
            "ECB DOVISH",
            "EURO FALLS",
            "DOWNWARD PRESSURE ON THE EURO",
        )
    elif cur == "GBP":
        currency_bullish = ("STRONGER GBP", "STERLING RALLY", "BOE HAWKISH", "GBP BULLISH")
        currency_bearish = ("WEAKER GBP", "STERLING FALLS", "BOE DOVISH", "GBP BEARISH")
    elif cur == "JPY":
        currency_bullish = ("STRONGER YEN", "JPY RALLY", "BOJ HAWKISH", "YEN GAINS")
        currency_bearish = ("WEAKER YEN", "JPY SLIPS", "BOJ DOVISH", "YEN FALLS")
    else:
        currency_bullish = (
            "SUPPORTS USD",
            "USD STRENGTH",
            "USD FIRMS",
            "USD BID",
            "DOLLAR STRENGTHENS",
            "HAWKISH FED",
        )
        currency_bearish = (
            "PRESSURE ON USD",
            "USD WEAK",
            "USD SLIPS",
            "USD FALLS",
            "DOLLAR WEAKENS",
            "DOVISH FED",
        )

    bull = sum(1 for t in currency_bullish if t in combined)
    bear = sum(1 for t in currency_bearish if t in combined)

    if cur == "USD":
        if "EUR/USD RALLY" in combined or "EURO RALLY" in combined:
            bear += 1
        if "EUR/USD LOWER" in combined or "DOWNWARD PRESSURE ON THE EURO" in combined:
            bull += 1

    if bull > bear and bull >= 1:
        return BIAS_CLASS_NEUTRAL_BULLISH_LEAN
    if bear > bull and bear >= 1:
        return BIAS_CLASS_NEUTRAL_BEARISH_LEAN

    if cur != "USD":
        return None

    generic_bullish = ("BULLISH", "HAWKISH", "STRENGTHEN", "RALLY", "HIGHER", "UPSIDE")
    generic_bearish = ("BEARISH", "DOVISH", "WEAKEN", "SELLOFF", "LOWER", "DOWNSIDE")
    bull = sum(1 for t in generic_bullish if t in combined)
    bear = sum(1 for t in generic_bearish if t in combined)
    if bull > bear and bull >= 1:
        return BIAS_CLASS_NEUTRAL_BULLISH_LEAN
    if bear > bull and bear >= 1:
        return BIAS_CLASS_NEUTRAL_BEARISH_LEAN
    return None


def classify_usd_reaction(
    immediate_reaction: str,
    news_impact: str = "",
    trading_implications: str = "",
    *,
    title: str = "",
    key_pairs: Optional[List[str]] = None,
    primary_currency: Optional[str] = None,
    reaction_rationale: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Classify live-news immediate_reaction with optional lean when reaction is neutral.
    Labels reference the event currency (EUR, GBP, …), not always USD.
    """
    reaction = str(immediate_reaction or "neutral").strip().lower()
    corpus = f"{news_impact}\n{trading_implications}"
    heuristic_ccy = detect_news_primary_currency(
        title=title,
        news_impact=news_impact,
        trading_implications=trading_implications,
        key_pairs=key_pairs,
    )
    gpt_ccy = str(primary_currency or "").strip().upper()
    if gpt_ccy and len(gpt_ccy) == 3:
        primary_ccy = gpt_ccy
        currency_source = "gpt" if gpt_ccy == heuristic_ccy else "gpt_with_heuristic_mismatch"
    else:
        primary_ccy = heuristic_ccy
        currency_source = "heuristic"
    if gpt_ccy and heuristic_ccy and gpt_ccy != heuristic_ccy:
        currency_source = "gpt_heuristic_mismatch"
    elif gpt_ccy and gpt_ccy == heuristic_ccy:
        currency_source = "gpt_heuristic_agree"

    if reaction == "bullish_usd":
        if primary_ccy != "USD":
            lean = infer_text_directional_lean(corpus, primary_ccy) or BIAS_CLASS_NEUTRAL_BULLISH_LEAN
            return {
                "immediate_reaction": reaction,
                "bias_classification": lean,
                "reaction_display": _format_display_label(lean, currency_code=primary_ccy),
                "reaction_currency": primary_ccy,
            }
        return {
            "immediate_reaction": reaction,
            "bias_classification": BIAS_CLASS_BULLISH,
            "reaction_display": _format_display_label(BIAS_CLASS_BULLISH, currency_code="USD"),
            "reaction_currency": "USD",
        }
    if reaction == "bearish_usd":
        if primary_ccy != "USD":
            lean = infer_text_directional_lean(corpus, primary_ccy) or BIAS_CLASS_NEUTRAL_BEARISH_LEAN
            return {
                "immediate_reaction": reaction,
                "bias_classification": lean,
                "reaction_display": _format_display_label(lean, currency_code=primary_ccy),
                "reaction_currency": primary_ccy,
            }
        return {
            "immediate_reaction": reaction,
            "bias_classification": BIAS_CLASS_BEARISH,
            "reaction_display": _format_display_label(BIAS_CLASS_BEARISH, currency_code="USD"),
            "reaction_currency": "USD",
        }

    lean = infer_text_directional_lean(corpus, primary_ccy)
    if lean == BIAS_CLASS_NEUTRAL_BULLISH_LEAN:
        classification = lean
    elif lean == BIAS_CLASS_NEUTRAL_BEARISH_LEAN:
        classification = lean
    else:
        classification = BIAS_CLASS_TRUE_NEUTRAL

    out = {
        "immediate_reaction": reaction,
        "bias_classification": classification,
        "reaction_display": _format_display_label(classification, currency_code=primary_ccy),
        "reaction_currency": primary_ccy,
        "reaction_currency_source": currency_source,
    }
    if reaction_rationale and str(reaction_rationale).strip():
        out["reaction_rationale"] = str(reaction_rationale).strip()[:400]
    return out


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
        title=str(out.get("title") or out.get("headline") or ""),
        key_pairs=out.get("key_pairs") if isinstance(out.get("key_pairs"), list) else None,
        primary_currency=out.get("primary_currency"),
        reaction_rationale=out.get("reaction_rationale"),
    )
    if classified.get("reaction_currency"):
        out["reaction_currency"] = classified["reaction_currency"]
    if classified.get("reaction_rationale"):
        out["reaction_rationale"] = classified["reaction_rationale"]
    if classified.get("reaction_currency_source"):
        out["reaction_currency_source"] = classified["reaction_currency_source"]
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
            f"{out.get('news_impact', '')}\n{out.get('trading_implications', '')}",
            str(classified.get("reaction_currency") or "USD"),
        )
        if lean:
            out["bias_classification"] = lean
            out["reaction_display"] = _format_display_label(
                lean,
                currency_code=str(classified.get("reaction_currency") or "USD"),
            )
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
