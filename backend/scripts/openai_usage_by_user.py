#!/usr/bin/env python3
"""
Fetch OpenAI Completions usage grouped by end-user (user_id).

We pass `user` in chat.completions.create (email or Firebase uid); OpenAI stores
that and the Usage API returns it as user_id when you request group_by=user_id.

Requires an Organization Admin API key for the Usage API:
  OPENAI_ADMIN_API_KEY  (or OPENAI_API_KEY as fallback; Admin key may be needed)

Usage:
  cd backend && python scripts/openai_usage_by_user.py
  cd backend && python scripts/openai_usage_by_user.py --days 7 --bucket 1h
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Load .env from backend/ so OPENAI_ADMIN_API_KEY is available when run from any cwd
try:
    from dotenv import load_dotenv
    _backend_dir = Path(__file__).resolve().parent.parent
    load_dotenv(_backend_dir / ".env")
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

USAGE_URL = "https://api.openai.com/v1/organization/usage/completions"


def get_env_key():
    key = os.getenv("OPENAI_ADMIN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        print("Set OPENAI_ADMIN_API_KEY (or OPENAI_API_KEY). Admin key may be required for Usage API.")
        sys.exit(1)
    return key


def fetch_usage_by_user(admin_key: str, start_time: int, end_time: int, bucket_width: str = "1d"):
    headers = {
        "Authorization": f"Bearer {admin_key}",
        "Content-Type": "application/json",
    }
    params = {
        "start_time": start_time,
        "end_time": end_time,
        "group_by": "user_id",
        "bucket_width": bucket_width,
        "limit": 31,
    }
    out = []
    page = None
    while True:
        if page:
            params["page"] = page
        r = requests.get(USAGE_URL, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        for bucket in data.get("data", []):
            for result in bucket.get("results", []):
                out.append(result)
        page = data.get("next_page")
        if not page:
            break
    return out


def main():
    parser = argparse.ArgumentParser(description="OpenAI completions usage by end-user (user_id)")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default 7)")
    parser.add_argument("--bucket", choices=["1m", "1h", "1d"], default="1d", help="Time bucket width (default 1d)")
    args = parser.parse_args()

    admin_key = get_env_key()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())

    print(f"Fetching completions usage from {start.date()} to {end.date()} (group_by=user_id)...")
    results = fetch_usage_by_user(admin_key, start_ts, end_ts, args.bucket)

    # Aggregate by user_id
    by_user = {}
    for r in results:
        uid = r.get("user_id") or "(no user)"
        if uid not in by_user:
            by_user[uid] = {"input_tokens": 0, "output_tokens": 0, "num_requests": 0}
        by_user[uid]["input_tokens"] += r.get("input_tokens", 0) or 0
        by_user[uid]["output_tokens"] += r.get("output_tokens", 0) or 0
        by_user[uid]["num_requests"] += r.get("num_model_requests", 0) or 0

    if not by_user:
        print("No completions usage in the requested range (or no permission for Usage API).")
        return

    print(f"\nPer-user completions usage (last {args.days} days):\n")
    for uid, counts in sorted(by_user.items(), key=lambda x: -x[1]["num_requests"]):
        total_tokens = counts["input_tokens"] + counts["output_tokens"]
        print(f"  {uid}")
        print(f"    requests: {counts['num_requests']}, input_tokens: {counts['input_tokens']}, output_tokens: {counts['output_tokens']}, total_tokens: {total_tokens}")
        print()


if __name__ == "__main__":
    main()
