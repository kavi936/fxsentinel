"""
Deterministic structured levels from ohlc_store — v0 (BTCUSD).

Algorithms: PDH/PDL/PDC, weekly H/L, 4H session range, round-number POI confluence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.markets.market_registry import get_market
from services.markets.ohlc_ingest_binance import ingest_market, resolution_to_binance_interval
from services.markets.ohlc_store import get_bar_list, load_bars

Level = Dict[str, Any]

POI_ROUND_PCT = 0.003
H4_SESSION_BARS = 6


def _day_tag(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")


def _ensure_bars(market_id: str, resolution: str, market: Dict[str, Any]) -> List[Dict[str, Any]]:
    bars = get_bar_list(market_id, resolution)
    if bars:
        return bars

    if market.get("ohlc_source") == "binance" and market.get("binance_symbol"):
        if resolution_to_binance_interval(resolution):
            ingest_market(market_id, market["binance_symbol"], resolution, limit=500)
            return get_bar_list(market_id, resolution)
    return []


def build_structured_levels(market_id: str) -> List[Level]:
    """
    Build allowlisted levels for chart overlays + GPT context.
    Same OHLC input → same output (deterministic).
    """
    market = get_market(market_id)
    if not market:
        return []

    daily = _ensure_bars(market_id, "D", market)
    h4 = _ensure_bars(market_id, "240", market)

    if len(daily) < 2:
        return []

    prior = daily[-2]
    as_of = datetime.now(timezone.utc).isoformat()
    prefix = market_id.lower()
    tag = _day_tag(int(prior["time"]))

    levels: List[Level] = []

    pdh = float(prior["high"])
    pdl = float(prior["low"])
    pdc = float(prior["close"])

    levels.append(
        {
            "level_id": f"{prefix}_pdh_{tag}",
            "kind": "level",
            "label": "Prior day high",
            "price": round(pdh, 2),
            "basis": "prior_day_high",
            "timeframe": "1D",
            "as_of": as_of,
            "source": "level_engine_v0",
        }
    )
    levels.append(
        {
            "level_id": f"{prefix}_pdl_{tag}",
            "kind": "level",
            "label": "Prior day low",
            "price": round(pdl, 2),
            "basis": "prior_day_low",
            "timeframe": "1D",
            "as_of": as_of,
            "source": "level_engine_v0",
        }
    )
    levels.append(
        {
            "level_id": f"{prefix}_pdc_{tag}",
            "kind": "level",
            "label": "Prior close",
            "price": round(pdc, 2),
            "basis": "prior_day_close",
            "timeframe": "1D",
            "as_of": as_of,
            "source": "level_engine_v0",
        }
    )

    week_slice = daily[-5:]
    if week_slice:
        wh = max(float(b["high"]) for b in week_slice)
        wl = min(float(b["low"]) for b in week_slice)
        levels.append(
            {
                "level_id": f"{prefix}_weekly_high_{tag}",
                "kind": "level",
                "label": "Weekly high",
                "price": round(wh, 2),
                "basis": "weekly_high",
                "timeframe": "1D",
                "as_of": as_of,
                "source": "level_engine_v0",
            }
        )
        levels.append(
            {
                "level_id": f"{prefix}_weekly_low_{tag}",
                "kind": "level",
                "label": "Weekly low",
                "price": round(wl, 2),
                "basis": "weekly_low",
                "timeframe": "1D",
                "as_of": as_of,
                "source": "level_engine_v0",
            }
        )

    if len(h4) >= 2:
        session = h4[-H4_SESSION_BARS:] if len(h4) >= H4_SESSION_BARS else h4
        rh = max(float(b["high"]) for b in session)
        rl = min(float(b["low"]) for b in session)
        levels.append(
            {
                "level_id": f"{prefix}_target_range_{tag}",
                "kind": "range",
                "label": "4H rotation zone",
                "price_low": round(rl, 2),
                "price_high": round(rh, 2),
                "basis": "session_value_zone_4h",
                "horizon": "day",
                "timeframe": "4H",
                "as_of": as_of,
                "source": "level_engine_v0",
            }
        )

        # Simple swing: extrema of last 12 bars excluding last (forming) bar
        swing_slice = h4[-13:-1] if len(h4) > 13 else h4[:-1]
        if swing_slice:
            swing_high = max(float(b["high"]) for b in swing_slice)
            swing_low = min(float(b["low"]) for b in swing_slice)
            levels.append(
                {
                    "level_id": f"{prefix}_swing_high_4h_{tag}",
                    "kind": "level",
                    "label": "4H swing high",
                    "price": round(swing_high, 2),
                    "basis": "swing_high_4h",
                    "timeframe": "4H",
                    "as_of": as_of,
                    "source": "level_engine_v0",
                }
            )
            levels.append(
                {
                    "level_id": f"{prefix}_swing_low_4h_{tag}",
                    "kind": "level",
                    "label": "4H swing low",
                    "price": round(swing_low, 2),
                    "basis": "swing_low_4h",
                    "timeframe": "4H",
                    "as_of": as_of,
                    "source": "level_engine_v0",
                }
            )

    # POI: PDH near round $1k (BTC)
    round_1k = round(pdh / 1000) * 1000
    if round_1k > 0 and abs(pdh - round_1k) / round_1k <= POI_ROUND_PCT:
        levels.append(
            {
                "level_id": f"{prefix}_poi_{int(round_1k)}",
                "kind": "poi",
                "label": f"POI · ${int(round_1k / 1000)}k confluence",
                "price": float(round_1k),
                "basis": "poi_confluence",
                "timeframe": "1D",
                "as_of": as_of,
                "source": "level_engine_v0",
            }
        )

    return levels


def ohlc_quality(market_id: str) -> Dict[str, Any]:
    doc = load_bars(market_id, "240") or load_bars(market_id, "D")
    return {
        "ohlc_as_of": doc.get("as_of") if doc else None,
        "ohlc_source": doc.get("source") if doc else None,
        "bar_count_4h": len(get_bar_list(market_id, "240")),
        "bar_count_1d": len(get_bar_list(market_id, "D")),
    }
