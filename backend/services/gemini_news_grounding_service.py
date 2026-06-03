#!/usr/bin/env python3
"""
Gemini Google Search grounding for live-news analysis (Phase 1+).

Fetches related headline evidence before OpenAI analysis. Fail-open: errors return
a skipped/failed pack and analysis continues without grounding context.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

PACK_VERSION = "2026-06-03"
_GROUNDING_REDIRECT_HOST = "vertexaisearch.cloud.google.com"

TIER_1_DOMAIN_SUFFIXES = (
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "cnbc.com",
    "marketwatch.com",
    "investing.com",
    "forexlive.com",
    "dailyfx.com",
    "fxstreet.com",
    "bbc.com",
    "bbc.co.uk",
    "apnews.com",
    "federalreserve.gov",
    "ecb.europa.eu",
    "bankofengland.co.uk",
    "boj.or.jp",
    "financialpost.com",
    "japantimes.co.jp",
    "bis.org",
)

TIER_2_DOMAIN_SUFFIXES = (
    "yahoo.com",
    "finance.yahoo.com",
    "businessinsider.com",
    "seekingalpha.com",
)

_VALID_STORY_ARC = frozenset({"new_development", "ongoing_story", "unclear"})
_VALID_RELATIONSHIP = frozenset({"corroborates", "contradicts", "background", "market_reaction"})
_VALID_RECENCY = frozenset({"last_24h", "last_7d", "older", "unknown"})

_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def is_live_news_gemini_grounding_enabled() -> bool:
    return os.getenv("LIVE_NEWS_GEMINI_GROUNDING_ENABLED", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def is_live_news_gemini_grounding_debug() -> bool:
    return os.getenv("LIVE_NEWS_GEMINI_GROUNDING_DEBUG", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _grounding_model() -> str:
    return (
        os.getenv("LIVE_NEWS_GEMINI_GROUNDING_MODEL")
        or os.getenv("GEMINI_GROUNDING_SPIKE_MODEL")
        or "gemini-2.5-flash"
    ).strip()


def _cache_ttl_sec() -> int:
    try:
        return max(60, int(os.getenv("LIVE_NEWS_GEMINI_GROUNDING_CACHE_TTL_SEC", "1800")))
    except (TypeError, ValueError):
        return 1800


def _cache_key(news_item: Dict[str, Any]) -> str:
    nid = str(news_item.get("id") or "")
    if nid:
        return f"id:{nid}"
    title = str(news_item.get("title") or "").strip().lower()
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    return f"title:{digest}"


def _skipped_pack(news_item: Dict[str, Any], reason: str) -> Dict[str, Any]:
    from services.analysis_context_pack import _infer_news_currency

    currency = _infer_news_currency(news_item)
    return _build_pack(
        news_item,
        primary_currency=currency,
        web_search_queries=[],
        grounding_chunks=[],
        structured=None,
        latency_ms=0,
        model=_grounding_model(),
        status_override="skipped",
        reason_override=reason,
    )


def _domain_from_uri(uri: str) -> str:
    try:
        host = (urlparse(uri).netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _normalize_domain_label(label: str) -> str:
    raw = (label or "").strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        return _domain_from_uri(raw)
    raw = raw.split("/")[0].split("?")[0]
    if raw.startswith("www."):
        raw = raw[4:]
    return raw


def _publisher_domain_from_chunk(title: str, uri: str) -> str:
    uri_host = _domain_from_uri(uri)
    title_domain = _normalize_domain_label(title)
    if uri_host == _GROUNDING_REDIRECT_HOST and title_domain:
        return title_domain
    if title_domain and "." in title_domain and len(title_domain) < 80:
        return title_domain
    return uri_host or title_domain


def _publisher_tier(domain: str) -> str:
    d = (domain or "").lower()
    for suffix in TIER_1_DOMAIN_SUFFIXES:
        if d == suffix or d.endswith("." + suffix):
            return "tier_1"
    for suffix in TIER_2_DOMAIN_SUFFIXES:
        if d == suffix or d.endswith("." + suffix):
            return "tier_2"
    return "other"


def _format_feed_context(news_item: Dict[str, Any], primary_currency: str) -> str:
    title = news_item.get("title") or ""
    summary = news_item.get("summary") or ""
    source = news_item.get("source") or ""
    impact = news_item.get("impact") or "medium"
    pairs = news_item.get("currency_pairs") or []
    pairs_str = ", ".join(str(p) for p in pairs[:6]) if pairs else "none listed"
    return f"""- Title: {title}
