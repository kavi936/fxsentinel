"""
Binance public klines ingest — interim OHLC for crypto markets (BTCUSDT).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from services.markets.ohlc_store import save_bars

logger = logging.getLogger(__name__)

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

# TradingView UDF resolution → Binance interval
RESOLUTION_TO_BINANCE: Dict[str, str] = {
    "1": "1m",
    "5": "5m",
    "15": "15m",
    "30": "30m",
    "60": "1h",
    "120": "2h",
    "240": "4h",
    "D": "1d",
    "1D": "1d",
    "W": "1w",
    "1W": "1w",
}


def resolution_to_binance_interval(resolution: str) -> Optional[str]:
    return RESOLUTION_TO_BINANCE.get(str(resolution).strip())


def fetch_klines(
    symbol: str,
    interval: str,
    *,
    limit: int = 500,
    start_time_ms: Optional[int] = None,
    end_time_ms: Optional[int] = None,
    timeout: float = 20.0,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms

    resp = requests.get(BINANCE_KLINES_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    raw = resp.json()
    bars: List[Dict[str, Any]] = []
    for row in raw:
        # Binance kline array:
        # [0] open_time [1-4] OHLC [5] base volume [6] close_time
        # [7] quote_volume [8] trades [9] taker_buy_base [10] taker_buy_quote
        open_ms = int(row[0])
        bar: Dict[str, Any] = {
            "time": open_ms // 1000,
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        }
        if len(row) > 7:
            bar["quote_volume"] = float(row[7])
        if len(row) > 8:
            bar["trades"] = int(row[8])
        if len(row) > 9:
            bar["taker_buy_volume"] = float(row[9])
        if len(row) > 10:
            bar["taker_buy_quote_volume"] = float(row[10])
        bars.append(bar)
    return bars


def ingest_market(
    market_id: str,
    binance_symbol: str,
    resolution: str,
    *,
    limit: int = 500,
) -> Tuple[List[Dict[str, Any]], str]:
    interval = resolution_to_binance_interval(resolution)
    if not interval:
        raise ValueError(f"Unsupported resolution for Binance: {resolution}")

    bars = fetch_klines(binance_symbol, interval, limit=limit)
    path = save_bars(
        market_id,
        resolution,
        bars,
        source="binance",
        meta={"binance_symbol": binance_symbol, "interval": interval, "limit": limit},
    )
    logger.info("Ingested %s bars for %s %s → %s", len(bars), market_id, resolution, path)
    return bars, path
