# AI Workflow & Multi-LLM Architecture Notes

Separate reference from `AI_ANALYSIS_WORKFLOW_IDEAS.md`. Focus: **how workflows create reliability**, **multi-model roles**, **routing**, **output contract**, **metrics**, and a **phased build**.

---

## What A Workflow Really Is (Trading AI)

A workflow is a **decision pipeline with memory and checks**, not “call LLM → return text.”

Each run should aim to:

1. Classify request/event type (`scheduled macro`, `breaking geopolitical`, `cross-asset flow`, etc.).
2. Gather required context (calendar, spot, vol regime, yields, positioning, prior narrative).
3. Score input quality (freshness, source trust, missing fields, conflict across feeds).
4. Choose analysis path (deterministic, LLM, or hybrid).
5. Produce standardized output (same schema every time).
6. Run consistency/risk validation.
7. Store forecast and monitor outcome for recalibration.

That turns outputs into a **product**, not a smart chatbot.

---

## Core Reliability Principles

- **Deterministic where possible**: math/rules for scoring, scenario thresholds, invalidations.
- **LLM where needed**: ambiguity, synthesis, narrative compression.
- **Single output contract**: traders should not hunt for fields.
- **Confidence must be calibrated**: a stated % should map to measurable outcomes over time.
- **Contradiction handling**: if macro scan and headline imply different USD skew, the system must **reconcile explicitly** (not silently contradict).
- **Fail-safe behavior**: when data is stale or conflicting, downgrade certainty or say **wait / no clear edge** when appropriate.

---

## Multi-LLM Strategy

Using several models is sound **only if each has a role**. Random switching adds noise.

### Recommended role split

| Role | Typical model tier | Job |
|------|-------------------|-----|
| **Fast / cheap** | Small, fast | Classification, extraction, tagging, quick summaries |
| **Reasoning** | Strong reasoning | Deep macro synthesis, scenario trees, regime interpretation |
| **Verifier / judge** | Strong + strict | Contradiction checks, logic consistency, output QA |

### Typical flow

1. Fast model: classify event, extract entities (pairs, countries, event type).
2. Deterministic layer: base scores, regime, calendar stress, data-quality flags.
3. Reasoning model: thesis **within those constraints** (no invented levels).
4. Verifier model: check for direction/scenario-label mismatch, unsupported confidence, missing invalidation.
5. If verification fails: repair pass, stricter template, or fallback (never ship silent nonsense).

This targets bugs like inconsistent CPI scenario labels and generic “80% confidence.”

---

## Routing Logic (Start With Rules, Not ML)

Example policy table (tune with product):

- **High-impact scheduled macro (CPI, NFP, FOMC)**  
  Deterministic scenario engine + reasoning model; optional pre/post windows (e.g. T-15m, T+1m, T+10m).

- **Breaking geopolitical / oil / Hormuz-type headline**  
  Fast headline pass → conflict check vs macro regime + risk proxies → escalate to deep model if conflict score high.

- **Low-impact news**  
  Lightweight model + short output; skip expensive depth unless user escalates.

---

## Output Contract (Must-Have Fields)

Every analysis type should converge on the same core shape:

| Field | Purpose |
|-------|---------|
| `thesis` | One-line stance |
| `direction` | Bullish / bearish / neutral (asset-specific if needed) |
| `confidence` + `confidence_basis` | Number + why (not a badge) |
| `time_horizon` | Scalp / intraday / swing / structural |
| `key_levels` | Anchored to **current spot** when possible |
| `invalidation` | What proves the thesis wrong |
| `scenario_table` | For event-driven releases (above / at / below) |
| `risk_flags` | Liquidity, correlation, event stacking |
| `data_quality` | Freshness, staleness, missing inputs |
| `model_trace` | Which path/models ran (debug + trust) |

---

## Evaluation: What “Reliable” Means

Track over time (weekly review):

- Directional hit rate by horizon (15m, 1h, 4h, 1d).
- **Calibration**: when confidence is X%, win rate should approximate X% (after enough samples).
- Contradiction rate (internal logic conflicts in one response).
- Actionability rate (has levels + invalidation + horizon).
- Latency to first usable brief.
- User override rate (ignored / disagreed with AI).

Improvement here matters as much as swapping models.

---

## Phased Build Plan

1. **Phase 1 — Fast win**: Unify output schema + add validator checks on every response path.
2. **Phase 2**: Router (event type + impact + conflict score + escalation).
3. **Phase 3**: Multi-model roles (fast → reasoner → verifier).
4. **Phase 4**: Confidence calibration from realized moves vs forecasts.
5. **Phase 5**: Trader-style personalization (scalper vs swing vs position) on top of the same contract.

---

## One-Line Summary

**Reliability = workflow (classification → quality → routing → standard output → verification → feedback), not a single smarter LLM.** Multiple models work best as **specialists + a verifier**, with deterministic math anchoring anything numeric.
