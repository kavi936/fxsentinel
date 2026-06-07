"""
Markets tab symbol registry — single source for UDF + research APIs.

Display ids (BTCUSD) may differ from quote/OHLC ids (BTCUSDT on Binance).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class MarketConfig(TypedDict, total=False):
    id: str
    label: str
    enabled: bool
    udf_symbol: str
    ohlc_source: str  # binance | mt5 | none
    binance_symbol: str
    mt5_symbol: str
    pricescale: int
    minmov: int
    session: str
    timezone: str
    supported_resolutions: List[str]


# pricescale: 10^decimals for TV UDF (e.g. 100 = 2 decimal places)
MARKETS: Dict[str, MarketConfig] = {
    "BTCUSD": {
        "id": "BTCUSD",
        "label": "BTC/USD",
        "enabled": True,
        "udf_symbol": "BTCUSD",
        "ohlc_source": "binance",
        "binance_symbol": "BTCUSDT",
        "mt5_symbol": "BTCUSD",
        "pricescale": 100,
        "minmov": 1,
        "session": "24x7",
        "timezone": "Etc/UTC",
        "supported_resolutions": ["60", "240", "D"],
    },
    "EURUSD": {
        "id": "EURUSD",
        "label": "EUR/USD",
        "enabled": False,
        "udf_symbol": "EURUSD",
        "ohlc_source": "mt5",
        "mt5_symbol": "EURUSD",
        "pricescale": 100000,
        "minmov": 1,
        "session": "24x5",
        "timezone": "Etc/UTC",
        "supported_resolutions": ["60", "240", "D"],
    },
    "GBPUSD": {
        "id": "GBPUSD",
        "label": "GBP/USD",
        "enabled": False,
        "udf_symbol": "GBPUSD",
        "ohlc_source": "mt5",
        "mt5_symbol": "GBPUSD",
        "pricescale": 100000,
        "minmov": 1,
        "session": "24x5",
        "timezone": "Etc/UTC",
        "supported_resolutions": ["60", "240", "D"],
    },
    "USDJPY": {
        "id": "USDJPY",
        "label": "USD/JPY",
        "enabled": False,
        "udf_symbol": "USDJPY",
        "ohlc_source": "mt5",
        "mt5_symbol": "USDJPY",
        "pricescale": 1000,
        "minmov": 1,
        "session": "24x5",
        "timezone": "Etc/UTC",
        "supported_resolutions": ["60", "240", "D"],
    },
}


def get_market(market_id: str) -> Optional[MarketConfig]:
    key = (market_id or "").upper()
    return MARKETS.get(key)


def list_enabled_markets() -> List[MarketConfig]:
    return [m for m in MARKETS.values() if m.get("enabled")]


def resolve_udf_symbol(symbol: str) -> Optional[MarketConfig]:
    """Resolve UDF request symbol (e.g. BTCUSD or FX:EURUSD) to market config."""
    raw = (symbol or "").strip().upper()
    if not raw:
        return None
    if raw in MARKETS:
        return MARKETS[raw]
    # FX:EURUSD → EURUSD
    if ":" in raw:
        return MARKETS.get(raw.split(":")[-1])
    return None
