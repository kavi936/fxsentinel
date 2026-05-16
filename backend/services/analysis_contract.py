"""
Analysis envelope contract (Phase 2).

Every trader-facing analysis response should pass through analysis_pipeline.finalize_analysis
so clients see a consistent wrapper: kind, profile, optional spine, observability, trace.

Spine field semantics for trader_brief_v1 (calendar, live news, economy scan):
  - confidence: synthesis certainty given inputs (not historical win rate).
  - bias: bullish | bearish | neutral for bias_subject (named in spine).
  - invalidation: what would stale or overturn the view.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# analysis_format_version lives in analysis_v1_spine.ANALYSIS_FORMAT_VERSION

# --- analysis_kind: what was analyzed ---
ANALYSIS_KIND_CALENDAR_EVENT = "calendar_event"
ANALYSIS_KIND_CALENDAR_EVENT_LEGACY = "calendar_event_legacy"
ANALYSIS_KIND_LIVE_NEWS = "live_news"
ANALYSIS_KIND_ECONOMY_SCAN = "economy_scan"

# --- spine_profile: which spine field set applies ---
SPINE_PROFILE_TRADER_BRIEF_V1 = "trader_brief_v1"
# Future: SPINE_PROFILE_PAIR_MACRO_V1 = "pair_macro_v1"

VALID_ANALYSIS_KINDS = frozenset(
    {
        ANALYSIS_KIND_CALENDAR_EVENT,
        ANALYSIS_KIND_CALENDAR_EVENT_LEGACY,
        ANALYSIS_KIND_LIVE_NEWS,
        ANALYSIS_KIND_ECONOMY_SCAN,
    }
)

VALID_SPINE_PROFILES = frozenset({SPINE_PROFILE_TRADER_BRIEF_V1})


def default_trace_for_kind(analysis_kind: str) -> List[str]:
    """Minimal pipeline trace until Phase 4 router adds route/model steps."""
    routes = {
        ANALYSIS_KIND_CALENDAR_EVENT: ["classify:calendar_event", "analyze:gpt_enhanced", "finalize:trader_brief_v1"],
        ANALYSIS_KIND_CALENDAR_EVENT_LEGACY: [
            "classify:calendar_event_legacy",
            "analyze:local",
            "finalize:trader_brief_v1",
        ],
        ANALYSIS_KIND_LIVE_NEWS: ["classify:live_news", "analyze:mvp_news", "finalize:trader_brief_v1"],
        ANALYSIS_KIND_ECONOMY_SCAN: [
            "classify:economy_scan",
            "analyze:deterministic_scan",
            "finalize:trader_brief_v1",
        ],
    }
    return list(routes.get(analysis_kind, ["finalize:unknown_kind"]))


def envelope_metadata(
    *,
    analysis_kind: str,
    spine_enabled: bool,
    spine_present: bool,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"analysis_kind": analysis_kind}
    if spine_enabled:
        meta["spine_profile"] = SPINE_PROFILE_TRADER_BRIEF_V1
    return meta


def build_v1_observability(
    payload: Dict[str, Any],
    *,
    latency_ms: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obs: Dict[str, Any] = {
        "spine_present": bool(payload.get("spine")),
        "scenario_warning_count": len(payload.get("scenario_alignment_warnings") or []),
        "alignment_status": payload.get("scenario_alignment_status"),
        "cross_context_note_present": bool(payload.get("cross_context_note")),
    }
    if latency_ms is not None:
        obs["latency_ms"] = latency_ms
    if extra:
        obs.update(extra)
    return {k: v for k, v in obs.items() if v is not None}
