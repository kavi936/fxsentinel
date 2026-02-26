# Steps to Get a Fully Working Alerts System (Main App on Railway)

**Quick reference:** Checklist is at the bottom of this doc. Health: `GET /api/health/alerts` and `GET /api/health/unified-alert-processor`.

You run **only the main app** on Railway. Alerts are driven by:

1. **Unified Alert Processor** – started when the app boots; runs in a background thread.
2. **News scheduler** – every 5 minutes the app fetches news in the background and runs the alert check on the new items.
3. **On every `/api/news` request** – when news is returned (fresh or cached), an alert check is triggered.

So alerts **do** run without a separate worker. Follow these steps to get them working end-to-end.

---

## Phase 1: Environment and basics

### Step 1.1 – Required environment variables (Railway)

In your Railway project, set:

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather). Required for sending alerts. |
| `FIREBASE_REALTIME_URL` | Your Firebase Realtime Database URL (e.g. `https://YOUR_PROJECT-default-rtdb.firebaseio.com`). |
| `FIREBASE_PROJECT_ID` | Optional; defaults from URL. |

Without `TELEGRAM_BOT_TOKEN`, the bot won’t send; without Firebase, no users/settings/deduplication.

### Step 1.2 – Telegram webhook (so users can connect the bot)

**Why this matters:** When a user taps “Connect Telegram” and sends `/start` to your bot, Telegram needs to deliver that message to your app. A **webhook** tells Telegram: “send all updates for this bot to this URL.” If the webhook isn’t set, your app never sees `/start`, so it never saves the user’s `chat_id` and they can’t receive alerts.

**What you need:**
- Your **Railway backend URL** (e.g. `https://fxsentinel-backend.up.railway.app` or whatever your service is called). No trailing slash.
- Your **bot token** (`TELEGRAM_BOT_TOKEN` from BotFather).

**Webhook URL to register:**  
`https://YOUR_RAILWAY_DOMAIN/api/telegram/webhook`  
Example: `https://fxsentinel-backend.up.railway.app/api/telegram/webhook`

---

#### Option A – Set the webhook manually (browser or terminal)

1. **In the browser** (easiest; you’ll paste your token once):
   - Open:
     ```
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://YOUR_RAILWAY_DOMAIN/api/telegram/webhook
     ```
   - Replace `<YOUR_BOT_TOKEN>` with your actual token (e.g. `123456:ABC-DEF...`) and `YOUR_RAILWAY_DOMAIN` with your real Railway URL.
   - Example:
     ```
     https://api.telegram.org/bot123456:ABC-DEF.../setWebhook?url=https://fxsentinel-backend.up.railway.app/api/telegram/webhook
     ```
   - You should see a JSON response like `{"ok":true,"result":true,"description":"Webhook was set"}`.

2. **Or with curl** (no token in browser history):
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://YOUR_RAILWAY_DOMAIN/api/telegram/webhook"}'
   ```
   Replace `<YOUR_BOT_TOKEN>` and `YOUR_RAILWAY_DOMAIN` as above.

---

#### Option B – Use the project script (from repo, with env set)

1. **Using the Railway-focused script** (finds your backend URL and sets the webhook):
   ```bash
   cd backend
   # Ensure .env has TELEGRAM_BOT_TOKEN (and FIREBASE_* if script needs them)
   python fix_telegram_webhook_railway.py
   ```
   It will try common Railway URL patterns and set the webhook to the one that responds. Follow any prompts.

2. **Or the generic webhook script** (you set the domain):
   ```bash
   cd backend
   export DOMAIN_URL="https://YOUR_RAILWAY_DOMAIN"   # e.g. https://fxsentinel-backend.up.railway.app
   python setup_telegram_webhook.py setup
   ```

---

#### Verify the webhook is set

Open this in the browser (with your token):

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

You should see something like:

```json
{"ok":true,"result":{"url":"https://YOUR_RAILWAY_DOMAIN/api/telegram/webhook", ...}}
```

If `url` is empty or wrong, set it again with Option A or B.

---

#### What happens when a user sends `/start`

1. User opens your bot (e.g. from the “Connect Telegram” link in your app) and sends `/start`.
2. Telegram sends an update (the message) to your webhook URL (`POST /api/telegram/webhook`).
3. Your backend receives it, reads the `chat_id` (and optional `start` parameter with user id), saves the `chat_id` to Firebase for that user, and can reply with a welcome message.
4. That user now has a stored `chat_id` and can receive alerts.

If the webhook isn’t set, step 2 never happens and your app never saves the `chat_id`.

### Step 1.3 – Confirm processors are running

After deploy, open:

- `https://YOUR_APP.up.railway.app/api/health/unified-alert-processor`

You should see `"status": "healthy"` and `"processor": { "running": true, "thread_alive": true }`.  
That’s the component that actually runs alert checks.  
(Note: `/api/health/alerts` was written for a separate worker; with “main app only” it may say “degraded” even when the unified processor is healthy. Prefer the unified-alert-processor health for “are alerts running?”.)

---

## Phase 2: At least one user can receive alerts

