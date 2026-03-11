# AI Analysis: Styling, Prompting, Data & Model Options

Evaluation of ways to make FXSentinel’s economic-event AI analysis more powerful: **prompting**, **data we provide**, **how we use the OpenAI API**, and **alternative/other LLMs**.

---

## 1. Current State Summary

| Layer | Location | What it does |
|-------|----------|---------------|
| **Entry** | `backend/app.py` → `get_enhanced_analysis()` | Validates event, builds `GPTMarketContext` from `live_market_data_service`, calls `gpt_ai_analyzer.analyze_macro_event()`. |
| **Analyzer** | `backend/services/gpt_ai_analysis.py` | `GPTAIAnalyzer`: validates event, merges live market data, checks cache, rate limit, selects model (GPT-4 turbo for high impact, else GPT-3.5), builds prompt, calls OpenAI Chat Completions, parses JSON from response. |
| **Prompt** | `_create_analysis_prompt()` | Single user prompt: event details, market context (prices, volatility, sentiment), trading sessions, VIX, risk appetite, pairs sentiment, economy context (from static JSON), policy targets. Asks for one big JSON (headline, key_takeaway, forward_scenarios, event_summary, market_reaction, implications_takeaways, trading_plan, big_picture, next_catalysts). |
| **System prompt** | Inline in `_generate_enhanced_gpt_analysis()` | One line: *"You are a professional forex market analyst with deep expertise in economic events and their market impact."* |
| **Data sources** | Various | Event (calendar), `live_market_data_service` (TradingView: prices, volatility, sentiment), `economy_context_service` (static `economyIndicators.json`), `_get_trading_sessions()`, `_get_market_sentiment_data()`, `_get_pairs_sentiment_data()`, policy targets. |
| **Output** | `_parse_gpt_response()` | Regex to find `{...}` in reply, `json.loads`, normalize `forward_scenarios` to bullish/bearish/neutral; map `analysis_confidence` to numeric score. Fallback if no JSON. |

**Limitations today**

- System prompt is minimal; no output-style or “voice” guidance.
- One-shot, no few-shot examples; model may drift in structure/tone.
- No use of OpenAI **structured outputs** (JSON schema); parsing is brittle.
- Rich context exists (economy, policy, sessions) but prompt is one large block; no explicit “reasoning then answer” step.
- Model choice is binary (high impact → GPT-4 turbo, else 3.5); no use of GPT-4o / 4o-mini / o1.
- No other LLM providers; no A/B or fallback.

---

## 2. Prompting Improvements

### 2.1 Stronger system prompt

**Current:** Single sentence.

**Improvements:**

- **Role and constraints:**  
  *“You are a senior macro/FX analyst. Your answers must be grounded only in the EVENT DETAILS and MARKET CONTEXT provided. Do not invent data. If something is unknown, say so. Prefer short, scannable sentences and concrete numbers.”*

- **Output style:**  
  *“Write for a professional trader: headlines and key_takeaway must be actionable in one read. Avoid filler and repetition across sections. Use the exact JSON keys requested; no extra keys.”*

- **Calibration:**  
  *“Assign analysis_confidence (High/Medium/Low) based on data quality and certainty. Use assumptions[] only when you had to assume something (e.g. liquidity, no other headlines).”*

**Where:** Extend the `system` message in `_generate_enhanced_gpt_analysis()` (and/or a shared constant in `gpt_ai_analysis.py`).

### 2.2 Structured output (OpenAI JSON mode / response_format)

**Current:** Free-form text; we regex-extract JSON, so commas in strings or newlines can break parsing.

**Improvement:** Use [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) so the model returns valid JSON only.

- In the API call, set `response_format={ "type": "json_object" }` (or a strict schema via the API if you adopt it).
- In the prompt, keep one clear “OUTPUT FORMAT (JSON):” block and state: “Return only a single JSON object, no markdown or explanation.”
- Optionally define a Pydantic/JSON schema and pass it where supported (e.g. with a wrapper that uses the same schema for validation in Python).

