#!/usr/bin/env python3
"""
Live-news correlation risk specificity (review §3.5).

Turns generic "correlation risk: medium" into pair/channel-specific guidance.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.analysis_contract import ANALYSIS_KIND_LIVE_NEWS


def _normalize_pair(pair: str) -> str:
    return str(pair or "").replace("-", "/").upper().strip()


def _extract_pairs(payload: Dict[str, Any], news_item: Optional[Dict[str, Any]]) -> List[str]:
    pairs: List[str] = []
    for candidate in (payload.get("key_pairs") or []):
        p = _normalize_pair(str(candidate))
        if p:
            pairs.append(p)
    for candidate in ((news_item or {}).get("currency_pairs") or []):
        p = _normalize_pair(str(candidate))
        if p and p not in pairs:
            pairs.append(p)
    return pairs[:4]


def _has_tokens(text: str, tokens: List[str]) -> bool:
    low = text.lower()
    return any(tok in low for tok in tokens)


def _channel_hints_for_pair(pair: str) -> List[str]:
    pair_key = pair.replace("/", "")
    hints: List[str] = []
    if pair_key == "EURUSD":
        hints.append("USD rates / Fed repricing vs EUR growth-confidence spread")
    elif pair_key == "GBPUSD":
        hints.append("USD rates impulse vs UK macro beta and risk sentiment")
    elif pair_key == "USDJPY":
        hints.append("US yield direction vs haven-risk regime (JPY can diverge in risk-off)")
    elif pair_key == "AUDUSD":
        hints.append("Global risk + China/commodities channel vs USD rate impulse")
    elif pair_key == "USDCAD":
        hints.append("Oil-beta spillover and North America macro divergence")
    elif pair_key == "USDCHF":
        hints.append("Safe-haven correlation (CHF/JPY) under stress headlines")
    elif pair_key == "XAU/USD":
        hints.append("Real-yield and USD inverse correlation via gold safe-haven flow")
    else:
        hints.append("Cross-asset risk and rate-differential spillover")
    return hints


def _derive_risk_level(payload: Dict[str, Any], narrative: str) -> str:
    reaction = str(payload.get("immediate_reaction") or "neutral").lower()
    risk_assessment = payload.get("risk_assessment") if isinstance(payload.get("risk_assessment"), dict) else {}
    base = str(risk_assessment.get("correlation_risk") or risk_assessment.get("market_volatility") or "medium").lower()
    if _has_tokens(narrative, ["high volatility", "sharp move", "risk-off", "spillover", "contagion", "gap risk"]):
        return "high"
    if reaction == "neutral" and _has_tokens(narrative, ["mixed", "two-sided", "range", "indecision"]):
        return "medium"
    if base in {"high", "medium", "low"}:
        return base
    return "medium"


def _build_detail(pairs: List[str], narrative: str, level: str) -> str:
    if not pairs:
        return "Correlation risk reflects potential spillover across major USD pairs if cross-asset sentiment flips."
    pair_bits = []
    for pair in pairs:
        hints = _channel_hints_for_pair(pair)
        pair_bits.append(f"{pair}: {hints[0]}")
    pair_text = "; ".join(pair_bits[:3])
    qualifier = {
        "high": "Cross-pair spillover risk is elevated",
        "medium": "Cross-pair spillover risk is moderate",
        "low": "Cross-pair spillover risk is contained",
    }.get(level, "Cross-pair spillover risk is moderate")
    trigger_note = ""
    if re.search(r"\bif\b", narrative, flags=re.IGNORECASE):
        trigger_note = " Use the stated If→then trigger as the confirmation gate before extrapolating to correlated pairs."
    return f"{qualifier}: {pair_text}.{trigger_note}"


def apply_news_correlation_risk_to_response(
    payload: Dict[str, Any],
    *,
    news_item: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(payload)
    pairs = _extract_pairs(out, news_item)
    corpus = f"{out.get('news_impact', '')}\n{out.get('trading_implications', '')}"
    level = _derive_risk_level(out, corpus)
    detail = _build_detail(pairs, corpus, level)

    risk = out.get("risk_assessment")
    if not isinstance(risk, dict):
        risk = {}
    risk["correlation_risk"] = level
    risk["correlation_pairs"] = pairs
    risk["correlation_risk_detail"] = detail
    out["risk_assessment"] = risk
    out["correlation_risk_display"] = {
        "level": level.upper(),
        "detail": detail,
        "pairs": pairs,
    }
    out["correlation_risk_applied"] = {
        "surface": "live_news",
        "pair_count": len(pairs),
        "level": level,
    }
    return out


def apply_news_correlation_risk_if_news(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    news_item: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_LIVE_NEWS:
        return dict(payload)
    return apply_news_correlation_risk_to_response(payload, news_item=news_item)

