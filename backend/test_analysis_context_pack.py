"""Tests for AnalysisContextPack (Phase B input layer)."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from services.analysis_context_pack import (
    HOLISTIC_MAX_AGE_HOURS,
    SURFACE_CALENDAR,
    SURFACE_LIVE_NEWS,
    build_analysis_context_pack,
    build_cross_surface_notes,
    extract_macro_snapshot_from_scan,
    render_pack_for_prompt,
    resolve_subject,
    shared_pack_signature,
)


def _sample_scan() -> dict:
    return {
        "country": "US",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "short_term": {"bias": "bearish", "score": -12.5, "confidence": 78},
        "long_term": {"bias": "neutral", "score": 2.0, "confidence": 65},
        "event_flags": {"calendar_stress_score": 82},
        "trader_brief": {
            "short_term_line": "Bearish · Score -12.5 · 78% confidence",
            "key_risk": "Geopolitical risk & energy prices",
        },
        "fx_pairs": [
            {"pair": "EURUSD", "bias": "bullish", "strength": "moderate"},
            {"pair": "USDJPY", "bias": "bearish", "strength": "light"},
        ],
        "highlights": [
            {
                "id": "geopolitical_energy",
                "emphasis": "ELEVATED",
                "detail": "Oil risk premia elevated.",
            }
        ],
    }


class AnalysisContextPackTests(unittest.TestCase):
    def test_resolve_subject_from_currency(self):
        subj = resolve_subject(subject_currency="USD")
        self.assertEqual(subj["currency"], "USD")
        self.assertEqual(subj["country_code"], "US")
        self.assertEqual(subj["economy_label"], "United States")

    def test_extract_macro_snapshot_from_scan(self):
        snap = extract_macro_snapshot_from_scan(_sample_scan())
        self.assertEqual(snap["source"], "holistic_scan")
        self.assertEqual(snap["short_term_bias"], "bearish")
        self.assertEqual(snap["calendar_stress_14d"], 82)
        self.assertEqual(snap["geopolitical_energy_risk"], "elevated")
        self.assertEqual(len(snap["top_pair_biases"]), 2)
        self.assertIn("Geopolitical", snap["one_line_summary"])

    def test_cross_surface_geo_elevated_vs_neutral_news(self):
        macro = extract_macro_snapshot_from_scan(_sample_scan())
        notes = build_cross_surface_notes(
            surface=SURFACE_LIVE_NEWS,
            macro_snapshot=macro,
            area_facts={
                "headline": "Oil jumps as Hormuz tensions escalate",
                "immediate_reaction": "neutral",
            },
        )
        self.assertIn("ELEVATED", notes["holistic_vs_headline_note"] or "")

    def test_cross_surface_bias_mismatch(self):
        macro = extract_macro_snapshot_from_scan(_sample_scan())
        notes = build_cross_surface_notes(
            surface=SURFACE_LIVE_NEWS,
            macro_snapshot=macro,
            area_facts={"immediate_reaction": "bullish_usd"},
        )
        self.assertIn("reconcile", (notes["holistic_vs_headline_note"] or "").lower())

    @patch("services.analysis_context_pack.build_market_snapshot_dict")
    @patch("services.analysis_context_pack._load_fresh_holistic_macro")
    def test_shared_block_matches_calendar_vs_news(
        self, mock_holistic, mock_market
    ):
        mock_market.return_value = {
            "instruments": [{"id": "EURUSD", "label": "EUR/USD", "price": 1.08, "change_pct": 0.1}],
            "selection_reason": "user_pairs",
            "quote_count": 100,
        }
        mock_holistic.return_value = extract_macro_snapshot_from_scan(_sample_scan())

        fixed_now = datetime(2026, 5, 20, 14, 0, tzinfo=timezone.utc)
        opts = {"now_utc": fixed_now, "include_holistic_macro": True}

        cal = build_analysis_context_pack(
            surface=SURFACE_CALENDAR,
            user_id="user-1",
            subject_currency="USD",
            context_text="US CPI",
            area_facts={"title": "CPI"},
            options=opts,
        )
        news = build_analysis_context_pack(
            surface=SURFACE_LIVE_NEWS,
            user_id="user-1",
            subject_currency="USD",
            context_text="US CPI",
            area_facts={"headline": "CPI"},
            options=opts,
        )

        cal_shared = shared_pack_signature(cal)
        news_shared = shared_pack_signature(news)
        self.assertEqual(cal_shared["user"], news_shared["user"])
        self.assertEqual(cal_shared["subject"], news_shared["subject"])
        self.assertEqual(cal_shared["macro_snapshot"], news_shared["macro_snapshot"])
        self.assertEqual(cal["personalization_mode"], "soft")
        self.assertEqual(news["personalization_mode"], "hard")

    @patch("services.analysis_context_pack.build_market_snapshot_dict")
    @patch("services.analysis_context_pack._load_fresh_holistic_macro")
    def test_stale_holistic_omitted(self, mock_holistic, mock_market):
        mock_market.return_value = {"instruments": [], "selection_reason": "unavailable", "quote_count": 0}
        mock_holistic.return_value = None

        pack = build_analysis_context_pack(
            surface=SURFACE_CALENDAR,
            user_id="user-1",
            subject_currency="USD",
            options={"include_holistic_macro": True},
        )
        self.assertEqual(pack["macro_snapshot"]["source"], "none")
        notes = pack["session_and_quality"]["quality_notes"]
        self.assertTrue(any("holistic scan" in n.lower() for n in notes))

    @patch("services.analysis_context_pack.build_market_snapshot_dict")
    @patch("services.analysis_context_pack._load_fresh_holistic_macro")
    def test_fresh_holistic_loaded_from_store(self, mock_holistic, mock_market):
        mock_market.return_value = {"instruments": [], "selection_reason": "unavailable", "quote_count": 0}
        now = datetime.now(timezone.utc)
        macro = extract_macro_snapshot_from_scan(_sample_scan(), scanned_at=now, now=now)
        macro["scan_id"] = "scan-abc"
        mock_holistic.return_value = macro

        pack = build_analysis_context_pack(
            surface=SURFACE_CALENDAR,
            token_user_info={"user_id": "u1"},
            subject_country_code="US",
            options={"now_utc": now, "include_holistic_macro": True},
        )
        self.assertEqual(pack["macro_snapshot"]["source"], "holistic_scan")
        self.assertEqual(pack["macro_snapshot"]["short_term_bias"], "bearish")
        freshness = pack["macro_snapshot"].get("freshness_hours")
        self.assertIsNotNone(freshness)
        self.assertLessEqual(freshness, HOLISTIC_MAX_AGE_HOURS)

    @patch("services.analysis_context_pack.build_market_snapshot_dict")
    @patch("services.analysis_context_pack._detect_market_session")
    def test_weekend_closed_illustrative_levels(self, mock_session, mock_market):
        mock_market.return_value = {"instruments": [], "selection_reason": "unavailable", "quote_count": 0}
        mock_session.return_value = {
            "market_session": "closed",
            "active_sessions": [],
            "notes": ["Major FX cash session closed (weekend or holiday)."],
        }

        pack = build_analysis_context_pack(
            surface=SURFACE_CALENDAR,
            subject_currency="USD",
            options={"include_holistic_macro": False},
        )
        self.assertEqual(pack["session_and_quality"]["market_session"], "closed")
        self.assertEqual(pack["session_and_quality"]["level_anchor_policy"], "illustrative")

        prompt = render_pack_for_prompt(pack)
        self.assertIn("illustrative", prompt.lower())
        self.assertIn("edge strength", prompt.lower())

    @patch("services.analysis_context_pack.build_market_snapshot_dict")
    def test_render_includes_personalization_mode(self, mock_market):
        mock_market.return_value = {
            "instruments": [{"id": "EURUSD", "label": "EUR/USD", "price": 1.0, "change_pct": 0.0}],
            "selection_reason": "user_pairs",
            "quote_count": 1,
        }
        pack = build_analysis_context_pack(
            surface=SURFACE_LIVE_NEWS,
            subject_currency="USD",
            options={"include_holistic_macro": False},
        )
        text = render_pack_for_prompt(pack)
        self.assertIn("PERSONALIZATION MODE", text)
        self.assertIn("HARD", text)

    @patch("services.economy_holistic_scan_store.economy_holistic_scan_store")
    def test_store_age_threshold(self, mock_store):
        from services.analysis_context_pack import _load_fresh_holistic_macro

        old = datetime.now(timezone.utc) - timedelta(hours=HOLISTIC_MAX_AGE_HOURS + 1)
        mock_store.get_recent_holistic_scans.return_value = [
            {"id": "old", "created_at": old.isoformat(), "scan_snapshot": _sample_scan()}
        ]
        result = _load_fresh_holistic_macro({"user_id": "u1"}, "US", now=datetime.now(timezone.utc))
        self.assertIsNone(result)

    def test_env_flag_disabled_by_default(self):
        prev = os.environ.get("ANALYSIS_CONTEXT_PACK_ENABLED")
        os.environ.pop("ANALYSIS_CONTEXT_PACK_ENABLED", None)
        try:
            from services.analysis_context_pack import should_include_holistic_macro

            self.assertFalse(should_include_holistic_macro())
        finally:
            if prev is not None:
                os.environ["ANALYSIS_CONTEXT_PACK_ENABLED"] = prev


if __name__ == "__main__":
    unittest.main()