**Benefits:** Fewer parse failures, no regex, optional validation against a schema before returning to the frontend.

### 2.3 Few-shot examples (1–2 in the prompt)

**Idea:** Add one pre-event and one post-event example (redacted) in the system or user prompt.

- Example: “PRE-EVENT example: [short snippet of event + context] → [short snippet of desired headline, key_takeaway, one scenario].”
- Redact real numbers if needed; keep structure and tone.

**Benefits:** More consistent structure (e.g. forward_scenarios wording, length of headline/key_takeaway), better handling of “no actual yet” vs “actual vs expected.”

### 2.4 Chain-of-thought (optional “reasoning then answer”)

**Idea:** Two-step call or a single prompt with explicit sections:

- **Option A – Two calls:**  
  1) “Given the event and context, in 2–3 short bullets state: surprise direction, main driver, key risk.”  
  2) “Using that reasoning, fill the following JSON: …” (use step 1 output as context).

- **Option B – Single prompt:**  
  “First briefly state: (1) How actual/expected compares to prior and trend, (2) Main policy implication, (3) Main FX channel. Then in the same response provide the JSON below.”

**Benefits:** Clearer reasoning, fewer contradictions, better use of economy/policy context. Cost/latency increase (especially with two calls).

### 2.5 Prompt structure and length

- **Sections:** Keep clear headers (EVENT DETAILS, MARKET CONTEXT, ECONOMIC CONTEXT, REQUIREMENTS, OUTPUT FORMAT) and put “OUTPUT FORMAT (JSON)” last so the model sees it immediately before generating.
- **Length:** Trim redundant instructions; move long “PRIMARY REQUIREMENTS” into a compact bullet list. Shorter prompts = cheaper and sometimes more reliable.
- **Explicit “do not”:** e.g. “Do not use markdown code fences around the JSON. Do not add keys that are not in the schema.”

---

## 3. Data We Provide: Richer Context

### 3.1 Already passed today

- Event: title, currency, impact, previous, expected, actual, (date/time from calendar).
- Market: current_prices, recent_volatility, market_sentiment (from TradingView), optional bond_yields, equity_indices, commodity_prices, key_levels.
- Economy: from static JSON (central bank rate, indicators) + policy targets (e.g. Fed 2% inflation, 4% unemployment).
- Sessions: active trading sessions, weekend/holiday flag, VIX, risk appetite, pairs sentiment (top 3 for currency).

### 3.2 Add or enrich

| Data | Source / approach | Why it helps |
|------|-------------------|--------------|
| **Upcoming events (next 1–2 weeks)** | Same calendar API used for the grid; filter by currency and impact | “Next catalysts” and “forward focus” can name real events and dates. |
| **Last release for same indicator** | Calendar or stored history | Compare “last time” vs “this time” (e.g. prior NFP vs this). |
| **Options-implied volatility** (e.g. FX vol surface, or VIX if we only have equity) | External API or broker | Volatility assessment and “typical move” can be data-driven. |
| **Time to event (minutes)** | Event datetime vs “now” (from backend) | Prompt can say “Event in 45 minutes” so the model can adjust for pre/post and liquidity. |
| **Recent headline or theme** (e.g. “Fed pivot”, “recession watch”) | Optional: 1–2 sentence from a news/sentiment service | Avoids generic “monitor central bank”; can tie analysis to current narrative. |

### 3.3 Pass “analysis type” and “missing data” explicitly

- In the prompt: “Analysis type: PRE_EVENT. Actual is not yet released; do not describe a realized outcome.”
- If we don’t have key_levels or vol: “Key levels: not provided. Do not invent specific levels; state that levels should be taken from the trader’s chart.”

This reduces hallucination and keeps tone consistent with what we actually have.

---

## 4. Using the OpenAI API Differently

### 4.1 Model choice

