# Live-lite security rotation checklist

Complete this **before** putting any secrets on Render or Vercel. Treat every Railway environment variable as possibly exposed (October 2025 Railway disclosure).

Do **not** copy old Railway values into Render “to save time.”

## 1. Audit spend / access

- [ ] OpenAI dashboard → Usage since Oct 21: unfamiliar spikes?
- [ ] OpenAI → set hard monthly budget (e.g. $5–10)
- [ ] Google AI Studio / Gemini: check quota and rotate key
- [ ] Stripe dashboard: unexpected charges or new webhooks?
- [ ] GitHub: unexpected commits, deploy keys, or Actions
- [ ] Firebase / Google Cloud: unexpected service accounts or keys

## 2. Rotate / revoke (create NEW keys, then disable OLD)

| Secret | Where to rotate | Notes |
|--------|-----------------|-------|
| `OPENAI_API_KEY` (+ admin key if any) | platform.openai.com → API keys | Revoke old; set usage limit |
| `GEMINI_API_KEY` | Google AI Studio | Revoke old |
| `STRIPE_SECRET_KEY` | Stripe → Developers → API keys | Roll secret; keep publishable if needed |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks | Point webhook at Render later or disable |
| `TELEGRAM_BOT_TOKEN` | BotFather `/revoke` | Rotate even if alerts stay off |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | my.telegram.org | Regenerate if Telethon was used |
| Firebase Admin JSON | Google Cloud → IAM → Service accounts → Keys | Add new key; **delete old key** |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Same Google Cloud SA or dedicated SA | Rotate if this lived in Railway |
| `RESEND_API_KEY` | resend.com | Rotate |
| `DOME_API_KEY` / `POLYROUTER_API_KEY` / `PROPHESEER_API_KEY` | Provider dashboards | Rotate |
| `FINNHUB_API_KEY` / Alpha Vantage / FMP / FRED | Provider dashboards | Rotate if used in Railway |
| SMTP password | Email provider | Rotate if set |

## 3. Railway cleanup

- [ ] Open Railway workspace → each service → Variables → **delete all secrets**
- [ ] Pause or delete the project (billing already cancelled)
- [ ] Revoke Railway account tokens / GitHub app access if unused

## 4. Local machine

- [ ] Replace values in `backend/.env` with **new** keys only (never commit)
- [ ] Confirm `.env`, `*.json` service accounts are gitignored (`git status` must not list them)
- [ ] Delete old Telethon `.session` files under `temp/` / `backend/` if present

## 5. Put NEW secrets only on Render

After rotation, set env vars on the Render web service (see `render.yaml`). Minimum for Overview live-lite:

- `LIVE_LITE_MODE=true`
- `OPENAI_API_KEY` (optional Analyze)
- `GEMINI_API_KEY` (optional grounding)
- Firebase Admin credentials (however your app loads them)
- `FINNHUB_API_KEY` or calendar sources you still use
- `ALERTS_ENABLED=false`
- `TELEGRAM_NEWS_ENABLED=false`
- `STRIPE_CHECKOUT_ENABLED=false`

## 6. Vercel

- [ ] Set `VITE_API_URL=https://<your-render-service>.onrender.com` (no trailing slash)
- [ ] Do **not** put OpenAI/Stripe secrets in Vercel (frontend only needs public Firebase + API URL)
- [ ] Redeploy frontend after changing `VITE_*`

## Done when

- [ ] Old keys revoked
- [ ] New keys only on Render (backend) / public config on Vercel
- [ ] Railway variables cleared
- [ ] `/api/health` on Render returns JSON
