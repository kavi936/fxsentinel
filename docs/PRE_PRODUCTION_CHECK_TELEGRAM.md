# Pre-production check: Telegram bot setup (seamless onboarding)

**Date:** 2025-03-08  
**Scope:** Changes for new-user Telegram setup (webhook deep link, bot decode/persist, Alerts copy, logging).

---

## 1. Code and build

- [x] **Lint:** No linter errors in `backend/app.py`, `backend/services/telegram_bot_setup.py`, `src/components/Alerts.jsx`.
- [x] **Frontend build:** `npm run build` succeeds.
- [x] **Types:** `send_welcome_alert(user_id, str(chat_id))` in both start and connect paths in `telegram_bot_setup.py`.

---

## 2. Security and logging

- [x] **Webhook:** Incoming Telegram update no longer logs full payload (avoids logging `/start TOKEN` in production). Logs only `chat_id` and whether message has text / command.
- [x] **Setup token:** Backend no longer prints the token value; only user id and token length.
- [x] **Access check:** Deep-link flow still calls `_verify_user_access(user_id)` before saving `chat_id`.

---

## 3. Flow verification (manual after deploy)

1. **Connect:** Dashboard → Alerts → Connect Telegram → open link (or “Open in app” on mobile).
2. **Auto-connect:** Telegram sends `/start TOKEN`; bot replies “You’re connected” and saves mapping.
3. **Verify:** Back in app, click “I’ve completed setup in Telegram” → should show connected.
4. **/status:** In Telegram, `/status` should show “Connected” (not “Not Connected”).
5. **/test:** Test alert should be received.

---

## 4. Environment

- `TELEGRAM_BOT_TOKEN` set in production.
- Webhook URL configured (if using webhook): `https://<your-domain>/api/telegram/webhook` set via Telegram Bot API or `/api/telegram/setup-webhook`.
- Firebase: Realtime Database rules allow write to `alerts/users/*` and `telegram_mappings/*` from backend.

---

## 5. Rollback

If issues occur after deploy:

- **Webhook:** Revert `backend/app.py` changes to the `/api/telegram/webhook` handler (exact `/start` match and previous welcome message).
- **Bot service:** Revert `backend/services/telegram_bot_setup.py` to previous start/connect logic (no token decode, no persist on start).
- **Frontend:** Revert `src/components/Alerts.jsx` instructions to the previous 4-step copy.

All changes are in these three files plus docs.
