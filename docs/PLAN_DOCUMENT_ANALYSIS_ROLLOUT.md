# Plan: Document Intelligence Rollout for Trader Analysis

**Status:** Proposed  
**Owner:** FXSentinel backend + data pipeline  
**Goal:** Turn central-bank and COT files into scalable, AI-usable analysis context without slowing deploys or increasing hosting cost unpredictably.

---

## 1) Product Goal

Enable traders to get actionable AI analysis from:
- Central bank statements, minutes, reports, press conferences
- COT positioning reports

While ensuring:
- Deploy speed remains fast
- Hosting costs stay predictable
- Analysis quality improves with document volume

---

## 2) Core Architecture (Recommended)

### A. Storage Separation (critical)
- Keep **metadata + summaries** in app/backend repo.
- Move **raw files** (PDF/HTML) to object storage + CDN:
  - Cloudflare R2 / AWS S3 + CloudFront / GCS
- Store file URLs in metadata (`sourceUrl` / `filePath` as CDN URL).

**Why:** avoids large deploy artifacts in Vercel/Railway and reduces CI/deploy time as document count grows.

### B. Ingestion Pipeline
- Trigger when a new document is added:
  1. Upload document to storage
  2. Queue ingestion job
  3. Extract text + normalize
  4. Chunk + enrich tags
  5. Generate summary + notes
  6. Generate embeddings
  7. Persist outputs for prompt injection + retrieval

### C. Retrieval + Analysis Layer
- Use RAG:
  - Retrieve top relevant chunks by bank/date/topic/currency
  - Combine with existing market/economic context in analysis prompts
- Return analysis with source-aware references (doc IDs / titles).

---

## 3) Data Model to Use

For each document, maintain 3 analysis layers:

1. **L1 summary context** (cheap + fast)
   - `shortSummary`
   - `aiNotes` (3–6 atomic notes)
   - `topics`

2. **L2 structured fields** (deterministic extraction)
   - `policyStance`: hawkish/dovish/neutral
   - `rateSignal`: hike/hold/cut bias
   - `inflationSignal`, `growthSignal`, `laborSignal`
   - `confidence`

3. **L3 retrieval chunks**
   - chunk text + embedding + section metadata

Current files already aligned with L1:
- `backend/data/central_bank_documents_ai_context.json`
- `backend/services/central_bank_ai_context.py`

---

## 4) Rollout Phases

## Phase 0 (Now) — Stabilize Current Setup
- Keep existing card + metadata flow.
- Continue adding docs and AI context summaries.
- Ensure file names/paths are URL-safe and tracked by git rules.

**Exit criteria:**
- All new docs have metadata + AI context entry
- No 404s on production document links

## Phase 1 — Background Ingestion MVP
- Add backend job runner for document ingestion.
- Auto-generate/refresh `shortSummary` + `aiNotes` from new docs.
- Save processing status per doc:
  - `pending`, `processing`, `ready`, `failed`

**Exit criteria:**
- New docs analyzed automatically
- Manual summary entry no longer required for normal flow

## Phase 2 — RAG in AI Analysis
- Add chunk retrieval by:
  - event currency
  - central bank
  - recency window
  - topics
- Inject top-k chunks + L1 summaries into analysis prompt.

**Exit criteria:**
- AI outputs reference current document context consistently
- Token usage within budget thresholds

## Phase 3 — Trader Features
- “What changed since last meeting?” diff mode
- “Policy stance tracker” (timeline per bank)
- COT positioning trend interpretation (crowding / reversal risk)

**Exit criteria:**
- User-facing analysis modules include doc intelligence consistently

---

## 5) Cost & Performance Controls

### Hosting / Deployment
- Do not bundle raw docs in frontend deploy artifact long-term.
- Keep Railway backend build context slim (exclude static docs where possible).
- Serve docs from CDN with aggressive caching.

### LLM Cost
- Precompute summaries once per doc.
- Cache analysis by `(doc_hash, prompt_version, model_version)`.
- Use cheap model for extraction/classification; stronger model for final synthesis.
- Limit prompt context (`max_docs`, `max_notes_per_doc`, `max_chunks`).

### Vector/DB Cost
- Embed only cleaned text (skip boilerplate pages).
- Re-embed only when content hash changes.
- Archive old chunks into lower-cost storage tiers if needed.

---

## 6) Operational Workflow (Recommended)

When adding a document:
1. Upload to object storage path by bank/date/type.
2. Add metadata entry (`id`, date, tags, currencies, URL).
3. Trigger ingestion job.
4. Validate generated summary/notes.
5. Mark as `ready`.

When analysis endpoint runs:
1. Resolve relevant bank/currency context
2. Pull L1 summary notes + top retrieved chunks
3. Merge with market/economic/prediction context
4. Generate final analysis

---

## 7) Suggested Next Implementation Tasks

1. Add `analysisStatus`, `docHash`, `processedAt` to metadata schema.
2. Create `document_ingestion_service.py` (extract/chunk/summarize/embed).
3. Add a queue worker (RQ/Celery/Bull-style equivalent).
4. Add retrieval helper in backend services (by bank/currency/topic/date).
5. Wire retrieval output into `gpt_ai_analysis` prompt builder.
6. Add monitoring dashboard counters:
   - docs processed/day
   - processing failures
   - average tokens/request
   - retrieval hit-rate

---

## 8) Risks and Mitigations

- **Risk:** Prompt bloat as document count grows  
  **Mitigation:** strict top-k retrieval + notes caps.

- **Risk:** Stale summaries or incorrect extraction  
  **Mitigation:** hash-based refresh + manual override fields.

- **Risk:** Deployment slowdown from binary files  
  **Mitigation:** migrate raw files to CDN/object storage.

- **Risk:** AI hallucinating unsupported claims  
  **Mitigation:** enforce citation-style prompt instructions + structured L2 fields.

---

## 9) Success Metrics

- < 5% increase in deploy time after doubling document count
- 99%+ document accessibility in production
- > 80% analyses include relevant document context when applicable
- Reduced manual ops time per new document
- Predictable monthly infra + token spend

---

## 10) Recommended Path for FXSentinel

Start with **Phase 1 MVP** immediately:
- keep your current metadata files,
- add ingestion worker,
- auto-populate AI context,
- then move to retrieval-enhanced analysis.

This gives fast feature delivery now without blocking on a full platform migration.

