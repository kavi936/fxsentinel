#!/usr/bin/env python3
"""Tests for per-pair holistic scan commentary."""

import unittest

from services.economy_holistic_scan_service import EconomyHolisticScanService
from services.holistic_pair_commentary import (
    build_pair_setup_copy,
    driver_mentions_pair_currency,
    drivers_are_too_similar,
    pair_explanations_are_distinct,
)


def _indicator(values):
    return {"chartData": values}


class HolisticPairCommentaryTests(unittest.TestCase):
    def test_us_scan_pair_drivers_are_not_copy_paste(self):
        service = EconomyHolisticScanService()
        indicators = {
            "inflation": _indicator([2.0, 2.1, 2.0, 2.2, 2.3, 2.4]),
            "interest-rate": _indicator([4.5, 4.6, 4.55, 4.58, 4.6, 4.62]),
            "gdp-growth": _indicator([2.0, 2.1, 2.0, 2.05, 2.1, 2.15]),
            "unemployment": _indicator([4.0, 3.9, 3.95, 3.92, 3.9, 3.88]),
        }
        yields = {
            "US02Y": {"price": 4.5, "change": 0.02},
            "US10Y": {"price": 4.6, "change": 0.01},
            "US30Y": {"price": 4.7, "change": 0.0},
        }
        scan = service.build_scan(
            country_code="US",
            indicators=indicators,
            events=[],
            yields=yields,
        )
        setups = scan.get("pair_setups") or []
        self.assertGreaterEqual(len(setups), 3)
        drivers = [row["driver"] for row in setups]
        self.assertFalse(drivers_are_too_similar(drivers[0], drivers[1]))
        ok, _ = pair_explanations_are_distinct(setups)
        self.assertTrue(ok)

    def test_pair_specific_tokens_present(self):
        eurusd = build_pair_setup_copy(
            pair="EURUSD",
            scan_country="US",
            pair_bias="bearish",
            scan_short_bias="bearish",
            event_risk_score=50.0,
            sentiment_label="balanced",
            macro_overlay={},
            quality_overrides={},
        )
        usdjpy = build_pair_setup_copy(
            pair="USDJPY",
            scan_country="US",
            pair_bias="bullish",
            scan_short_bias="bearish",
            event_risk_score=50.0,
            sentiment_label="balanced",
            macro_overlay={},
            quality_overrides={},
        )
        self.assertTrue(driver_mentions_pair_currency("EURUSD", eurusd["driver"]))
        self.assertTrue(driver_mentions_pair_currency("USDJPY", usdjpy["driver"]))
        self.assertIn("BoJ", usdjpy["driver"])
        self.assertIn("ECB", eurusd["driver"])

    def test_gpt_validation_rejects_duplicate_drivers(self):
        service = EconomyHolisticScanService()
        generated = {
            "narrative": {
                "short_term": "Bearish short-term regime with energy risk scenarios possible.",
                "long_term": "Long-term neutral with mixed policy and growth offsets across horizons.",
                "fx": "FX transmission channels remain active across major USD crosses today.",
                "geopolitical_energy": "Geopolitical and energy risk remains elevated across importers.",
            },
            "pair_explanations": [
                {"pair": "EURUSD", "driver": "Same generic driver text for all pairs here.", "invalidation": "Invalid if yields flip."},
                {"pair": "USDJPY", "driver": "Same generic driver text for all pairs here.", "invalidation": "Invalid if yields flip."},
            ],
        }
        ok, errors = service._validate_holistic_narrative(generated, _sample_scan())
        self.assertFalse(ok)
        self.assertTrue(any("too_similar" in e for e in errors))


def _sample_scan():
    return {
        "short_term": {"bias": "bearish"},
        "pair_setups": [
            {"pair": "EURUSD"},
            {"pair": "USDJPY"},
        ],
    }


if __name__ == "__main__":
    unittest.main()
