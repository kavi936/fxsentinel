# AI Analysis Card – Formatting Analysis

This doc summarises where the AI Analysis card lives, how GPT content is used, and what can be improved for formatting.

---

## 1. Where the card and data live

| Layer | Location | Role |
|-------|----------|------|
| **UI** | `src/components/Overview.jsx` ~4348–4840 | Renders the AI Analysis card; content when `aiAnalysisState === 'event-analysis'` and `aiAnalysis` is set. |
| **Styles** | `src/components/Overview.css` | `.ai-analysis-card`, `.ai-analysis-content`, `.key-takeaway`, `.market-reaction-value`, `.scenario-content p`, `.ai-analysis-expandable`, `.analysis-details`, etc. |
| **Data fetch** | `Overview.jsx` ~3070–3310 | `handleRequestAnalysis` → `generateEventAnalysis()` → POST `/api/enhanced-analysis/<event.id>`. |
| **Backend** | `backend/app.py` `/api/enhanced-analysis/<news_id>` | Builds response from `gpt_ai_analyzer.analyze_macro_event()` and returns JSON (snake_case). |
| **GPT service** | `backend/services/gpt_ai_analysis.py` | `GPTAnalysisResult` and prompt; GPT returns plain text in JSON fields (no explicit markdown in prompt). |

---

## 2. What’s displayed from GPT

- **Quick scan**: `headline`, `key_takeaway`, confidence bar, and chips (Event Impact, Volatility, Risk Level, Market Sentiment).
- **Forward scenarios**: Three blocks (Bullish / Bearish / Neutral) from `forward_scenarios.bullish`, `.bearish`, `.neutral`.
- **Market scenarios**: Table (Above / On forecast / Below) from `calculateMarketScenarios(aiAnalysis.eventSummary, eventTitle)`.
- **Expandable sections**: Event Summary, Market Reaction, Implications & Takeaways, Trading Plan, Big Picture, Next Catalysts. Each section’s GPT text is rendered via `safeRenderValue(...)`.

---

## 3. How text is rendered today (why formatting is limited)

- **`safeRenderValue(value)`** (Overview.jsx ~338–363): Converts value to a string (handles null, string, number, boolean, array, object). It does **not**:
  - Interpret newlines (`\n`) as line breaks
  - Interpret markdown (e.g. `**bold**`, `- bullet`)
- All GPT text is rendered inside `<p>`, `<div className="market-reaction-value">`, etc. as **plain text**. So:
  - Newlines in the API string appear as spaces or a single block unless CSS uses `white-space: pre-line`.
  - Any markdown would show as literal characters.

---

## 4. API response shape (relevant to formatting)

- Backend returns **snake_case** keys: `event_summary`, `market_reaction`, `implications_takeaways`, `trading_plan`, `big_picture`, `forward_scenarios`, `key_takeaway`, etc.
- Frontend transform (Overview.jsx ~3191–3297) builds a single object and uses **camelCase** for `eventSummary` but reads from `analysis.eventSummary`. The API actually sends `event_summary`, so the code should use `analysis.event_summary` for the event summary (or normalize all keys once). This is a separate bug; formatting work can assume the transformed object is correct after that is fixed.

---

## 5. Formatting improvements we can make

1. **Newlines**  
   - Option A: Split `safeRenderValue(text)` on `\n` and render as multiple `<p>` or fragments with `<br />`.  
   - Option B: Render in a wrapper with `white-space: pre-line` (and ensure no unsafe HTML).

2. **Lists**  
   - If GPT returns lines like `- item` or `• item`, detect and render as `<ul>/<li>` (with sanitisation).

3. **Typography and spacing**  
   - Tweak CSS for:
     - `.key-takeaway`, `.headline-text`
     - `.market-reaction-value`, `.scenario-content p`
     - `.details-content` and section labels  
   - Improve line-height, paragraph spacing, and max-width for readability.

4. **Optional markdown**  
   - If the backend or prompt is later changed to return markdown, add a small safe renderer (e.g. bold + bullets only) or a trusted markdown library with sanitisation.

5. **Cleanup**  
   - Remove debug `console.log` calls in the AI Analysis card (e.g. around 4490–4492) before or as part of formatting work.

---

## 6. Key file/line references

- **Card container**: `Overview.jsx` ~4348 (`className="ai-analysis-card grid-card"`).
- **Content block**: `Overview.jsx` ~4416–4828 (`aiAnalysisState === 'event-analysis' && aiAnalysis`).
- **Helpers**: `safeRenderValue` ~338, `parseRiskLevel` ~292, `parseVolatility` ~307, `parseMarketBias` ~322.
- **Expandable sections**: `Overview.jsx` ~4635–4824 (`ai-analysis-expandable`, `analysis-details`).
- **CSS**: `Overview.css` ~3939 (`.ai-analysis-card`), ~4411 (`.ai-analysis-content`), ~7737 (`.key-takeaway`), ~7803 (`.scenario-content p`), ~8056 (`.ai-analysis-expandable`), ~8265 (`.market-reaction-value`).

You can start formatting by (1) adding newline handling and (2) tightening typography and spacing in the card and expandable sections.
