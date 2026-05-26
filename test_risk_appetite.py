#!/usr/bin/env python3
"""
Unit tests for composite Risk Appetite (multi-factor macro index).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from services.market_sentiment_service import MarketSentimentService


def test_risk_appetite_scenario(name, quotes, expected_level, expected_percentage_range, vix_data=None):
    print(f"\n{'=' * 60}")
    print(f"TEST: {name}")
    print(f"{'=' * 60}")

    service = MarketSentimentService()
    result = service._calculate_risk_appetite(quotes, vix_data)

    print(f"Result: level={result['level']}, pct={result['percentage']:.1f}")
    print(f"  detail: {result.get('detail_macro', '')}")

    level_match = result["level"] == expected_level
    pct = result["percentage"]
    percentage_match = expected_percentage_range[0] <= pct <= expected_percentage_range[1]

    if level_match and percentage_match:
        print("✅ PASS")
        return True

    print("❌ FAIL")
    if not level_match:
        print(f"   Expected level {expected_level}, got {result['level']}")
    if not percentage_match:
        print(f"   Expected pct in {expected_percentage_range}, got {pct:.1f}")
    return False


def main():
    print("=" * 60)
    print("COMPOSITE RISK APPETITE TESTS")
    print("=" * 60)

    passed = 0
    total = 0

    # Broad risk-off: havens, equities, vol, gold
    total += 1
    if test_risk_appetite_scenario(
        "Broad risk-off",
        {
            "USDJPY": {"price": 150.0, "changePercent": -0.40},
            "USDCHF": {"price": 0.88, "changePercent": -0.35},
            "SPX": {"price": 5000.0, "changePercent": -1.2},
            "IXIC": {"price": 16000.0, "changePercent": -1.5},
            "VIX": {"price": 22.0, "changePercent": 8.0},
            "GOLD": {"price": 2400.0, "changePercent": 0.5},
            "AUDUSD": {"price": 0.66, "changePercent": -0.35},
            "USDCAD": {"price": 1.36, "changePercent": 0.25},
        },
        "low",
        (0, 40),
    ):
        passed += 1

    # Broad risk-on
    total += 1
    if test_risk_appetite_scenario(
        "Broad risk-on",
        {
            "USDJPY": {"price": 151.0, "changePercent": 0.35},
            "USDCHF": {"price": 0.89, "changePercent": 0.28},
            "SPX": {"price": 5100.0, "changePercent": 0.9},
            "IXIC": {"price": 16500.0, "changePercent": 1.1},
            "VIX": {"price": 14.0, "changePercent": -5.0},
            "GOLD": {"price": 2350.0, "changePercent": -0.4},
            "USOIL": {"price": 75.0, "changePercent": 1.0},
            "AUDUSD": {"price": 0.67, "changePercent": 0.45},
            "NZDUSD": {"price": 0.61, "changePercent": 0.40},
            "USDCAD": {"price": 1.35, "changePercent": -0.30},
            "BTCUSDT": {"price": 65000.0, "changePercent": 2.5},
        },
        "high",
        (62, 100),
    ):
        passed += 1

    # Quiet / mixed — should sit near neutral (~50), not 100
    total += 1
    if test_risk_appetite_scenario(
        "Quiet FX (no false 100%)",
        {
            "USDJPY": {"price": 150.0, "changePercent": 0.02},
            "USDCHF": {"price": 0.88, "changePercent": -0.01},
            "EURUSD": {"price": 1.08, "changePercent": 0.03},
        },
        "medium",
        (42, 58),
    ):
        passed += 1

    # Flight to quality: equities down + yields down
    total += 1
    if test_risk_appetite_scenario(
        "Flight to quality (eq down, yields down)",
        {
            "USDJPY": {"price": 149.0, "changePercent": -0.25},
            "USDCHF": {"price": 0.87, "changePercent": -0.20},
            "SPX": {"price": 4900.0, "changePercent": -0.7},
            "US10Y": {"price": 4.2, "changePercent": -0.06},
            "GOLD": {"price": 2420.0, "changePercent": 0.35},
        },
        "low",
        (8, 48),
    ):
        passed += 1

    # Missing changePercent fallback
    total += 1
    if test_risk_appetite_scenario(
        "change/price fallback",
        {
            "USDJPY": {"price": 150.0, "change": -0.525},
            "USDCHF": {"price": 0.88, "change": -0.00264},
            "SPX": {"price": 5000.0, "changePercent": -0.8},
        },
        "low",
        (0, 45),
    ):
        passed += 1

    # Sparse quotes — renormalized pillars, neutral-ish
    total += 1
    if test_risk_appetite_scenario(
        "Sparse quotes",
        {"EURUSD": {"price": 1.08, "changePercent": 0.05}, "GBPUSD": {"price": 1.27, "changePercent": 0.04}},
        "medium",
        (45, 55),
    ):
        passed += 1

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {passed}/{total} passed")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
