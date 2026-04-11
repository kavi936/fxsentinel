#!/usr/bin/env python3
"""
Trader onboarding / profile fields stored on Firestore users/{uid}.
Used for personalization (pairs, experience, style) and marketing opt-in.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from firebase_admin import firestore

logger = logging.getLogger(__name__)

# Broker-style instruments: FX (EUR/USD), commodities (XAU/USD), indices (US500/USD), crypto (BTC/USD).
# Alphanumeric segments 2–12 chars each side; not individual stocks.
INSTRUMENT_PATTERN = re.compile(r"^[A-Z0-9]{2,12}/[A-Z0-9]{2,12}$")
TRADING_STYLES = frozenset({"day", "swing", "both", "unsure"})
EXPERIENCE_LEVELS = frozenset({"beginner", "intermediate", "advanced"})
PRIMARY_GOALS = frozenset(
    {
        "stay_informed",
        "analysis_workflow",
        "alerts",
        "learning",
        "other",
    }
)
REFERRAL_SOURCES = frozenset(
    {
        "search",
        "social_x",
        "youtube",
        "instagram",
        "tiktok",
        "facebook",
        "linkedin",
        "discord",
        "reddit",
        "friend",
        "blog_news",
        "podcast",
        "other",
        "prefer_not_say",
    }
)
MAX_PAIRS = 24
ONBOARDING_SURVEY_VERSION = 1


def _timestamp_to_iso(val: Any) -> Optional[str]:
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
    return None


def _normalize_pair(p: str) -> str:
    return re.sub(r"\s+", "", (p or "").strip().upper())


def validate_trader_payload(data: Dict[str, Any], allow_skip: bool) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate PUT body. If allow_skip and skipped is True, only skipped flag matters.
    Returns (ok, error_message, normalized_dict).
    """
    if not isinstance(data, dict):
        return False, "Body must be a JSON object", None

    skipped = bool(data.get("skipped"))
    if allow_skip and skipped:
        return True, None, {"skipped": True}

    ts = data.get("trading_style")
    exp = data.get("experience_level")
    pairs = data.get("primary_pairs")
    marketing = data.get("marketing_opt_in")
    primary_goal = data.get("primary_goal")
    referral_source = data.get("referral_source")

    if ts is None or ts not in TRADING_STYLES:
        return False, f"trading_style must be one of: {', '.join(sorted(TRADING_STYLES))}", None
    if exp is None or exp not in EXPERIENCE_LEVELS:
        return False, f"experience_level must be one of: {', '.join(sorted(EXPERIENCE_LEVELS))}", None
    if not isinstance(pairs, list) or len(pairs) < 1:
        return False, "primary_pairs must be a non-empty array of pair strings (e.g. EUR/USD)", None
    if len(pairs) > MAX_PAIRS:
        return False, f"At most {MAX_PAIRS} pairs allowed", None

    normalized_pairs: List[str] = []
    seen = set()
    for raw in pairs:
        if not isinstance(raw, str):
            return False, "Each primary_pairs entry must be a string", None
        p = _normalize_pair(raw)
        if not INSTRUMENT_PATTERN.match(p):
            return (
                False,
                f"Invalid instrument format: {raw!r} (use BASE/QUOTE, e.g. EUR/USD, XAU/USD, US500/USD)",
                None,
            )
        if p not in seen:
            seen.add(p)
            normalized_pairs.append(p)

    if len(normalized_pairs) < 1:
        return False, "primary_pairs must contain at least one valid pair", None

    if marketing is not None and not isinstance(marketing, bool):
        return False, "marketing_opt_in must be a boolean", None

    if primary_goal is None or primary_goal not in PRIMARY_GOALS:
        return False, f"primary_goal must be one of: {', '.join(sorted(PRIMARY_GOALS))}", None
    if referral_source is None or referral_source not in REFERRAL_SOURCES:
        return False, f"referral_source must be one of: {', '.join(sorted(REFERRAL_SOURCES))}", None

    out: Dict[str, Any] = {
        "skipped": False,
        "trading_style": ts,
        "experience_level": exp,
        "primary_pairs": normalized_pairs,
        "marketing_opt_in": bool(marketing) if marketing is not None else False,
        "primary_goal": primary_goal,
        "referral_source": referral_source,
    }
    return True, None, out


