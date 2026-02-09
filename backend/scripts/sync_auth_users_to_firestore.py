#!/usr/bin/env python3
"""
One-time (or occasional) sync: create Firestore users/<uid> for every Firebase Auth user
that does not yet have a document. This backfills 'user details' so that:

- Billing/subscription UI and usage limits work consistently for all existing users.
- You have a single source of truth in Firestore for free-tier defaults and optional
  user_email / user_name from Auth.

Does NOT overwrite existing users/<uid> docs (preserves Stripe and usage data).
Uses same Firebase Admin setup as list_firebase_users.py (service account or env).
"""

import sys
import os
from datetime import datetime, timezone

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_dir)

try:
    from dotenv import load_dotenv
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

try:
    import firebase_admin
    from firebase_admin import auth, credentials, initialize_app, firestore
except ImportError:
    print("❌ Error: firebase-admin is not installed")
    print("   Install it with: pip install firebase-admin")
    sys.exit(1)


def _date_to_firestore(d):
    """Firestore does not accept datetime.date; use start-of-day UTC as datetime."""
    if d is None:
        return None
    if hasattr(d, 'date') and callable(getattr(d, 'date', None)):
        d = d.date()
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


def initialize_firebase_admin():
    """Initialize Firebase Admin SDK (Auth + Firestore)."""
    try:
        if not firebase_admin._apps:
            project_id = os.getenv('FIREBASE_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT') or 'fxsentinel'
            if not os.getenv('GOOGLE_CLOUD_PROJECT'):
                os.environ['GOOGLE_CLOUD_PROJECT'] = project_id

            service_account_path = os.path.join(
                os.path.dirname(__file__), '..', 'firebase-service-account.json'
            )
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                initialize_app(cred, {'projectId': project_id})
                print(f"✅ Firebase Admin initialized (project: {project_id})")
            else:
                initialize_app(options={'projectId': project_id})
                print(f"✅ Firebase Admin initialized with default credentials (project: {project_id})")
        return True
    except Exception as e:
        print(f"❌ Error initializing Firebase Admin: {e}")
        return False


def list_all_auth_users(max_results=10_000):
    """List Firebase Auth users with pagination."""
    users = []
    next_page_token = None
    while True:
        if next_page_token:
            result = auth.list_users(max_results=min(1000, max_results - len(users)), page_token=next_page_token)
        else:
            result = auth.list_users(max_results=min(1000, max_results))
        for user in result.users:
            users.append({
                'uid': user.uid,
                'email': (user.email or '').strip() or None,
                'display_name': (user.display_name or '').strip() or None,
            })
        if not result.has_next_page or len(users) >= max_results:
            break
        next_page_token = result.next_page_token
    return users


def sync_auth_users_to_firestore(dry_run=False):
    """
    For each Firebase Auth user, create Firestore users/<uid> if it doesn't exist.
    Sets free-tier defaults and copies email/display name from Auth.
    """
    db = firestore.client()
    users_ref = db.collection('users')
    today = datetime.now(timezone.utc).date()
    current_month_start = today.replace(day=1)

    auth_users = list_all_auth_users()
    print(f"📋 Found {len(auth_users)} Firebase Auth user(s)")

    created = 0
    skipped = 0
    errors = 0

    for u in auth_users:
        uid = u['uid']
        email = u.get('email')
        display_name = u.get('display_name')

        try:
            doc_ref = users_ref.document(uid)
            if doc_ref.get().exists:
                skipped += 1
                continue

            if dry_run:
                print(f"  [DRY RUN] Would create users/{uid} (email={email or 'n/a'})")
                created += 1
                continue

            doc_ref.set({
                'subscription_status': 'free',
                'monthly_analysis_count': 0,
                'daily_analysis_count': 0,
                'last_monthly_reset': _date_to_firestore(current_month_start),
                'last_daily_reset': _date_to_firestore(today),
                'account_created': datetime.now(timezone.utc),
                **({'user_email': email} if email else {}),
                **({'user_name': display_name} if display_name else {}),
            })
            created += 1
            print(f"  ✅ Created users/{uid} ({email or 'no email'})")
        except Exception as e:
            errors += 1
            print(f"  ❌ users/{uid}: {e}")

    return created, skipped, errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sync Firebase Auth users into Firestore (create missing users/<uid> only)")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be created, do not write")
    args = parser.parse_args()

    print("=" * 60)
    print("Sync Firebase Auth users → Firestore (users collection)")
    print("=" * 60)

    if not initialize_firebase_admin():
        sys.exit(1)

    created, skipped, errors = sync_auth_users_to_firestore(dry_run=args.dry_run)

    print()
    print("Summary:")
    print(f"  Created: {created}")
    print(f"  Skipped (already existed): {skipped}")
    print(f"  Errors: {errors}")
    if args.dry_run and created:
        print("  (Run without --dry-run to apply changes)")
    print("✅ Done")


if __name__ == '__main__':
    main()
