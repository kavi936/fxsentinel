"""
Live quote for Markets tab — Binance first for crypto, TradingView fallback.

Quotes are cached in memory (QUOTE_CACHE_TTL_SEC) so many clients polling /quote
share one upstream fetch per market.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

from services.markets.binance_ticker import fetch_ticker_24hr
from services.markets.market_registry import get_market
from services.markets.market_timeframes import QUOTE_CACHE_TTL_SEC

logger = logging.getLogger(__name__)

try:
    from services.tradingview_market_data import fetch_tradingview_quotes
except ImportError:
    fetch_tradingview_quotes = None  # type: ignore

# market_id → (monotonic_fetched_at, payload)
_quote_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def _quote_instrument_id(market: Dict[str, Any]) -> str:
    if market.get("binance_symbol"):
        return market["binance_symbol"]
    return market.get("udf_symbol", market["id"])


def _tv_quote(market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not fetch_tradingview_quotes:
        return None
    inst_id = _quote_instrument_id(market)
    row = (fetch_tradingview_quotes() or {}).get(inst_id)
    if not row:
        return None
    return {
        "symbol": inst_id,
        "price": row.get("price"),
        "change": row.get("change"),
        "changePercent": row.get("changePercent"),
        "source": row.get("source", "tradingview"),
        "as_of": row.get("lastUpdate"),
    }


def _fetch_market_live_quote(market_id: str) -> Dict[str, Any]:
    market = get_market(market_id)
    if not market:
        return {"error": "unknown_market", "market_id": market_id}

    if not market.get("enabled"):
        return {"error": "market_disabled", "market_id": market_id}

    binance_symbol = market.get("binance_symbol")
    if market.get("ohlc_source") == "binance" and binance_symbol:
        try:
            quote = fetch_ticker_24hr(binance_symbol)
            quote["market_id"] = market_id
            quote["display_label"] = market.get("label", market_id)
            quote["instrument_id"] = binance_symbol
            return quote
        except Exception as e:
            logger.warning("Binance ticker failed for %s: %s", market_id, e)
            fallback = _tv_quote(market)
            if fallback:
                fallback["market_id"] = market_id
                fallback["display_label"] = market.get("label", market_id)
                fallback["instrument_id"] = _quote_instrument_id(market)
                fallback["fallback_from"] = "binance_error"
                return fallback
            return {"error": "quote_unavailable", "market_id": market_id, "detail": str(e)}

    tv = _tv_quote(market)
    if tv:
        tv["market_id"] = market_id
        tv["display_label"] = market.get("label", market_id)
        tv["instrument_id"] = _quote_instrument_id(market)
        return tv

    return {"error": "quote_unavailable", "market_id": market_id}


def get_market_live_quote(market_id: str, *, refresh: bool = True) -> Dict[str, Any]:
    mid = (market_id or "").upper()
    if not mid:
        return {"error": "unknown_market", "market_id": market_id}

    if refresh:
        cached = _quote_cache.get(mid)
        if cached:
            fetched_at, payload = cached
            if time.monotonic() - fetched_at < QUOTE_CACHE_TTL_SEC:
                return payload

    payload = _fetch_market_live_quote(mid)
    if not payload.get("error"):
        _quote_cache[mid] = (time.monotonic(), payload)
    return payload
