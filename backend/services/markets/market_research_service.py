"""
Assemble Markets research DTO — quote, levels, deterministic verdict until global GPT runs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.markets.level_engine import build_structured_levels, ohlc_quality
from services.markets.market_news_filter import fetch_btc_market_news
from services.markets.market_registry import get_market
from services.markets.ohlc_ingest_binance import ingest_market

BTC_CROSS_ASSETS = ("ETHUSDT", "SPX", "VIX", "US10Y", "GOLD")

try:
    from services.tradingview_market_data import fetch_tradingview_quotes
except ImportError:
    fetch_tradingview_quotes = None  # type: ignore


def _quote_instrument_id(market: Dict[str, Any]) -> str:
    if market.get("binance_symbol"):
        return market["binance_symbol"]
    return market.get("udf_symbol", market["id"])


def _find_level(levels: List[Dict[str, Any]], basis: str) -> Optional[Dict[str, Any]]:
    for lv in levels:
        if lv.get("basis") == basis:
            return lv
    return None


def _deterministic_verdict(levels: List[Dict[str, Any]], spot: Optional[float]) -> Dict[str, str]:
    pdh = _find_level(levels, "prior_day_high")
    pdl = _find_level(levels, "prior_day_low")
    rng = next((l for l in levels if l.get("kind") == "range"), None)

    if spot is None or not pdh or not pdl:
        return {
            "bias": "neutral",
            "display_bias": "TRUE NEUTRAL",
            "conviction": "low",
            "day_summary": "Awaiting live quote and OHLC to compute intraday bias.",
            "swing_summary": "Structure levels loaded from daily and 4H bars.",
        }

    mid = (float(pdh["price"]) + float(pdl["price"])) / 2
    if spot > float(pdh["price"]):
        bias, display = "bullish", "BULLISH LEAN"
        day = f"Price above prior day high ({pdh['price']:,.0f}) — momentum favors continuation unless rejected back inside range."
    elif spot < float(pdl["price"]):
        bias, display = "bearish", "BEARISH LEAN"
        day = f"Price below prior day low ({pdl['price']:,.0f}) — defensive intraday structure until reclaim of PDL."
    elif spot >= mid:
        bias, display = "neutral", "NEUTRAL · BULLISH LEAN"
        day = f"Price holding upper half of prior day range ({pdl['price']:,.0f}–{pdh['price']:,.0f}) — mild bullish bias."
    else:
        bias, display = "neutral", "NEUTRAL · BEARISH LEAN"
        day = f"Price in lower half of prior day range ({pdl['price']:,.0f}–{pdh['price']:,.0f}) — mild bearish bias."

    swing = "Swing structure references weekly high/low and 4H rotation zone from the level engine."
    if rng:
        swing = (
            f"4H rotation zone {rng['price_low']:,.0f}–{rng['price_high']:,.0f}; "
            "swing bias follows whether price accepts above or below this band."
        )

    return {
        "bias": bias,
        "display_bias": display,
        "conviction": "medium" if abs(spot - mid) > (float(pdh["price"]) - float(pdl["price"])) * 0.15 else "low",
        "day_summary": day,
        "swing_summary": swing,
    }


def _deterministic_headline(levels: List[Dict[str, Any]], spot: Optional[float], market_label: str) -> str:
    verdict = _deterministic_verdict(levels, spot)
    pdh = _find_level(levels, "prior_day_high")
    pdl = _find_level(levels, "prior_day_low")
    if not spot or not pdh or not pdl:
        return f"{market_label} research snapshot — levels from latest OHLC ingest."

    short = market_label.split("/")[0].strip()
    return (
        f"{short} trading {spot:,.0f} with {verdict['display_bias'].lower()} vs "
        f"prior day range {pdl['price']:,.0f}–{pdh['price']:,.0f}."
    )


def _invalidation_lines(levels: List[Dict[str, Any]]) -> List[str]:
    pdl = _find_level(levels, "prior_day_low")
    pdh = _find_level(levels, "prior_day_high")
    out = []
    if pdl:
        out.append(f"Sustained break below prior day low ({float(pdl['price']):,.0f})")
    else:
        out.append("Break below prior day low")
    if pdh:
        out.append(f"Rejection from prior day high ({float(pdh['price']):,.0f}) on rising risk-off")
    else:
        out.append("Rejection at prior day high")
    return out


def _headline_emphasis(verdict: Dict[str, str]) -> List[str]:
    phrases = []
    db = verdict.get("display_bias", "")
    if "BULLISH" in db:
        phrases.append("bullish lean")
    if "BEARISH" in db:
        phrases.append("bearish lean")
    if "NEUTRAL" in db:
        phrases.append("neutral")
    return phrases[:2]


def _build_cross_assets(quotes: Dict[str, Any]) -> List[Dict[str, Any]]:
    from services.tradingview_instruments import instrument_by_id

    inst_map = instrument_by_id()
    out: List[Dict[str, Any]] = []
    for inst_id in BTC_CROSS_ASSETS:
        row = quotes.get(inst_id) or {}
        inst = inst_map.get(inst_id, {})
        out.append(
            {
                "id": inst_id,
                "label": inst.get("label", inst_id),
                "price": row.get("price"),
                "changePercent": row.get("changePercent"),
            }
        )
    return out


def refresh_ohlc(market_id: str) -> None:
    """Pull latest bars before level build (Binance markets only)."""
    market = get_market(market_id)
    if not market or market.get("ohlc_source") != "binance":
        return
    symbol = market.get("binance_symbol")
    if not symbol:
        return
    for res in market.get("supported_resolutions") or ["240", "60", "D"]:
        try:
            ingest_market(market_id, symbol, res, limit=500)
        except Exception:
            pass


def build_research(market_id: str, *, refresh: bool = True) -> Dict[str, Any]:
    market = get_market(market_id)
    if not market:
        return {"error": "unknown_market", "market_id": market_id}

    if not market.get("enabled"):
        return {"error": "market_disabled", "market_id": market_id}

    if refresh:
        refresh_ohlc(market_id)

    levels = build_structured_levels(market_id)
    quality = ohlc_quality(market_id)

    quotes: Dict[str, Any] = {}
    if fetch_tradingview_quotes:
        quotes = fetch_tradingview_quotes() or {}

    quote_row: Dict[str, Any] = {}
    inst_id = _quote_instrument_id(market)
    if quotes:
        quote_row = quotes.get(inst_id, {})

    spot = quote_row.get("price")
    if spot is not None:
        try:
            spot = float(spot)
        except (TypeError, ValueError):
            spot = None

    verdict = _deterministic_verdict(levels, spot)
    headline = _deterministic_headline(levels, spot, market.get("label", market_id))
    as_of = datetime.now(timezone.utc).isoformat()

    return {
        "market_id": market_id,
        "display_label": market.get("label", market_id),
        "as_of": as_of,
        "headline": headline,
        "headline_emphasis": _headline_emphasis(verdict),
        "quote": {
            "price": spot,
            "changePercent": quote_row.get("changePercent"),
            "source": quote_row.get("source", "tradingview"),
            "instrument_id": _quote_instrument_id(market),
        },
        "verdict": verdict,
        "structured_levels": levels,
        "cross_assets": _build_cross_assets(quotes) if market_id == "BTCUSD" else [],
        "catalysts": [],
        "news": fetch_btc_market_news(5) if market_id == "BTCUSD" else [],
        "thesis": {
            "headline": "Deterministic structure snapshot",
            "body": verdict["day_summary"],
        },
        "invalidation": _invalidation_lines(levels),
        "latest_run": None,
        "data_quality": {
            **quality,
            "levels_ok": len(levels) >= 3,
            "note": "level_engine_v0 · global GPT run not attached",
        },
    }