Alerts are sent only to users who:

- Have **alert settings** in Firebase (under `alerts/users/<safe_user_id>/`),
- Have **Telegram enabled** in those settings,
- Have a valid **telegram_chat_id** stored (from completing the bot’s `/start` flow).

### Step 2.1 – See who’s in Firebase (local script)

From the repo root, with a `.env` in `backend/` (or env vars set) pointing at your **production** Firebase:

```bash
cd backend
python3 -c "
import sys
sys.path.insert(0, '.')
from services.firebase_realtime_storage import FirebaseRealtimeStorage
f = FirebaseRealtimeStorage()
users = f.get_all_users_with_alerts()
print('Users with alert settings:', len(users))
for u in users:
    uid = u.get('user_id')
    chat = u.get('telegram_chat_id')
    settings = u.get('settings', {})
    tg = settings.get('telegram_enabled') or settings.get('channels', {}).get('telegram', {}).get('enabled')
    print('  user_id (hash):', uid, '| chat_id:', chat or 'MISSING', '| telegram_enabled:', tg)
"
```

Interpretation:

- **0 users** → No one has alert settings yet. They need to open the app, go to Alerts/Settings, and save preferences (and connect Telegram).
- **Users with `chat_id: MISSING`** → They haven’t completed “Connect Telegram” (or webhook isn’t set).
- **Users with `telegram_enabled: False`** → Turn on Telegram in app, or fix via script below.

### Step 2.2 – Get your Telegram chat_id

1. Open your bot link (e.g. `https://t.me/YourBot?start=YOUR_FIREBASE_UID` if you use start param).
2. Send `/start` in the chat.
3. Either:
   - Check Railway logs for the webhook request; you should see the `chat_id` in the update, or
   - Use a small script that calls `getUpdates` (with the bot token) and shows the last message’s `chat.id`.

That number is your `chat_id`.

### Step 2.3 – Enable Telegram for a user (if needed)

If you have a real Firebase Auth UID and the chat_id from 2.2, run locally (against production Firebase):

```bash
# From repo root
python scripts/enable_telegram_for_user.py
```

Then edit the script’s `__main__` (bottom of the file) to pass your **Firebase Auth UID** and **Telegram chat_id**:

```python
if __name__ == '__main__':
    enable_telegram_for_user('YOUR_FIREBASE_AUTH_UID', 'YOUR_TELEGRAM_CHAT_ID')
```

Run again. Then re-run the snippet from Step 2.1 and confirm that user has a `chat_id` and `telegram_enabled` True.

### Step 2.4 – Ensure live news alerts are enabled for that user

In Firebase, for that user’s `settings`, ensure:

- `channels.telegram.enabled` is true (done by enable script), and
- Preferences allow live news, e.g. `preferences.alertTypes.liveNews` is true (or missing, which defaults to allowed in code).

You can set this in the app’s Alerts/Settings UI, or by updating the user’s `settings` in Firebase accordingly.

---

## Phase 3: Trigger a run and confirm delivery

### Step 3.1 – Rely on the 5-minute scheduler

The main app starts a daemon thread that every 5 minutes:

- Fetches news (RSS + alternative + Telegram),
- Saves to cache,
- Calls `check_news_alerts_async(fresh_news)`.

So with **no traffic**, alert checks still run every 5 minutes. You don’t have to call `/api/news` yourself for alerts to run.

### Step 3.2 – Force a run once (optional)

To test immediately:

- Call your production API so that news is fetched and the alert check runs, e.g.  
  `GET https://YOUR_APP.up.railway.app/api/news?force_refresh=true`  
  (or open the app and trigger a refresh).
- Or wait up to 5 minutes for the scheduler.

### Step 3.3 – Check logs

In Railway logs, look for lines like:

- `Background news fetch: saved … items to cache` then `Triggered alert check for … news items` (or from background fetch: `check_news_alerts_async`).
- `Processing alerts for N users`
- `Alert approved for user …`
- `Telegram alert sent to …`

If you see “No users with alerts enabled” or “User … has no Telegram chat ID” or “Telegram disabled”, go back to Phase 2.

### Step 3.4 – Send a test alert from the app

If your app has a “Send test alert” (or similar) button that calls the backend:

- Use it while logged in as the user you enabled. You should receive a Telegram message. That confirms bot token + chat_id + send path.

---

## Phase 4: Avoid “no alerts” due to deduplication

The system deduplicates so the same story isn’t sent twice. If **all** news is treated as already sent (e.g. stale hashes in Firebase), no alerts go out.

- **Normal case**: Per-user and global-hash TTLs (e.g. 30 minutes) and cleanup should prevent this. If you’ve never had alerts working, this is less likely.
- **If you see** logs like “all already sent globally” or “Duplicate prevented” for every item, then:
  - In Firebase Realtime, under `alert_deduplication/content_hashes`, you can delete old keys or wait for expiry.
  - For a **one-off test**, you can set in code `PersistentAlertDeduplication.force_send_mode = True`, deploy, trigger one run, then set it back to `False` and redeploy. Don’t leave force_send on in production.

