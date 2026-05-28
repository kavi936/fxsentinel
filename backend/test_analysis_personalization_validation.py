#!/usr/bin/env python3
"""Tests for post-parse personalization validators."""

import unittest

from services.analysis_personalization_validation import (
    apply_personalization_to_response,
    normalize_pair,
    validate_and_enforce_calendar,
    validate_and_enforce_news,
    validate_holistic_scan,
)
from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
)


class TestNormalizePair(unittest.TestCase):
    def test_slash_and_compact(self):
        self.assertEqual(normalize_pair("eur/usd"), "EURUSD")
        self.assertEqual(normalize_pair("EURUSD"), "EURUSD")


class TestCalendarPersonalization(unittest.TestCase):
    def test_reorders_trading_plan_pairs(self):
        payload = {
            "headline": "US CPI",
            "big_picture": {"summary": "Multi-week USD trend depends on inflation path."},
            "trading_plan": {"pairs": ["USD/JPY", "EUR/USD", "GBP/USD"]},
            "market_reaction": {"notes": "Watch London session trigger near 1.0850."},
        }
        personalization = {
            "profile_available": True,
            "trading_style": "both",
            "primary_pairs": ["EURUSD"],
        }
        out, meta = validate_and_enforce_calendar(payload, personalization)
        self.assertEqual(out["trading_plan"]["pairs"][0], "EUR/USD")
        self.assertIn("reordered_trading_plan.pairs", meta["enforcement_actions"])
        self.assertGreaterEqual(meta["compliance_score"], 50)

    def test_swing_check_fails_without_horizon_keywords(self):
        payload = {
            "headline": "GDP",
            "big_picture": {"summary": "Growth is steady."},
            "trading_plan": {},
            "market_reaction": {},
        }
        personalization = {
            "profile_available": True,
            "trading_style": "swing",
            "primary_pairs": [],
        }
        _, meta = validate_and_enforce_calendar(payload, personalization)
        swing_checks = [c for c in meta["checks"] if c["id"] == "swing_horizon_framing"]
        self.assertEqual(len(swing_checks), 1)
        self.assertFalse(swing_checks[0]["passed"])


class TestNewsPersonalization(unittest.TestCase):
    def test_reorders_key_pairs(self):
        payload = {
            "news_impact": "EUR moves on ECB headlines.",
            "trading_implications": "If EUR/USD breaks 1.09, watch follow-through over the next 2-4 hours.",
            "key_pairs": ["USD/JPY", "EUR/USD"],
            "timeframe": "next 2-4 hours",
        }
        personalization = {
            "profile_available": True,
            "trading_style": "day",
            "primary_pairs": ["EURUSD"],
        }
        out, meta = validate_and_enforce_news(payload, personalization)
        self.assertEqual(out["key_pairs"][0], "EUR/USD")
        self.assertIn("reordered_key_pairs", meta["enforcement_actions"])


class TestHolisticPersonalization(unittest.TestCase):
    def test_reorders_pair_setups(self):
        scan = {
            "narrative": {
                "short_term": "Session trigger at 1.0850 invalidates below 1.0820.",
                "long_term": "Multi-week EUR bias stays data-dependent.",
            },
            "pair_setups": [
                {"pair": "USD/JPY", "bias": "neutral"},
                {"pair": "EUR/USD", "bias": "bullish"},
            ],
        }
        personalization = {
            "profile_available": True,
            "trading_style": "both",
            "primary_pairs": ["EURUSD"],
        }
        out, meta = validate_holistic_scan(scan, personalization)
        self.assertEqual(out["pair_setups"][0]["pair"], "EUR/USD")
        self.assertIn("reordered_pair_setups", meta["enforcement_actions"])


class TestApplyToResponse(unittest.TestCase):
    def test_attach_metadata_on_calendar_kind(self):
        payload = {"headline": "NFP", "big_picture": {"summary": "Multi-week labor trend."}}
        personalization = {"profile_available": True, "trading_style": "swing", "primary_pairs": []}
        out = apply_personalization_to_response(
            payload,
            ANALYSIS_KIND_CALENDAR_EVENT,
            personalization,
        )
        self.assertIn("personalization_applied", out)
        self.assertEqual(out["personalization_applied"]["surface"], "economic_calendar")

    def test_economy_scan_wraps_scan(self):
        payload = {
            "status": "success",
            "scan": {
                "narrative": {"long_term": "Multi-week regime.", "short_term": "Trigger at London open."},
                "pair_setups": [],
            },
        }
        personalization = {"profile_available": True, "trading_style": "both", "primary_pairs": ["EURUSD"]}
        out = apply_personalization_to_response(
            payload,
            ANALYSIS_KIND_ECONOMY_SCAN,
            personalization,
        )
        self.assertIn("personalization_applied", out)
        self.assertEqual(out["personalization_applied"]["surface"], "holistic_scan")

    def test_live_news_kind(self):
        payload = {
            "news_impact": "Gold volatility rises.",
            "trading_implications": "Watch XAU/USD over the next session.",
            "key_pairs": ["XAU/USD"],
            "timeframe": "London session",
        }
        personalization = {"profile_available": True, "trading_style": "day", "primary_pairs": ["XAUUSD"]}
        out = apply_personalization_to_response(payload, ANALYSIS_KIND_LIVE_NEWS, personalization)
        self.assertIn("personalization_applied", out)


if __name__ == "__main__":
    unittest.main()
