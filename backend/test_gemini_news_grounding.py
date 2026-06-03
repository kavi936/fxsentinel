#!/usr/bin/env python3
"""Tests for Gemini live-news grounding service (Phase 1+)."""

import os
import unittest
from unittest.mock import patch

from services.gemini_news_grounding_service import (
    fetch_related_evidence,
    render_related_evidence_prompt_block,
    _build_pack,
    _extract_json_object,
    _merge_structured_with_chunks,
    _normalize_structured,
    _publisher_domain_from_chunk,
    _publisher_tier,
)


class TestPublisherTier(unittest.TestCase):
    def test_redirect_uses_chunk_title_domain(self):
        domain = _publisher_domain_from_chunk(
            "reuters.com",
            "https://vertexaisearch.cloud.google.com/grounding-api-redirect/abc",
        )
        self.assertEqual(domain, "reuters.com")
        self.assertEqual(_publisher_tier(domain), "tier_1")


class TestStructuredParse(unittest.TestCase):
    def test_extract_json_object(self):
        raw = '{"story_arc": "ongoing_story", "related_items": []}'
        parsed = _extract_json_object(raw)
        self.assertEqual(parsed["story_arc"], "ongoing_story")

    def test_merge_structured_with_chunks(self):
        structured = _normalize_structured(
            {
                "story_arc": "new_development",
                "synthesis_bullets": ["BoJ in focus"],
                "related_items": [
                    {
                        "headline": "BoJ Governor signals patience on rates",
                        "publisher": "reuters.com",
                        "relationship": "corroborates",
                        "takeaway": "Markets see less urgency for hikes.",
                        "recency_bucket": "last_24h",
                        "key_fact": "",
                    }
                ],
            }
        )
        evidence = _merge_structured_with_chunks(
            structured,
            [
                {
                    "uri": "https://vertexaisearch.cloud.google.com/x",
                    "title": "reuters.com",
                    "domain": "reuters.com",
                }
            ],
        )
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["id"], "E1")
        self.assertEqual(evidence[0]["relationship"], "corroborates")
        self.assertIn("urgency", evidence[0]["snippet"].lower())
        self.assertEqual(evidence[0]["publisher_tier"], "tier_1")


class TestRenderPromptBlock(unittest.TestCase):
    def test_skipped_returns_empty(self):
        pack = {"quality": {"status": "skipped"}}
        self.assertEqual(render_related_evidence_prompt_block(pack), "")

    def test_ok_includes_relationship_and_story_arc(self):
        structured = _normalize_structured(
            {
                "story_arc": "ongoing_story",
                "primary_entities": ["BoJ", "JPY"],
                "synthesis_bullets": ["Yen sensitive to US yields."],
                "contradictions_note": "",
                "related_items": [
                    {
                        "headline": "Yen weakens ahead of BoJ",
                        "publisher": "bloomberg.com",
                        "relationship": "market_reaction",
                        "takeaway": "USD/JPY bid on yield spread.",
                        "recency_bucket": "unknown",
                    }
                ],
            }
        )
        pack = _build_pack(
            {"title": "BoJ speech", "summary": "", "source": "MUFG"},
            primary_currency="JPY",
            web_search_queries=["boj usd jpy"],
            grounding_chunks=[],
            structured=structured,
            latency_ms=100,
            model="gemini-2.5-flash",
        )
        block = render_related_evidence_prompt_block(pack)
        self.assertIn("ongoing story", block)
        self.assertIn("relationship: market reaction", block)
        self.assertIn("[E1]", block)
        self.assertIn("Yen sensitive", block)


class TestFetchRelatedEvidence(unittest.TestCase):
    def test_disabled_returns_skipped(self):
        with patch.dict(os.environ, {"LIVE_NEWS_GEMINI_GROUNDING_ENABLED": "false"}, clear=False):
            pack = fetch_related_evidence({"id": "1", "title": "Test headline"})
        self.assertEqual(pack["quality"]["status"], "skipped")

    @patch("services.gemini_news_grounding_service._call_gemini")
    def test_enabled_calls_gemini(self, mock_call):
        mock_call.return_value = _build_pack(
            {"title": "CPI hot", "summary": "", "source": "Bloomberg"},
            primary_currency="USD",
            web_search_queries=["us cpi"],
            grounding_chunks=[],
            structured=_normalize_structured(
                {
                    "synthesis_bullets": ["Inflation sticky."],
                    "related_items": [],
                }
            ),
            latency_ms=50,
            model="gemini-2.5-flash",
        )
        with patch.dict(
            os.environ,
            {
                "LIVE_NEWS_GEMINI_GROUNDING_ENABLED": "true",
                "GEMINI_API_KEY": "test-key",
            },
            clear=False,
        ):
            pack = fetch_related_evidence(
                {"id": "99", "title": "CPI hot", "summary": "", "source": "Bloomberg"}
            )
        self.assertEqual(pack["quality"]["status"], "ok_with_summary")
        self.assertIn("Inflation sticky", pack["retrieval_summary"])
        mock_call.assert_called_once()

    @patch("services.gemini_news_grounding_service._call_gemini")
    def test_gemini_error_fail_open(self, mock_call):
        mock_call.side_effect = RuntimeError("API timeout")
        with patch.dict(
            os.environ,
            {
                "LIVE_NEWS_GEMINI_GROUNDING_ENABLED": "true",
                "GEMINI_API_KEY": "test-key",
            },
            clear=False,
        ):
            pack = fetch_related_evidence({"id": "2", "title": "Oil jumps"})
        self.assertEqual(pack["quality"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
