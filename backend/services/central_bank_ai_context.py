"""
Central Bank Documents AI Context - Injection-friendly summaries for AI models.

Loads backend/data/central_bank_documents_ai_context.json (not exposed to frontend).
Use get_context_for_currency() or get_context_for_prompt() to enrich AI prompts.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

# Path to the AI-only context file (backend-only, not in frontend bundle)
_AI_CONTEXT_PATH = Path(__file__).resolve().parent.parent / "data" / "central_bank_documents_ai_context.json"

# Map currency codes to central bank IDs for filtering
_CURRENCY_TO_BANK = {
    "USD": "FED",
    "EUR": "ECB",
    "GBP": "BOE",
    "JPY": "BOJ",
    "CHF": "SNB",
    "CAD": "BOC",
    "AUD": "RBA",
    "NZD": "RBNZ",
}

# Document metadata: need centralBank and date for filtering (loaded from main docs or we keep a minimal map)
# Since we don't want to load the public JSON, we embed a minimal id->bank map from our AI context keys
_DOC_ID_TO_BANK = {
    "boj-2025-12-29-summary-opinions": "BOJ",
    "boj-2025-10-31-outlook-report": "BOJ",
    "fed-2026-01-16-bowman-speech": "FED",
    "fed-2026-01-11-powell-statement": "FED",
    "boe-2025-11-05-monetary-policy-report": "BOE",
    "boj-2026-01-23-outlook-report": "BOJ",
    "boj-2026-01-28-meeting-minutes": "BOJ",
    "fed-2026-01-28-fomc-statement": "FED",
    "ecb-2026-02-06-monetary-statement": "ECB",
    "boe-2026-02-01-monetary-policy-report": "BOE",
    "cftc-2026-03-03-cot-long-metals": "FED",
    "cftc-2026-03-03-cot-short-forex": "FED",
}


def _load_ai_context() -> Dict:
    """Load AI context from JSON. Returns empty dict if file missing."""
    try:
        if _AI_CONTEXT_PATH.exists():
            with open(_AI_CONTEXT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("documents", {})
    except (json.JSONDecodeError, IOError) as e:
        pass  # Silently fallback to empty
    return {}


# Module-level cache (loaded once)
_AI_CONTEXT: Optional[Dict] = None


def _get_context() -> Dict:
    global _AI_CONTEXT
    if _AI_CONTEXT is None:
        _AI_CONTEXT = _load_ai_context()
    return _AI_CONTEXT


def get_context_for_currency(
    currency: str,
    max_docs: int = 3,
    max_notes_per_doc: int = 5,
) -> str:
    """
    Get central bank document summaries relevant to a currency, formatted for prompt injection.

    Args:
        currency: Currency code (USD, EUR, GBP, JPY, etc.)
        max_docs: Max number of documents to include
        max_notes_per_doc: Max aiNotes per document to limit token usage

    Returns:
        Formatted string ready to inject into an AI prompt.
    """
    bank = _CURRENCY_TO_BANK.get(currency.upper())
    if not bank:
        return ""

    docs = _get_context()
    matching = [
        (doc_id, ctx)
        for doc_id, ctx in docs.items()
        if _DOC_ID_TO_BANK.get(doc_id) == bank
    ]
    # Sort by doc_id (contains date) - newest first
    matching.sort(key=lambda x: x[0], reverse=True)
    matching = matching[:max_docs]

    lines = []
    for doc_id, ctx in matching:
        summary = ctx.get("shortSummary", "")
        notes = ctx.get("aiNotes", [])[:max_notes_per_doc]
        lines.append(f"- {bank} ({doc_id}):\n  Summary: {summary}")
        if notes:
            lines.append("  Notes: " + "; ".join(notes))
    if not lines:
        return ""
    return "CENTRAL BANK DOCUMENT CONTEXT:\n" + "\n".join(lines)


def get_context_for_prompt(
    currencies: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    max_docs: int = 5,
    max_notes_per_doc: int = 5,
) -> str:
    """
    Get central bank document context for AI prompt injection.

    Args:
        currencies: Filter to these currency codes (e.g. ["USD", "EUR"]). If None, include all.
        topics: Filter docs containing these topics (e.g. ["inflation", "policy_normalization"]). If None, no topic filter.
        max_docs: Maximum documents to include
        max_notes_per_doc: Maximum aiNotes per document

    Returns:
        Formatted string for prompt injection.
    """
    docs = _get_context()
    matching = []
    for doc_id, ctx in docs.items():
        bank = _DOC_ID_TO_BANK.get(doc_id)
        if currencies and bank:
            # Check if any of the currencies map to this bank
            if bank not in {_CURRENCY_TO_BANK.get(c.upper()) for c in currencies if c}:
                continue
        if topics:
            ctx_topics = set(ctx.get("topics", []))
            if not any(t.lower() in " ".join(ctx_topics).lower() for t in topics):
                continue
        matching.append((doc_id, ctx))
    matching.sort(key=lambda x: x[0], reverse=True)
    matching = matching[:max_docs]

    lines = []
    for doc_id, ctx in matching:
        bank = _DOC_ID_TO_BANK.get(doc_id, "CB")
        summary = ctx.get("shortSummary", "")
        notes = ctx.get("aiNotes", [])[:max_notes_per_doc]
        lines.append(f"- {bank} ({doc_id}):\n  Summary: {summary}")
        if notes:
            lines.append("  Notes: " + "; ".join(notes))
    if not lines:
        return ""
    return "CENTRAL BANK DOCUMENT CONTEXT:\n" + "\n".join(lines)


def reload_context() -> None:
    """Force reload of AI context (e.g. after file update)."""
    global _AI_CONTEXT
    _AI_CONTEXT = None
