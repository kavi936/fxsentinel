#!/usr/bin/env python3
"""Tests for Phase H holistic GPT narrative enrichment."""

import os
import unittest
from unittest.mock import patch

from services.economy_holistic_scan_service import EconomyHolisticScanService


def _sample_scan() -> dict:
    return {
        "country": "US",
        "economy": "United States",
        "timestamp": "2026-05-27T10:00:00",
        "short_term": {"bias": "bearish", "score": -22.0, "confidence": 76},
        "long_term": {"bias": "neutral", "score": 3.5, "confidence": 64},
        "event_flags": {"calendar_stress_score": 80},
        "yield_context": {"investor_sentiment": "balanced"},
        "trader_brief": {"short_term_line": "Bearish regime"},
        "highlights": {},
        "pair_setups": [
            {"pair": "EURUSD", "driver": "old", "invalidation": "old"},
            {"pair": "USDJPY", "driver": "old", "invalidation": "old"},
        ],
        "narrative": {
            "short_term": "old short term narrative baseline",
            "long_term": "old long term narrative baseline",
            "fx": "old fx narrative baseline",
            "geopolitical_energy": "old geo baseline",
        },
    }


def _generated() -> dict:
    return {
        "narrative": {
            "short_term": "Latest economy scan remains bearish short-term, while scenario upside exists on a surprise.",
            "long_term": "Longer horizon remains mixed with neutral baseline as growth and policy offset.",
            "fx": "FX transmission favors quote-side pressure if USD weakens and yield repricing follows through.",
            "geopolitical_energy": "Geopolitical and energy risk remains elevated and can amplify volatility.",
        },
        "pair_explanations": [
            {"pair": "EURUSD", "driver": "USD downside supports EURUSD upside.", "invalidation": "Invalid if yields reprice hawkishly."},
            {"pair": "USDJPY", "driver": "USD softness pressures USDJPY lower if risk remains stable.", "invalidation": "Invalid if haven demand spikes."},
        ],
    }