---

## Duplicates and app restarts

**Yes – the app checks for alerts already sent after restart.** Deduplication state is stored in **Firebase** at `alert_deduplication/alerts/{alert_key}` (per user + per story). Every check does a GET to Firebase, so:

- After an app restart, the next run still sees “sent” records and will not resend those alerts.
- The same applies across multiple app instances (e.g. replicas) as long as they use the same Firebase project.

**Why you might still see the same alert twice:**

1. **TTL** – Each “sent” record expires after **2 hours** (`alert_ttl_hours`). If the same story is still in the feed and gets processed again after 2 hours, it can be sent again. If you want to avoid that, increase `alert_ttl_hours` in `persistent_alert_deduplication.py`.
2. **Different content key** – The dedup key is built from the story’s `id` when present, otherwise from normalized title + source. If the same story appears with a different `id` (e.g. from another source) or without an `id`, it gets a different key and can be sent again.
3. **Firebase errors** – If the GET or PUT to Firebase fails occasionally, the code may “fail open” and send, which can cause rare duplicates.

---

## Phase 5: Optional – monitoring and sanity checks

- **Unified processor**: `GET /api/health/unified-alert-processor` – confirms the alert thread is running and shows basic metrics.
- **Telegram**: `GET /api/health/telegram` – confirms the Telegram monitor (for receiving user commands) is present.
- **List users locally**: Use the snippet in Step 2.1 whenever you want to see who has `chat_id` and Telegram enabled.

---

## Debugging duplicate alerts

Use these log lines (e.g. in Railway logs or exported JSON) to see why a duplicate might have been sent.

### Log prefixes to search for

| Grep / search for | Meaning |
|-------------------|--------|
| `📋 DEDUP_ALLOW` | Dedup check passed: no record in Firebase or record expired. Alert is allowed to proceed. |
| `📋 DEDUP_BLOCK` | Dedup check blocked send: Firebase had a non-expired `reserved` or `sent` record. |
| `📋 RESERVED` | This process won the reservation for this (user, content). Only one sender should see this per (user, story). |
| `📋 SENT` | Telegram send succeeded. Log includes `content=...` (dedup key) and `user=...`. |

### How to interpret

1. **Same story sent twice**  
   Search for `📋 SENT` and the story title or a unique part of it. If you see **two** `📋 SENT` lines with the **same** `content=...` and **same** `user=...`, a duplicate got through. Compare the exact `content=` value in both lines:
   - If `content=` is **identical**, the bug is in reserve/send or timing (e.g. two processes, or TTL).
   - If `content=` is **different** for the “same” story, the dedup key is inconsistent (e.g. different `id` or title/source). Fix by making the content key stable for the same article.

2. **Why did it pass dedup?**  
   For that `content=` and `user=`, look for the previous `📋 DEDUP_ALLOW` or `📋 DEDUP_BLOCK`:
   - `DEDUP_ALLOW (no record in Firebase)` = first time, or Firebase had no record (e.g. GET failed or path wrong).
   - `DEDUP_ALLOW (no record or expired)` = record existed but was expired (TTL).
   - If you see **two** `DEDUP_ALLOW` for the same `content=` and `user=` before two `SENT`, the second check ran before the first send wrote to Firebase, or the key differs slightly.

3. **Reservation**  
   For each (user, story) you should see at most one `📋 RESERVED` followed by one `📋 SENT`. If you see two `RESERVED` with the same content and user, two processes/threads both thought they won; that’s a bug.

4. **Useful grep examples** (Railway or local logs)  
   - All dedup decisions: `DEDUP_ALLOW` or `DEDUP_BLOCK`  
   - All sends: `SENT`  
   - One user (replace with your user hash prefix): `user=a44dfd290db489ed`  
   - One story (replace with part of title or id): `content=news:8857318740138943045` or `title=ECB Mustn`

### Firebase check (optional)

In Firebase Realtime Database, open:

`alert_deduplication/alerts`

Each key is a hash of `(news, content, user_id)`. Check whether the same story has **one** record per user (status `sent` or `reserved`) or multiple. If you see two different keys for the same article, the content string is different (e.g. different `id` or title/source).

---

## Checklist (quick reference)

- [ ] Railway env: `TELEGRAM_BOT_TOKEN`, `FIREBASE_REALTIME_URL` set.
- [ ] Telegram webhook set to `https://YOUR_APP/api/telegram/webhook`.
- [ ] `/api/health/unified-alert-processor` returns healthy.
- [ ] At least one user in Firebase has `telegram_chat_id` and Telegram enabled in settings.
- [ ] That user has completed bot `/start` (so `chat_id` is stored).
- [ ] Either wait 5 minutes or call `/api/news?force_refresh=true` and check logs for “Processing alerts for N users” and “Telegram alert sent”.
- [ ] (Optional) Send test alert from app and receive it in Telegram.

Once these are done, the alerts system on the single main app on Railway is fully functional: the scheduler and `/api/news` will trigger the unified processor, which will send high-impact news to every user who has Telegram connected and enabled.