| Model | Use case | Cost (approx) | Notes |
|-------|----------|----------------|-------|
| **gpt-4o** | Default for all events | Mid | Strong reasoning, good at following format; newer than 4-turbo. |
| **gpt-4o-mini** | Low/medium impact or “quick” tier | Low | Cheaper; good for simpler events or first pass. |
| **gpt-4-turbo / gpt-4o** | High-impact only (current) | Higher | Keep for NFP, CPI, FOMC if you want maximum quality on those. |
| **o1 / o1-mini** | Optional “deep reasoning” tier | Highest | Use only for selected high-stakes analyses; latency higher. |

**Suggestion:** Prefer **gpt-4o** as default (or gpt-4o-mini for low impact) and keep 4-turbo or o1 only for a small set of “tier 1” events. Unify model names and cost in `_select_model()` and `_calculate_cost_estimate()`.

### 4.2 Structured outputs and response_format

- Use `response_format={ "type": "json_object" }` (and optional schema when supported) so the model returns only JSON.
- In the prompt: “Return only a single JSON object with the following keys: …”
- Parse with `json.loads` and validate required keys (and types) before building `GPTAnalysisResult`.

### 4.3 User / metadata for usage tracking

- You already pass `user` (email or id) for OpenAI usage; keep it. Optionally add a `metadata` or custom identifier in the request so you can tag “FXSentinel / enhanced-analysis” in the dashboard.

### 4.4 Multiple calls (optional)

- **Two-step:** (1) Short “reasoning” completion; (2) Main completion that takes reasoning + event + context and returns the full JSON. Only for premium or high-impact if you want to justify extra cost/latency.
- **Caching:** You already cache by event+type; ensure cache key includes a hash of “material” context (e.g. event id, expected/actual, date) so you don’t serve stale analysis after a number has been revised.

### 4.5 Embeddings (optional, for retrieval)

- If you later add “similar past events” or “similar analyses,” you could:  
  - Embed event title + currency + indicator type (and optionally outcome).  
  - Store in a vector DB; at analysis time, retrieve top-k and add “Similar past events: …” to the prompt.  
- Not required for the current single-event analysis but useful if you expand to “compare to last NFP” or “historical surprise distribution.”

---

## 5. Other LLMs / AI Models

### 5.1 OpenAI-only alternatives (same key)

- **Same key, different models:** Use gpt-4o, gpt-4o-mini, o1 as above; no new key.
- **Azure OpenAI:** Same API shape; different base URL and API key. Use if you need enterprise compliance or regional endpoints; prompt/data design stays the same.

### 5.2 Anthropic Claude (separate key)

- **API:** `anthropic` package; `messages` + `model` (e.g. `claude-3-5-sonnet-20241022`).
- **Pros:** Strong long-context, good instruction-following; different “voice” for A/B or fallback.
- **Cons:** Separate key and billing; need to map your JSON schema to Claude’s response (they support tool use / structured output in some models).
- **Integration:** Add `AnthropicAnalyzer` in a new module; same interface `analyze_macro_event(event, context, type) -> Result`. Router in `app.py` or config: `provider = "openai" | "anthropic"` (and optionally fallback: try OpenAI, on failure try Claude).

### 5.3 Google Gemini (separate key)

- **API:** `google-generativeai` or REST; model e.g. `gemini-1.5-pro` or `gemini-1.5-flash`.
- **Pros:** Long context, multimodal (if you ever add charts); competitive pricing.
- **Cons:** Slightly different message format and rate limits; JSON mode may need prompt engineering.
- **Integration:** Same idea: `GeminiAnalyzer`, same interface; router or fallback in app.

### 5.4 Local / OpenAI-compatible (e.g. LiteLLM, Ollama)

- **LiteLLM:** Single client; switch model via string (e.g. `openai/gpt-4o`, `anthropic/claude-3-5-sonnet`, `ollama/llama3`). Good for trying many providers with minimal code change.
- **Ollama / local models:** Run Llama, Mistral, etc. locally; no per-token cost, but quality and speed vary. Use for dev or “draft” tier; keep OpenAI/Claude for production quality.
- **Consideration:** Local models may be weaker at strict JSON; prefer a clear prompt + post-parse/validation.

