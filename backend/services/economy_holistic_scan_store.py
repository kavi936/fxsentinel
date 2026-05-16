"""
Per-user Holistic Scan snapshots in Firestore (same pattern as calendar_analysis_store).
Lets traders reopen past scans without re-running the endpoint.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from firebase_admin import firestore

logger = logging.getLogger(__name__)


def _jsonable_firestore_value(val: Any) -> Any:
    """Convert Firestore / datetime values to JSON-serializable forms."""
    if val is None:
        return None
    if isinstance(val, dict):
        return {k: _jsonable_firestore_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_jsonable_firestore_value(x) for x in val]
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, "timestamp") and callable(getattr(val, "timestamp")):
        try:
            if hasattr(val, "isoformat"):
                return val.isoformat()
        except Exception:
            pass
    return val


class EconomyHolisticScanStore:
    def __init__(self):
        try:
            self.db = firestore.client()
            self.firebase_available = True
            logger.info("EconomyHolisticScanStore initialized with Firestore")
        except Exception as e:
            logger.warning("Firebase not available for EconomyHolisticScanStore: %s", e)
            self.db = None
            self.firebase_available = False

    def _get_user_doc_id(self, user_info: Dict[str, Any]) -> Optional[str]:
        if not user_info:
            return None
        user_id = (user_info.get("user_id") or "").strip()
        user_email = (user_info.get("user_email") or "").strip()
        if user_id:
            return user_id
        if user_email:
            return "email_" + hashlib.sha256(user_email.encode()).hexdigest()[:28]
        return None

    def save_holistic_scan(
        self,
        user_info: Optional[Dict[str, Any]],
        country_code: str,
        scan_snapshot: Dict[str, Any],
        analysis_format_version: Optional[str] = None,
        spine: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if not self.firebase_available or not self.db:
            logger.debug("Firebase unavailable, skipping holistic scan persistence")
            return None
        if not user_info:
            return None
        user_doc_id = self._get_user_doc_id(user_info)
        if not user_doc_id:
            return None

        try:
            cc = (country_code or "").upper()
            doc_ref = (
                self.db.collection("users")
                .document(user_doc_id)
                .collection("economyHolisticScans")
                .document()
            )
            doc_ref.set(
                {
                    "country_code": cc,
                    "economy_label": scan_snapshot.get("economy") or cc,
                    "scan_snapshot": scan_snapshot,
                    # Additive V1 fields for shared brief on restored "Recent scans".
                    "analysis_format_version": analysis_format_version,
                    "spine": spine,
                    "created_at": firestore.SERVER_TIMESTAMP,
                }
            )
            logger.info(
                "Saved holistic scan for user=%s country=%s id=%s",
                user_doc_id,
                cc,
                doc_ref.id,
            )
            return doc_ref.id
        except Exception as e:
            logger.error("Error saving holistic scan: %s", e)
            return None

    def get_recent_holistic_scans(
        self,
        user_info: Dict[str, Any],
        limit: int = 15,
        country_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.firebase_available or not self.db:
            return []
        user_doc_id = self._get_user_doc_id(user_info)
        if not user_doc_id:
            return []

        fetch_cap = min(200, max(limit * 10, limit)) if country_code else limit

        try:
            col = (
                self.db.collection("users")
                .document(user_doc_id)
                .collection("economyHolisticScans")
            )
            query = (
                col.order_by("created_at", direction=firestore.Query.DESCENDING)
                .limit(fetch_cap)
                .stream()
            )

            results: List[Dict[str, Any]] = []
            for doc in query:
                data = doc.to_dict() or {}
                data["id"] = doc.id
                data["created_at"] = _jsonable_firestore_value(data.get("created_at"))
                results.append(data)

            if country_code:
                cc = country_code.upper()
                results = [r for r in results if (r.get("country_code") or "").upper() == cc][
                    :limit
                ]
            else:
                results = results[:limit]

            return results
        except Exception as e:
            logger.error("Error getting holistic scan history: %s", e)
            return []


economy_holistic_scan_store = EconomyHolisticScanStore()
