#!/usr/bin/env python3
"""
Aggregate FXSentinel user data from Firebase Auth, Firestore, and Realtime DB
for the local admin dashboard.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

RTDB_FETCH_TIMEOUT_SECONDS = 8
TELEGRAM_CHAT_FETCH_TIMEOUT = (2, 4)

logger = logging.getLogger(__name__)


def _rtdb_user_key(user_id: str) -> str:
    if user_id and re.fullmatch(r"[a-fA-F0-9]{32}", user_id.strip()):
        return user_id.strip().lower()
    return hashlib.md5(user_id.encode()).hexdigest()


def _to_iso(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if hasattr(val, "timestamp") and callable(val.timestamp):
        try:
            return datetime.fromtimestamp(val.timestamp(), tz=timezone.utc).isoformat()
        except (OSError, ValueError, TypeError):
            pass
    return str(val)


def _auth_ts_ms_to_iso(ts_ms: Optional[int]) -> Optional[str]:
    if not ts_ms:
        return None
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    except (OSError, ValueError, TypeError):
        return None


def _days_ago(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, delta.days)
    except (ValueError, TypeError):
        return None


def analytics_exclude_emails() -> set:
    """Emails omitted from headline stats (developers + optional test accounts)."""
    emails: set = set()
    for key in ("DEVELOPER_EMAILS", "ANALYTICS_EXCLUDE_EMAILS"):
        raw = os.getenv(key, "")
        emails.update(e.strip().lower() for e in raw.split(",") if e.strip())
    return emails


def is_analytics_excluded(email: str, exclude: Optional[set] = None) -> bool:
    exclude = exclude or analytics_exclude_emails()
    return (email or "").strip().lower() in exclude


def is_never_activated(user: Dict[str, Any]) -> bool:
    """
    Signed up but never meaningfully used the product:
    no AI, no Telegram alerts, and no completed onboarding.
    """
    if user.get("is_excluded"):
        return False
    if user.get("receives_alert_delivery"):
        return False
    if (user.get("total_ai_analyses") or 0) > 0:
        return False
    if user.get("onboarding_status") == "completed":
        return False
    if not user.get("has_firestore_doc"):
        return True
    return user.get("onboarding_status") in ("pending", "skipped", "no_firestore")


def annotate_user_flags(user: Dict[str, Any], exclude: Optional[set] = None) -> Dict[str, Any]:
    exclude = exclude or analytics_exclude_emails()
    user["is_excluded"] = is_analytics_excluded(user.get("email", ""), exclude)
    user["never_activated"] = is_never_activated(user)
    return user


class AdminUserDashboardService:
    """Merge Auth, Firestore, alerts RTDB, and feedback into dashboard payloads."""

    def __init__(self):
        self._auth = None
        self._db = None
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_at: Optional[datetime] = None
        self._cache_ttl_seconds = 120

    def _ensure_auth(self) -> bool:
        if self._auth is not None:
            return True
        try:
            from firebase_admin import auth

            self._auth = auth
            return True
        except Exception as e:
            logger.warning("Firebase Auth unavailable for admin dashboard: %s", e)
            return False

    def _ensure_firestore(self) -> bool:
        if self._db is not None:
            return True
        try:
            from firebase_admin import firestore

            self._db = firestore.client()
            return True
        except Exception as e:
            logger.warning("Firestore unavailable for admin dashboard: %s", e)
            return False

    def _rtdb_base_url(self) -> Optional[str]:
        project = os.getenv("FIREBASE_PROJECT_ID", "fxsentinel")
        url = os.getenv("FIREBASE_REALTIME_URL", f"https://{project}-default-rtdb.firebaseio.com")
        return url.rstrip("/") if url else None

    def _telegram_chat_ids_by_rtdb_key(self) -> Dict[str, str]:
        """
        Who receives Telegram alert delivery — chat_id only.
        Skips alert settings and history entirely (those caused multi-minute hangs).
        """
        base = self._rtdb_base_url()
        if not base:
            return {}

        def fetch_one(safe_user_id: str) -> Optional[tuple]:
            try:
                import requests

                chat_resp = requests.get(
                    f"{base}/alerts/users/{safe_user_id}/telegram_chat_id.json",
                    timeout=TELEGRAM_CHAT_FETCH_TIMEOUT,
                )
                if chat_resp.status_code != 200 or not chat_resp.content:
                    return None
                chat_id = chat_resp.json()
                if chat_id:
                    return (safe_user_id, str(chat_id))
            except Exception:
                pass
            return None

        keyed: Dict[str, str] = {}
        try:
            import requests
            from concurrent.futures import ThreadPoolExecutor, as_completed

            shallow = requests.get(
                f"{base}/alerts/users.json?shallow=true",
                timeout=(3, 8),
            )
            shallow.raise_for_status()
            user_keys = list((shallow.json() or {}).keys()) if shallow.content else []
            if not user_keys:
                return {}

            with ThreadPoolExecutor(max_workers=20) as pool:
                futures = [pool.submit(fetch_one, k) for k in user_keys]
                for fut in as_completed(futures, timeout=25):
                    row = fut.result()
                    if row:
                        keyed[row[0]] = row[1]
        except Exception as e:
            logger.warning("Telegram delivery lookup skipped: %s", e)
        return keyed

    def _list_auth_users(self, max_results: int = 10_000) -> List[Dict[str, Any]]:
        if not self._ensure_auth():
            return []

        users: List[Dict[str, Any]] = []
        next_page_token = None

        while len(users) < max_results:
            page_size = min(1000, max_results - len(users))
            if next_page_token:
                result = self._auth.list_users(max_results=page_size, page_token=next_page_token)
            else:
                result = self._auth.list_users(max_results=page_size)

            for user in result.users:
                providers = [p.provider_id for p in user.provider_data]
                users.append(
                    {
                        "uid": user.uid,
                        "email": user.email or "",
                        "display_name": user.display_name or "",
                        "email_verified": bool(user.email_verified),
                        "disabled": bool(user.disabled),
                        "providers": providers,
                        "provider_label": "google" if "google.com" in providers else "email",
                        "created_at": _auth_ts_ms_to_iso(user.user_metadata.creation_timestamp),
                        "last_sign_in": _auth_ts_ms_to_iso(user.user_metadata.last_sign_in_timestamp),
                    }
                )

            if not result.has_next_page:
                break
            next_page_token = result.next_page_token

        return users

    def _firestore_users_map(self) -> Dict[str, Dict[str, Any]]:
        if not self._ensure_firestore():
            return {}

        out: Dict[str, Dict[str, Any]] = {}
        try:
            for doc in self._db.collection("users").stream():
                out[doc.id] = doc.to_dict() or {}
        except Exception as e:
            logger.error("Failed to stream Firestore users: %s", e)
        return out

    def _feedback_stats(self) -> Dict[str, Any]:
        if not self._ensure_firestore():
            return {"total": 0, "recent": []}

        recent: List[Dict[str, Any]] = []
        try:
            for doc in self._db.collection("feedback_submissions").limit(8).stream():
                d = doc.to_dict() or {}
                recent.append(
                    {
                        "id": doc.id,
                        "user_email": d.get("user_email", ""),
                        "category": d.get("category", ""),
                        "rating": d.get("rating"),
                        "created_at": _to_iso(d.get("created_at")),
                        "message_preview": (d.get("message") or "")[:120],
                    }
                )
        except Exception as e:
            logger.warning("Feedback stats unavailable: %s", e)

        return {"total": len(recent), "recent": recent}

    def _onboarding_status(self, fs: Optional[Dict[str, Any]]) -> str:
        if not fs:
            return "no_firestore"
        if fs.get("onboarding_survey_completed_at"):
            return "completed"
        if fs.get("onboarding_survey_skipped_at"):
            return "skipped"
        return "pending"

    def _merge_user(
        self,
        auth_user: Dict[str, Any],
        fs: Optional[Dict[str, Any]],
        telegram_chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        uid = auth_user["uid"]
        tp = (fs or {}).get("trader_profile") or {}

        subscription = (fs or {}).get("subscription_status") or "unknown"
        if not fs:
            subscription = "unknown"

        return {
            "uid": uid,
            "email": auth_user.get("email") or (fs or {}).get("user_email") or "",
            "display_name": auth_user.get("display_name") or (fs or {}).get("user_name") or "",
            "email_verified": auth_user.get("email_verified", False),
            "disabled": auth_user.get("disabled", False),
            "providers": auth_user.get("providers") or [],
            "provider_label": auth_user.get("provider_label", "email"),
            "created_at": auth_user.get("created_at"),
            "last_sign_in": auth_user.get("last_sign_in"),
            "days_since_signup": _days_ago(auth_user.get("created_at")),
            "days_since_active": _days_ago(auth_user.get("last_sign_in")),
            "has_firestore_doc": fs is not None,
            "subscription_status": subscription,
            "monthly_analysis_count": (fs or {}).get("monthly_analysis_count", 0) or 0,
            "daily_analysis_count": (fs or {}).get("daily_analysis_count", 0) or 0,
            "stripe_customer_id": (fs or {}).get("stripe_customer_id"),
            "total_ai_analyses": (fs or {}).get("total_ai_analyses", 0) or 0,
            "last_ai_usage": _to_iso((fs or {}).get("last_ai_usage")),
            "welcome_email_sent": bool((fs or {}).get("welcome_email_sent")),
            "onboarding_status": self._onboarding_status(fs),
            "onboarding_completed_at": _to_iso((fs or {}).get("onboarding_survey_completed_at")),
            "onboarding_skipped_at": _to_iso((fs or {}).get("onboarding_survey_skipped_at")),
            "trading_style": tp.get("trading_style"),
            "experience_level": tp.get("experience_level"),
            "primary_goal": tp.get("primary_goal"),
            "referral_source": tp.get("referral_source"),
            "marketing_opt_in": tp.get("marketing_opt_in"),
            "primary_pairs": list(tp.get("primary_pairs") or []),
            "primary_pairs_count": len(tp.get("primary_pairs") or []),
            "telegram_chat_id": telegram_chat_id,
            "telegram_connected": bool(telegram_chat_id),
            "receives_alert_delivery": bool(telegram_chat_id),
        }

    def _compute_summary(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        week_buckets: Dict[str, int] = defaultdict(int)

        for u in users:
            created = u.get("created_at")
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    week_start = (dt - timedelta(days=dt.weekday())).date().isoformat()
                    week_buckets[week_start] += 1
                except (ValueError, TypeError):
                    pass

        # Last 12 weeks, oldest first
        weeks_sorted = sorted(week_buckets.items())[-12:]

        def count_where(key, val):
            return sum(1 for u in users if u.get(key) == val)

        referral = Counter(u.get("referral_source") or "unknown" for u in users if u.get("onboarding_status") == "completed")
        experience = Counter(u.get("experience_level") or "unknown" for u in users if u.get("onboarding_status") == "completed")
        goals = Counter(u.get("primary_goal") or "unknown" for u in users if u.get("onboarding_status") == "completed")
        trading_styles = Counter(u.get("trading_style") or "unknown" for u in users if u.get("onboarding_status") == "completed")
        completed = [u for u in users if u.get("onboarding_status") == "completed"]
        primary_pairs = Counter()
        for u in completed:
            for pair in u.get("primary_pairs") or []:
                if pair:
                    primary_pairs[pair] += 1
        marketing_yes = sum(1 for u in completed if u.get("marketing_opt_in") is True)

        active_7d = sum(1 for u in users if (u.get("days_since_active") or 999) <= 7)
        active_30d = sum(1 for u in users if (u.get("days_since_active") or 999) <= 30)
        ai_users = sum(1 for u in users if (u.get("total_ai_analyses") or 0) > 0)
        total_ai = sum(u.get("total_ai_analyses") or 0 for u in users)
        alert_delivery = sum(1 for u in users if u.get("receives_alert_delivery"))
        never_activated = sum(1 for u in users if u.get("never_activated"))
        total = len(users)

        return {
            "total_users": total,
            "firestore_docs": sum(1 for u in users if u.get("has_firestore_doc")),
            "email_signups": count_where("provider_label", "email"),
            "google_signups": count_where("provider_label", "google"),
            "email_verified": sum(1 for u in users if u.get("email_verified")),
            "onboarding_completed": count_where("onboarding_status", "completed"),
            "onboarding_skipped": count_where("onboarding_status", "skipped"),
            "onboarding_pending": count_where("onboarding_status", "pending"),
            "onboarding_no_firestore": count_where("onboarding_status", "no_firestore"),
            "onboarding_completion_rate_pct": round(
                count_where("onboarding_status", "completed") / total * 100
            ) if total else 0,
            "marketing_opt_in_count": marketing_yes,
            "marketing_opt_in_pct": round(marketing_yes / len(completed) * 100) if completed else 0,
            "subscription_free": count_where("subscription_status", "free"),
            "subscription_premium": count_where("subscription_status", "premium"),
            "subscription_developer": count_where("subscription_status", "developer"),
            "subscription_unknown": count_where("subscription_status", "unknown"),
            "active_last_7_days": active_7d,
            "active_last_30_days": active_30d,
            "active_30d_pct": round(active_30d / total * 100) if total else 0,
            "ai_users": ai_users,
            "ai_users_pct": round(ai_users / total * 100) if total else 0,
            "total_ai_analyses": total_ai,
            "telegram_connected": sum(1 for u in users if u.get("telegram_connected")),
            "alert_delivery_users": alert_delivery,
            "alert_delivery_pct": round(alert_delivery / total * 100) if total else 0,
            "never_activated": never_activated,
            "never_activated_pct": round(never_activated / total * 100) if total else 0,
            "signups_by_week": [{"week": w, "count": c} for w, c in weeks_sorted],
            "referral_sources": dict(referral.most_common()),
            "experience_levels": dict(experience.most_common()),
            "primary_goals": dict(goals.most_common()),
            "trading_styles": dict(trading_styles.most_common()),
            "primary_pairs": dict(primary_pairs.most_common(30)),
            "generated_at": now.isoformat(),
        }

    def _build_insights(self, users: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Human-oriented slices: top users, alert recipients, onboarding breakdown."""
        total = summary.get("total_users") or 0
        completed = summary.get("onboarding_completed") or 0

        def pct(part, whole):
            return round(part / whole * 100) if whole else 0

        def user_row(u):
            return {
                "email": u.get("email") or "",
                "display_name": u.get("display_name") or "",
                "uid": u.get("uid") or "",
                "days_since_active": u.get("days_since_active"),
            }

        top_ai = sorted(
            [u for u in users if (u.get("total_ai_analyses") or 0) > 0],
            key=lambda u: u.get("total_ai_analyses") or 0,
            reverse=True,
        )[:20]

        alert_recipients = [
            {
                **user_row(u),
                "telegram_chat_id": u.get("telegram_chat_id"),
            }
            for u in users
            if u.get("receives_alert_delivery")
        ]

        recently_active = sorted(
            [u for u in users if u.get("last_sign_in") and u.get("days_since_active") is not None],
            key=lambda u: u.get("days_since_active") or 999,
        )[:20]

        never_activated_users = sorted(
            [u for u in users if u.get("never_activated")],
            key=lambda u: u.get("created_at") or "",
            reverse=True,
        )[:30]

        marketing_opt_in_users = [
            {
                **user_row(u),
                "referral_source": u.get("referral_source"),
            }
            for u in users
            if u.get("onboarding_status") == "completed" and u.get("marketing_opt_in") is True
        ]

        def breakdown(counter_dict, base_count):
            if not counter_dict or not base_count:
                return []
            return [
                {"key": k, "count": v, "pct": pct(v, base_count)}
                for k, v in sorted(counter_dict.items(), key=lambda x: -x[1])
            ]

        headlines = [
            f"{total} real users (internal/test accounts excluded) — {summary.get('active_last_30_days', 0)} ({summary.get('active_30d_pct', 0)}%) active in the last 30 days.",
            f"{summary.get('never_activated', 0)} ({summary.get('never_activated_pct', 0)}%) signed up but never used the product (no AI, alerts, or completed onboarding).",
            f"{summary.get('ai_users', 0)} users ({summary.get('ai_users_pct', 0)}%) have used AI analysis ({summary.get('total_ai_analyses', 0)} runs total).",
            f"{summary.get('alert_delivery_users', 0)} users ({summary.get('alert_delivery_pct', 0)}%) receive Telegram alert delivery.",
            f"{completed} completed onboarding ({summary.get('onboarding_completion_rate_pct', 0)}%) — {summary.get('marketing_opt_in_count', 0)} opted in to marketing emails.",
        ]

        return {
            "headlines": headlines,
            "top_ai_users": [
                {
                    **user_row(u),
                    "total_ai_analyses": u.get("total_ai_analyses") or 0,
                    "last_ai_usage": u.get("last_ai_usage"),
                }
                for u in top_ai
            ],
            "alert_delivery": alert_recipients,
            "recently_active": [
                {**user_row(u), "last_sign_in": u.get("last_sign_in")}
                for u in recently_active
            ],
            "never_activated": [
                {
                    **user_row(u),
                    "created_at": u.get("created_at"),
                    "onboarding_status": u.get("onboarding_status"),
                    "has_firestore_doc": u.get("has_firestore_doc"),
                }
                for u in never_activated_users
            ],
            "marketing_opt_in_users": marketing_opt_in_users,
            "onboarding": {
                "survey_responses": completed,
                "completion_rate_pct": summary.get("onboarding_completion_rate_pct", 0),
                "skipped": summary.get("onboarding_skipped", 0),
                "pending": summary.get("onboarding_pending", 0),
                "marketing_opt_in": summary.get("marketing_opt_in_count", 0),
                "marketing_opt_in_pct": summary.get("marketing_opt_in_pct", 0),
                "referral_sources": breakdown(summary.get("referral_sources"), completed),
                "experience_levels": breakdown(summary.get("experience_levels"), completed),
                "primary_goals": breakdown(summary.get("primary_goals"), completed),
                "trading_styles": breakdown(summary.get("trading_styles"), completed),
                "primary_pairs": breakdown(summary.get("primary_pairs"), completed),
            },
        }

    def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        if (
            not force_refresh
            and self._cache
            and self._cache_at
            and (datetime.now(timezone.utc) - self._cache_at).total_seconds() < self._cache_ttl_seconds
        ):
            return self._cache

        # Direct synchronous calls — threading deadlocks the Firebase gRPC client on macOS.
        auth_users = self._list_auth_users()
        fs_map = self._firestore_users_map()
        telegram_map = self._telegram_chat_ids_by_rtdb_key()
        feedback = self._feedback_stats()

        if not auth_users:
            raise RuntimeError(
                "Could not load users from Firebase Auth. Check firebase-service-account.json and network."
            )

        merged: List[Dict[str, Any]] = []
        for au in auth_users:
            uid = au["uid"]
            fs = fs_map.get(uid)
            chat_id = telegram_map.get(_rtdb_user_key(uid))
            merged.append(self._merge_user(au, fs, chat_id))

        merged.sort(key=lambda u: u.get("created_at") or "", reverse=True)

        exclude = analytics_exclude_emails()
        for u in merged:
            annotate_user_flags(u, exclude)

        excluded_count = sum(1 for u in merged if u.get("is_excluded"))
        analytics_users = [u for u in merged if not u.get("is_excluded")]

        summary = self._compute_summary(analytics_users)
        summary["excluded_count"] = excluded_count
        insights = self._build_insights(analytics_users, summary)

        payload = {
            "summary": summary,
            "insights": insights,
            "users": merged,
            "meta": {
                "analytics_user_count": len(analytics_users),
                "excluded_count": excluded_count,
                "excludes_developer_emails": True,
                "marketing_opt_in_count": len(insights.get("marketing_opt_in_users") or []),
            },
            "feedback": feedback,
            "sources": {
                "firebase_auth": bool(auth_users),
                "firestore": bool(fs_map),
                "telegram_delivery": bool(telegram_map),
            },
        }

        self._cache = payload
        self._cache_at = datetime.now(timezone.utc)
        return payload


admin_user_dashboard = AdminUserDashboardService()