- Summary: {summary}
- Source: {source}
- Impact (our feed): {impact}
- Primary currency: {primary_currency}
- Currency pairs (our feed): {pairs_str}"""


def _build_retrieval_prompt(news_item: Dict[str, Any], primary_currency: str) -> str:
    feed_context = _format_feed_context(news_item, primary_currency)
    return f"""You are a forex news researcher. Use Google Search to find RELATED coverage of this headline (not duplicate reposts of the same wire).

PRIMARY ARTICLE (our feed):
{feed_context}

TASK:
1. Perform at most TWO focused web searches.
2. Find up to 6 related pieces from credible financial publishers when possible.
3. Focus on: corroboration, contradiction, prior context, market reaction — not generic forex education.
4. Do NOT invent facts, quotes, or URLs. Use only what search supports. Use "unknown" when unsure.

Respond with ONLY valid JSON (no markdown fences), matching this schema:
{{
  "story_arc": "new_development | ongoing_story | unclear",
  "primary_entities": ["Fed", "BoJ", "CPI", ...],
  "synthesis_bullets": ["max 6 short bullets on what related coverage shows overall"],
  "contradictions_note": "one sentence if sources disagree, else empty string",
  "related_items": [
    {{
      "headline": "actual related article headline from search",
      "publisher": "publisher name or domain",
      "relationship": "corroborates | contradicts | background | market_reaction",
      "takeaway": "one sentence: why this matters for FX traders",
      "recency_bucket": "last_24h | last_7d | older | unknown",
      "key_fact": "optional specific data point or quote fragment from search, else empty"
    }}
  ]
}}

