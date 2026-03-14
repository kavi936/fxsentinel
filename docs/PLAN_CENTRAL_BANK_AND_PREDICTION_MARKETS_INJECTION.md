# Plan: Central Bank Documents + Prediction Markets Injection into AI Analysis

**Status:** Ready to implement  
**Scope:** Single-currency calendar event analysis (the prompt built in `gpt_ai_analysis._create_analysis_prompt`).  
**Goal:** Inject relevant central bank document summaries (AI points) and prediction market expectations into the AI prompt, then update the prompt so GPT uses them correctly.

---

## What We Have

| Piece | Location | Purpose |
|-------|----------|--------|
| **Central bank AI context** | `backend/services/central_bank_ai_context.py` | Loads `backend/data/central_bank_documents_ai_context.json` (shortSummary, aiNotes, topics per doc). |
| **One-call helper** | `get_context_for_currency(currency, max_docs=3, max_notes_per_doc=5, include_prediction_markets=True)` | Returns a single string: "CENTRAL BANK DOCUMENT CONTEXT:" block + optional "Prediction market expectations (Polymarket, ...):" block for that currency’s central bank. |
| **Prediction markets** | `central_bank_ai_context.get_prediction_markets_context_for_currency(currency)` | Called inside `get_context_for_currency` when `include_prediction_markets=True`; uses `prediction_markets_context.get_central_bank_context(bank)` and formats for prompt. |
| **Prompt builder** | `backend/services/gpt_ai_analysis.py` → `_create_analysis_prompt()` | Builds event + economy context + market context; **does not yet** inject central bank docs or prediction markets. |

---

## Plan of Action

### Step 1: Wire injection in `gpt_ai_analysis.py`

1. **Import**  
   - In `gpt_ai_analysis.py`, add:  
     `from services.central_bank_ai_context import get_context_for_currency`

2. **Compute section**  
   - In `_create_analysis_prompt()`, after the economy context block is built (including policy target text), add:
     - `central_bank_pm_section = get_context_for_currency(currency, max_docs=3, max_notes_per_doc=5, include_prediction_markets=True)`
     - Keep it as a separate variable (not merged into `economy_context_section`) so we can place it and instruct on it explicitly in the prompt.

3. **Inject into prompt**  
   - In the same method, in the prompt string:
     - Insert `central_bank_pm_section` **after** `economy_context_section` and **before** "MARKET CONTEXT:" so the model sees: EVENT DETAILS → ECONOMIC CONTEXT (indicators + policy) → CENTRAL BANK DOCUMENT CONTEXT + PREDICTION MARKETS → MARKET CONTEXT → ...
     - Use a clear label if the block is non-empty, e.g.  
       `CENTRAL BANK & PREDICTION MARKET CONTEXT (use for policy stance and market-implied expectations):`  
       then the raw output of `get_context_for_currency` (which already contains "CENTRAL BANK DOCUMENT CONTEXT:" and possibly the Polymarket block). So the template would add something like:
       - If `central_bank_pm_section`: after `{economy_context_section}`, add a new line and then `central_bank_pm_section`.
       - This keeps a single, clear place in the prompt for both documents and prediction markets.

**Rationale:** One call to `get_context_for_currency(currency, include_prediction_markets=True)` gives both document summaries and Polymarket expectations for that event’s currency. No need to call prediction_markets separately from the analyzer.

---

### Step 2: Update the prompt instructions

Add a short **usage block** that tells the model how to use the new section (documents + prediction markets). Place it in the "PRIMARY ANALYSIS REQUIREMENTS" (or equivalent) so it’s enforced. Suggested wording (to be placed after economy context instructions):

- **Central bank document context**  
  - Use the central bank document summaries and notes to inform **policy stance**, **recent communication**, and **key themes** (e.g. data-dependent, inflation focus).  
  - Reconcile the **event outcome** (or expected outcome) with this stance (e.g. "in line with recent FOMC guidance", "contrasts with ECB’s emphasis on …").

- **Prediction market expectations**  
  - Use prediction market expectations as **one input** among others (economic context, document context, market context).  
  - When you rely on them, **say so** (e.g. "Market-implied probability of a cut is X%; this supports …").  
  - Do **not** present market-implied probabilities as your own forecast; label them as market expectations.

**Rationale:** So the model treats documents as authoritative communication context and prediction markets as cited, not as its own numbers.

---

### Step 3: Optional checks and docs

- **Currency support:** `get_context_for_currency` already returns `""` for currencies without a mapped bank; no change needed for unsupported currencies.
- **Token usage:** `max_docs=3` and `max_notes_per_doc=5` keep the block small; we can tune later if needed.
- **Docs:** After implementation, update `docs/AI_ANALYSIS_DATA_VALIDATION_NOTES.md` to state that central bank document context and prediction market expectations are injected for the event’s currency in the calendar AI analysis prompt and how the model is instructed to use them.

---

## Order of Work

1. Implement **Step 1** (import, compute `central_bank_pm_section`, inject into prompt string).  
2. Implement **Step 2** (add usage instructions for central bank docs + prediction markets).  
3. Run a quick manual test (e.g. trigger analysis for a USD or EUR event and confirm the prompt contains the new section).  
4. Update **Step 3** (validation notes doc).

---

## Out of Scope (for later)

- **Multi-currency prompts:** If we later add prompts that involve multiple currencies, we can switch to `get_context_for_prompt(currencies=[...], include_prediction_markets=True)` and inject that instead.
- **Topic filtering:** `get_context_for_prompt(..., topics=["inflation"])` is available if we want to restrict docs by topic in the future.
- **Enhanced / trader analysis:** Same pattern can be applied in `enhanced_ai_analysis.py` and `enhanced_trader_analysis.py` if those prompts also need central bank + prediction market context.
