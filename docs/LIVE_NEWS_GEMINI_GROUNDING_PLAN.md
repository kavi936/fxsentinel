# Live News — Gemini Grounding (Related Headlines) Plan

**Status:** Phase 1 + structured retrieval (flag off by default)  
**Created:** 2026-06-02  
**Purpose:** Add **Google Search grounding via Gemini** before ChatGPT live-news analysis, so each headline is analyzed with corroborated, recent related coverage — not only our internal news cache.

**Related docs:**

| Doc | Role |
| --- | --- |
| [ANALYSIS_INPUT_LAYER.md](../ANALYSIS_INPUT_LAYER.md) | Shared `AnalysisContextPack`; Phase D live-news wiring |
| [LIVE_NEWS_ANALYSIS_CARD_DOCUMENTATION.md](./LIVE_NEWS_ANALYSIS_CARD_DOCUMENTATION.md) | End-to-end live news + analysis card |
| [CALENDAR_ANALYSIS_INDICATOR_CHARTS_PLAN.md](./CALENDAR_ANALYSIS_INDICATOR_CHARTS_PLAN.md) | Parallel pattern: enrich analysis input, GPT never invents series |
| [FXSentinel_AI_Analysis_Review.md](./FXSentinel_AI_Analysis_Review.md) | Quality / trust bar for analysis output |

---

## 1. Problem

Live news analysis today (`mvp_news_analyzer` → OpenAI) reasons mainly over:

- The **single article** (title + summary + source),
- **Live market snapshots** (prices, VIX, pair sentiment),
- Optional **holistic macro snapshot** when `ANALYSIS_CONTEXT_PACK_ENABLED=true`.

It does **not** reliably answer:

- Is this headline **new** or a **repeat** of an ongoing story?
- Do **other credible outlets** report the same fact or a different angle?
- What **prior headlines** in the last 24h–7d set context for the move?

Our **persistent news cache** is optimized for feed speed, not for retrieval quality: dedupe, source metadata, and impact scoring are imperfect, so “search our cache for similar headlines” is a weak substitute for live web corroboration.

**Goal:** Before OpenAI writes trader-facing analysis, run a **retrieval step** (Gemini + Google Search) that returns a small, **structured evidence pack** of related headlines. ChatGPT must reason only from that pack (+ existing market/holistic context).

---

## 2. Why Gemini (decision)

| Criterion | Gemini | Grok (for reference) |
| --- | --- | --- |
| Web search / corroboration | **Google Search grounding**, citations in API | `web_search` tool |
| X / Twitter | Not native | `x_search` (future optional add-on) |
| Cost (paid) | **$14 / 1k search queries** after free tier | **$5 / 1k tool calls** |
| Free tier | **5,000 search queries/month** (Gemini 3, shared) | None on tools |
| Fit for “credible headline pack” | **Primary choice** | Better for social-only pass later |

**Billing note (Gemini 3):** One API request can trigger **multiple** search queries; each query counts toward the 5k/month allowance and paid tier. Prompts must cap behavior (“at most 2 searches”).

---

## 3. Design principles

| Principle | Meaning |
| --- | --- |
| **Retrieve then reason** | Gemini finds evidence; OpenAI (`mvp_news_analyzer`) analyzes. Do not merge into one model call in v1. |
| **Structured first** | Evidence is JSON (`RelatedEvidencePack`), not prose dumps. Testable and loggable. |
| **No source, no claim** | Final GPT prompt: only reference evidence IDs `E1`…`En`; no invented prior headlines. |
| **Do not use internal cache for corroboration** | Gemini grounding replaces cache search for this feature. Cache remains the **feed**, not the **truth layer**. |
| **Fail open** | If retrieval fails, times out, or quality is low → run existing analysis path unchanged. |
| **Feature-flagged** | Off in production until sign-off; same pattern as `ANALYSIS_CONTEXT_PACK_ENABLED`. |
| **Cache retrieval** | Hash `(normalized_title, primary_currency, day)` → TTL 15–30 min to cut cost on repeat clicks/alerts. |