class HolisticGPTNarrativeTests(unittest.TestCase):
    def setUp(self):
        self.service = EconomyHolisticScanService()

    def test_holistic_prompt_requests_emphasis_markers(self):
        payload = self.service._build_holistic_narrative_prompt_payload(_sample_scan(), "US")
        prompt = self.service._create_holistic_narrative_prompt(payload)
        self.assertIn("**double asterisks**", prompt)
        self.assertIn("may contain **", prompt)

    def test_holistic_prompt_includes_curated_overlay_rules(self):
        scan = _sample_scan()
        scan["curated_macro_overlay"] = {
            "version": "1.1.0",
            "global_themes": [{"id": "test", "title": "Test theme", "severity": "critical"}],
            "economy_hook": "US hook",
        }
        prompt = self.service._create_holistic_narrative_prompt(
            self.service._build_holistic_narrative_prompt_payload(scan, "US")
        )
        self.assertIn("curated_macro_overlay", prompt)
        self.assertIn("editorial floor", prompt.lower())

    def test_macro_theme_highlights_from_overlay_file(self):
        overlay = self.service._load_holistic_overlay()
        themes = overlay.get("global_themes") or []
        if len(themes) < 2:
            self.skipTest("overlay needs multiple global_themes")
        items = self.service._macro_theme_highlight_items(overlay, "US")
        self.assertEqual(len(items), len(themes))
        self.assertEqual(items[0]["id"], "geopolitical_energy")
        self.assertTrue(str(items[1]["id"]).startswith("macro_theme_"))
        curated = self.service._build_curated_macro_overlay(overlay, "US")
        self.assertEqual(len(curated["theme_digest"]), len(themes))
        self.assertEqual(curated["geo_severity"], str(themes[0].get("severity", "watch")).upper())

    def test_validate_generated_payload_passes(self):
        ok, errors = self.service._validate_holistic_narrative(_generated(), _sample_scan())
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_validate_contradiction_fails(self):
        bad = _generated()
        bad["narrative"]["short_term"] = "The baseline is clearly bullish and strongly trending."
        ok, errors = self.service._validate_holistic_narrative(bad, _sample_scan())
        self.assertFalse(ok)
        self.assertTrue(any("contradiction" in e for e in errors))

    def test_merge_updates_only_narrative_and_pair_explanations(self):
        scan = _sample_scan()
        merged = self.service._merge_holistic_narrative(scan, _generated())
        self.assertIn("bearish short-term", merged["narrative"]["short_term"])
        self.assertNotEqual(merged["pair_setups"][0]["driver"], "old")
        self.assertEqual(merged["short_term"]["bias"], "bearish")
        self.assertEqual(merged["short_term"]["score"], -22.0)

    @patch.object(EconomyHolisticScanService, "_generate_holistic_narrative_with_gpt")
    @patch.object(EconomyHolisticScanService, "_build_narrative")
    @patch.object(EconomyHolisticScanService, "_build_pair_setups")
    @patch.object(EconomyHolisticScanService, "_build_highlights")
    @patch.object(EconomyHolisticScanService, "_build_trader_brief")
    @patch.object(EconomyHolisticScanService, "_build_event_flags")
    @patch.object(EconomyHolisticScanService, "_build_trading_ranges")
    @patch.object(EconomyHolisticScanService, "_build_yield_context")
    @patch.object(EconomyHolisticScanService, "_build_short_components")
    @patch.object(EconomyHolisticScanService, "_build_long_components")
    @patch.object(EconomyHolisticScanService, "_load_holistic_overlay")
    @patch.object(EconomyHolisticScanService, "_load_central_bank_snippets")
    @patch.object(EconomyHolisticScanService, "_map_fx_pairs")
    def test_build_scan_fallback_metadata_on_gpt_error(
        self,
        mock_map_pairs,
        mock_cb,
        mock_overlay,
        mock_long,
        mock_short,
        mock_yield,
        mock_ranges,
        mock_flags,
        mock_brief,
        mock_highlights,
        mock_pair_setups,
        mock_narrative,
        mock_gpt,
    ):
        prev_enabled = os.environ.get("HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED")
        prev_api = os.environ.get("OPENAI_API_KEY")
        os.environ["HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED"] = "true"
        os.environ["OPENAI_API_KEY"] = "test-key"
        try:
            mock_overlay.return_value = {}
            mock_cb.return_value = {"bank": "FED", "snippets": []}
            mock_short.return_value = []
            mock_long.return_value = []
            mock_yield.return_value = {"investor_sentiment": "balanced", "source": "test"}
            mock_ranges.return_value = {}
            mock_flags.return_value = {"calendar_stress_score": 80}
            mock_brief.return_value = {"short_term_line": "x"}
            mock_highlights.return_value = {}
            mock_pair_setups.return_value = [{"pair": "EURUSD", "driver": "old", "invalidation": "old"}]
            mock_narrative.return_value = {
                "short_term": "old narrative",
                "long_term": "old narrative",
                "fx": "old narrative",
                "geopolitical_energy": "old narrative",
                "central_bank_context": "old narrative",
            }
            mock_map_pairs.return_value = [{"pair": "EURUSD", "bias": "bullish", "strength": "light"}]
            mock_gpt.return_value = {"ok": False, "error": "rate_limited", "model_used": "gpt-4o-mini", "cost_estimate": 0.0}

            scan = self.service.build_scan(
                country_code="US",
                indicators={},
                events=[],
                yields={},
                personalization={},
                user_info={"user_id": "u1"},
            )
            self.assertEqual(scan["narrative_source"], "deterministic_fallback")
            self.assertEqual(scan["narrative_validation"], "failed")
        finally:
            if prev_enabled is None:
                os.environ.pop("HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED", None)
            else:
                os.environ["HOLISTIC_SCAN_GPT_NARRATIVE_ENABLED"] = prev_enabled
            if prev_api is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = prev_api


if __name__ == "__main__":
    unittest.main()

