#!/usr/bin/env python3
"""
Shared macro score bands for holistic scans and bias classification.

Narrower neutral band (v2) so opposing drivers surface as leans/direction more often
without GPT overriding deterministic scores.
"""

from __future__ import annotations

from typing import Any, Dict

# Holistic composite score scale (-100 … +100)
SCORE_MIN = -100
SCORE_MAX = 100

# v2 bands — was ±20 neutral / ±21 conviction; too often "neutral"
NEUTRAL_BAND_MIN = -12
NEUTRAL_BAND_MAX = 12
LEAN_THRESHOLD = 3
BIAS_BULLISH_MIN = 15
BIAS_BEARISH_MAX = -15

BIAS_CLASS_BULLISH = "bullish"
BIAS_CLASS_BEARISH = "bearish"
BIAS_CLASS_TRUE_NEUTRAL = "true_neutral"
BIAS_CLASS_NEUTRAL_BULLISH_LEAN = "neutral_bullish_lean"
BIAS_CLASS_NEUTRAL_BEARISH_LEAN = "neutral_bearish_lean"

DISPLAY_LABELS = {
    BIAS_CLASS_BULLISH: "BULLISH",
    BIAS_CLASS_BEARISH: "BEARISH",
    BIAS_CLASS_TRUE_NEUTRAL: "TRUE NEUTRAL",
    BIAS_CLASS_NEUTRAL_BULLISH_LEAN: "NEUTRAL · BULLISH LEAN",
    BIAS_CLASS_NEUTRAL_BEARISH_LEAN: "NEUTRAL · BEARISH LEAN",
}

HEADLINE_LABELS = {
    BIAS_CLASS_BULLISH: "BULLISH",
    BIAS_CLASS_BEARISH: "BEARISH",
    BIAS_CLASS_TRUE_NEUTRAL: "TRUE NEUTRAL",
    BIAS_CLASS_NEUTRAL_BULLISH_LEAN: "BULLISH LEAN",
    BIAS_CLASS_NEUTRAL_BEARISH_LEAN: "BEARISH LEAN",
}


def score_to_base_bias(score: float) -> str:
    if score >= BIAS_BULLISH_MIN:
        return BIAS_CLASS_BULLISH
    if score <= BIAS_BEARISH_MAX:
        return BIAS_CLASS_BEARISH
    return "neutral"


def compute_directional_conviction(
    score: float,
    data_confidence: int,
    *,
    incomplete: bool = False,
) -> str:
    """
    How decisive the directional score is given input quality (not GPT opinion).
    """
    if incomplete or data_confidence < 55:
        return "low"
    abs_score = abs(float(score))
    if abs_score >= 35 and data_confidence >= 70:
        return "high"
    if abs_score >= BIAS_BULLISH_MIN or abs_score > LEAN_THRESHOLD:
        return "medium"
    return "low"


def neutral_band_contract() -> Dict[str, Any]:
    return {
        "min": NEUTRAL_BAND_MIN,
        "max": NEUTRAL_BAND_MAX,
        "label": f"Neutral band ({NEUTRAL_BAND_MIN} to +{NEUTRAL_BAND_MAX})",
        "bullish_min": BIAS_BULLISH_MIN,
        "bearish_max": BIAS_BEARISH_MAX,
        "lean_threshold": LEAN_THRESHOLD,
    }
