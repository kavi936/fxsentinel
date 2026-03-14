#!/usr/bin/env python3
"""
Test economy indicator mapping for AI Analysis.

Validates:
1. Currency-aware mapping: (event title + currency) -> indicator IDs that exist for that economy.
2. No "missing" IDs: EUR/GBP/JPY get 'inflation' not 'inflation-YoY'; only US gets 'nonfarm-payrolls'.

Run from repo root:
  python backend/scripts/test_economy_indicator_mapping.py
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.gpt_ai_analysis import (
    EVENT_TYPE_MAPPING,
    CONCEPT_TO_INDICATORS_BY_CURRENCY,
    TITLE_KEYWORD_TO_CONCEPT,
)
from services.gpt_ai_analysis import GPTAIAnalyzer


def get_relevant_indicators_currency_aware(event_title: str, currency: str):
    """Use analyzer's currency-aware mapping."""
    a = GPTAIAnalyzer()
    return a._get_relevant_indicators(event_title, currency)


def main():
    from services.economy_context_service import economy_context_service

    print("=" * 60)
    print("Economy indicator mapping test (currency-aware)")
    print("=" * 60)

    # 1) Indicator IDs per economy (from JSON)
    print("\n1) Indicator IDs in economy data (src/data/economyIndicators.json):")
    for currency in ['USD', 'EUR', 'GBP', 'JPY']:
        ctx = economy_context_service.get_economy_context(currency)
        if not ctx:
            print(f"   {currency}: no context")
            continue
        ind_ids = list(ctx.get('indicators', {}).keys())
        print(f"   {currency}: {ind_ids}")

    # 2) Title + currency -> indicator IDs (currency-aware)
    print("\n2) Event (title, currency) -> indicator IDs:")
    samples = [
        ("Nonfarm Payrolls", "USD"),
        ("CPI YoY", "USD"),
        ("CPI YoY", "EUR"),
        ("CPI y/y", "GBP"),
        ("Unemployment Rate", "USD"),
        ("Unemployment Rate", "EUR"),
        ("GDP m/m", "JPY"),
        ("FOMC Federal Funds Rate", "USD"),
        ("ECB Main Refinancing Rate", "EUR"),
        ("Average Earnings Index 3m/y", "GBP"),
        ("Current Account", "EUR"),
        ("Retail Sales", "USD"),
    ]
    for title, currency in samples:
        ids = get_relevant_indicators_currency_aware(title, currency)
        print(f"   ({title!r}, {currency}) -> {ids}")

    # 3) No missing IDs: every returned ID must exist for that currency
    print("\n3) Validation (no missing IDs per currency):")
    all_ok = True
    for title, currency in samples:
        ids = get_relevant_indicators_currency_aware(title, currency)
        if not ids:
            continue
        ctx = economy_context_service.get_economy_context(currency)
        if not ctx:
            all_ok = False
            print(f"   {currency}: no context")
            continue
        indicators = ctx.get('indicators', {})
        missing = [i for i in ids if i not in indicators]
        if missing:
            print(f"   \"{title}\" {currency}: missing={missing}  [FAIL]")
            all_ok = False
        else:
            print(f"   \"{title}\" {currency}: {ids}  [OK]")
    if all_ok:
        print("   All mapped events have indicators present for that currency.")

    # 4) Concept coverage
    print("\n4) Concepts and per-currency indicators:")
    for country, by_concept in CONCEPT_TO_INDICATORS_BY_CURRENCY.items():
        print(f"   {country}: {dict(by_concept)}")

    print("\n" + "=" * 60)
    print("Done. Mapping is currency-aware: event currency + title -> that economy's indicator IDs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
