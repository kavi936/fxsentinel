"""
Canonical calendar market scenarios (Phase 3).

Single source of truth for:
  - Event direction (higher print bullish vs bearish for event currency)
  - Market Scenarios table rows (above / on forecast / below)
  - Mapping GPT forward_scenarios keys (bullish/bearish/neutral) to outcomes
  - Alignment validation vs scenario prose

Ported from Overview.jsx getEventDirectionMapping + calculateMarketScenarios.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# forward_scenarios keys always describe surprise paths, not currency labels:
#   bullish  -> above consensus
#   bearish  -> below consensus
#   neutral  -> on consensus
FORWARD_KEY_TO_OUTCOME = {
    "bullish": "above",
    "bearish": "below",
    "neutral": "on_forecast",
}


def parse_numeric_value(value: Any) -> Optional[float]:
    if value is None or value == "" or value == "N/A":
        return None
    cleaned = re.sub(r"[^\d.-]", "", str(value))
    if not cleaned:
        return None
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    return None if parsed != parsed else parsed  # NaN guard


def format_value_with_unit(value: float, original_expected: Any) -> str:
    original = str(original_expected or "")
    if not original or original == "N/A":
        return str(value)
    has_percent = "%" in original
    unit_match = re.search(r"[KMkmBb]", original)
    unit = unit_match.group(0).upper() if unit_match else ""
    formatted = round(value * 100) / 100
    if has_percent:
        return f"{formatted}%"
    if unit:
        return f"{formatted}{unit}"
    return str(formatted)


def get_event_direction_mapping(event_title: str) -> Dict[str, Any]:
    """
    Returns { higher_is_bullish_for_currency: bool, event_type: str }.
    Matches Overview.jsx getEventDirectionMapping.
    """
    if not event_title:
        return {"higher_is_bullish_for_currency": True, "event_type": "unknown"}

    t = event_title.lower()

    if any(
        x in t
        for x in (
            "unemployment",
            "jobless",
            "jobless claims",
            "initial claims",
            "continuing claims",
            "unemployment rate",
            "unemployment claims",
        )
    ):
        return {"higher_is_bullish_for_currency": False, "event_type": "unemployment"}

    if any(
        x in t
        for x in (
            "wage",
            "average earnings",
            "earnings growth",
            "hourly earnings",
            "wage growth",
        )
    ):
        return {"higher_is_bullish_for_currency": False, "event_type": "wages"}

    if any(
        x in t
        for x in (
            "cpi",
            "consumer price index",
            "consumer price",
            "inflation",
            "ppi",
            "producer price index",
            "producer price",
            "core inflation",
            "core cpi",
        )
    ):
        return {"higher_is_bullish_for_currency": False, "event_type": "inflation"}

    if any(
        x in t
        for x in (
            "non-farm payrolls",
            "nonfarm payrolls",
            "nfp",
            "adp employment",
            "adp payrolls",
            "payrolls",
            "employment change",
            "employment rate",
            "job creation",
            "jobs created",
        )
    ) or ("employment" in t and "unemployment" not in t):
        return {"higher_is_bullish_for_currency": True, "event_type": "employment"}

    if any(
        x in t
        for x in (
            "interest rate",
            "rate decision",
            "fed rate",
            "ecb rate",
            "boe rate",
            "boj rate",
            "rba rate",
            "boc rate",
            "snb rate",
            "rbnz rate",
            "cash rate",
            "policy rate",
            "monetary policy",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "interest_rate"}

    if any(
        x in t
        for x in (
            "gdp",
            "gross domestic product",
            "economic growth",
            "gdp growth",
            "gdp qoq",
            "gdp yoy",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "gdp"}

    if any(
        x in t
        for x in (
            "trade balance",
            "trade surplus",
            "trade deficit",
            "current account",
            "balance of trade",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "trade_balance"}

    if any(
        x in t
        for x in ("retail sales", "consumer spending", "retail trade")
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "retail_sales"}

    if any(
        x in t
        for x in (
            "manufacturing",
            "industrial production",
            "factory orders",
            "durable goods",
            "industrial output",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "manufacturing"}

    if any(
        x in t
        for x in ("pmi", "purchasing managers index", "purchasing managers")
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "pmi"}

    if any(
        x in t
        for x in (
            "home sales",
            "housing starts",
            "building permits",
            "new home sales",
            "existing home sales",
            "house price",
            "housing market",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "housing"}

    if any(
        x in t
        for x in (
            "consumer confidence",
            "consumer sentiment",
            "business confidence",
            "business sentiment",
            "sentiment index",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "confidence"}

    if any(
        x in t
        for x in (
            "budget balance",
            "budget surplus",
            "budget deficit",
            "government budget",
        )
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "budget"}

    if any(
        x in t
        for x in ("business inventories", "inventory", "stockpiles")
    ):
        return {"higher_is_bullish_for_currency": False, "event_type": "inventories"}

    if any(
        x in t
        for x in ("personal income", "personal spending", "personal consumption")
    ):
        return {"higher_is_bullish_for_currency": True, "event_type": "personal"}

    return {"higher_is_bullish_for_currency": True, "event_type": "default"}


def _row(value: str, sentiment: str) -> Dict[str, str]:
    sl = sentiment.lower()
    if sl == "ranging":
        sentiment_class = "ranging"
    elif "bearish" in sl:
        sentiment_class = "bearish"
    else:
        sentiment_class = "bullish"
    return {
        "value": value,
        "sentiment": sentiment,
        "sentiment_class": sentiment_class,
        "ccy_bias": sentiment_class if sentiment_class != "ranging" else "neutral",
    }


def build_market_scenarios(
    *,
    event_title: str,
    currency: str,
    expected: Any,
    expected_display: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build canonical market scenarios table. Returns None if expected is not parseable.
    """
    numeric = parse_numeric_value(expected)
    if numeric is None:
        return None

    mapping = get_event_direction_mapping(event_title)
    higher = bool(mapping["higher_is_bullish_for_currency"])
    display = expected_display if expected_display not in (None, "", "N/A") else expected
    forecast_value = format_value_with_unit(numeric, display)

    if higher:
        above_row = _row(f">{forecast_value}", "Bullish")
        below_row = _row(f"<{forecast_value}", "Bearish")
    else:
        above_row = _row(f">{forecast_value}", "Bearish")
        below_row = _row(f"<{forecast_value}", "Bullish")

    on_row = _row(forecast_value, "Ranging")

    return {
        "currency": (currency or "USD").upper(),
        "event_type": mapping["event_type"],
        "higher_is_bullish_for_currency": higher,
        "expected_numeric": numeric,
        "expected_display": str(display or forecast_value),
        "forward_key_to_outcome": dict(FORWARD_KEY_TO_OUTCOME),
        "rows": {
            "above": [above_row],
            "on_forecast": [on_row],
            "below": [below_row],
        },
    }


