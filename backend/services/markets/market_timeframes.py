"""
API timeframe labels ↔ internal resolution keys (ohlc_store / UDF).

Internal keys match RESOLUTION_TO_BINANCE in ohlc_ingest_binance.py.
"""

from __future__ import annotations

from typing import Dict, Optional

# Binance klines: max 1000 bars per request
OHLC_MAX_BARS = 1000

# Re-fetch from Binance when on-disk cache is older than this (chart polls every ~30s)
OHLC_LIVE_REFRESH_SEC = 30

# In-memory quote cache — one Binance call per market per TTL regardless of client count
QUOTE_CACHE_TTL_SEC = 5

# Chart / GET /ohlc?tf=… → ohlc_store resolution key
API_TF_TO_RESOLUTION: Dict[str, str] = {
    "15M": "15",
    "30M": "30",
    "1H": "60",
    "2H": "120",
    "4H": "240",
    "1D": "D",
    "1W": "W",
}


def api_timeframe_to_resolution(timeframe: str) -> Optional[str]:
    return API_TF_TO_RESOLUTION.get((timeframe or "").strip().upper())