---

## 4. Proposed architecture

```text
User clicks "Get AI Analysis" (LiveNewsFeed)
    │
    ▼
GET /api/analysis/<news_id>  (app.py → generate_news_analysis)
    │
    ├─► [NEW] gemini_news_grounding_service.fetch_related_evidence(news_item)
    │       • Gemini model + google_search tool
    │       • Returns RelatedEvidencePack (JSON)
    │       • Cached in memory/Firebase optional (phase 2)
    │
    ├─► mvp_news_analyzer.analyze_news(..., related_evidence=pack)
    │       • Inject RELATED EVIDENCE block into _create_enhanced_prompt
    │       • Existing market data + optional AnalysisContextPack unchanged
    │
    ├─► finalize_analysis(ANALYSIS_KIND_LIVE_NEWS, ...)
    │       • Optional: attach pack summary on response for UI (phase 3)
    │
    └─► analysis_history.add_analysis(...)
```

**Out of scope for v1:** Pre-fetch grounding on every `/api/news` poll (too expensive). Grounding runs **only on explicit analysis** (and optionally high-impact alerts in phase 4).

---

## 5. `RelatedEvidencePack` contract

`pack_version: 2026-06-03` — Gemini returns **structured JSON** (not bullets-only).

```yaml
story_context:
  story_arc: new_development | ongoing_story | unclear
  primary_entities: [Fed, BoJ, ...]
  contradictions_note: string

synthesis_bullets: string[]
retrieval_summary: string          # bullets joined for ChatGPT prompt

evidence[]:                        # max 6
  id: E1
  headline: string                 # actual related headline (not just domain)
  publisher: string
  snippet: string                  # takeaway + optional key_fact
  relationship: corroborates | contradicts | background | market_reaction
  recency_bucket: last_24h | last_7d | older | unknown   # approximate; not exact publish time
  key_fact: string
  url: string                      # from grounding chunk when domain matches
  publisher_tier: tier_1 | tier_2 | other
```

Publish time is **not** required; use `recency_bucket` only when search supports it.

**API note:** `google_search` + `response_mime_type: application/json` is rejected (400). Retrieval uses text output and server-side JSON extraction.

**Publisher tiers (backend, not Gemini):** Map domain → tier using an allowlist in code (e.g. Reuters, Bloomberg, FT, WSJ, CNBC, central banks `.gov` / `.ecb.europa.eu`, etc.). Drop or down-rank `tier_other` below threshold.

---

## 6. Gemini integration (technical)

### 6.1 API surface

