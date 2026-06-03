#!/usr/bin/env python3
"""
Phase 0 — Gemini Google Search grounding spike for live-news related headlines.

One headline in → RelatedEvidencePack JSON out, using groundingMetadata (verifiable URLs).

Requires:
  pip install google-genai python-dotenv
  GEMINI_API_KEY in backend/.env

Usage:
  cd backend && python scripts/gemini_grounding_spike.py \\
    --title "Fed's Powell says..." --summary "..." --source Reuters --currency USD

  cd backend && python scripts/gemini_grounding_spike.py --batch
  cd backend && python scripts/gemini_grounding_spike.py --batch --output data/gemini_spike_results.json

See docs/LIVE_NEWS_GEMINI_GROUNDING_PLAN.md §9 Phase 0.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

try:
    from dotenv import load_dotenv

    load_dotenv(_BACKEND / ".env")
except ImportError:
    pass

PACK_VERSION = "2026-06-02"

# Domains we treat as tier_1 for Phase 0 scoring (expand in Phase 2).
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
)

TIER_2_DOMAIN_SUFFIXES = (
    "yahoo.com",
    "finance.yahoo.com",
    "businessinsider.com",
    "seekingalpha.com",
    "zerohedge.com",
)


_GROUNDING_REDIRECT_HOST = "vertexaisearch.cloud.google.com"


def _domain_from_uri(uri: str) -> str:
    try:
        host = (urlparse(uri).netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _normalize_domain_label(label: str) -> str:
    """Turn grounding chunk title (often 'reuters.com') into a comparable domain."""
    raw = (label or "").strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        raw = _domain_from_uri(raw)
    else:
        raw = raw.split("/")[0].split("?")[0]
        if raw.startswith("www."):
            raw = raw[4:]
    return raw


def _publisher_domain_from_chunk(title: str, uri: str) -> str:
    """
    Gemini grounding returns redirect URLs; real publisher is usually in chunk.title.
    """
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
        if d == suffix or d.endswith("." + suffix) or d.endswith(suffix):
            return "tier_1"
    for suffix in TIER_2_DOMAIN_SUFFIXES:
        if d == suffix or d.endswith("." + suffix) or d.endswith(suffix):
            return "tier_2"
    return "other"


def _build_retrieval_prompt(news_item: Dict[str, Any]) -> str:
    title = news_item.get("title") or ""
    summary = news_item.get("summary") or ""
    source = news_item.get("source") or ""
    currency = news_item.get("primary_currency") or "USD"
    return f"""You are a forex news researcher. Use Google Search to find RELATED coverage of this breaking headline (not duplicate reposts of the exact same wire).

PRIMARY HEADLINE (analyze in context of this story):
- Title: {title}
- Summary: {summary}
- Source: {source}
- Primary currency: {currency}

TASK:
1. Perform at most TWO focused web searches.
2. Find 3–6 related articles from credible financial publishers (Reuters, Bloomberg, FT, WSJ, CNBC, central banks, etc.) from the last 7 days when possible.
3. Prefer stories that add context: prior statements, market reaction, corroboration, or timeline — not generic forex education.

Reply with a short bullet summary (max 6 bullets) of what related coverage shows. Do not invent URLs — search results supply sources."""


def _chunks_from_grounding_metadata(meta: Any) -> Tuple[List[str], List[Dict[str, str]]]:
    """Return (web_search_queries, [{uri, title, domain}, ...])."""
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


def build_related_evidence_pack(
    news_item: Dict[str, Any],
    *,
    web_search_queries: List[str],
    grounding_chunks: List[Dict[str, str]],
    latency_ms: int,
    model: str,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    title = str(news_item.get("title") or "")
    currency = str(news_item.get("primary_currency") or "USD").upper()[:3]

    evidence: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(_dedupe_chunks(grounding_chunks)[:8], start=1):
        domain = chunk.get("domain") or ""
        tier = _publisher_tier(domain)
        evidence.append(
            {
                "id": f"E{idx}",
                "title": chunk.get("title") or domain,
                "snippet": "",
                "source": domain or "unknown",
                "url": chunk.get("uri") or "",
                "published_at": None,
                "relevance_score": 0.7 if tier == "tier_1" else 0.5 if tier == "tier_2" else 0.3,
                "publisher_tier": tier,
            }
        )

    tier_1_count = sum(1 for e in evidence if e.get("publisher_tier") == "tier_1")
    if error:
        status, reason = "failed", error
    elif not evidence:
        status, reason = "low_evidence", "No grounding chunks returned"
    elif tier_1_count < 1:
        status, reason = "low_evidence", f"No tier_1 sources in {len(evidence)} chunks"
    else:
        status, reason = "ok", f"{tier_1_count} tier_1 source(s) in {len(evidence)} items"

    return {
        "pack_version": PACK_VERSION,
        "surface": "live_news",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": {
            "primary_headline": title,
            "primary_currency": currency,
            "search_queries_used": web_search_queries,
            "gemini_model": model,
        },
        "quality": {
            "status": status,
            "reason": reason,
            "search_query_count": len(web_search_queries),
            "evidence_count": len(evidence),
            "tier_1_count": tier_1_count,
        },
        "evidence": evidence,
        "grounding_meta": {
            "provider": "gemini",
            "latency_ms": latency_ms,
        },
    }


def fetch_grounding_for_news(
    news_item: Dict[str, Any],
    *,
    api_key: str,
    model: str,
) -> Tuple[Dict[str, Any], str]:
    """
    Call Gemini with google_search. Returns (pack, model_text_summary).
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = _build_retrieval_prompt(news_item)
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool], temperature=0.2)

    started = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    text = (getattr(response, "text", None) or "").strip()
    queries: List[str] = []
    chunks: List[Dict[str, str]] = []
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        meta = getattr(candidates[0], "grounding_metadata", None)
        queries, chunks = _chunks_from_grounding_metadata(meta)

    pack = build_related_evidence_pack(
        news_item,
        web_search_queries=queries,
        grounding_chunks=chunks,
        latency_ms=latency_ms,
        model=model,
    )
    return pack, text


