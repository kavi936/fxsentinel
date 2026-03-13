# Central Bank Documents – AI Context (Backend Only)

## Purpose

This document describes the **AI-injection-only** data used to enrich prompts with central bank document summaries. It is **not exposed to the frontend** and is used only by backend AI analysis services.

---

## Location

**File:** `backend/data/central_bank_documents_ai_context.json`

- **Visibility:** Backend-only. Never served to the frontend.
- **Structure:** JSON with document IDs as keys; each value has `shortSummary`, `aiNotes`, and `topics`.

---

## Schema

For each document:

```json
{
  "doc-id": {
    "shortSummary": "1-3 sentence summary for prompt injection.",
    "aiNotes": [
      "Atomic fact 1.",
      "Atomic fact 2.",
      "Atomic fact 3."
    ],
    "topics": ["topic1", "topic2", "topic3"]
  }
}
```

- **shortSummary**: Brief summary suitable for prompt context.
- **aiNotes**: Short, atomic facts the model can combine with other data.
- **topics**: Normalized topics for filtering (e.g. `boj`, `fed`, `inflation`, `policy_normalization`).

---

## How to Wire It to the AI Model

### 1. Load the helper

```python
from backend.services.central_bank_ai_context import get_central_bank_context_for_prompt
```

### 2. Get context for an event (by currency)

```python
# Get relevant central bank context for USD events
context_block = get_central_bank_context_for_prompt(currency="USD", max_docs=3, max_notes_per_doc=4)

# Inject into your prompt
prompt = f"""
...
CENTRAL BANK DOCUMENT CONTEXT (for policy/relevant macro events):
{context_block}
...
"""
```

### 3. Get context for a specific central bank

```python
# Get all FED-related document context
context_block = get_central_bank_context_for_prompt(central_bank="FED", max_docs=5)

# Or ECB, BOE, BOJ
context_block = get_central_bank_context_for_prompt(central_bank="ECB", max_docs=3)
```

### 4. Get context by topic

```python
# Get documents tagged with inflation
context_block = get_central_bank_context_for_prompt(topics=["inflation", "policy_normalization"], max_docs=4)
```

---

## Keeping It Updated

When you add or update documents in `public/central-bank-documents.json`:

1. Add the corresponding entry in `backend/data/central_bank_documents_ai_context.json` under the same document ID.
2. Fill in `shortSummary`, `aiNotes`, and `topics`.
3. Optionally update `lastUpdated` at the top of the file.

---

## Token Budget Tips

- Keep `shortSummary` to 1–3 sentences.
- Limit `aiNotes` to 3–5 atomic facts per document.
- In prompts, restrict to `max_docs=3–5` and `max_notes_per_doc=3–4` to avoid blowing the token budget.
