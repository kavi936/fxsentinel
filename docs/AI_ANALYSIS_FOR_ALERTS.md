# AI analysis and alerts – usage and how to disable

## What’s happening

**Alerts can trigger paid AI analysis and use API credits.**

1. **Unified path** (main app): when processing live news, it calls `should_analyze_with_ai(news_item)`. If that returns `True`, it calls `_trigger_ai_analysis(news_item)` **before** sending the alert.
2. **API path** (worker → `/api/alerts/trigger`): same – it computes `needs_ai_analysis = should_analyze_with_ai(alert_data)` and passes it into `_send_alert_to_user(..., needs_ai_analysis)`.
3. **`_trigger_ai_analysis`** does a **GET** to your backend: `GET {API_BASE_URL}/api/analysis/{news_id}`. That request is server-to-server (no user token).
4. **`/api/analysis/<news_id>`** calls `generate_news_analysis(news_item)` → **MVP News Analyzer** → `analyze_news()`.
5. **MVP analyzer** has `should_use_gpt_analysis()` returning **True** for all news, so it calls **`_analyze_with_gpt()`**, which uses the **OpenAI API** (and falls back to free analysis only if there’s no key or rate limit).

So every high-impact alert that qualifies for AI (forex high-impact + credible source or critical keywords) triggers one **OpenAI** call via the MVP analyzer. That drives your usage up even though the request is from the alert system, not from a user clicking “Analyze” in the UI.

---

## How to stop alerts from using AI (and API credits)

Set this in your environment (e.g. in `.env` or your deployment config):

```bash
DISABLE_AI_FOR_ALERTS=true
```

Supported values (case-insensitive): `true`, `1`, `yes`. Any other value (or unset) keeps the previous behaviour (AI for alerts when the news qualifies).

**Effect:**

- `should_analyze_with_ai()` always returns **False**, so no alert is marked as “needs AI”.
- `_trigger_ai_analysis()` returns **None** immediately and does **not** call `/api/analysis/{news_id}`, so no MVP/OpenAI call is made for alerts.

Alerts will still be sent; they just won’t include AI-generated analysis (e.g. “Check dashboard for detailed analysis” style content without the GPT block).

---

## Where it’s implemented

| File | Change |
|------|--------|
| `backend/services/news_alert_trigger.py` | `should_analyze_with_ai()`: if `DISABLE_AI_FOR_ALERTS` is true/1/yes, return False. `_trigger_ai_analysis()`: if same env is set, return None without calling the API. |

---

## Optional: re-enable later

Remove `DISABLE_AI_FOR_ALERTS` or set it to `false`/`0`/`no` to allow AI analysis for alerts again (same behaviour as before this change).