- **Docs:** [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- **Tool:** `google_search` on Gemini 3.x models (not legacy `google_search_retrieval` on 2.x).
- **Suggested model for retrieval-only:** `gemini-3.1-flash-lite` (cheap tokens; retrieval task is structured JSON, not long prose).
- **SDK:** `google-genai` Python package (or REST). Store key as `GEMINI_API_KEY` in `backend/.env`.

### 6.2 Request shape (conceptual)

- **System:** You are a financial news researcher. Return **only** valid JSON matching the schema. Use Google Search to find related coverage. Max **2** search queries.
- **User:** Primary headline, summary, source, published time, primary currency, affected pairs.
- **Tools:** `google_search` enabled.
- **Generation:** `temperature: 0.2`, `response_mime_type: application/json` (if supported) or strict JSON-in-markdown parsing with validation.

### 6.3 Post-processing (our backend)

1. Parse JSON; on failure → `quality.status = failed`, skip pack in prompt.
2. Dedupe by normalized title + domain.
3. Enforce max **6** evidence items.
4. Require at least **1** `tier_1` source for `quality.status = ok`; else `low_evidence` (still pass to GPT with a “weak corroboration” flag).
5. Strip HTML, truncate snippets.

### 6.4 Prompt block for OpenAI (insertion point)

New constant in `analysis_context_pack.py` or `gemini_news_grounding_service.py`:

```text
RELATED HEADLINE EVIDENCE (mandatory grounding):
- Use ONLY items E1..En below for claims about prior news, corroboration, or "markets already knew".
- If quality.status is low_evidence or failed, say uncertainty explicitly; do not invent related headlines.

{rendered_evidence_list}
```

Wire into `mvp_news_analyzer._create_enhanced_prompt()` **after** headline facts, **before** trading-session / market blocks.

---

## 7. Code touchpoints (implementation map)

| Phase | File | Change |
| --- | --- | --- |
| **0** | `backend/.env.example` | `GEMINI_API_KEY`, `LIVE_NEWS_GEMINI_GROUNDING_ENABLED=false`, `LIVE_NEWS_GEMINI_GROUNDING_DEBUG=false` |
| **1** | `backend/services/gemini_news_grounding_service.py` | **New** — fetch, validate, rank, cache, `RelatedEvidencePack` |
| **1** | `backend/services/news_publisher_tiers.py` | **New** (optional) — domain → tier map |
| **2** | `backend/services/mvp_news_analyzer.py` | Accept `related_evidence`; extend `_create_enhanced_prompt` |
| **2** | `backend/app.py` | `generate_news_analysis()` call grounding when flag on |
| **3** | `backend/services/analysis_pipeline.py` | Optional: `apply_related_evidence_display_if_news()` for UI fields |
| **3** | `src/components/LiveNewsFeed.jsx` | Optional collapsible “Related coverage” list with links |
| **4** | `backend/services/news_alert_trigger.py` | High-impact only + `DISABLE_AI_FOR_ALERTS` respect |
| **tests** | `backend/test_gemini_news_grounding.py` | Mock Gemini responses; schema + tier filter |

**Do not** ground via `persistent_news_cache` for this feature.

---

## 8. Environment flags

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | (unset) | Required when grounding enabled |
| `LIVE_NEWS_GEMINI_GROUNDING_ENABLED` | `false` | Master switch for retrieval step |
| `LIVE_NEWS_GEMINI_GROUNDING_DEBUG` | `false` | Log pack + include `related_evidence` on API response |
| `LIVE_NEWS_GEMINI_GROUNDING_MODEL` | `gemini-3.1-flash-lite` | Override model id |
| `LIVE_NEWS_GEMINI_GROUNDING_CACHE_TTL_SEC` | `1800` | Retrieval cache TTL |
| `LIVE_NEWS_GEMINI_GROUNDING_TIMEOUT_SEC` | `20` | Fail open after timeout |

Independent of `ANALYSIS_CONTEXT_PACK_ENABLED` — both can be on; holistic snapshot and related evidence are complementary.

---

## 9. Phased rollout

### Phase 0 — Spike (1–2 days)

- [ ] Gemini API key in dev `.env` (`GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/))
- [x] CLI script: `backend/scripts/gemini_grounding_spike.py` — one headline in, JSON pack out
- [x] 10-headline workbook: `backend/data/gemini_grounding_spike_headlines.json`
- [ ] Run batch + save report; manually review evidence quality
- [ ] Record avg `search_query_count` and latency (script prints summary)

**Exit criteria:** ≥7/10 packs have `quality.status == ok` (≥1 tier_1 source in evidence); median latency &lt;15s.

#### Phase 0 — first run notes (2026-06-03)

Initial batch reported **0/10 ok** — that was misleading. Gemini returned useful related summaries and 3–8 evidence chunks per headline, but **publisher tier scoring used the redirect host** (`vertexaisearch.cloud.google.com`) instead of the chunk `title` field (`reuters.com`, `fxstreet.com`, `investing.com`, etc.). After fixing domain extraction in `gemini_grounding_spike.py`, re-run `--batch` for a fair score.

| Signal | First run | Target |
| --- | --- | --- |
| Related narrative in `model_summary` | Good (on-topic Fed/CPI/oil/etc.) | Yes |
| Evidence chunks returned | Yes (3–8 each) | Yes |
| Tier_1 auto-score | Broken (redirect URL bug) | ≥1 tier_1 per headline |
| Median latency ~16.6s | Slightly over 15s | &lt;15s ideal; &lt;20s acceptable for v1 |
| Search queries per call | Often 2–4 (prompt asked max 2) | Tighten prompt + monitor cost |

**What we are aiming for:** corroborated related coverage in structured evidence + short summary for GPT — **not** 0% because of a scoring bug.

#### Phase 0 — how to run

```bash
cd backend
pip install google-genai   # or: pip install -r requirements.txt
# Add GEMINI_API_KEY=... to backend/.env

# Single headline
python3 scripts/gemini_grounding_spike.py \
  --title "Fed's Powell says inflation progress uneven" \
  --summary "Powell said the Fed is not in a hurry to cut rates." \
  --source Reuters --currency USD

# Full workbook (10 headlines)
python3 scripts/gemini_grounding_spike.py --batch

# Save JSON report for review
python3 scripts/gemini_grounding_spike.py --batch \
  --output data/gemini_spike_results.json
```

**What to check manually:** Open 2–3 `evidence[].url` links per headline — are they truly related and credible? Note false positives in a comment on the PR or in `data/gemini_spike_results.json`.

**Scoring (automated in batch):** `tier_1` = Reuters, Bloomberg, FT, WSJ, CNBC, central banks, etc. (see `TIER_1_DOMAIN_SUFFIXES` in spike script). `ok` requires at least one tier_1 chunk in grounding metadata.

### Phase 1 — Service + flag (backend only)

- [x] Implement `gemini_news_grounding_service.py`
- [x] Unit tests with mocked API (`backend/test_gemini_news_grounding.py`)
- [x] Wire into `generate_news_analysis` behind `LIVE_NEWS_GEMINI_GROUNDING_ENABLED`
- [x] Fail open on any error
- [x] In-memory TTL cache
- [x] Inject evidence block in `mvp_news_analyzer._create_enhanced_prompt`
- [x] Attach `related_evidence` on API response when grounding ran

**Exit criteria:** `/api/analysis/<id>` logs pack when debug on; OpenAI prompt contains evidence block; no regression when flag off.

**Enable locally:** set `GEMINI_API_KEY` and `LIVE_NEWS_GEMINI_GROUNDING_ENABLED=true` in `backend/.env`, restart backend, run **Get AI Analysis** on a live headline.

### Phase 2 — UX + prompt + citations

- [x] `GET /api/analysis/<id>/related-evidence` (warms cache; no billing increment)
- [x] Live news two-step client: grounding → full analysis
- [x] Staged loading UI (`LiveNewsAnalysisLoading`) with real synthesis preview
- [x] Related coverage footer + `[E1]` linkify in prose
- [x] Prompt rules: mandatory `[En]` when evidence ok
- [ ] Tune publisher tier list with real feed sources
- [ ] Optional: pass `quality.status` into `finalize_analysis` observability

**Exit criteria:** Side-by-side review — 20 headlines with flag on vs off; fewer “fabricated context” failures; users see step 1/2 loading and sources footer.

### Phase 3 — UI polish (optional)

- [ ] Tier badges on related coverage rows
- [ ] Do not show raw Gemini prose — only `evidence[]` (enforced in footer)

### Phase 4 — Alerts (optional, cost-sensitive)

- [ ] Only `impact == high` + user alert enabled
- [ ] Respect existing `DISABLE_AI_FOR_ALERTS`
- [ ] Share same retrieval cache as UI

---

## 10. Cost model (planning)

Assume **2 search queries** per analysis on average (Gemini 3 billing).

| Volume | Search cost (after 5k free/mo) | Notes |
| --- | --- | --- |
| 500 analyses/mo | **$0** (within free queries) | Ideal for beta |
| 2,000 analyses/mo | ~**$42**/mo search + Flash-Lite tokens | 4k queries × $14/1k |
| 5,000 analyses/mo | ~**$140**/mo search | Add retrieval cache + consider high-impact-only |

**Mitigations:** TTL cache, high-impact-only for alerts, skip grounding when `analysis_history` has same `news_id` analyzed in last 24h (optional).

---

## 11. Observability

Log per request (info/debug):

- `news_id`, `quality.status`, `evidence_count`, `search_query_count`, `latency_ms`, `cache_hit`
- Never log full `GEMINI_API_KEY`

Add to `v1_observability.extra` when spine enabled:

```json
{ "gemini_grounding": { "status": "ok", "evidence_count": 4, "search_query_count": 2 } }
```

---

## 12. GPT final-analysis rules (add to prompt)

Short block to append in `_create_enhanced_prompt`:

1. Related headlines: cite as `[E1]`, `[E2]` only from the evidence section.
2. If evidence contradicts the primary article, state that explicitly.
3. Do not claim “markets already priced this in” without evidence support.
4. If `quality.status` is not `ok`, reduce confidence and avoid timeline claims.

---

## 13. Non-goals (v1)

| # | Out of scope |
| --- | --- |
| NG1 | Searching `persistent_news_cache` for related items |
| NG2 | Replacing OpenAI analyzer with Gemini for final prose |
| NG3 | Grok / X search (document as Phase 5+ optional) |
| NG4 | Grounding on every `/api/news` poll |
| NG5 | Calendar / holistic scan (reuse pack contract later, separate prompt work) |

---

## 14. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Gemini runs 4+ searches | Hard cap in prompt; monitor `search_query_count` |
| JSON parse failures | Fail open; retry once with “JSON only” reminder |
| Latency &gt; 30s | Timeout 20s; skip grounding |
| Hallucinated evidence titles | Require URLs from grounding metadata; drop items without URL |
| Cost spike from alerts | Phase 4 gating; cache |

---

## 15. How to start implementing (first PR)

**Smallest useful PR:**

1. Add `docs/LIVE_NEWS_GEMINI_GROUNDING_PLAN.md` (this file) ✅  
2. Add `backend/services/gemini_news_grounding_service.py` with:
   - `is_live_news_gemini_grounding_enabled()`
   - `fetch_related_evidence(news_item) -> RelatedEvidencePack`
   - Stub implementation returning `quality.status = skipped` when flag off  
3. Add `backend/test_gemini_news_grounding.py` (mocked HTTP)  
4. Wire one line in `generate_news_analysis()` to call fetch and log when `LIVE_NEWS_GEMINI_GROUNDING_DEBUG=true` (no prompt change yet)

**Second PR:** Real Gemini call + prompt injection in `mvp_news_analyzer`.

**Third PR:** UI related-coverage strip + observability.

---

## 16. Local dev checklist

1. Create API key in [Google AI Studio](https://aistudio.google.com/).
2. `backend/.env`:
   ```bash
   GEMINI_API_KEY=...
   LIVE_NEWS_GEMINI_GROUNDING_ENABLED=true
   LIVE_NEWS_GEMINI_GROUNDING_DEBUG=true
   ```
3. Restart backend.
4. Pick a high-impact headline in Live News → **Get AI Analysis**.
5. Confirm logs show `RelatedEvidencePack` with `evidence_count > 0`.
6. Compare analysis text with flag on vs off.

---

## 17. Future extensions

- **Calendar:** Same pack type; queries anchored on event title + currency + release time.
- **Grok `x_search`:** Optional second pass for `impact == high` when social narrative matters.
- **Firebase cache:** Share retrieval packs across users for same headline hash.
- **ANALYSIS_INPUT_LAYER.md:** Add Phase I row when Phase 1 ships.

---

## Progress tracker

| Phase | Description | Status |
| --- | --- | --- |
| 0 | Spike + manual QA | Done (API validated) |
| 1 | `gemini_news_grounding_service` + flag + fail open | **Done** |
| 2 | MVP prompt injection + tier filter | Not started |
| 3 | UI related coverage | Not started |
| 4 | Alerts (high-impact) | Not started |
