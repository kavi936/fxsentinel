# Duplicate alert debugging – what logs to capture

If the same live news alert is still sent twice, capture the following so we can see why dedup didn’t block the second send.

---

## 1. Log lines that matter (grep or search for these)

| Log pattern | What it tells us |
|-------------|-------------------|
| `📋 DEDUP_KEY news content=` | **Content key** used for this story (title+source). If you see the same story twice, **both lines must show the same `content=` value**. If they differ, we have a key mismatch (e.g. title/source normalization). |
| `📋 DEDUP_ALLOW` | Dedup check **allowed** this send (no record in Firebase or expired). |
| `📋 DEDUP_BLOCK` | Dedup check **blocked** this send (record already reserved/sent). |
| `📋 RESERVED content=... (we won)` | This sender **won** the reservation for that content+user. |
| `📋 SENT content=... user=...` | Alert was **delivered** and marked sent (Unified path). |
| `🔍 Quick deduplication check` / `🔍 Double-check deduplication` | Unified path doing check before/after lock. |
| `🔍 _check_and_reserve_alert attempt` | Reserve attempt; includes alert key prefix. |
| `Duplicate prevented` / `Reservation lost` | Dedup or reserve blocked this send. |
| `Processing news alert from dedicated worker` | **API path** (worker → `/api/alerts/trigger`) is sending. |
| `Triggered async alert check for` | **Unified path** (main app) is processing news. |
| `✅ Successfully sent alert to user` | API path reports a send. |
| `Alert sent successfully to user` | NewsAlertTrigger / API path. |
| `⏳ Waiting 15s before next alert` | Unified path applied per-user delay after a send. |

---

## 2. What to capture when a duplicate happens

1. **Time window**  
   e.g. “both alerts arrived between 17:52 and 17:53 UTC”.

2. **Full log lines** (from app + worker if separate) for that window containing **any** of:
   - `DEDUP_KEY`
   - `DEDUP_ALLOW` / `DEDUP_BLOCK`
   - `RESERVED`
   - `SENT`
   - `_check_and_reserve_alert`
   - `Processing news alert from dedicated worker`
   - `Triggered async alert check`
   - `Successfully sent alert`
   - `Duplicate prevented` / `Reservation lost`

3. **For the duplicate story, specifically:**
   - Every line with the **exact title** (e.g. “Kashkari” or “Iran war”).
   - Every line with `content=...` or `DEDUP_KEY ... content=...` for that story (so we can confirm both sends used the **same** content key).

4. **Which process(es)** produced the logs (e.g. “main app only” vs “main app + background worker”), so we know if both Unified and API path were active.

---

## 3. How to interpret them

- **Same content key, second send has DEDUP_ALLOW**  
  Second sender didn’t see the first’s record (Firebase read after write, or second request hit a different instance). Need to look at timing and whether we need a short delay or stronger read-after-write.

- **Different content keys for the same story**  
  Key is still varying (e.g. title/source different between paths). We’d fix normalization or key construction so both paths produce the same key.

- **Second send has DEDUP_BLOCK or “Reservation lost”**  
  Dedup is working; the duplicate might be from an older run or a different alert type. Check timestamps and alert type.

- **One send from “Processing news alert from dedicated worker” and one from “Triggered async alert check” / “SENT”**  
  Both API and Unified path sent; then we check whether they used the same `DEDUP_KEY` and why the second wasn’t blocked (e.g. different key or Firebase not yet updated).

---

## 4. Quick one-liner (if logs are in a file or stdout)

After a duplicate, save logs and run:

```bash
# Replace with your log file or pipe
grep -E "DEDUP_KEY|DEDUP_ALLOW|DEDUP_BLOCK|RESERVED|SENT|check_and_reserve|dedicated worker|Triggered async|Successfully sent|Duplicate prevented|Reservation lost" your_log_file.txt
```

Then share the output (with timestamps) for the ~2–3 minutes around the duplicate.

---

## 5. Optional: temporary extra logging

If you need more detail, you can temporarily add:

- In **Unified path** (`unified_alert_processor._send_alert_to_user`): log “Unified path” + `user_id` + first 60 chars of title when entering the function.
- In **API path** (e.g. `main_app` or `scripts/main_app` route that calls `_send_alert_to_user`): log “API path” + `user_id` + first 60 chars of title when handling a news alert.

That makes it obvious which path each send came from when both run close together.
