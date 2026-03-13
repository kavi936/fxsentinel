"""
Calendar AI Analysis Store
Persists per-user economic calendar analyses in Firestore so they can be reused
across sessions without re-running expensive GPT analysis.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)


class CalendarAnalysisStore:
    """Store and retrieve per-user calendar AI analyses."""

    def __init__(self):
        try:
            self.db = firestore.client()
            self.firebase_available = True
            logger.info("✅ CalendarAnalysisStore initialized with Firestore")
        except Exception as e:
            logger.warning(f"⚠️ Firebase not available for CalendarAnalysisStore: {e}")
            self.db = None
            self.firebase_available = False

    def _get_user_doc_id(self, user_info: Dict[str, Any]) -> Optional[str]:
        """Mirror AIUsageTracker's strategy: prefer uid, otherwise hashed email."""
        if not user_info:
            return None

        user_id = (user_info.get("user_id") or "").strip()
        user_email = (user_info.get("user_email") or "").strip()

        if user_id:
            return user_id
        if user_email:
            return "email_" + hashlib.sha256(user_email.encode()).hexdigest()[:28]
        return None

    def save_calendar_analysis(
        self,
        user_info: Optional[Dict[str, Any]],
        event: Dict[str, Any],
        enhanced_analysis: Dict[str, Any],
        analysis_type: str,
    ) -> None:
        """
        Persist a calendar analysis snapshot for a given user and event.

        This stores enough data for the frontend to re-display the analysis
        without calling GPT again.
        """
        if not self.firebase_available or not self.db:
            logger.debug("Firebase not available, skipping calendar analysis persistence")
            return

        if not user_info:
            logger.debug("No user_info provided, skipping calendar analysis persistence")
            return

        user_doc_id = self._get_user_doc_id(user_info)
        if not user_doc_id:
            logger.debug("Could not derive user document id, skipping calendar analysis persistence")
            return

        try:
            # Build a stable document id per event + analysis_type so we upsert
            event_id = event.get("id") or enhanced_analysis.get("event_id")
            if not event_id:
                logger.debug("Event has no id, skipping calendar analysis persistence")
                return

            doc_id = f"{event_id}_{analysis_type}"

            # Keep a compact snapshot shaped for the frontend
            now = datetime.now(timezone.utc)
            doc = {
                "event_id": event_id,
                "analysis_type": analysis_type,
                "event_title": event.get("title") or enhanced_analysis.get("headline"),
                "event_currency": event.get("currency"),
                "event_date": event.get("date"),
                "event_time": event.get("time"),
                "impact": event.get("impact"),
                "analysis_snapshot": enhanced_analysis,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": now,
            }

            user_ref = self.db.collection("users").document(user_doc_id)
            analyses_col = user_ref.collection("calendarAnalyses")

            # Upsert so we don't duplicate entries for the same event/type
            analyses_col.document(doc_id).set(doc, merge=True)

            logger.info(
                f"✅ Saved calendar analysis for user={user_doc_id}, event_id={event_id}, type={analysis_type}"
            )
        except Exception as e:
            logger.error(f"❌ Error saving calendar analysis: {e}")

    def get_recent_calendar_analyses(
        self, user_info: Dict[str, Any], limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Fetch the most recent calendar analyses for a user."""
        if not self.firebase_available or not self.db:
            return []

        user_doc_id = self._get_user_doc_id(user_info)
        if not user_doc_id:
            return []

        try:
            user_ref = self.db.collection("users").document(user_doc_id)
            analyses_col = user_ref.collection("calendarAnalyses")

            query = (
                analyses_col.order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )

            results: List[Dict[str, Any]] = []
            for doc in query:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            return results
        except Exception as e:
            logger.error(f"❌ Error getting recent calendar analyses: {e}")
            return []


# Global instance
calendar_analysis_store = CalendarAnalysisStore()

