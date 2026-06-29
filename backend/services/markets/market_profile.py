"""
Load per-market research profiles (JSON) — wiring diagram for context sources.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_PROFILES_DIR = Path(__file__).resolve().parent / "profiles"

# Shipped fallback — keeps platform context alive if profiles/ is missing on deploy
_BUILTIN_PROFILES: Dict[str, Dict[str, Any]] = {
    "BTCUSD": {
        "market_id": "BTCUSD",
        "label": "BTC/USD",
        "quote_instrument_id": "BTCUSDT",
        "ohlc_source": "binance",
        "narrative_frame": "Risk-on liquidity vs crypto-specific shock",
        "cross_assets": ["ETHUSDT", "SPX", "VIX", "US10Y", "GOLD"],
        "economy_scans": [{"country": "US", "max_age_hours": 72}],
        "calendar_filter": {
            "tags": [
                "FOMC",
                "CPI",
                "PCE",
                "NFP",
                "GDP",
                "Fed",
                "Payroll",
                "Employment",
                "Interest Rate",
                "Inflation",
            ],
            "currencies": ["USD"],
            "impact_min": "medium",
            "horizon_days": 7,
            "max_items": 8,
        },
        "news_filter": {
            "keywords": [
                "bitcoin",
                "btc",
                "crypto",
                "cryptocurrency",
                "ethereum",
                "etf",
                "sec",
                "binance",
                "regulation",
                "fed",
                "liquidity",
            ],
            "max_items": 8,
        },
        "platform_context": {"market_sentiment": True, "prediction_markets": False},
    },
}


@lru_cache(maxsize=16)
def load_market_profile(market_id: str) -> Optional[Dict[str, Any]]:
    mid = (market_id or "").upper()
    path = _PROFILES_DIR / f"{mid}.json"
    if path.is_file():
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data["market_id"] = mid
                return data
        except Exception as e:
            logger.warning("Failed to load market profile %s from %s: %s", mid, path, e)

    builtin = _BUILTIN_PROFILES.get(mid)
    if builtin:
        logger.info("Using built-in market profile for %s (JSON file missing or unreadable)", mid)
        return dict(builtin)

    logger.debug("No market profile for %s", mid)
    return None
