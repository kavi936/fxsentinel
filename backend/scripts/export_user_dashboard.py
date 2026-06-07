#!/usr/bin/env python3
"""
Export all FXSentinel user data to CSV + print summary.

Merges Firebase Auth + Firestore users/{uid}.
Telegram chat IDs only (who receives alert delivery) — no alert settings/history.

Usage:
  cd backend && python3 scripts/export_user_dashboard.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone

backend_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, backend_dir)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(backend_dir, ".env"))
except ImportError:
    pass

try:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore, initialize_app
except ImportError:
    print("❌ pip install firebase-admin")
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None


def init_firebase():
    if firebase_admin._apps:
        return True
    project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fxsentinel"
    sa_path = os.path.join(backend_dir, "firebase-service-account.json")
    try:
        if os.path.exists(sa_path):
            initialize_app(credentials.Certificate(sa_path), {"projectId": project_id})
        else:
            initialize_app(options={"projectId": project_id})
        print(f"✅ Firebase ready ({project_id})", flush=True)
        return True
    except Exception as e:
        print(f"❌ Firebase init failed: {e}")
        return False


def ts_iso(ms):
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def rtdb_key(uid):
    if uid and re.fullmatch(r"[a-fA-F0-9]{32}", uid.strip()):
        return uid.strip().lower()
    return hashlib.md5(uid.encode()).hexdigest()


def load_auth_users():
    users = []
    token = None
    while True:
        page = auth.list_users(max_results=1000, page_token=token) if token else auth.list_users(max_results=1000)
        for u in page.users:
            providers = [p.provider_id for p in u.provider_data]
            users.append({
                "uid": u.uid,
                "email": u.email or "",
                "display_name": u.display_name or "",
                "email_verified": u.email_verified,
                "providers": ",".join(providers),
                "provider_label": "google" if "google.com" in providers else "email",
                "created_at": ts_iso(u.user_metadata.creation_timestamp),
                "last_sign_in": ts_iso(u.user_metadata.last_sign_in_timestamp),
            })
        if not page.has_next_page:
            break
        token = page.next_page_token
    return users


def load_firestore_map():
    db = firestore.client()
    out = {}
    for doc in db.collection("users").stream():
        out[doc.id] = doc.to_dict() or {}
    return out


def load_telegram_chat_ids():
    """Who gets alert delivery — chat_id only, fetched in parallel (no settings/history)."""
    if not requests:
        return {}
    from concurrent.futures import ThreadPoolExecutor, as_completed

    project = os.getenv("FIREBASE_PROJECT_ID", "fxsentinel")
    base = os.getenv("FIREBASE_REALTIME_URL", f"https://{project}-default-rtdb.firebaseio.com").rstrip("/")
    out = {}

    def fetch_one(key):
        try:
            c = requests.get(
                f"{base}/alerts/users/{key}/telegram_chat_id.json",
                timeout=(2, 3),
            )
            if c.status_code == 200 and c.content and c.json():
                return key, str(c.json())
        except requests.RequestException:
            pass
        return None

    try:
        shallow = requests.get(f"{base}/alerts/users.json?shallow=true", timeout=(3, 8))
        shallow.raise_for_status()
        keys = list((shallow.json() or {}).keys())
        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(fetch_one, k) for k in keys]
            for fut in as_completed(futures, timeout=25):
                row = fut.result()
                if row:
                    out[row[0]] = row[1]
    except Exception as e:
        print(f"⚠️  Telegram delivery lookup skipped: {e}", flush=True)
    return out


def onboarding_status(fs):
    if not fs:
        return "no_firestore"
    if fs.get("onboarding_survey_completed_at"):
        return "completed"
    if fs.get("onboarding_survey_skipped_at"):
        return "skipped"
    return "pending"


def merge_row(au, fs, telegram_chat_id):
    tp = (fs or {}).get("trader_profile") or {}
    sub = (fs or {}).get("subscription_status") or ("unknown" if not fs else "free")
    row = {
        "email": au["email"] or (fs or {}).get("user_email", ""),
        "display_name": au["display_name"] or (fs or {}).get("user_name", ""),
        "uid": au["uid"],
        "provider": au["provider_label"],
        "email_verified": au["email_verified"],
        "created_at": au["created_at"],
        "last_sign_in": au["last_sign_in"],
        "has_firestore_doc": fs is not None,
        "subscription_status": sub if fs else "unknown",
        "total_ai_analyses": (fs or {}).get("total_ai_analyses") or 0,
        "onboarding_status": onboarding_status(fs),
        "referral_source": tp.get("referral_source") or "",
        "experience_level": tp.get("experience_level") or "",
        "primary_goal": tp.get("primary_goal") or "",
        "trading_style": tp.get("trading_style") or "",
        "marketing_opt_in": tp.get("marketing_opt_in"),
        "primary_pairs_count": len(tp.get("primary_pairs") or []),
        "telegram_chat_id": telegram_chat_id or "",
        "receives_alert_delivery": bool(telegram_chat_id),
    }
    from services.admin_user_dashboard import annotate_user_flags
    return annotate_user_flags(row)


def print_summary(rows, analytics_rows):
    total = len(analytics_rows)
    print("\n" + "=" * 55)
    print(f"  Real users (excluded internal/test): {total}")
    if len(rows) != total:
        print(f"  Excluded from stats:               {len(rows) - total}")
    print(f"  Firestore profiles:  {sum(1 for r in analytics_rows if r['has_firestore_doc'])}")
    print(f"  Google / Email:      {sum(1 for r in analytics_rows if r['provider']=='google')} / {sum(1 for r in analytics_rows if r['provider']=='email')}")
    print(f"  Email verified:      {sum(1 for r in analytics_rows if r['email_verified'])}")
    print(f"  Used AI:             {sum(1 for r in analytics_rows if r['total_ai_analyses'] > 0)}")
    print(f"  Never activated:     {sum(1 for r in analytics_rows if r.get('never_activated'))}")
    print(f"  Alert delivery:      {sum(1 for r in analytics_rows if r['receives_alert_delivery'])}")
    print(f"  Marketing opt-in:    {sum(1 for r in analytics_rows if r.get('marketing_opt_in') is True and r['onboarding_status']=='completed')}")
    print(f"  Onboarding done:     {sum(1 for r in analytics_rows if r['onboarding_status']=='completed')}")
    refs = Counter(r["referral_source"] for r in analytics_rows if r["referral_source"])
    if refs:
        print("  Top referral sources:")
        for k, v in refs.most_common(5):
            print(f"    {k}: {v}")
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", default=os.path.join(backend_dir, "..", "user_dashboard_export.csv"))
    parser.add_argument(
        "--marketing-only",
        action="store_true",
        help="Export only users who completed onboarding and opted in to marketing emails",
    )
    args = parser.parse_args()

    print("Starting user export…", flush=True)
    if not init_firebase():
        sys.exit(1)

    t0 = time.time()
    print("  Loading Auth users…", flush=True)
    auth_users = load_auth_users()
    print(f"  Auth: {len(auth_users)} users ({time.time()-t0:.1f}s)", flush=True)

    t1 = time.time()
    print("  Loading Firestore…", flush=True)
    fs_map = load_firestore_map()
    print(f"  Firestore: {len(fs_map)} docs ({time.time()-t1:.1f}s)", flush=True)

    t2 = time.time()
    print("  Loading Telegram delivery targets…", flush=True)
    telegram_map = load_telegram_chat_ids()
    print(f"  Telegram linked: {len(telegram_map)} ({time.time()-t2:.1f}s)", flush=True)

    rows = []
    for au in auth_users:
        fs = fs_map.get(au["uid"])
        chat_id = telegram_map.get(rtdb_key(au["uid"]))
        rows.append(merge_row(au, fs, chat_id))

    rows.sort(key=lambda r: r["created_at"], reverse=True)
    analytics_rows = [r for r in rows if not r.get("is_excluded")]

    if args.marketing_only:
        export_rows = [
            r for r in analytics_rows
            if r.get("onboarding_status") == "completed" and r.get("marketing_opt_in") is True
        ]
        default_csv = os.path.join(backend_dir, "..", "marketing_opt_in_export.csv")
        path = os.path.abspath(default_csv if args.output == os.path.join(backend_dir, "..", "user_dashboard_export.csv") else args.output)
    else:
        export_rows = rows
        path = os.path.abspath(args.output)

    print_summary(rows, analytics_rows)

    fields = list(export_rows[0].keys()) if export_rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(export_rows)
    label = "Marketing opt-in" if args.marketing_only else "Users"
    print(f"✅ {label} CSV saved: {path}  ({len(export_rows)} rows, {time.time()-t0:.1f}s total)")


if __name__ == "__main__":
    main()
