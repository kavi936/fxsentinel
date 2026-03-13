"""
Test prediction markets context and central_bank_ai_context wiring.
Uses sampled cache so it does not require a live API or populated cache.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from services.prediction_markets_service import prediction_markets_service
from services.prediction_markets_context import (
    get_central_bank_context,
    get_event_context,
    get_fx_pair_context,
    format_central_bank_context_for_prompt,
)
from services.central_bank_ai_context import (
    get_context_for_currency,
    get_prediction_markets_context_for_currency,
)


def test_with_sampled_cache():
    """Run context and formatter with a few mock Fed markets; assert structure and content."""
    sample = [
        {
            "id": "polymarket:test-1",
            "platform": "polymarket",
            "question": "Will the Fed cut rates by at least 25 bps at the March 2026 FOMC meeting?",
            "yes_price": 0.63,
            "no_price": 0.37,
            "volume": 150000,
            "resolution_date": "2026-03-20T00:00:00+00:00",
            "price_delta_24h": 4.2,
            "conviction_level": "high",
            "conviction_score": 72,
            "event_title": "Fed March 2026",
            "event_slug": "fed-march-2026",
        },
        {
            "id": "polymarket:test-2",
            "platform": "polymarket",
            "question": "Will the Fed hold rates unchanged in March 2026?",
            "yes_price": 0.25,
            "no_price": 0.75,
            "volume": 80000,
            "resolution_date": "2026-03-20T00:00:00+00:00",
            "price_delta_24h": -1.5,
            "conviction_level": "medium",
            "event_title": "FOMC March 2026",
        },
    ]
    prediction_markets_service.cached_markets = sample
    try:
        fed = get_central_bank_context("Fed", horizon_days=120, max_markets=5)
        assert fed.get("provider") == "prediction_markets" and fed.get("central_bank") == "Fed"
        assert len(fed.get("markets", [])) == 2
        probs = [m.get("yes_probability") for m in fed["markets"]]
        assert 63 in probs or 63.0 in probs
        assert 25 in probs or 25.0 in probs

        s = format_central_bank_context_for_prompt(fed)
        assert len(s) > 0 and "Prediction market" in s and "Fed" in s and "63%" in s and "25%" in s

        pm_usd = get_prediction_markets_context_for_currency("USD", max_markets=5)
        assert "Fed" in pm_usd and "63%" in pm_usd

        full = get_context_for_currency("USD", max_docs=0, include_prediction_markets=True)
        assert full and "Prediction market" in full

        ev = get_event_context("CPI", "US", max_markets=2)
        fx = get_fx_pair_context("EURUSD", max_markets=3)
        assert "provider" in ev and "markets" in ev
        assert fx.get("fx_pair") == "EURUSD" and "central_banks" in fx
    finally:
        prediction_markets_service.cached_markets = None


if __name__ == "__main__":
    test_with_sampled_cache()
    print("OK: All tests passed. Context is sampleable and formatting works.")
