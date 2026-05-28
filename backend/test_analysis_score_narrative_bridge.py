#!/usr/bin/env python3
"""Tests for holistic score ↔ narrative bridge (#10)."""

import unittest

from services.analysis_score_narrative_bridge import (
    apply_score_narrative_bridge_to_scan,
    build_score_bridge_sentence,
    has_score_bridge_language,
    requires_score_bridge,
    validate_score_bridge_in_generated,
)


def _scan_with_breakdown() -> dict:
    return {
        "short_term": {
            "score": -16,
            "display_bias": "NEUTRAL · BEARISH LEAN",
            "position_label": "Neutral band, bearish lean",
            "component_breakdown": {
                "drivers": [
                    {
                        "name": "Rate momentum",
                        "contribution": 8.5,
                        "contribution_display": "+8.5",
                        "available": True,
                    },
                    {
                        "name": "Event risk",
                        "contribution": -12.0,
                        "contribution_display": "-12.0",
                        "available": True,
                    },
                    {
                        "name": "Inflation momentum",
                        "contribution": -4.2,
                        "contribution_display": "-4.2",
                        "available": True,
                    },
                ]
            },
        },
        "curated_macro_overlay": {
            "geo_severity": "CRITICAL",
            "global_themes": [{"title": "Strait of Hormuz closure"}],
        },
        "narrative": {"geopolitical_energy": "Oil shock risk remains acute."},
        "highlights": {"items": [{"id": "geopolitical_energy", "label": "Geo", "emphasis": "CRITICAL", "detail": "x"}]},
    }


class ScoreNarrativeBridgeTests(unittest.TestCase):
    def test_requires_score_bridge_only_critical_elevated(self):
        self.assertTrue(requires_score_bridge("CRITICAL"))
        self.assertTrue(requires_score_bridge("elevated"))
        self.assertFalse(requires_score_bridge("WATCH"))

    def test_build_score_bridge_sentence_mentions_drivers(self):
        sentence = build_score_bridge_sentence(_scan_with_breakdown())
        self.assertIsNotNone(sentence)
        assert sentence is not None
        self.assertIn("Hormuz", sentence)
        self.assertIn("Rate momentum", sentence)
        self.assertIn("Event risk", sentence)
        self.assertIn("-16", sentence)

    def test_validate_fails_without_bridge(self):
        ok, reason = validate_score_bridge_in_generated(
            {"narrative": {"geopolitical_energy": "Risk is high."}},
            _scan_with_breakdown(),
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "score_bridge_missing_or_weak")

    def test_validate_passes_with_bridge_language(self):
        generated = {
            "narrative": {
                "geopolitical_energy": (
                    "Theme is critical. The short-term composite stays neutral because "
                    "Rate momentum (+8.5) is partly offset by Event risk (-12.0) — net effect."
                )
            }
        }
        ok, reason = validate_score_bridge_in_generated(generated, _scan_with_breakdown())
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_apply_injects_deterministic_bridge(self):
        scan = apply_score_narrative_bridge_to_scan(_scan_with_breakdown())
        self.assertTrue(scan["score_bridge_present"])
        self.assertIn("Score bridge", scan["score_narrative_bridge"])
        self.assertIn("Score bridge", scan["narrative"]["geopolitical_energy"])
        ids = [i["id"] for i in scan["highlights"]["items"]]
        self.assertIn("score_narrative_bridge", ids)

    def test_apply_skips_when_not_required(self):
        scan = _scan_with_breakdown()
        scan["curated_macro_overlay"]["geo_severity"] = "WATCH"
        out = apply_score_narrative_bridge_to_scan(scan)
        self.assertFalse(out["score_bridge_required"])
        self.assertFalse(out["score_bridge_present"])

    def test_has_score_bridge_language_driver_match(self):
        text = (
            "Composite score stays in the neutral band because Rate momentum offsets Event risk."
        )
        self.assertTrue(has_score_bridge_language(text, _scan_with_breakdown()["short_term"]))


if __name__ == "__main__":
    unittest.main()
