"""
Venue quant features from enriched OHLC — volume profile, etc.

Raw transforms only; level_engine decides chart objects.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# 5 calendar days × 6 four-hour bars per day
PROFILE_LOOKBACK_BARS_4H = 30
PROFILE_NUM_BINS = 80
VALUE_AREA_PCT = 0.70


def _bar_volume(bar: Dict[str, Any]) -> float:
    """Prefer quote volume (USD on BTCUSDT) when present."""
    qv = bar.get("quote_volume")
    if qv is not None:
        try:
            v = float(qv)
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass
    try:
        return max(0.0, float(bar.get("volume") or 0))
    except (TypeError, ValueError):
        return 0.0


def _bin_mid(price_low: float, step: float, idx: int) -> float:
    return price_low + (idx + 0.5) * step


def compute_volume_profile(
    bars: List[Dict[str, Any]],
    *,
    lookback_bars: int = PROFILE_LOOKBACK_BARS_4H,
    num_bins: int = PROFILE_NUM_BINS,
    value_area_pct: float = VALUE_AREA_PCT,
) -> Optional[Dict[str, Any]]:
    """
    Fixed-range histogram: distribute each bar's volume across price bins
    overlapping [low, high]. Returns POC + value area (VAH/VAL).
    """
    if not bars or lookback_bars < 2 or num_bins < 4:
        return None

    window = bars[-lookback_bars:]
    if len(window) < lookback_bars // 2:
        return None

    try:
        range_low = min(float(b["low"]) for b in window)
        range_high = max(float(b["high"]) for b in window)
    except (KeyError, TypeError, ValueError):
        return None

    if range_high <= range_low:
        return None

    step = (range_high - range_low) / num_bins
    if step <= 0:
        return None

    hist = [0.0] * num_bins

    for bar in window:
        vol = _bar_volume(bar)
        if vol <= 0:
            continue
        try:
            lo = float(bar["low"])
            hi = float(bar["high"])
        except (KeyError, TypeError, ValueError):
            continue

        if hi <= lo:
            idx = min(num_bins - 1, max(0, int((lo - range_low) / step)))
            hist[idx] += vol
            continue

        span = hi - lo
        for i in range(num_bins):
            bin_lo = range_low + i * step
            bin_hi = bin_lo + step
            overlap = max(0.0, min(hi, bin_hi) - max(lo, bin_lo))
            if overlap > 0:
                hist[i] += vol * (overlap / span)

    total = sum(hist)
    if total <= 0:
        return None

    poc_idx = max(range(num_bins), key=lambda i: hist[i])
    poc_price = round(_bin_mid(range_low, step, poc_idx), 2)

    target = total * value_area_pct
    included = {poc_idx}
    accumulated = hist[poc_idx]

    while accumulated < target and len(included) < num_bins:
        candidates: List[Tuple[int, int]] = []
        for idx in included:
            if idx > 0 and (idx - 1) not in included:
                candidates.append((idx - 1, abs(idx - 1 - poc_idx)))
            if idx < num_bins - 1 and (idx + 1) not in included:
                candidates.append((idx + 1, abs(idx + 1 - poc_idx)))
        if not candidates:
            break
        candidates.sort(key=lambda x: (x[1], x[0]))
        next_idx = candidates[0][0]
        included.add(next_idx)
        accumulated += hist[next_idx]

    val_idx = min(included)
    vah_idx = max(included)
    val_price = round(range_low + val_idx * step, 2)
    vah_price = round(range_low + (vah_idx + 1) * step, 2)

    poc_share = hist[poc_idx] / total if total else 0.0

    return {
        "poc": poc_price,
        "vah": vah_price,
        "val": val_price,
        "lookback_bars": len(window),
        "num_bins": num_bins,
        "value_area_pct": value_area_pct,
        "feature_metrics": {
            "volume_pct_at_poc": round(poc_share, 4),
            "value_area_pct": value_area_pct,
            "lookback_bars": len(window),
            "profile_low": round(range_low, 2),
            "profile_high": round(range_high, 2),
        },
    }