### 5.5 Suggested rollout

1. **Short term:** Improve prompts and data (sections 2–3); add OpenAI `response_format` and possibly gpt-4o/4o-mini (section 4). No new providers yet.
2. **Next:** Add one alternative (e.g. Claude) behind a feature flag or config; same `analyze_macro_event` contract; compare quality and cost on a sample of events.
3. **Later:** Optional “model” in the API (e.g. `?model=openai` vs `anthropic`) or “tier” (e.g. premium = gpt-4o, standard = 4o-mini, draft = local).

---

## 6. Styling and Formatting of Analysis (for the UI)

### 6.1 What the model returns

- Today: One JSON with headline, key_takeaway, forward_scenarios (bullish/bearish/neutral), event_summary, market_reaction, implications_takeaways, trading_plan, big_picture, next_catalysts.
- Frontend uses these as-is (with `safeRenderValue` and optional markdown/line breaks if you add them).

### 6.2 Making output “styled” and scannable

- **In the prompt:** Ask for “short, scannable bullets where applicable” and “use **bold** only for the most important phrase in a sentence (one per section).” If the frontend will render markdown, say “You may use **bold** and line breaks for readability.”
- **Length caps (optional):** e.g. “headline: max 15 words; key_takeaway: max 2 sentences; each scenario: max 2 sentences.” Reduces wall-of-text.
- **Numbering and lists:** “For next_catalysts and trading_plan.best_approach, use short numbered lists where helpful.”

### 6.3 Frontend

- **Already done:** Clean card layout, sections, confidence, scenarios.
- **Optional:** Render `key_takeaway` and section text as markdown (e.g. `react-markdown`) so **bold** and newlines from the model show up. Sanitize HTML if you ever allow limited tags.
- **Consistency:** Ensure backend uses the same field names (snake_case) and the frontend expects them (camelCase mapping already in place); any new fields (e.g. assumptions[]) should be added to the contract and UI if you want to show them.

---

## 7. Prioritized Action List

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| **P0** | Use OpenAI `response_format={ "type": "json_object" }` and tighten “return only JSON” in prompt | Low | Fewer parse errors, more reliable responses. |
| **P0** | Expand system prompt (role, constraints, output style, confidence) | Low | More consistent tone and structure. |
| **P1** | Add time-to-event and “PRE_EVENT / POST_EVENT” explicitly in prompt; add “missing data” caveats | Low | Less hallucination, better calibration. |
| **P1** | Switch default to gpt-4o (or 4o-mini for low impact); update cost tracking | Low | Better quality and/or cost control. |
| **P2** | Enrich context: next 1–2 weeks of calendar events for same currency; last release for same indicator | Medium | Richer “next catalysts” and comparison. |
| **P2** | One few-shot example (pre and post) in prompt | Medium | More consistent structure. |
| **P3** | Optional second provider (Claude or Gemini) behind config; same interface | Medium | Redundancy and A/B. |
| **P3** | Optional chain-of-thought (single-prompt “reasoning then JSON”) for high-impact | Medium | Clearer reasoning. |
| **Later** | Markdown rendering for analysis body in frontend; prompt asks for bold/bullets | Low | Better readability. |

---

## 8. References in Codebase

- **Prompt and API call:** `backend/services/gpt_ai_analysis.py`  
  - `_create_analysis_prompt()` (lines ~1886–2149)  
  - `_generate_enhanced_gpt_analysis()` (lines ~1216–1285)  
  - `_parse_gpt_response()` (lines ~2151–2222)
- **Model selection and cost:** `_select_model()`, `_calculate_cost_estimate()`
- **Context building:** `app.py` `get_enhanced_analysis()` builds `GPTMarketContext`; analyzer uses `live_market_data_service`, `economy_context_service`, and internal helpers for sessions, sentiment, pairs.

Implementing the P0 and P1 items above will make the analysis more powerful and reliable without adding new infrastructure; P2/P3 and other LLMs can follow as needed.
