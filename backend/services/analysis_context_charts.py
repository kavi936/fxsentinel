#!/usr/bin/env python3
"""
Calendar analysis context chart — one mini indicator series per event (Phase 1).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.analysis_contract import ANALYSIS_KIND_CALENDAR_EVENT
from services.analysis_indicator_registry import (
    ECONOMY_TO_CURRENCY,
    INDICATOR_TITLES,
    INFLATION_INDICATOR_IDS,
    list_indicators_for_economy,
    pick_best_indicator_for_event,
    resolve_economy_key,
)
from services.economy_context_service import economy_context_service

INFLATION_TARGET_PCT = 2.0


def _indicator_title(indicator_id: str) -> str:
    return INDICATOR_TITLES.get(indicator_id, indicator_id.replace("-", " ").title())


def build_context_chart_payload(
    indicator_id: str,
    economy: str,
    *,
    caption: Optional[str] = None,
    selection_source: str = "deterministic",
) -> Optional[Dict[str, Any]]:
    currency = ECONOMY_TO_CURRENCY.get(economy.upper())
    if not currency:
        return None

    row = economy_context_service.get_indicator_by_id(currency, indicator_id)
    if not row or not isinstance(row, dict):
        return None

    chart_data = row.get("chartData")
    chart_dates = row.get("chartDates")
    if not isinstance(chart_data, list) or len(chart_data) < 2:
        return None
    if not isinstance(chart_dates, list):
        chart_dates = []

    show_target = indicator_id in INFLATION_INDICATOR_IDS

    payload: Dict[str, Any] = {
        "id": indicator_id,
        "title": _indicator_title(indicator_id),
        "currentValue": row.get("currentValue"),
        "asOf": row.get("asOf"),
        "unit": row.get("unit"),
        "source": row.get("source"),
        "chartData": chart_data,
        "chartDates": chart_dates,
        "showTargetLine": show_target,
        "selection_source": selection_source,
    }
    if show_target:
        payload["targetValue"] = INFLATION_TARGET_PCT
    if caption and str(caption).strip():
        payload["caption"] = str(caption).strip()[:320]
    return payload


def resolve_context_chart_for_event(
    event: Dict[str, Any],
    *,
    gpt_indicator_id: Optional[str] = None,
    gpt_caption: Optional[str] = None,
) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    country = event.get("country_code") or event.get("country")
    currency = event.get("currency")
    economy = resolve_economy_key(country, currency)
    allowed: List[str] = list_indicators_for_economy(economy) if economy else []

    meta: Dict[str, Any] = {
        "economy": economy,
        "currency": currency,
        "country_code_resolved": economy,
        "allowed_indicator_ids": allowed,
        "selected_indicator_id": None,
    }

    if not economy or not allowed:
        return None, meta

    title = str(event.get("title") or "")
    selection_source = "deterministic"
    indicator_id = pick_best_indicator_for_event(economy, title)

    gpt_id = str(gpt_indicator_id or "").strip()
    if gpt_id and gpt_id in allowed:
        indicator_id = gpt_id
        selection_source = "gpt"

    meta["selected_indicator_id"] = indicator_id
    chart = build_context_chart_payload(
        indicator_id,
        economy,
        caption=gpt_caption,
        selection_source=selection_source,
    )
    if chart is None and indicator_id:
        # Fallback: first allowed with valid series
        for fallback_id in allowed:
            chart = build_context_chart_payload(
                fallback_id,
                economy,
                selection_source="gpt_fallback" if gpt_id else "deterministic",
            )
            if chart:
                meta["selected_indicator_id"] = fallback_id
                break

    return chart, meta


def apply_context_chart_if_calendar(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_CALENDAR_EVENT or not event:
        return payload

    out = dict(payload)
    gpt_block = out.get("context_chart") if isinstance(out.get("context_chart"), dict) else {}
    gpt_id = gpt_block.get("indicator_id")
    gpt_caption = gpt_block.get("caption")

    chart, meta = resolve_context_chart_for_event(
        event,
        gpt_indicator_id=gpt_id,
        gpt_caption=gpt_caption,
    )
    out["context_chart"] = chart
    out["context_chart_meta"] = meta
    return out
