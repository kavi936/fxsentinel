"""
Deterministic Holistic Scan service for economies tab.

Why this exists:
- Keep scoring logic on backend so it is testable/versioned.
- Reuse existing indicator + calendar inputs and return a stable contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class EconomyHolisticScanService:
    """Build a deterministic short/long macro scan for one economy."""

    VERSION = "economy_scan_v1"
    SUPPORTED_COUNTRIES = {"US", "EUR", "GBP", "JPY"}

    COUNTRY_PAIRS = {
        "US": ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD"],
        "EUR": ["EURUSD", "EURGBP", "EURJPY"],
        "GBP": ["GBPUSD", "EURGBP", "GBPJPY"],
        "JPY": ["USDJPY", "EURJPY", "GBPJPY"],
    }

    def build_scan(
        self,
        country_code: str,
        indicators: Optional[Dict[str, Any]],
        events: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        country = (country_code or "").upper()
        if country not in self.SUPPORTED_COUNTRIES:
            raise ValueError(f"Unsupported country code: {country}")

        indicator_map = indicators or {}
        calendar_events = events or []

        short_components = self._build_short_components(country, indicator_map, calendar_events)
        long_components = self._build_long_components(country, indicator_map)

        short_total = self._sum_weighted(short_components)
        long_total = self._sum_weighted(long_components)

        missing_signals = self._collect_missing_signals(short_components, long_components)
        staleness_seconds = self._estimate_staleness_seconds(indicator_map)

        return {
            "country": country,
            "timestamp": datetime.utcnow().isoformat(),
            "short_term": {
                "bias": self._score_to_bias(short_total),
                "score": short_total,
                "confidence": self._confidence(short_components, missing_signals, staleness_seconds),
                "drivers": short_components,
            },
            "long_term": {
                "bias": self._score_to_bias(long_total),
                "score": long_total,
                "confidence": self._confidence(long_components, missing_signals, staleness_seconds),
                "drivers": long_components,
            },
            "fx_pairs": self._map_fx_pairs(country, short_total),
            "data_quality": {
                "status": self._quality_status(missing_signals, staleness_seconds),
                "missing_signals": missing_signals,
                "staleness_seconds": staleness_seconds,
            },
            "model_version": self.VERSION,
        }

    def _build_short_components(self, country: str, indicators: Dict[str, Any], events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        inflation = self._momentum(indicators.get("inflation-YoY"))
        rates = self._momentum(indicators.get("interest-rate"))
        growth = self._momentum(indicators.get("gdp-qoq"))
        risk = self._event_risk(country, events)

        return [
            self._driver("Rate momentum", 0.35, rates, "Policy-rate direction over recent prints"),
            self._driver("Inflation momentum", 0.25, inflation, "Disinflation supports easing; re-acceleration supports tightening"),
            self._driver("Growth momentum", 0.20, growth, "Near-term growth surprise impulse"),
            self._driver("Event risk", 0.20, -risk, "Upcoming high-impact events increase uncertainty"),
        ]

    def _build_long_components(self, country: str, indicators: Dict[str, Any]) -> List[Dict[str, Any]]:
        inflation = self._momentum(indicators.get("inflation-YoY"))
        rates = self._momentum(indicators.get("interest-rate"))
        unemployment = self._momentum(indicators.get("unemployment-rate"))
        growth = self._momentum(indicators.get("gdp-qoq"))

        # Keep these derived signals nullable so missing inputs never crash scan generation.
        policy_alignment = ((rates - inflation) / 2.0) if (rates is not None and inflation is not None) else None
        labor_strength = (-unemployment) if unemployment is not None else None  # lower unemployment is macro-supportive

        return [
            self._driver("Policy alignment", 0.30, policy_alignment, "Real-rate / policy alignment proxy"),
            self._driver("Growth trend", 0.30, growth, "Medium-term growth trajectory"),
            self._driver("Inflation trend", 0.20, inflation, "Inflation regime pressure"),
            self._driver("Labor trend", 0.20, labor_strength, "Employment backdrop resilience"),
        ]

    def _driver(self, name: str, weight: float, signal: Optional[float], note: str) -> Dict[str, Any]:
        if signal is None:
            return {
                "name": name,
                "direction": "neutral",
                "weight": weight,
                "note": f"{note} (missing signal)",
                "contribution": 0.0,
                "available": False,
            }

        clipped = max(min(signal, 100.0), -100.0)
        direction = "positive" if clipped > 0 else ("negative" if clipped < 0 else "neutral")
        return {
            "name": name,
            "direction": direction,
            "weight": weight,
            "note": note,
            "contribution": round(clipped * weight, 2),
            "available": True,
        }

    def _momentum(self, indicator: Optional[Dict[str, Any]]) -> Optional[float]:
        if not indicator:
            return None
        raw = indicator.get("chartData") or []
        values = [self._to_float(v) for v in raw]
        values = [v for v in values if v is not None]
        if len(values) < 4:
            return None
        latest = sum(values[-2:]) / 2.0
        baseline = sum(values[-6:-2]) / 4.0 if len(values) >= 6 else sum(values[:-2]) / max(len(values) - 2, 1)
        if baseline == 0:
            return None
        # Convert to bounded score so different indicators can be blended.
        pct_change = ((latest - baseline) / abs(baseline)) * 100.0
        return max(min(pct_change * 2.0, 100.0), -100.0)

    def _event_risk(self, country: str, events: List[Dict[str, Any]]) -> float:
        target_currency = "USD" if country == "US" else country
        cutoff = datetime.utcnow() + timedelta(days=14)
        risk = 0.0
        for event in events:
            if (event.get("currency") or "").upper() != target_currency:
                continue
            impact = (event.get("impact") or "").lower()
            if impact not in {"high", "medium"}:
                continue
            date_str = event.get("date")
            if date_str:
                try:
                    event_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if event_date > cutoff:
                        continue
                except Exception:
                    pass
            risk += 25.0 if impact == "high" else 12.5
        return min(risk, 100.0)

    def _map_fx_pairs(self, country: str, short_score: float) -> List[Dict[str, Any]]:
        bias = self._score_to_bias(short_score)
        strength = "strong" if abs(short_score) >= 45 else ("medium" if abs(short_score) >= 20 else "light")
        pairs = self.COUNTRY_PAIRS.get(country, [])
        results: List[Dict[str, Any]] = []

        ccy = "USD" if country == "US" else country
        for pair in pairs:
            base = pair[:3]
            quote = pair[3:]
            if bias == "neutral":
                pair_bias = "neutral"
            elif base == ccy:
                pair_bias = "bullish" if bias == "bullish" else "bearish"
            elif quote == ccy:
                pair_bias = "bearish" if bias == "bullish" else "bullish"
            else:
                pair_bias = "neutral"
            results.append(
                {
                    "pair": pair,
                    "bias": pair_bias,
                    "strength": strength,
                    "reason": f"{country} short-term macro bias is {bias}",
                }
            )
        return results

    def _sum_weighted(self, components: List[Dict[str, Any]]) -> float:
        return round(sum(c.get("contribution", 0.0) for c in components), 2)

    def _collect_missing_signals(self, short_components: List[Dict[str, Any]], long_components: List[Dict[str, Any]]) -> List[str]:
        names: List[str] = []
        for item in [*short_components, *long_components]:
            if not item.get("available", True):
                names.append(item.get("name", "unknown_signal"))
        return sorted(list(set(names)))

    def _estimate_staleness_seconds(self, indicators: Dict[str, Any]) -> int:
        newest: Optional[datetime] = None
        for indicator in indicators.values():
            as_of = indicator.get("asOf")
            if not as_of:
                continue
            try:
                dt = datetime.strptime(as_of, "%Y-%m-%d")
            except Exception:
                continue
            if newest is None or dt > newest:
                newest = dt
        if newest is None:
            return -1
        return int(max((datetime.utcnow() - newest).total_seconds(), 0))

    def _confidence(self, components: List[Dict[str, Any]], missing: List[str], staleness_seconds: int) -> int:
        available = sum(1 for c in components if c.get("available", True))
        total = max(len(components), 1)
        base = int((available / total) * 100)
        if staleness_seconds > 60 * 60 * 24 * 45:
            base -= 20
        elif staleness_seconds > 60 * 60 * 24 * 21:
            base -= 10
        if missing:
            base -= min(len(missing) * 5, 20)
        return max(min(base, 95), 20)

    def _quality_status(self, missing: List[str], staleness_seconds: int) -> str:
        if staleness_seconds == -1:
            return "limited"
        if staleness_seconds > 60 * 60 * 24 * 45 or len(missing) >= 3:
            return "limited"
        if staleness_seconds > 60 * 60 * 24 * 21 or len(missing) >= 1:
            return "fair"
        return "good"

    def _score_to_bias(self, score: float) -> str:
        if score > 20:
            return "bullish"
        if score < -20:
            return "bearish"
        return "neutral"

    def _to_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return None
        cleaned = value.replace("%", "").replace(",", "").strip()
        if cleaned in {"", "N/A", "--", "TBD"}:
            return None
        try:
            return float(cleaned)
        except Exception:
            return None


economy_holistic_scan_service = EconomyHolisticScanService()

