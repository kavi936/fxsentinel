"""
Deterministic Holistic Scan service for economies tab.

Why this exists:
- Keep scoring logic on backend so it is testable/versioned.
- Reuse existing indicator + calendar inputs and return a stable contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
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

    # Same `centralBank` field as Overview’s `src/data/central-bank-documents.json`
    COUNTRY_TO_CB_BANK = {"US": "FED", "EUR": "ECB", "GBP": "BOE", "JPY": "BOJ"}

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parent.parent.parent

    def _load_holistic_overlay(self) -> Dict[str, Any]:
        path = Path(__file__).resolve().parent.parent / "data" / "holistic_scan_context.json"
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"version": None, "lastUpdated": None, "global_themes": [], "economy_hooks": {}}

    def _load_central_bank_snippets(self, country: str) -> Dict[str, Any]:
        """
        Pulls key excerpts from the same JSON catalog the Overview Central Bank Analysis uses:
        `src/data/central-bank-documents.json` (bundled in frontend via `useCentralBankDocuments`).
        """
        bank = self.COUNTRY_TO_CB_BANK.get(country)
        if not bank:
            return {"bank": None, "snippets": [], "source": None, "catalog_version": None}

        candidates = [
            self._repo_root() / "src" / "data" / "central-bank-documents.json",
            Path(__file__).resolve().parent.parent / "data" / "central-bank-documents.json",
        ]
        data = None
        used_path = None
        for path in candidates:
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                try:
                    used_path = str(path.relative_to(self._repo_root()))
                except ValueError:
                    used_path = str(path)
                break
            except Exception:
                continue
        if not data:
            return {
                "bank": bank,
                "snippets": [],
                "source": "src/data/central-bank-documents.json",
                "catalog_version": None,
                "error": "catalog_unavailable",
            }

        docs = [d for d in data.get("documents", []) if d.get("centralBank") == bank]
        docs.sort(key=lambda d: d.get("date") or "", reverse=True)
        snippets: List[Dict[str, Any]] = []
        for d in docs[:3]:
            desc = (d.get("description") or "").strip()
            if len(desc) > 240:
                desc = desc[:237] + "..."
            snippets.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "date": d.get("date"),
                    "description": desc,
                }
            )
        return {
            "bank": bank,
            "snippets": snippets,
            "source": used_path or "src/data/central-bank-documents.json",
            "catalog_version": data.get("version"),
        }

    def build_scan(
        self,
        country_code: str,
        indicators: Optional[Dict[str, Any]],
        events: Optional[List[Dict[str, Any]]],
        yields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        country = (country_code or "").upper()
        if country not in self.SUPPORTED_COUNTRIES:
            raise ValueError(f"Unsupported country code: {country}")

        indicator_map = indicators or {}
        calendar_events = events or []
        yield_map = yields or {}

        yield_context = self._build_yield_context(country, yield_map)
        short_components = self._build_short_components(country, indicator_map, calendar_events, yield_context)
        long_components = self._build_long_components(country, indicator_map, yield_context)

        short_total = self._sum_weighted(short_components)
        long_total = self._sum_weighted(long_components)

        missing_signals = self._collect_missing_signals(short_components, long_components)
        staleness_seconds = self._estimate_staleness_seconds(indicator_map)
        event_risk = self._event_risk(country, calendar_events)

        short_term_payload = {
                "bias": self._score_to_bias(short_total),
                "score": short_total,
                "confidence": self._confidence(short_components, missing_signals, staleness_seconds),
                "drivers": short_components,
            }
        long_term_payload = {
                "bias": self._score_to_bias(long_total),
                "score": long_total,
                "confidence": self._confidence(long_components, missing_signals, staleness_seconds),
                "drivers": long_components,
            }

        fx_pairs = self._map_fx_pairs(country, short_total)
        macro_overlay = self._load_holistic_overlay()
        central_bank_context = self._load_central_bank_snippets(country)
        highlights = self._build_highlights(
            country=country,
            short_term=short_term_payload,
            long_term=long_term_payload,
            yield_context=yield_context,
            fx_pairs=fx_pairs,
            data_quality_status=self._quality_status(missing_signals, staleness_seconds),
            missing_signals=missing_signals,
            staleness_seconds=staleness_seconds,
            event_risk_score=event_risk,
            macro_overlay=macro_overlay,
            central_bank_context=central_bank_context,
        )

        return {
            "country": country,
            "economy": self._country_label(country),
            "timestamp": datetime.utcnow().isoformat(),
            "short_term": {
                **short_term_payload,
            },
            "long_term": {
                **long_term_payload,
            },
            "highlights": highlights,
            "yield_context": yield_context,
            "trading_ranges": self._build_trading_ranges(short_total, long_total, yield_context),
            "narrative": self._build_narrative(
                country, short_total, long_total, yield_context, macro_overlay, central_bank_context
            ),
            "context_sources": {
                "macro_overlay": {
                    "file": "backend/data/holistic_scan_context.json",
                    "lastUpdated": macro_overlay.get("lastUpdated"),
                    "version": macro_overlay.get("version"),
                },
                "central_bank_documents": {
                    "file": central_bank_context.get("source"),
                    "catalog_version": central_bank_context.get("catalog_version"),
                    "bank": central_bank_context.get("bank"),
                    "documents_sampled": len(central_bank_context.get("snippets") or []),
                },
            },
            "fx_pairs": fx_pairs,
            "data_quality": {
                "status": self._quality_status(missing_signals, staleness_seconds),
                "missing_signals": missing_signals,
                "staleness_seconds": staleness_seconds,
            },
            "model_version": self.VERSION,
        }

    def _build_short_components(
        self,
        country: str,
        indicators: Dict[str, Any],
        events: List[Dict[str, Any]],
        yield_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        inflation = self._momentum(indicators.get("inflation-YoY"))
        rates = self._momentum(indicators.get("interest-rate"))
        growth = self._momentum(indicators.get("gdp-qoq"))
        risk = self._event_risk(country, events)
        daily_change_signal = yield_context.get("short_term_signal")

        return [
            self._driver("Rate momentum", 0.35, rates, "Policy-rate direction over recent prints"),
            self._driver("Inflation momentum", 0.25, inflation, "Disinflation supports easing; re-acceleration supports tightening"),
            self._driver("Growth momentum", 0.20, growth, "Near-term growth surprise impulse"),
            self._driver("Yield daily impulse", 0.20, daily_change_signal, "2Y/10Y/30Y daily changes imply near-term rate repricing"),
            self._driver("Event risk", 0.15, -risk, "Upcoming high-impact events increase uncertainty"),
        ]

    def _build_long_components(self, country: str, indicators: Dict[str, Any], yield_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        inflation = self._momentum(indicators.get("inflation-YoY"))
        rates = self._momentum(indicators.get("interest-rate"))
        unemployment = self._momentum(indicators.get("unemployment-rate"))
        growth = self._momentum(indicators.get("gdp-qoq"))
        curve_signal = yield_context.get("long_term_signal")

        # Keep these derived signals nullable so missing inputs never crash scan generation.
        policy_alignment = ((rates - inflation) / 2.0) if (rates is not None and inflation is not None) else None
        labor_strength = (-unemployment) if unemployment is not None else None  # lower unemployment is macro-supportive

        return [
            self._driver("Policy alignment", 0.25, policy_alignment, "Real-rate / policy alignment proxy"),
            self._driver("Growth trend", 0.25, growth, "Medium-term growth trajectory"),
            self._driver("Inflation trend", 0.20, inflation, "Inflation regime pressure"),
            self._driver("Labor trend", 0.20, labor_strength, "Employment backdrop resilience"),
            self._driver("Yield curve regime", 0.10, curve_signal, "2s10s and 10s30s shape reflects long-horizon investor expectations"),
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

    def _build_yield_context(self, country: str, yields: Dict[str, Any]) -> Dict[str, Any]:
        ticker_map = {
            "US": ("US02Y", "US10Y", "US30Y"),
            "EUR": ("EU02Y", "EU10Y", "EU30Y"),
            "GBP": ("GB02Y", "GB10Y", "GB30Y"),
            "JPY": ("JP02Y", "JP10Y", "JP30Y"),
        }
        fallback_map = {
            "EUR": ("DE02Y", "DE10Y", "DE30Y"),
        }

        keys = ticker_map.get(country, ("US02Y", "US10Y", "US30Y"))
        two = yields.get(keys[0]) or yields.get(fallback_map.get(country, ("", "", ""))[0]) or {}
        ten = yields.get(keys[1]) or yields.get(fallback_map.get(country, ("", "", ""))[1]) or {}
        thirty = yields.get(keys[2]) or yields.get(fallback_map.get(country, ("", "", ""))[2]) or {}

        y2 = self._to_float(two.get("price"))
        y10 = self._to_float(ten.get("price"))
        y30 = self._to_float(thirty.get("price"))

        c2 = self._to_float(two.get("change"))
        c10 = self._to_float(ten.get("change"))
        c30 = self._to_float(thirty.get("change"))

        slope_2s10s = (y10 - y2) if (y10 is not None and y2 is not None) else None
        slope_10s30s = (y30 - y10) if (y30 is not None and y10 is not None) else None

        # Daily short-term impulse: rising yields imply hawkish repricing, falling implies dovish repricing.
        change_values = [v for v in [c2, c10, c30] if v is not None]
        avg_change = (sum(change_values) / len(change_values)) if change_values else None
        short_term_signal = max(min((avg_change or 0.0) * 400.0, 100.0), -100.0) if avg_change is not None else None

        long_term_signal = None
        if slope_2s10s is not None:
            long_term_signal = max(min(slope_2s10s * 100.0, 100.0), -100.0)

        sentiment = self._yield_sentiment_label(slope_2s10s, avg_change)
        source = two.get("source") or ten.get("source") or thirty.get("source") or "fallback"

        return {
            "2Y": {"value": y2, "change": c2},
            "10Y": {"value": y10, "change": c10},
            "30Y": {"value": y30, "change": c30},
            "curve_2s10s": slope_2s10s,
            "curve_10s30s": slope_10s30s,
            "investor_sentiment": sentiment,
            "short_term_signal": short_term_signal,
            "long_term_signal": long_term_signal,
            "source": source,
        }

    def _yield_sentiment_label(self, slope_2s10s: Optional[float], avg_change: Optional[float]) -> str:
        if slope_2s10s is None and avg_change is None:
            return "limited_data"
        if slope_2s10s is not None and slope_2s10s < -0.25:
            return "inversion_defensive"
        if avg_change is not None and avg_change > 0.02:
            return "hawkish_repricing"
        if avg_change is not None and avg_change < -0.02:
            return "dovish_repricing"
        if slope_2s10s is not None and slope_2s10s > 0.20:
            return "normalizing_growth_bias"
        return "balanced"

    def _build_trading_ranges(self, short_score: float, long_score: float, yield_context: Dict[str, Any]) -> Dict[str, str]:
        short_bias = self._score_to_bias(short_score)
        long_bias = self._score_to_bias(long_score)
        sentiment = yield_context.get("investor_sentiment", "balanced")
        short_text = (
            f"Short-term regime is {short_bias}. Daily yield impulse and event risk suggest "
            f"{'breakout-prone' if sentiment in {'hawkish_repricing', 'dovish_repricing'} else 'range-to-trend'} conditions over coming sessions."
        )
        long_text = (
            f"Long-term regime is {long_bias}. Curve structure ({sentiment}) implies "
            f"{'defensive positioning and lower conviction trend extension' if sentiment == 'inversion_defensive' else 'gradual macro trend development across weeks to months'}."
        )
        return {"short_term": short_text, "long_term": long_text}

    def _build_narrative(
        self,
        country: str,
        short_score: float,
        long_score: float,
        yield_context: Dict[str, Any],
        macro_overlay: Dict[str, Any],
        central_bank_context: Dict[str, Any],
    ) -> Dict[str, str]:
        short_bias = self._score_to_bias(short_score)
        long_bias = self._score_to_bias(long_score)
        y2 = yield_context.get("2Y", {}).get("value")
        y10 = yield_context.get("10Y", {}).get("value")
        y30 = yield_context.get("30Y", {}).get("value")
        c2 = yield_context.get("2Y", {}).get("change")
        c10 = yield_context.get("10Y", {}).get("change")
        c30 = yield_context.get("30Y", {}).get("change")
        sentiment = yield_context.get("investor_sentiment", "balanced")
        sentiment_phrase = sentiment.replace("_", " ")

        short_text = (
            f"{self._country_label(country)} short-term macro conditions currently screen as {short_bias}. "
            f"Sovereign benchmark yields for this economy are at 2Y / 10Y / 30Y of "
            f"{self._fmt(y2)} / {self._fmt(y10)} / {self._fmt(y30)}, with session moves of "
            f"{self._fmt_signed(c2)} / {self._fmt_signed(c10)} / {self._fmt_signed(c30)}. "
            f"Together that reads as a {sentiment_phrase} rate backdrop—markets are repricing near-term policy and growth expectations, which is the main bridge from rates into FX here."
        )
        long_text = (
            f"On a longer horizon, the regime reads {long_bias}. The indicator composite and yield-curve shape are blended to estimate whether policy is moving toward "
            f"tightening persistence, neutral stabilization, or easing repricing. This keeps long-term direction anchored to macro structure instead of one-off event noise."
        )
        fx_text = (
            f"FX implications are mapped into correlated pairs using base/quote orientation. "
            f"When {self._country_label(country)} has a stronger yield and policy profile, pairs where this economy's currency is the base tend to inherit bullish bias, "
            f"while quote-side exposure tends to inherit bearish bias; the reverse applies when the scan weakens."
        )

        theme = (macro_overlay.get("global_themes") or [{}])[0] if macro_overlay.get("global_themes") else {}
        hook = (macro_overlay.get("economy_hooks") or {}).get(country, "")
        geopolitical_energy = " ".join(
            s for s in [theme.get("summary", "").strip(), theme.get("energy_channel", "").strip(), hook.strip()] if s
        )
        if not geopolitical_energy:
            geopolitical_energy = (
                "No curated geopolitical/energy overlay is configured; extend `backend/data/holistic_scan_context.json` to reflect current risks."
            )

        cb_snippets = central_bank_context.get("snippets") or []
        bank = central_bank_context.get("bank") or "N/A"
        if cb_snippets:
            first = cb_snippets[0]
            central_bank_text = (
                f"Policy communication context ({bank}, from the same document catalog as Overview’s Central Bank Analysis): "
                f"“{first.get('description', '')}” "
                f"(see {first.get('title', 'latest release')} dated {first.get('date', 'n/a')})."
            )
        else:
            central_bank_text = (
                f"No recent entries were loaded for {bank} from `central-bank-documents.json`; add or refresh documents in that catalog to deepen policy context."
            )

        return {
            "short_term": short_text,
            "long_term": long_text,
            "fx": fx_text,
            "geopolitical_energy": geopolitical_energy,
            "central_bank_context": central_bank_text,
        }

    def _build_highlights(
        self,
        country: str,
        short_term: Dict[str, Any],
        long_term: Dict[str, Any],
        yield_context: Dict[str, Any],
        fx_pairs: List[Dict[str, Any]],
        data_quality_status: str,
        missing_signals: List[str],
        staleness_seconds: int,
        event_risk_score: float,
        macro_overlay: Dict[str, Any],
        central_bank_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Structured key points for UI: bold label + emphasis token + supporting detail.
        Contract guarantees at least `rules.minimum_items` entries for consistent layout.
        """
        st_bias = (short_term.get("bias") or "neutral").upper()
        lt_bias = (long_term.get("bias") or "neutral").upper()
        st_score = short_term.get("score")
        lt_score = long_term.get("score")
        st_conf = short_term.get("confidence")
        lt_conf = long_term.get("confidence")
        sentiment = (yield_context.get("investor_sentiment") or "balanced").replace("_", " ").upper()

        y2 = yield_context.get("2Y", {}).get("value")
        y10 = yield_context.get("10Y", {}).get("value")
        y30 = yield_context.get("30Y", {}).get("value")
        c2 = yield_context.get("2Y", {}).get("change")
        c10 = yield_context.get("10Y", {}).get("change")
        c30 = yield_context.get("30Y", {}).get("change")
        curve = yield_context.get("curve_2s10s")
        curve_10s30s = yield_context.get("curve_10s30s")

        top = fx_pairs[0] if fx_pairs else {}
        pair_line = f"{top.get('pair', 'N/A')} → {(top.get('bias') or 'neutral').upper()}"
        if len(fx_pairs) > 1:
            second = fx_pairs[1]
            pair_line += f"; {second.get('pair')} → {(second.get('bias') or 'neutral').upper()}"

        stale_note = (
            f"Oldest indicator ~{staleness_seconds // 86400}d behind UTC" if staleness_seconds >= 0 else "Indicator dates incomplete"
        )

        theme0 = (macro_overlay.get("global_themes") or [{}])[0] if macro_overlay.get("global_themes") else {}
        geo_title = (theme0.get("title") or "Geopolitical & energy").strip()
        geo_sev = (theme0.get("severity") or "watch").upper()
        geo_detail = " ".join(
            s for s in [theme0.get("summary", "").strip(), (macro_overlay.get("economy_hooks") or {}).get(country, "").strip()] if s
        ) or "See `backend/data/holistic_scan_context.json` for curated risks."

        cb_bank = central_bank_context.get("bank") or "N/A"
        cb_first = (central_bank_context.get("snippets") or [{}])[0]
        cb_emphasis = f"{cb_bank} · {cb_first.get('date') or 'n/a'}" if cb_first else f"{cb_bank} (no docs)"
        cb_detail = (cb_first.get("title") or "Latest policy library entry") + (
            f" — {(cb_first.get('description') or '')[:160]}…" if cb_first.get("description") else ""
        )

        items: List[Dict[str, Any]] = [
            {
                "id": "short_term_regime",
                "label": "Short-term regime",
                "emphasis": st_bias,
                "detail": f"Composite score {st_score} with {st_conf}% confidence on a 2–6 week horizon.",
            },
            {
                "id": "long_term_regime",
                "label": "Long-term regime",
                "emphasis": lt_bias,
                "detail": f"Composite score {lt_score} with {lt_conf}% confidence on a 3–12 month horizon.",
            },
            {
                "id": "geopolitical_energy",
                "label": geo_title,
                "emphasis": geo_sev,
                "detail": geo_detail,
            },
            {
                "id": "central_bank_catalog",
                "label": "Central bank document context",
                "emphasis": cb_emphasis,
                "detail": cb_detail or f"Same JSON catalog as Overview: `src/data/central-bank-documents.json` ({cb_bank}).",
            },
            {
                "id": "yield_tape",
                "label": "Live sovereign yields",
                "emphasis": sentiment,
                "detail": (
                    f"2Y / 10Y / 30Y: {self._fmt(y2)} / {self._fmt(y10)} / {self._fmt(y30)}. "
                    f"Session change (Δ): {self._fmt_signed(c2)} / {self._fmt_signed(c10)} / {self._fmt_signed(c30)}."
                ),
            },
            {
                "id": "curve_shape",
                "label": "Curve diagnostics",
                "emphasis": (
                    f"2s10s {curve:+.2f} pp" if curve is not None else "2s10s N/A"
                ),
                "detail": (
                    f"10s30s {curve_10s30s:+.2f} pp. "
                    f"Steepening often ties to growth/reflation; flat/inverted warns late-cycle or recession pricing."
                    if curve_10s30s is not None
                    else "Use 2s10s with daily yield moves to infer near-term rate repricing vs long-run growth."
                ),
            },
            {
                "id": "fx_lead",
                "label": "FX map (correlated pairs)",
                "emphasis": pair_line,
                "detail": "Bias uses base/quote orientation vs this economy’s currency; strength label reflects composite short-term score.",
            },
            {
                "id": "event_risk",
                "label": "Calendar stress (14 days)",
                "emphasis": f"{int(round(min(event_risk_score, 100)))} / 100",
                "detail": "Higher = more high/medium-impact events for this currency in the next two weeks; raises volatility of interpretation.",
            },
            {
                "id": "data_quality",
                "label": "Scan reliability",
                "emphasis": data_quality_status.upper(),
                "detail": f"{stale_note}. Missing signal families: {len(missing_signals)} ({', '.join(missing_signals[:4])}{'…' if len(missing_signals) > 4 else ''}).",
            },
        ]

        minimum = 5
        while len(items) < minimum:
            items.append(
                {
                    "id": f"pad_{len(items)}",
                    "label": "Context",
                    "emphasis": "NEUTRAL",
                    "detail": "Additional macro context will refine as more indicators connect.",
                }
            )

        return {
            "rules": {
                "minimum_items": minimum,
                "render": {
                    "bold": ["label"],
                    "highlight": ["emphasis"],
                    "body": "detail",
                },
            },
            "items": items,
        }

    def _country_label(self, country: str) -> str:
        labels = {
            "US": "United States",
            "EUR": "Euro Area",
            "GBP": "United Kingdom",
            "JPY": "Japan",
        }
        return labels.get(country, country)

    def _fmt(self, v: Optional[float]) -> str:
        return "N/A" if v is None else f"{v:.2f}%"

    def _fmt_signed(self, v: Optional[float]) -> str:
        return "N/A" if v is None else f"{v:+.2f}"

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

