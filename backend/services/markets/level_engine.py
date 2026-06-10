"""
Deterministic structured levels from ohlc_store — v0 + v1 volume profile (BTCUSD).

v0: PDH/PDL/PDC, weekly H/L, 4H session range, round-number POI.
v1: 5-day 4H volume POC + value area (VAH/VAL) from feature_engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.markets.feature_engine import PROFILE_LOOKBACK_BARS_4H, compute_volume_profile
from services.markets.market_registry import get_market
from services.markets.market_timeframes import OHLC_MAX_BARS
from services.markets.ohlc_ingest_binance import ingest_market, resolution_to_binance_interval
from services.markets.ohlc_store import get_bar_list, load_bars

Level = Dict[str, Any]

POI_ROUND_PCT = 0.003
H4_SESSION_BARS = 6
LEVEL_ENGINE_VERSION = "v1"


def _day_tag(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")


def _ensure_bars(
    market_id: str,
    resolution: str,
    market: Dict[str, Any],
    *,
    min_bars: int = 2,
) -> List[Dict[str, Any]]:
    bars = get_bar_list(market_id, resolution)
    need_ingest = len(bars) < min_bars

    if market.get("ohlc_source") == "binance" and market.get("binance_symbol"):
        if resolution_to_binance_interval(resolution) and need_ingest:
            limit = OHLC_MAX_BARS if resolution == "240" else 500
            ingest_market(market_id, market["binance_symbol"], resolution, limit=limit)
            return get_bar_list(market_id, resolution)
    return bars


def build_structured_levels(market_id: str) -> List[Level]:
    """
    Build allowlisted levels for chart overlays + GPT context.
    Same OHLC input → same output (deterministic).
    """
    market = get_market(market_id)
    if not market:
        return []

    daily = _ensure_bars(market_id, "D", market)
    h4 = _ensure_bars(market_id, "240", market, min_bars=PROFILE_LOOKBACK_BARS_4H)

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

    profile = compute_volume_profile(h4)
    if profile:
        vol_tag = _day_tag(int(h4[-1]["time"]))
        metrics = profile.get("feature_metrics") or {}
        levels.append(
            {
                "level_id": f"{prefix}_vol_poc_{vol_tag}",
                "kind": "poi",
                "label": "Volume POC (5D 4H)",
                "price": profile["poc"],
                "basis": "volume_poc",
                "timeframe": "4H",
                "horizon": "swing",
                "as_of": as_of,
                "source": "level_engine_v1",
                "feature_metrics": metrics,
            }
        )
        levels.append(
            {
                "level_id": f"{prefix}_vol_va_{vol_tag}",
                "kind": "range",
                "label": "Value area (5D 4H)",
                "price_low": profile["val"],
                "price_high": profile["vah"],
                "basis": "value_area_4h_5d",
                "horizon": "swing",
                "timeframe": "4H",
                "as_of": as_of,
                "source": "level_engine_v1",
                "feature_metrics": metrics,
            }
        )

    return levels


def ohlc_quality(market_id: str) -> Dict[str, Any]:
    doc_4h = load_bars(market_id, "240")
    doc_d = load_bars(market_id, "D")
    doc = doc_4h or doc_d
    h4 = get_bar_list(market_id, "240")
    enriched = sum(1 for b in h4 if b.get("quote_volume") is not None)
    return {
        "ohlc_as_of": doc.get("as_of") if doc else None,
        "ohlc_source": doc.get("source") if doc else None,
        "bar_count_4h": len(h4),
        "bar_count_1d": len(get_bar_list(market_id, "D")),
        "levels_version": LEVEL_ENGINE_VERSION,
        "enriched_bars_4h": enriched,
        "volume_profile_ok": len(h4) >= PROFILE_LOOKBACK_BARS_4H,
    }
