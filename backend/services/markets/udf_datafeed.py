"""
TradingView UDF-compatible datafeed — historical bars from ohlc_store.

Ref: https://www.tradingview.com/charting-library-docs/latest/connecting_data/udf/
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.markets.market_registry import MARKETS, get_market, list_enabled_markets, resolve_udf_symbol
from services.markets.ohlc_ingest_binance import ingest_market, resolution_to_binance_interval
from services.markets.ohlc_store import get_bar_list, load_bars

logger = logging.getLogger(__name__)

# Max bars per history request (TV may paginate)
DEFAULT_HISTORY_LIMIT = 500


def udf_config() -> Dict[str, Any]:
    enabled = list_enabled_markets()
    resolutions: List[str] = []
    for m in enabled:
        for r in m.get("supported_resolutions") or []:
            if r not in resolutions:
                resolutions.append(r)
    if not resolutions:
        resolutions = ["60", "240", "D"]

    return {
        "supports_search": True,
        "supports_group_request": False,
        "supports_marks": False,
        "supports_timescale_marks": False,
        "supports_time": True,
        "exchanges": [{"value": "FXSentinel", "name": "FXSentinel", "desc": "FXSentinel Markets"}],
        "symbols_types": [
            {"name": "crypto", "value": "crypto"},
            {"name": "forex", "value": "forex"},
        ],
        "supported_resolutions": resolutions,
    }


def udf_symbol_info(symbol: str) -> Dict[str, Any]:
    market = resolve_udf_symbol(symbol)
    if not market:
        return {"s": "error", "errmsg": f"Unknown symbol: {symbol}"}

    sym = market["udf_symbol"]
    ohlc_source = market.get("ohlc_source", "none")
    asset_type = "crypto" if sym == "BTCUSD" else "forex"

    return {
        "name": sym,
        "ticker": sym,
        "description": market.get("label", sym),
        "type": asset_type,
        "session": market.get("session", "24x7"),
        "timezone": market.get("timezone", "Etc/UTC"),
        "exchange": "FXSentinel",
        "listed_exchange": "FXSentinel",
        "format": "price",
        "pricescale": market.get("pricescale", 100000),
        "minmov": market.get("minmov", 1),
        "has_intraday": True,
        "has_daily": True,
        "has_weekly_and_monthly": True,
        "supported_resolutions": market.get("supported_resolutions") or ["60", "240", "D"],
        "volume_precision": 2,
        "data_status": "streaming" if market.get("enabled") else "endofday",
        "currency_code": "USD",
        "original_currency_code": "USD",
        "visible_plots_set": "ohlcv",
        "s": "ok",
        "meta": {"ohlc_source": ohlc_source, "enabled": market.get("enabled", False)},
    }


def udf_search(query: str, *, limit: int = 30) -> List[Dict[str, Any]]:
    q = (query or "").strip().upper()
    results: List[Dict[str, Any]] = []
    for market in MARKETS.values():
        sym = market["udf_symbol"]
        label = market.get("label", sym)
        if q and q not in sym and q not in label.upper():
            continue
        if not market.get("enabled"):
            continue
        results.append(
            {
                "symbol": sym,
                "full_name": f"FXSentinel:{sym}",
                "description": label,
                "exchange": "FXSentinel",
                "ticker": sym,
                "type": "crypto" if sym == "BTCUSD" else "forex",
            }
        )
        if len(results) >= limit:
            break
    return results


def _ensure_bars(market_id: str, resolution: str, market: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load from store; refresh from Binance if missing or empty."""
    bars = get_bar_list(market_id, resolution)
    if bars:
        return bars

    source = market.get("ohlc_source")
    if source == "binance" and market.get("binance_symbol"):
        if resolution_to_binance_interval(resolution):
            try:
                ingest_market(market_id, market["binance_symbol"], resolution, limit=DEFAULT_HISTORY_LIMIT)
                return get_bar_list(market_id, resolution)
            except Exception as e:
                logger.warning("Binance ingest failed for %s %s: %s", market_id, resolution, e)
        return []

    if source == "mt5":
        # MT5 bridge not wired yet
        return []

    return []


def udf_history(
    symbol: str,
    resolution: str,
    from_ts: int,
    to_ts: int,
    *,
    countback: Optional[int] = None,
) -> Dict[str, Any]:
    market = resolve_udf_symbol(symbol)
    if not market:
        return {"s": "error", "errmsg": f"Unknown symbol: {symbol}"}

    if not market.get("enabled"):
        return {"s": "no_data", "nextTime": None}

    market_id = market["id"]
    resolution = str(resolution).strip()

    if market.get("ohlc_source") == "mt5":
        bars = get_bar_list(market_id, resolution)
        if not bars:
            return {
                "s": "no_data",
                "nextTime": None,
                "errmsg": "MT5 feed not connected — enable after bridge spike",
            }
    else:
        bars = _ensure_bars(market_id, resolution, market)

    if not bars:
        return {"s": "no_data", "nextTime": None}

    # Filter [from, to) — UDF uses Unix seconds
    filtered = [b for b in bars if from_ts <= int(b["time"]) < to_ts]

    if countback and countback > 0 and len(filtered) > countback:
        filtered = filtered[-countback:]

    if not filtered:
        # Hint for TV pagination: nextTime = oldest bar before window
        before = [b for b in bars if int(b["time"]) < from_ts]
        next_time = int(before[-1]["time"]) if before else None
        return {"s": "no_data", "nextTime": next_time}

    t = [int(b["time"]) for b in filtered]
    o = [float(b["open"]) for b in filtered]
    h = [float(b["high"]) for b in filtered]
    l = [float(b["low"]) for b in filtered]
    c = [float(b["close"]) for b in filtered]
    v = [float(b.get("volume", 0)) for b in filtered]

    doc = load_bars(market_id, resolution)
    meta_source = (doc or {}).get("source", market.get("ohlc_source"))

    return {
        "s": "ok",
        "t": t,
        "o": o,
        "h": h,
        "l": l,
        "c": c,
        "v": v,
        "meta": {"source": meta_source, "market_id": market_id, "resolution": resolution},
    }


def markets_ohlc_json(market_id: str, timeframe: str, *, limit: int = 200) -> Dict[str, Any]:
    """FXSentinel-native OHLC shape (parallel to UDF for Lightweight Charts path)."""
    market = get_market(market_id)
    if not market:
        return {"error": "unknown_market"}

    tf = timeframe.upper()
    resolution = (
        tf.replace("4H", "240")
        .replace("1H", "60")
        .replace("1D", "D")
    )
    bars = _ensure_bars(market["id"], resolution, market)
    if limit and len(bars) > limit:
        bars = bars[-limit:]

    doc = load_bars(market["id"], resolution)
    return {
        "market_id": market["id"],
        "timeframe": timeframe,
        "source": (doc or {}).get("source"),
        "as_of": (doc or {}).get("as_of"),
        "bars": bars,
    }
