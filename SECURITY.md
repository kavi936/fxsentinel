# Security

## Reporting

If you find a vulnerability in this public portfolio repo or the live demo at [fxsentinel.io](https://fxsentinel.io), email **kavi.cf412@gmail.com**. Please do not open a public issue with exploit details.

## What is intentionally public

- Application source code (this repository)
- Firebase **web** config identifiers used by the browser client (restricted by Firebase Auth / security rules — not Admin credentials)
- Documentation and architecture notes

## What must never be in git

- `.env` / API secrets (OpenAI, Gemini, Stripe secret, Telegram bot token, etc.)
- Firebase **Admin** / Google service-account JSON (private keys)
- Telethon `.session` files
- User exports / PII CSVs

These are gitignored. See `config/env.example` for variable **names** only.

## Operators (founder)

After any hosting-provider incident, rotate keys before redeploying. Checklist: [`docs/LIVE_LITE_SECURITY_ROTATION.md`](docs/LIVE_LITE_SECURITY_ROTATION.md).

Demo host runs with `LIVE_LITE_MODE=true` (alerts / Telegram ingest / Stripe checkout off) to reduce attack surface and cost.