class UserTraderProfileStore:
    """Read/write trader_profile and onboarding timestamps on users/{uid}."""

    def __init__(self):
        # Lazy Firestore client: app.py imports this module before initialize_app() runs, so
        # firestore.client() must not run in __init__ or it fails permanently for the process.
        self.db = None

    def _ensure_client(self) -> bool:
        if self.db is not None:
            return True
        try:
            self.db = firestore.client()
            logger.info("UserTraderProfileStore: Firestore client ready")
            return True
        except Exception as e:
            logger.warning("UserTraderProfileStore: Firestore not available: %s", e)
            return False

    def _ref(self, uid: str):
        return self.db.collection("users").document(uid)

    def get_profile(self, uid: str) -> Dict[str, Any]:
        """Return JSON-serializable profile + needs_survey flag."""
        default_tp = {
            "trading_style": None,
            "experience_level": None,
            "primary_pairs": [],
            "marketing_opt_in": None,
            "primary_goal": None,
            "referral_source": None,
        }
        if not self._ensure_client():
            # Prefer showing the survey when we cannot read Firestore; skipping looked like "instant redirect to dashboard".
            return {
                "needs_survey": True,
                "trader_profile": default_tp,
                "onboarding_survey_completed_at": None,
                "onboarding_survey_skipped_at": None,
                "onboarding_survey_version": ONBOARDING_SURVEY_VERSION,
                "firestore_available": False,
            }

        try:
            snap = self._ref(uid).get()
            if not snap.exists:
                return {
                    "needs_survey": True,
                    "trader_profile": default_tp,
                    "onboarding_survey_completed_at": None,
                    "onboarding_survey_skipped_at": None,
                    "onboarding_survey_version": ONBOARDING_SURVEY_VERSION,
                    "firestore_available": True,
                }

            d = snap.to_dict() or {}
            tp = d.get("trader_profile") or {}
            if not isinstance(tp, dict):
                tp = {}

            trader_profile = {
                "trading_style": tp.get("trading_style") if tp.get("trading_style") in TRADING_STYLES else None,
                "experience_level": tp.get("experience_level") if tp.get("experience_level") in EXPERIENCE_LEVELS else None,
                "primary_pairs": tp.get("primary_pairs") if isinstance(tp.get("primary_pairs"), list) else [],
                "marketing_opt_in": tp.get("marketing_opt_in") if isinstance(tp.get("marketing_opt_in"), bool) else None,
                "primary_goal": tp.get("primary_goal") if tp.get("primary_goal") in PRIMARY_GOALS else None,
                "referral_source": tp.get("referral_source") if tp.get("referral_source") in REFERRAL_SOURCES else None,
            }

            completed = d.get("onboarding_survey_completed_at")
            skipped = d.get("onboarding_survey_skipped_at")
            needs_survey = completed is None and skipped is None

            return {
                "needs_survey": needs_survey,
                "trader_profile": trader_profile,
                "onboarding_survey_completed_at": _timestamp_to_iso(completed),
                "onboarding_survey_skipped_at": _timestamp_to_iso(skipped),
                "onboarding_survey_version": d.get("onboarding_survey_version") or ONBOARDING_SURVEY_VERSION,
                "firestore_available": True,
            }
        except Exception as e:
            logger.exception("get_profile failed for %s: %s", uid, e)
            return {
                "needs_survey": True,
                "trader_profile": default_tp,
                "onboarding_survey_completed_at": None,
                "onboarding_survey_skipped_at": None,
                "onboarding_survey_version": ONBOARDING_SURVEY_VERSION,
                "firestore_available": False,
                "error": "read_failed",
            }

    def put_profile(self, uid: str, email: Optional[str], normalized: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Apply validated payload. Ensures users/{uid} exists (merge) without clobbering billing fields."""
        if not self._ensure_client():
            return False, "Firestore not available"

        try:
            ref = self._ref(uid)
            now = datetime.now(timezone.utc)

            if normalized.get("skipped"):
                ref.set(
                    {
                        "onboarding_survey_skipped_at": now,
                        "onboarding_survey_version": ONBOARDING_SURVEY_VERSION,
                        **({"user_email": email} if email else {}),
                    },
                    merge=True,
                )
                return True, None

            tp = {
                "trading_style": normalized["trading_style"],
                "experience_level": normalized["experience_level"],
                "primary_pairs": normalized["primary_pairs"],
                "marketing_opt_in": normalized["marketing_opt_in"],
                "primary_goal": normalized["primary_goal"],
                "referral_source": normalized["referral_source"],
                "updated_at": now,
            }
            ref.set(
                {
                    "trader_profile": tp,
                    "onboarding_survey_completed_at": now,
                    "onboarding_survey_skipped_at": None,
                    "onboarding_survey_version": ONBOARDING_SURVEY_VERSION,
                    **({"user_email": email} if email else {}),
                },
                merge=True,
            )
            return True, None
        except Exception as e:
            logger.exception("put_profile failed for %s: %s", uid, e)
            return False, str(e)


user_trader_profile_store = UserTraderProfileStore()
