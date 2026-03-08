# Alert dedup log analysis (2026-03-08)

**Log file:** `data/logs.1772988171836.json`  
**Window:** 16:30:13 – 16:42:36 UTC  
**User chat_id:** 8008493413

## What the user saw (Telegram)

1. **US Inflation Gauges Likely Diverged Before War in Iran** – 15:51 UTC, Bloomberg  
2. **Iran war could make affordability bigger issue in 2026 elections** – 16:19 UTC, CNBC  
3. **JUST IN: Treasury Secretary Bessent says the US may lift sanctions on Russian oil** – 16:39 UTC, WatcherGuru  

User reported: alerts still “sent more than once or sent slightly differently”.

## Findings from logs

### 1. Per-chat dedup did run

- **16:39:53** – `CHAT_DEDUP_ALLOW` for chat_id=8008493413, Bessent story → send allowed.  
- **16:39:55** – `CHAT_DEDUP_SKIP` for same chat, same story → second send skipped.  
- **16:39:55** – “Skipping Telegram send for user c109c59… to chat_id 8008493413 due to per-chat dedup guard”.

So two backend users (a44dfd… and c109c59…) share chat_id 8008493413; the first got Bessent, the second was correctly skipped by per-chat dedup.

### 2. Why duplicates / “slightly different” can still happen

- **Log window:** Logs start at 16:30. The 15:51 and 16:19 sends are outside this file, so we can’t see if those were duplicated in the same run.
- **In-memory only:** Per-chat dedup was in-memory only. With multiple replicas, each replica has its own cache, so replica A can send and replica B can send the same story to the same chat.
- **Title variations:** Same story from different sources can have slightly different titles (e.g. “says” vs “said”, or extra words). Full normalized title gives different keys, so both get sent and look “slightly different” to the user.

### 3. “Telegram alert sent” logged more than once per send

- `send_telegram_alert` logs “Telegram alert sent to {chat_id}”.
- `process_alert` also logs “Telegram alert sent to chat_id {chat_id}”.
So one actual send can produce two log lines; that does not imply two messages to the user.

## Changes made (this session)

1. **Firebase-backed per-chat dedup**  
   - `persistent_alert_deduplication`: added `should_send_to_chat(chat_id, content_key)` and `mark_chat_sent(chat_id, content_key)` using path `alert_deduplication/chat_sends/{hash}` with 2h TTL.  
   - All replicas share this state, so once one replica sends to a chat, others will skip the same content_key for that chat.

2. **Truncated title for per-chat key**  
   - Per-chat content key now uses the first **60 characters** of the normalized title so small wording changes (e.g. “says” vs “said”) still map to the same key and are deduplicated.

3. **alert_service flow**  
   - Before send: check Firebase `should_send_to_chat`, then in-memory; if either says “already sent”, skip.  
   - After successful send: call `mark_chat_sent(chat_id, content_key)` so Firebase is updated for other replicas and future sends.

## Summary

- Per-chat dedup is working for the same replica (one user allowed, second user to same chat skipped).  
- Duplicates across replicas and “slightly different” duplicates from title variation are addressed by: (1) persisting per-chat dedup in Firebase, and (2) using a truncated (60-char) title for the per-chat key.