def forward_scenarios_by_outcome(
    forward_scenarios: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """Re-key GPT forward_scenarios to above / on_forecast / below."""
    fs = forward_scenarios or {}
    return {
        "above": str(fs.get("bullish") or ""),
        "on_forecast": str(fs.get("neutral") or ""),
        "below": str(fs.get("bearish") or ""),
    }


def expected_ccy_bias_for_outcome(
    market_scenarios: Dict[str, Any],
    outcome: str,
) -> Optional[str]:
    rows = (market_scenarios.get("rows") or {}).get(outcome) or []
    if not rows:
        return None
    return str(rows[0].get("ccy_bias") or "").lower() or None


def _text_implies_ccy_bullish(text: str, currency: str) -> Optional[bool]:
    if not text:
        return None
    cur = (currency or "USD").upper()
    if cur != "USD":
        return None
    if re.search(
        r"USD\s+(strengthens|surge|strong|rally|higher|bullish)",
        text,
        re.I,
    ) or re.search(
        r"(dollar|greenback)\s+(strengthens|strong|rally|surge)",
        text,
        re.I,
    ):
        return True
    if re.search(
        r"USD\s+(weakens|weak|fall|drop|lower|bearish)",
        text,
        re.I,
    ) or re.search(
        r"(dollar|greenback)\s+(weakens|weak|fall|drop)",
        text,
        re.I,
    ):
        return False
    return None


def calendar_scenario_alignment_warnings(
    event_title: str,
    currency: str,
    forward_scenarios: Optional[Dict[str, Any]],
    market_scenarios: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Compare each forward_scenarios bucket (mapped to an outcome) against
    canonical ccy bias for that outcome.
    """
    warnings: List[str] = []
    ms = market_scenarios or build_market_scenarios(
        event_title=event_title,
        currency=currency,
        expected=None,
    )
    if not ms:
        return _legacy_inflation_usd_warning(event_title, currency, forward_scenarios)

    fs = forward_scenarios or {}
    cur = (currency or "USD").upper()

    for fkey, outcome in FORWARD_KEY_TO_OUTCOME.items():
        text = str(fs.get(fkey) or "")
        if not text.strip():
            continue
        expected_bias = expected_ccy_bias_for_outcome(ms, outcome)
        if expected_bias not in ("bullish", "bearish"):
            continue
        implied = _text_implies_ccy_bullish(text, cur)
        if implied is None:
            continue
        implied_bias = "bullish" if implied else "bearish"
        if implied_bias != expected_bias:
            outcome_label = outcome.replace("_", " ")
            warnings.append(
                f"The '{fkey}' scenario ({outcome_label}) prose implies {cur} "
                f"{implied_bias}, but the canonical table labels that outcome as "
                f"{expected_bias.capitalize()} for {cur}. Use outcome-aligned copy or "
                f"see forward_scenarios_by_outcome."
            )
    return warnings


def _legacy_inflation_usd_warning(
    event_title: str,
    currency: str,
    forward_scenarios: Optional[Dict[str, Any]],
) -> List[str]:
    """Fallback when expected value missing — keep CPI/USD hot-print check."""
    mapping = get_event_direction_mapping(event_title)
    if mapping["higher_is_bullish_for_currency"] is not False:
        return []
    if (currency or "").upper() != "USD":
        return []
    fs = forward_scenarios or {}
    text = str(fs.get("bullish") or "")
    implied = _text_implies_ccy_bullish(text, "USD")
    if implied is True:
        return [
            "Scenario copy may disagree with the Market Scenarios table for this event type: "
            "above-consensus prints are bearish for USD in the canonical table, while the "
            "bullish scenario text implies USD strength."
        ]
    return []


def attach_canonical_calendar_scenarios(
    payload: Dict[str, Any],
    *,
    event_title: str,
    currency: str,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Add market_scenarios + forward_scenarios_by_outcome. Returns (payload, market_scenarios)."""
    out = dict(payload)
    es = out.get("event_summary") or {}
    expected = es.get("expected")
    if expected is None or expected == "N/A":
        expected = es.get("forecast") or es.get("consensus")

    ms = build_market_scenarios(
        event_title=event_title,
        currency=currency,
        expected=expected,
        expected_display=es.get("expected"),
    )
    if ms:
        out["market_scenarios"] = ms
        fs = out.get("forward_scenarios")
        if isinstance(fs, dict):
            out["forward_scenarios_by_outcome"] = forward_scenarios_by_outcome(fs)
    return out, ms
