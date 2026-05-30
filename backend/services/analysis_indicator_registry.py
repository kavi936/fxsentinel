#!/usr/bin/env python3
"""
Indicator catalog + event → single best chart for calendar analysis context.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Keys match src/data/economyIndicators.json top-level economies
SUPPORTED_ECONOMIES = frozenset({"US", "EUR", "GBP", "JPY"})

ECONOMY_TO_CURRENCY: Dict[str, str] = {
    "US": "USD",
    "EUR": "EUR",
    "GBP": "GBP",
    "JPY": "JPY",
}

ECONOMY_INDICATOR_IDS: Dict[str, List[str]] = {
    "US": [
        "interest-rate",
        "inflation-YoY",
        "core-inflation-YoY",
        "gdp-growth",
        "unemployment",
        "nonfarm-payrolls",
    ],
    "EUR": [
        "interest-rate",
        "inflation",
        "core-inflation-YoY",
        "gdp-growth",
        "unemployment",
        "current-account",
    ],
    "GBP": [
        "interest-rate",
        "inflation",
        "core-inflation-YoY",
        "gdp-growth",
        "unemployment",
        "wage-growth",
    ],
    "JPY": [
        "interest-rate",
        "inflation",
        "core-inflation-YoY",
        "gdp-growth",
        "unemployment",
        "current-account",
    ],
}

INDICATOR_TITLES: Dict[str, str] = {
    "interest-rate": "Policy rate",
    "inflation-YoY": "CPI (YoY)",
    "core-inflation-YoY": "Core inflation (YoY)",
    "inflation": "Inflation (YoY)",
    "gdp-growth": "GDP growth",
    "unemployment": "Unemployment rate",
    "nonfarm-payrolls": "Non-farm payrolls",
    "current-account": "Current account",
    "wage-growth": "Wage growth",
}

INFLATION_INDICATOR_IDS = frozenset(
    {"inflation-YoY", "core-inflation-YoY", "inflation"}
)

# Aliases on calendar events → economyIndicators.json keys
COUNTRY_ALIASES: Dict[str, str] = {
    "US": "US",
    "USA": "US",
    "USD": "US",
    "EU": "EUR",
    "EUR": "EUR",
    "EZ": "EUR",
    "GB": "GBP",
    "UK": "GBP",
    "GBP": "GBP",
    "JP": "JPY",
    "JPY": "JPY",
}

# (indicator_id, keyword phrases) — first match wins; IDs must exist for that economy
_PICK_RULES: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {
    "US": [
        ("core-inflation-YoY", ("core pce", "core cpi", "core inflation")),
        ("inflation-YoY", ("cpi", "inflation", "pce")),
        ("nonfarm-payrolls", ("nonfarm payroll", "nonfarm payrolls", "nfp", "payrolls")),
        ("unemployment", ("unemployment rate", "jobless claims", "unemployment")),
        ("gdp-growth", ("gdp",)),
        ("interest-rate", ("fomc", "fed rate", "fund rate", "rate decision", "interest rate")),
    ],
    "EUR": [
        ("core-inflation-YoY", ("core inflation", "core cpi", "core hicp")),
        ("inflation", ("cpi", "hicp", "inflation", "pce")),
        ("unemployment", ("unemployment",)),
        ("gdp-growth", ("gdp",)),
        ("current-account", ("current account", "trade balance")),
        ("interest-rate", ("ecb", "refinancing rate", "rate decision", "deposit rate")),
    ],
    "GBP": [
        ("core-inflation-YoY", ("core cpi", "core inflation")),
        ("inflation", ("cpi", "inflation")),
        ("wage-growth", ("wage growth", "average earnings", "earnings index")),
        ("unemployment", ("unemployment", "claimant count")),
        ("gdp-growth", ("gdp",)),
        ("interest-rate", ("boe", "bank rate", "rate decision", "interest rate")),
    ],
    "JPY": [
        ("core-inflation-YoY", ("core cpi", "core inflation")),
        ("inflation", ("cpi", "inflation")),
        ("unemployment", ("unemployment",)),
        ("gdp-growth", ("gdp",)),
        ("current-account", ("current account", "trade balance")),
        ("interest-rate", ("boj", "policy rate", "rate decision", "interest rate")),
    ],
}


def resolve_economy_key(
    country_code: Optional[str] = None,
    currency: Optional[str] = None,
) -> Optional[str]:
    """Map event country/currency to economyIndicators.json key."""
    for raw in (country_code, currency):
        if not raw:
            continue
        key = str(raw).strip().upper()
        if key in COUNTRY_ALIASES:
            resolved = COUNTRY_ALIASES[key]
            if resolved in SUPPORTED_ECONOMIES:
                return resolved
    return None


def list_indicators_for_economy(economy: str) -> List[str]:
    return list(ECONOMY_INDICATOR_IDS.get((economy or "").upper(), []))


def pick_best_indicator_for_event(economy: str, event_title: str) -> Optional[str]:
    """Pick the single most relevant indicator for this release title."""
    eco = (economy or "").upper()
    allowed = set(list_indicators_for_economy(eco))
    if not allowed:
        return None

    title = str(event_title or "").lower()
    for ind_id, keywords in _PICK_RULES.get(eco, []):
        if ind_id not in allowed:
            continue
        if any(kw in title for kw in keywords):
            return ind_id

    # Generic fallbacks when title is vague
    if "interest-rate" in allowed and any(
        kw in title for kw in ("rate", "central bank", "monetary")
    ):
        return "interest-rate"
    if "gdp-growth" in allowed and "growth" in title:
        return "gdp-growth"

    return list(allowed)[0]