def _load_batch_headlines(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Batch file must be a JSON array")
    return data


def _print_pack_summary(pack: Dict[str, Any], summary_text: str) -> None:
    q = pack.get("quality") or {}
    print(f"  status={q.get('status')}  evidence={q.get('evidence_count')}  "
          f"tier_1={q.get('tier_1_count')}  searches={q.get('search_query_count')}  "
          f"latency_ms={pack.get('grounding_meta', {}).get('latency_ms')}")
    print(f"  reason: {q.get('reason')}")
    for ev in pack.get("evidence") or []:
        print(f"    [{ev.get('id')}] ({ev.get('publisher_tier')}) {ev.get('title')[:70]}")
        print(f"         {ev.get('url')[:100]}")
    if summary_text:
        snippet = re.sub(r"\s+", " ", summary_text)[:400]
        print(f"  model_summary: {snippet}...")


def run_batch(
    headlines: List[Dict[str, Any]],
    *,
    api_key: str,
    model: str,
    output_path: Optional[Path],
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    latencies: List[int] = []
    ok_count = 0

    print(f"\nRunning batch ({len(headlines)} headlines), model={model}\n")

    for i, item in enumerate(headlines, 1):
        print(f"[{i}/{len(headlines)}] {item.get('category')}: {(item.get('title') or '')[:60]}...")
        try:
            pack, summary = fetch_grounding_for_news(item, api_key=api_key, model=model)
            latencies.append(int(pack.get("grounding_meta", {}).get("latency_ms") or 0))
            if (pack.get("quality") or {}).get("status") == "ok":
                ok_count += 1
            _print_pack_summary(pack, summary)
            results.append(
                {
                    "input": item,
                    "pack": pack,
                    "model_summary": summary,
                }
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            pack = build_related_evidence_pack(
                item,
                web_search_queries=[],
                grounding_chunks=[],
                latency_ms=0,
                model=model,
                error=str(exc),
            )
            results.append({"input": item, "pack": pack, "model_summary": "", "error": str(exc)})
        print()

    latencies_sorted = sorted(latencies) if latencies else [0]
    median_latency = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else 0
    report = {
        "ran_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "headline_count": len(headlines),
        "ok_count": ok_count,
        "ok_rate": ok_count / len(headlines) if headlines else 0,
        "median_latency_ms": median_latency,
        "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
        "exit_criteria": {
            "target_ok_rate": 0.7,
            "target_median_latency_ms": 15000,
            "passed_ok_rate": ok_count >= 7 if len(headlines) >= 10 else ok_count >= max(1, int(0.7 * len(headlines))),
            "passed_latency": median_latency < 15000,
        },
        "results": results,
    }

    print("=" * 60)
    print(f"OK rate: {ok_count}/{len(headlines)} ({100 * report['ok_rate']:.0f}%)")
    print(f"Median latency: {median_latency} ms  (target < 15000)")
    print(f"Phase 0 exit: ok_rate={'PASS' if report['exit_criteria']['passed_ok_rate'] else 'FAIL'}  "
          f"latency={'PASS' if report['exit_criteria']['passed_latency'] else 'FAIL'}")
    print("=" * 60)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Wrote {output_path}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 0 Gemini grounding spike")
    parser.add_argument("--title", help="Primary headline title")
    parser.add_argument("--summary", default="", help="Headline summary")
    parser.add_argument("--source", default="Unknown", help="Primary source label")
    parser.add_argument("--currency", default="USD", help="Primary currency (USD, EUR, ...)")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run 10-headline workbook from data/gemini_grounding_spike_headlines.json",
    )
    parser.add_argument(
        "--batch-file",
        type=Path,
        default=_BACKEND / "data" / "gemini_grounding_spike_headlines.json",
        help="JSON array of headlines for --batch",
    )
    parser.add_argument("--output", type=Path, help="Write batch JSON report to this path")
    parser.add_argument(
        "--model",
        default=os.getenv("GEMINI_GROUNDING_SPIKE_MODEL", "gemini-2.5-flash"),
        help="Gemini model id (must support google_search grounding)",
    )
    args = parser.parse_args()

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        print("Missing GEMINI_API_KEY. Add to backend/.env (get key from https://aistudio.google.com/)")
        return 1

    try:
        from google import genai  # noqa: F401
    except ImportError:
        print("Install: pip install google-genai")
        return 1

    if args.batch:
        headlines = _load_batch_headlines(args.batch_file)
        run_batch(headlines, api_key=api_key, model=args.model, output_path=args.output)
        return 0

    if not args.title:
        parser.error("Provide --title or use --batch")

    news_item = {
        "title": args.title,
        "summary": args.summary,
        "source": args.source,
        "primary_currency": args.currency,
    }
    print(f"Model: {args.model}\n")
    pack, summary = fetch_grounding_for_news(news_item, api_key=api_key, model=args.model)
    _print_pack_summary(pack, summary)
    print("\nFull pack JSON:\n")
    print(json.dumps(pack, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