Rules:
- related_items: 3 to 6 entries when possible; omit items you cannot support from search.
- recency_bucket is approximate only — use unknown if unclear (exact publish times are NOT required).
- headline must describe the related story, not just a domain name."""


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text or not text.strip():
        return None
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(raw[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _normalize_structured(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not data:
        return {
            "story_arc": "unclear",
            "primary_entities": [],
            "synthesis_bullets": [],
            "contradictions_note": "",
            "related_items": [],
        }

    arc = str(data.get("story_arc") or "unclear").lower().strip()
    if arc not in _VALID_STORY_ARC:
        arc = "unclear"

    entities = data.get("primary_entities") or []
    if not isinstance(entities, list):
        entities = []
    entities = [str(e).strip() for e in entities if str(e).strip()][:8]

    bullets = data.get("synthesis_bullets") or []
    if not isinstance(bullets, list):
        bullets = []
    bullets = [str(b).strip() for b in bullets if str(b).strip()][:6]

    contradictions = str(data.get("contradictions_note") or "").strip()[:500]

    items_in = data.get("related_items") or []
    related_items: List[Dict[str, str]] = []
    if isinstance(items_in, list):
        for raw_item in items_in[:8]:
            if not isinstance(raw_item, dict):
                continue
            headline = str(raw_item.get("headline") or "").strip()
            publisher = str(raw_item.get("publisher") or "").strip()
            takeaway = str(raw_item.get("takeaway") or "").strip()
            if not headline and not takeaway:
                continue
            rel = str(raw_item.get("relationship") or "background").lower().strip()
            if rel not in _VALID_RELATIONSHIP:
                rel = "background"
            recency = str(raw_item.get("recency_bucket") or "unknown").lower().strip()
            if recency not in _VALID_RECENCY:
                recency = "unknown"
            key_fact = str(raw_item.get("key_fact") or "").strip()[:300]
            domain = _normalize_domain_label(publisher) if publisher else ""
            related_items.append(
                {
                    "headline": headline or publisher,
                    "publisher": publisher or domain or "unknown",
                    "publisher_domain": domain,
                    "relationship": rel,
                    "takeaway": takeaway,
                    "recency_bucket": recency,
                    "key_fact": key_fact,
                }
            )

    return {
        "story_arc": arc,
        "primary_entities": entities,
        "synthesis_bullets": bullets,
        "contradictions_note": contradictions,
        "related_items": related_items[:6],
    }


def _chunks_from_grounding_metadata(meta: Any) -> Tuple[List[str], List[Dict[str, str]]]:
    if meta is None:
        return [], []

    queries = getattr(meta, "web_search_queries", None) or []
    chunks_raw = getattr(meta, "grounding_chunks", None) or []
    queries_out = [str(q) for q in queries if q]
    chunks_out: List[Dict[str, str]] = []

    for chunk in chunks_raw:
        web = getattr(chunk, "web", None)
        if web is None and isinstance(chunk, dict):
            web = chunk.get("web")
        if web is None:
            continue
        uri = getattr(web, "uri", None) or (web.get("uri") if isinstance(web, dict) else "") or ""
        title = getattr(web, "title", None) or (web.get("title") if isinstance(web, dict) else "") or ""
        uri = str(uri).strip()
        title = str(title).strip()
        if not uri:
            continue
        domain = _publisher_domain_from_chunk(title, uri)
        chunks_out.append({"uri": uri, "title": title or domain, "domain": domain})

    return queries_out, chunks_out


def _dedupe_chunks(chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for c in chunks:
        key = (c.get("domain") or "", (c.get("title") or "").lower()[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _domain_matches(publisher_domain: str, chunk_domain: str) -> bool:
    if not publisher_domain or not chunk_domain:
        return False
    p, c = publisher_domain.lower(), chunk_domain.lower()
    return p == c or p.endswith("." + c) or c.endswith("." + p)


def _merge_structured_with_chunks(
    structured: Dict[str, Any],
    grounding_chunks: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    """Build evidence rows from Gemini JSON + attach grounding URLs where domains match."""
    chunks = _dedupe_chunks(grounding_chunks)
    used_chunk_idx: set = set()
    evidence: List[Dict[str, Any]] = []

    for item in structured.get("related_items") or []:
        domain = item.get("publisher_domain") or _normalize_domain_label(item.get("publisher") or "")
        url = ""
        for idx, chunk in enumerate(chunks):
            if idx in used_chunk_idx:
                continue
            if _domain_matches(domain, chunk.get("domain") or ""):
                url = chunk.get("uri") or ""
                used_chunk_idx.add(idx)
                if not domain:
                    domain = chunk.get("domain") or domain
                break
        tier = _publisher_tier(domain)
        snippet_parts = [item.get("takeaway") or ""]
        if item.get("key_fact"):
            snippet_parts.append(f"Key fact: {item['key_fact']}")
        evidence.append(
            {
                "headline": item.get("headline") or item.get("publisher") or domain,
                "publisher": item.get("publisher") or domain,
                "snippet": " ".join(p for p in snippet_parts if p).strip()[:500],
                "source": domain or "unknown",
                "url": url,
                "relationship": item.get("relationship") or "background",
                "recency_bucket": item.get("recency_bucket") or "unknown",
                "key_fact": item.get("key_fact") or "",
                "relevance_score": 0.75 if tier == "tier_1" else 0.55 if tier == "tier_2" else 0.35,
                "publisher_tier": tier,
            }
        )

    for idx, chunk in enumerate(chunks):
        if idx in used_chunk_idx:
            continue
        domain = chunk.get("domain") or ""
        tier = _publisher_tier(domain)
        evidence.append(
            {
                "headline": chunk.get("title") or domain,
                "publisher": domain,
                "snippet": "",
                "source": domain,
                "url": chunk.get("uri") or "",
                "relationship": "background",
                "recency_bucket": "unknown",
                "key_fact": "",
                "relevance_score": 0.7 if tier == "tier_1" else 0.5 if tier == "tier_2" else 0.3,
                "publisher_tier": tier,
            }
        )

    for i, row in enumerate(evidence[:6], start=1):
        row["id"] = f"E{i}"
    return evidence[:6]


def _synthesis_text(structured: Dict[str, Any]) -> str:
    bullets = structured.get("synthesis_bullets") or []
    if bullets:
        return "\n".join(f"- {b}" for b in bullets)
    return ""


def _build_pack(
    news_item: Dict[str, Any],
    *,
    primary_currency: str,
    web_search_queries: List[str],
    grounding_chunks: List[Dict[str, str]],
    structured: Optional[Dict[str, Any]],
    latency_ms: int,
    model: str,
    error: Optional[str] = None,
    status_override: Optional[str] = None,
    reason_override: Optional[str] = None,
) -> Dict[str, Any]:
    norm = _normalize_structured(structured)
    evidence = _merge_structured_with_chunks(norm, grounding_chunks)
    retrieval_summary = _synthesis_text(norm)

    tier_1_count = sum(1 for e in evidence if e.get("publisher_tier") == "tier_1")
    has_structured_items = bool(norm.get("related_items"))
    has_summary = bool(retrieval_summary)

    if status_override:
        status, reason = status_override, reason_override or ""
    elif error:
        status, reason = "failed", error
    elif not evidence and not has_summary and not has_structured_items:
        status, reason = "low_evidence", "No structured items or grounding chunks returned"
    elif tier_1_count < 1 and not has_summary:
        status, reason = "low_evidence", f"No tier_1 sources in {len(evidence)} items"
    elif tier_1_count < 1:
        status, reason = "ok_with_summary", "Structured context OK; limited tier_1 publisher matches"
    else:
        status, reason = "ok", f"{tier_1_count} tier_1 source(s) in {len(evidence)} items"

    return {
        "pack_version": PACK_VERSION,
        "surface": "live_news",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": {
            "primary_headline": str(news_item.get("title") or ""),
            "primary_currency": primary_currency,
            "search_queries_used": web_search_queries,
            "gemini_model": model,
        },
        "story_context": {
            "story_arc": norm.get("story_arc"),
            "primary_entities": norm.get("primary_entities"),
            "contradictions_note": norm.get("contradictions_note"),
        },
        "quality": {
            "status": status,
            "reason": reason,
            "search_query_count": len(web_search_queries),
            "evidence_count": len(evidence),
            "tier_1_count": tier_1_count,
        },
        "evidence": evidence,
        "retrieval_summary": retrieval_summary,
        "synthesis_bullets": norm.get("synthesis_bullets"),
        "grounding_meta": {
            "provider": "gemini",
            "latency_ms": latency_ms,
        },
    }


def render_related_evidence_prompt_block(pack: Optional[Dict[str, Any]]) -> str:
    """Prompt section for OpenAI — only cite evidence IDs from this block."""
    if not pack:
        return ""
    quality = pack.get("quality") or {}
    status = str(quality.get("status") or "").lower()
    if status == "skipped":
        return ""

    lines = [
        "RELATED HEADLINE EVIDENCE (Google Search grounding — mandatory rules):",
        "- Use ONLY items E1..En below for claims about prior news, corroboration, contradiction, or 'markets already knew'.",
        "- Do NOT invent other headlines, URLs, or facts.",
    ]
    if status in ("low_evidence", "failed"):
        lines.append(
            "- Grounding quality is weak; reduce confidence on corroboration claims and state uncertainty."
        )
    elif status == "ok_with_summary":
        lines.append(
            "- Publisher tier-1 matches are limited; lean on synthesis but avoid overstating corroboration."
        )

    story_ctx = pack.get("story_context") or {}
    arc = story_ctx.get("story_arc")
    if arc and arc != "unclear":
        lines.append(f"- Story arc (from web search): {arc.replace('_', ' ')}")
    entities = story_ctx.get("primary_entities") or []
    if entities:
        lines.append(f"- Key entities in related coverage: {', '.join(entities[:6])}")
    if story_ctx.get("contradictions_note"):
        lines.append(f"- Source disagreement: {story_ctx['contradictions_note']}")

    summary = (pack.get("retrieval_summary") or "").strip()
    if summary:
        lines.append("\nRETRIEVAL SYNTHESIS (from web search):")
        lines.append(summary[:2000])

    evidence = pack.get("evidence") or []
    if evidence:
        lines.append("\nRELATED ITEMS (cite as [E1], [E2], ... for corroboration / context claims):")
        for ev in evidence:
            eid = ev.get("id") or "?"
            tier = ev.get("publisher_tier") or "other"
            headline = ev.get("headline") or ev.get("publisher") or "unknown"
            publisher = ev.get("publisher") or ev.get("source") or ""
            rel = (ev.get("relationship") or "background").replace("_", " ")
            recency = ev.get("recency_bucket") or "unknown"
            takeaway = (ev.get("snippet") or "").strip()
            line = f"- [{eid}] ({tier}) {headline}"
            if publisher and publisher.lower() not in headline.lower():
                line += f" — {publisher}"
            line += f" | relationship: {rel} | recency: {recency}"
            if takeaway:
                line += f" | {takeaway[:280]}"
            lines.append(line)

    if status in ("ok", "ok_with_summary") and evidence:
        lines.append(
            "- In news_impact and trading_implications, include at least one inline citation [E1]..[En] "
            "when stating corroboration, contradiction, or prior-market context."
        )
        lines.append(
            "- Do not claim outlets reported something unless you cite the matching [En] from the list above."
        )

    lines.append("")
    return "\n".join(lines)


def _call_gemini(news_item: Dict[str, Any], primary_currency: str) -> Dict[str, Any]:
    from google import genai
    from google.genai import types

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    model = _grounding_model()
    client = genai.Client(api_key=api_key)
    prompt = _build_retrieval_prompt(news_item, primary_currency)
    grounding_tool = types.Tool(google_search=types.GoogleSearch())

    # Google Search tool cannot be combined with response_mime_type=application/json
    # (API returns 400 INVALID_ARGUMENT). Parse JSON from plain text instead.
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=0.2,
    )

    started = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    text = (getattr(response, "text", None) or "").strip()
    structured = _normalize_structured(_extract_json_object(text))
    if not structured.get("related_items") and not structured.get("synthesis_bullets") and text:
        structured["synthesis_bullets"] = [
            line.lstrip("-• ").strip() for line in text.splitlines() if line.strip()
        ][:6]

    queries: List[str] = []
    chunks: List[Dict[str, str]] = []
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        meta = getattr(candidates[0], "grounding_metadata", None)
        queries, chunks = _chunks_from_grounding_metadata(meta)

    return _build_pack(
        news_item,
        primary_currency=primary_currency,
        web_search_queries=queries,
        grounding_chunks=chunks,
        structured=structured,
        latency_ms=latency_ms,
        model=model,
    )


def fetch_related_evidence(news_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch RelatedEvidencePack for a news item. Fail-open: never raises to caller.
    """
    if not is_live_news_gemini_grounding_enabled():
        return _skipped_pack(news_item, "LIVE_NEWS_GEMINI_GROUNDING_ENABLED is off")

    from services.analysis_context_pack import _infer_news_currency

    primary_currency = _infer_news_currency(news_item)
    item_for_prompt = {**news_item, "primary_currency": primary_currency}

    key = _cache_key(news_item)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and cached[0] > now:
        if is_live_news_gemini_grounding_debug():
            logger.info("Gemini grounding cache hit for %s", key)
        return cached[1]

    try:
        pack = _call_gemini(item_for_prompt, primary_currency)
        _cache[key] = (now + _cache_ttl_sec(), pack)
        q = pack.get("quality") or {}
        logger.info(
            "Gemini grounding news_id=%s status=%s evidence=%s searches=%s latency_ms=%s story_arc=%s",
            news_item.get("id"),
            q.get("status"),
            q.get("evidence_count"),
            q.get("search_query_count"),
            (pack.get("grounding_meta") or {}).get("latency_ms"),
            (pack.get("story_context") or {}).get("story_arc"),
        )
        return pack
    except Exception as exc:
        logger.warning("Gemini grounding failed (fail-open): %s", exc)
        return _build_pack(
            item_for_prompt,
            primary_currency=primary_currency,
            web_search_queries=[],
            grounding_chunks=[],
            structured=None,
            latency_ms=0,
            model=_grounding_model(),
            error=str(exc)[:200],
        )
