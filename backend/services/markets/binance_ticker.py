"""
Binance spot ticker — live BTCUSDT (and other pairs) for Markets tab.

Uses public REST (no API key): GET /api/v3/ticker/24hr
Same venue as OHLC klines so chart + live quote stay aligned.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

BINANCE_TICKER_24HR_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"


def fetch_ticker_24hr(symbol: str, *, timeout: float = 10.0) -> Dict[str, Any]:
    """24h rolling stats including last price and daily change %."""
    sym = symbol.upper()
    resp = requests.get(BINANCE_TICKER_24HR_URL, params={"symbol": sym}, timeout=timeout)
    resp.raise_for_status()
    raw = resp.json()

    price = float(raw["lastPrice"])
    change_abs = float(raw["priceChange"])
    change_pct = float(raw["priceChangePercent"])

    return {
        "symbol": sym,
        "price": price,
        "change": change_abs,
        "changePercent": change_pct,
        "open": float(raw.get("openPrice", 0)),
        "high": float(raw.get("highPrice", 0)),
        "low": float(raw.get("lowPrice", 0)),
        "volume": float(raw.get("volume", 0)),
        "quoteVolume": float(raw.get("quoteVolume", 0)),
        "source": "binance",
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


def fetch_last_price(symbol: str, *, timeout: float = 8.0) -> Optional[float]:
    """Lightweight last-price only (fallback)."""
    sym = symbol.upper()
    resp = requests.get(BINANCE_PRICE_URL, params={"symbol": sym}, timeout=timeout)
    resp.raise_for_status()
    return float(resp.json()["price"])
