#!/usr/bin/env python3
"""
Pair-specific commentary for holistic scan pair_setups.

Deterministic copy when GPT narrative is off; sensitivity hints when GPT is on.
Each pair gets drivers/invalidations keyed to base/quote currency economics.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def normalize_pair(pair: str) -> str:
    raw = str(pair or "").strip().upper().replace("/", "")
    if len(raw) == 6 and raw.isalpha():
        return raw
    return raw


def _word_set(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{4,}", (text or "").lower())}


def drivers_are_too_similar(a: str, b: str, threshold: float = 0.68) -> bool:
    """True when two driver strings share too much vocabulary (copy-paste guard)."""
    # Compare only pair-specific prose (before any shared overlay appendix).
    a = (a or "").split(" Overlay:")[0].strip()
    b = (b or "").split(" Overlay:")[0].strip()
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return False
    overlap = len(wa & wb) / min(len(wa), len(wb))
    return overlap >= threshold


def pair_explanations_are_distinct(rows: List[Dict[str, Any]]) -> Tuple[bool, str]:
    drivers = [str(r.get("driver") or "").strip() for r in rows if isinstance(r, dict)]
    for i in range(len(drivers)):
        for j in range(i + 1, len(drivers)):
            if drivers_are_too_similar(drivers[i], drivers[j]):
                return False, f"pair_drivers_too_similar:{i}:{j}"
    return True, ""


def _energy_geo_suffix(macro_overlay: Dict[str, Any]) -> str:
    themes = macro_overlay.get("global_themes") or []
    if not themes:
        return ""
    title = str(themes[0].get("title") or "").strip()
    severity = str(themes[0].get("severity") or "").lower()
    if not title:
        return ""
    if severity == "critical":
        return f" Overlay: {title} (CRITICAL) — prioritize energy/terms-of-trade channel."
    return f" Watch: {title}."


def _format_pair_display(pair_norm: str) -> str:
    if len(pair_norm) == 6:
        return f"{pair_norm[:3]}/{pair_norm[3:]}"
    return pair_norm


# (pair_norm) -> required token in driver for GPT validation (currency or institution)
PAIR_REQUIRED_TOKENS: Dict[str, Tuple[str, ...]] = {
    "EURUSD": ("eur", "ecb", "euro"),
    "USDJPY": ("jpy", "yen", "boj", "japan"),
    "GBPUSD": ("gbp", "sterling", "boe", "uk", "gilt"),
    "AUDUSD": ("aud", "aussie", "rba", "commodity", "china"),
    "EURGBP": ("eur", "ecb", "gbp", "boe", "euro", "sterling"),
    "EURJPY": ("eur", "ecb", "jpy", "yen", "boj"),
    "GBPJPY": ("gbp", "jpy", "boe", "boj", "sterling", "yen"),
    "USDCAD": ("cad", "boc", "canada", "oil"),
    "NZDUSD": ("nzd", "rbnz", "china", "dairy"),
}


def driver_mentions_pair_currency(pair_norm: str, driver: str) -> bool:
    tokens = PAIR_REQUIRED_TOKENS.get(pair_norm, ())
    lowered = (driver or "").lower()
    return any(t in lowered for t in tokens) if tokens else True


def build_pair_setup_copy(
    *,
    pair: str,
    scan_country: str,
    pair_bias: str,
    scan_short_bias: str,
    event_risk_score: float,
    sentiment_label: str,
    macro_overlay: Dict[str, Any],
    quality_overrides: Dict[str, Any],
    economy_hook: str = "",
) -> Dict[str, str]:
    """
    Return pair-specific driver, invalidation, and key_risk strings.
    """
    pair_norm = normalize_pair(pair)
    display = _format_pair_display(pair_norm)
    country = (scan_country or "US").upper()
    geo_suffix = _energy_geo_suffix(macro_overlay)
    hook = (economy_hook or "").strip()
    hook_bit = f" {hook}" if hook and len(hook) < 220 else ""

    high_events = event_risk_score >= 80.0
    stale = quality_overrides.get("stale")
    incomplete = quality_overrides.get("incomplete")

    conviction_note = (
        f"Conviction reduced — missing signal families; treat {display} as directional lean only."
        if incomplete
        else (
            f"Conviction reduced on {display} — macro inputs are stale; refresh before sizing."
            if stale
            else f"Conviction normal on {display} given available signals."
        )
    )

    # Pair-specific bodies (deterministic, not copy-paste across pairs)
    if pair_norm == "EURUSD":
        driver = (
            f"{display}: ECB terminal-rate hold vs Fed 'disciplined optionality' frames the cross; "
            f"euro-area energy import shock and terms-of-trade pressure vs USD safe-haven bid when risk spikes."
        )
        invalidation = (
            "Invalidated if EZ inflation surprise forces ECB hike pricing (EUR bid) or Hormuz de-escalation "
            "eases EUR energy premium faster than USD haven demand fades."
            if high_events
            else "Invalidated if US data re-accelerates Fed hike pricing or EUR HICP softens enough to unwind energy premium."
        )
        key_risk = "ECB–Fed repricing + euro-area energy import costs"

    elif pair_norm == "USDJPY":
        driver = (
            f"{display}: Japan's energy-import vulnerability often dominates haven flows — "
            f"BoJ gradual tightening vs import-cost drag; watch 157–161 intervention zone and risk sentiment."
        )
        invalidation = (
            "Invalidated if MoF/BoJ intervention accelerates below 157 or a risk-off repatriation bid overwhelms oil-import JPY weakness."
            if high_events
            else "Invalidated if BoJ signals faster hikes or US yields collapse, reversing USD/JPY carry pressure."
        )
        key_risk = "BoJ pace + Gulf energy pass-through to Japan CPI"

    elif pair_norm == "GBPUSD":
        driver = (
            f"{display}: BoE caught between energy-driven headline CPI and soft growth — "
            f"gilt yield overshoot vs Fed hold; sterling tracks US risk tone and UK wage/inflation surprises."
        )
        invalidation = (
            "Invalidated if BoE pushback caps hike pricing, or UK energy shock fades faster than US data resilience."
            if high_events
            else "Invalidated if US exceptionalism reasserts via yields, or UK activity data surprises up."
        )
        key_risk = "BoE policy mispricing vs energy shock"

    elif pair_norm == "AUDUSD":
        driver = (
            f"{display}: Commodity and China-demand channel for AUD vs USD haven/reflation dynamics — "
            f"iron ore/ risk appetite vs US rates and geopolitical USD bid."
        )
        invalidation = (
            "Invalidated if China stimulus/commodity rally lifts AUD despite USD firmness, or broad risk-off crushes AUD without USD bid."
            if high_events
            else "Invalidated if RBA surprises hawkish or US soft landing narrative fades USD support."
        )
        key_risk = "China growth + commodity beta vs USD haven"

    elif pair_norm == "EURGBP":
        driver = (
            f"{display}: Relative EZ vs UK energy exposure and ECB vs BoE pricing — "
            f"cross driven by inflation surprise divergence, not just global risk."
        )
        invalidation = "Invalidated if UK fiscal/gilt stress or EZ growth shock flips relative rate expectations."
        key_risk = "ECB vs BoE inflation pass-through differential"

    elif pair_norm == "EURJPY":
        driver = (
            f"{display}: EUR energy-import stress vs JPY import-cost headwind — "
            f"policy divergence (ECB hold vs BoJ gradual hikes) inside a risk-sensitive cross."
        )
        invalidation = "Invalidated if haven JPY bid dominates on geopolitical escalation, or EUR terms-of-trade improve on oil relief."
        key_risk = "Energy shock split: euro area vs Japan importer"

    elif pair_norm == "GBPJPY":
        driver = (
            f"{display}: Sterling BoE/gilt story vs JPY energy-import and intervention risk — "
            f"both legs sensitive to global risk, but through different domestic channels."
        )
        invalidation = "Invalidated if UK data forces BoE repricing or USD/JPY intervention spills into cross volatility."
        key_risk = "UK inflation/growth mix vs Japan energy + BoJ"

    elif pair_norm == "USDCAD":
        driver = (
            f"{display}: CAD oil-beta vs USD haven — Canadian terms-of-trade vs US rates/geopolitical USD demand."
        )
        invalidation = "Invalidated if oil supply shock inverts (CAD bid) or BoC/Fed divergence reprices sharply."
        key_risk = "Oil channel + North America rates"

    elif pair_norm == "NZDUSD":
        driver = (
            f"{display}: NZD China/commodity beta vs USD — dairy/China demand sensitivity vs US yield and haven flows."
        )
        invalidation = "Invalidated if China activity surprises lift NZD, or RBNZ rhetoric turns hawkish into USD strength."
        key_risk = "China demand + RBNZ vs Fed"

    else:
        if scan_short_bias == "neutral":
            driver = f"{display}: Range conditions; map {country} macro impulse through base/quote rate and risk channels."
        else:
            driver = (
                f"{display}: {country} short-term {scan_short_bias} regime transmitted via "
                f"{pair_bias} bias with {sentiment_label} yield backdrop."
            )
        invalidation = (
            "Invalidated if oil/geopolitical stress reshapes haven flows faster than domestic macro impulse."
            if high_events
            else "Invalidated if yield impulse or domestic data flips the cross bias."
        )
        key_risk = "Macro regime transmission"

    # Keep geo overlay on key_risk (shared macro headwind), not repeated in every driver string.
    if geo_suffix:
        key_risk = f"{key_risk}.{geo_suffix}"

    primary_pair_by_country = {
        "US": "EURUSD",
        "EUR": "EURUSD",
        "GBP": "GBPUSD",
        "JPY": "USDJPY",
    }
    if hook_bit and pair_norm == primary_pair_by_country.get(country) and hook_bit.lower() not in driver.lower():
        driver = f"{driver.rstrip('.')}.{hook_bit[:160]}"

    return {
        "driver": driver,
        "invalidation": invalidation,
        "key_risk": key_risk,
        "conviction_note": conviction_note,
        "sensitivity_tags": list(PAIR_REQUIRED_TOKENS.get(pair_norm, ()))[:4],
    }


def pair_sensitivity_hints_for_gpt(
    pair_setups: List[Dict[str, Any]],
    scan_country: str,
    macro_overlay: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Compact hints passed to GPT so pair_explanations stay currency-specific."""
    hooks = (macro_overlay or {}).get("economy_hooks") or {}
    economy_hook = str(hooks.get((scan_country or "US").upper(), "") or "")
    if not economy_hook:
        economy_hook = str(macro_overlay.get("economy_hook") or "")
    hints: List[Dict[str, Any]] = []
    for row in pair_setups[:4]:
        pair = normalize_pair(row.get("pair") or "")
        if not pair:
            continue
        copy = build_pair_setup_copy(
            pair=pair,
            scan_country=scan_country,
            pair_bias=str(row.get("bias") or "neutral"),
            scan_short_bias="neutral",
            event_risk_score=0.0,
            sentiment_label="balanced",
            macro_overlay=macro_overlay,
            quality_overrides={},
            economy_hook=economy_hook,
        )
        hints.append(
            {
                "pair": pair,
                "required_tokens": list(PAIR_REQUIRED_TOKENS.get(pair, ())),
                "key_risk": copy["key_risk"],
                "deterministic_seed": copy["driver"][:240],
            }
        )
    return hints
