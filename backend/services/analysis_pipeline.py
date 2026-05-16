"""
Phase 2 — single finalize path for all analysis API responses.

Callers run area-specific analyzers first, then finalize_analysis() to attach:
  - analysis_kind, spine_profile (when spine on)
  - spine + calendar validators (via analysis_v1_spine)
  - optional live-news cross-context
  - v1_observability and trace

See analysis_contract.py for envelope semantics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_CALENDAR_EVENT_LEGACY,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
    VALID_ANALYSIS_KINDS,
    build_v1_observability,
    default_trace_for_kind,
    envelope_metadata,
)
from services.analysis_v1_spine import (
    is_analysis_v1_enabled,
    is_analysis_v1_spine_enabled,
    merge_v1_calendar_response,
    merge_v1_economy_scan_response,
    merge_v1_legacy_local_calendar_response,
    merge_v1_news_response,
)

logger = logging.getLogger(__name__)


@dataclass
class FinalizeContext:
    """Per-request inputs required to build spine and side effects."""

    country_code: Optional[str] = None
    validated_event: Optional[Dict[str, Any]] = None
    analysis_type: Optional[str] = None
    news_item: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    token_user_info: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    trace_steps: Optional[List[str]] = None
    observability_extra: Dict[str, Any] = field(default_factory=dict)


def build_live_news_cross_context_note(
    token_user_info: Optional[Dict[str, Any]],
    analysis_result: Dict[str, Any],
) -> str:
    """
    Optional cross-check: live-news USD reaction vs latest US holistic short-term regime.
    """
    if not token_user_info:
        return ""
    try:
        from services.economy_holistic_scan_store import economy_holistic_scan_store

        recent = economy_holistic_scan_store.get_recent_holistic_scans(
            user_info=token_user_info,
            limit=1,
            country_code="US",
        )
        if not recent:
            return ""
        snap = (recent[0] or {}).get("scan_snapshot") or {}
        scan_bias = str(((snap.get("short_term") or {}).get("bias") or "neutral")).lower()
        news_reaction = str(analysis_result.get("immediate_reaction") or "").lower()
        if news_reaction == "bullish_usd":
            news_bias = "bullish"
        elif news_reaction == "bearish_usd":
            news_bias = "bearish"
        else:
            news_bias = "neutral"

        if news_bias in ("bullish", "bearish") and scan_bias in ("bullish", "bearish") and news_bias != scan_bias:
            return (
                "Cross-check: latest US holistic scan short-term regime is "
                f"{scan_bias.upper()}, while this headline implies {news_bias.upper()} USD pressure. "
                "Treat as potential regime/headline tension and reduce conviction until confirmed."
            )
        if news_bias in ("bullish", "bearish") and scan_bias == news_bias:
            return (
                "Cross-check: headline direction aligns with the latest US holistic short-term regime, "
                "which supports directional confidence."
            )
        return ""
    except Exception as cross_err:
        logger.debug("Live news cross-context note unavailable (non-critical): %s", cross_err)
        return ""


def _apply_spine(
    payload: Dict[str, Any],
    analysis_kind: str,
    ctx: FinalizeContext,
) -> Dict[str, Any]:
    if analysis_kind == ANALYSIS_KIND_CALENDAR_EVENT:
        if not ctx.validated_event:
            raise ValueError("FinalizeContext.validated_event required for calendar_event")
        return merge_v1_calendar_response(
            payload,
            validated_event=ctx.validated_event,
            analysis_type=ctx.analysis_type or "pre_event",
        )
    if analysis_kind == ANALYSIS_KIND_CALENDAR_EVENT_LEGACY:
        if not ctx.event:
            raise ValueError("FinalizeContext.event required for calendar_event_legacy")
        return merge_v1_legacy_local_calendar_response(payload, event=ctx.event)
    if analysis_kind == ANALYSIS_KIND_LIVE_NEWS:
        if not ctx.news_item:
            raise ValueError("FinalizeContext.news_item required for live_news")
        return merge_v1_news_response(payload, ctx.news_item)
    if analysis_kind == ANALYSIS_KIND_ECONOMY_SCAN:
        if not ctx.country_code:
            raise ValueError("FinalizeContext.country_code required for economy_scan")
        return merge_v1_economy_scan_response(payload, ctx.country_code)
    raise ValueError(f"Unsupported analysis_kind for spine merge: {analysis_kind}")


def _apply_news_cross_context(out: Dict[str, Any], ctx: FinalizeContext) -> Dict[str, Any]:
    cross_note = build_live_news_cross_context_note(ctx.token_user_info, out)
    if not cross_note:
        return out
    out = dict(out)
    out["cross_context_note"] = cross_note
    spine = out.get("spine")
    if isinstance(spine, dict):
        spine = dict(spine)
        existing = str(spine.get("confidence_reason") or "").strip()
        spine["confidence_reason"] = f"{existing} {cross_note}".strip()
        out["spine"] = spine
    return out


def finalize_analysis(
    payload: Dict[str, Any],
    *,
    analysis_kind: str,
    context: Optional[FinalizeContext] = None,
    spine_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Attach unified envelope fields to an analyzer payload (additive only).

    Does not run GPT/MVP/scan — callers produce body first, then finalize.
    """
    if analysis_kind not in VALID_ANALYSIS_KINDS:
        raise ValueError(f"Invalid analysis_kind: {analysis_kind}")

    # V1 off (default): return analyzer payload unchanged — legacy UX on wire + UI.
    if spine_enabled is None and not is_analysis_v1_enabled():
        return dict(payload)
    if spine_enabled is False:
        return dict(payload)

    ctx = context or FinalizeContext()
    if spine_enabled is None:
        spine_enabled = is_analysis_v1_spine_enabled()

    out = dict(payload)
    out.update(envelope_metadata(analysis_kind=analysis_kind, spine_enabled=spine_enabled, spine_present=False))

    if spine_enabled:
        out = _apply_spine(out, analysis_kind, ctx)
        out.update(
            envelope_metadata(
                analysis_kind=analysis_kind,
                spine_enabled=True,
                spine_present=bool(out.get("spine")),
            )
        )
        if analysis_kind == ANALYSIS_KIND_LIVE_NEWS:
            out = _apply_news_cross_context(out, ctx)

    trace_steps = ctx.trace_steps if ctx.trace_steps is not None else default_trace_for_kind(analysis_kind)
    now_iso = datetime.now(timezone.utc).isoformat()
    out["trace"] = {"steps": trace_steps, "finalized_at": now_iso}

    obs = build_v1_observability(out, latency_ms=ctx.latency_ms, extra=ctx.observability_extra)
    obs["generated_at"] = now_iso
    out["v1_observability"] = obs

    return out
