"""
Unified economic calendar service (Step 1: ForexFactory live feed).

Single entry point for calendar data across API, alerts, Markets, and economy scan.
Step 2 (later): MQL5 ingest writes to the same store shape — swap primary source here.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EconomicCalendarService:
    """ForexFactory live (primary) + hybrid embedded list (fallback on FF failure)."""

    def get_economic_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[List[Dict], str]:
        """
        Return (events, source_label) for the requested date range.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        ff_events: List[Dict] = []
        ff_ok = False
        try:
            from services.global_economic_calendar import global_economic_calendar

            ff_events = global_economic_calendar.get_economic_events(start_date, end_date) or []
            ff_ok = global_economic_calendar.last_fetch_succeeded
        except Exception as e:
            logger.warning("ForexFactory calendar fetch failed: %s", e)

        if ff_events:
            return ff_events, "ForexFactory (live)"

        if ff_ok:
            # Feed succeeded but nothing in range (e.g. user asked for next month only).
            return [], "ForexFactory (live)"

        logger.warning("ForexFactory unavailable — using hybrid calendar fallback")
        try:
            from services.hybrid_economic_calendar import hybrid_economic_calendar

            hybrid_events = hybrid_economic_calendar.get_economic_events(start_date, end_date) or []
            if hybrid_events:
                return hybrid_events, "Hybrid Calendar (fallback)"
        except Exception as e:
            logger.error("Hybrid calendar fallback failed: %s", e)

        return [], "no_data"

    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Look up a single event by id from FF store, then hybrid."""
        if not event_id:
            return None

        try:
            from services.global_economic_calendar import global_economic_calendar

            match = global_economic_calendar.get_event_by_id(event_id)
            if match:
                return match
        except Exception as e:
            logger.debug("FF event lookup failed: %s", e)

        try:
            from services.hybrid_economic_calendar import hybrid_economic_calendar

            start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
            for event in hybrid_economic_calendar.get_economic_events(start, end) or []:
                if event.get("id") == event_id:
                    return event
        except Exception as e:
            logger.debug("Hybrid event lookup failed: %s", e)

        return None

    def refresh_feed(self, force: bool = False) -> bool:
        """Pull latest ForexFactory JSON into the on-disk feed store."""
        try:
            from services.global_economic_calendar import global_economic_calendar

            return global_economic_calendar.refresh_feed(force=force)
        except Exception as e:
            logger.error("Calendar feed refresh failed: %s", e)
            return False

    def get_feed_metadata(self) -> Dict:
        try:
            from services.global_economic_calendar import global_economic_calendar

            return global_economic_calendar.get_feed_metadata()
        except Exception as e:
            return {"error": str(e)}


economic_calendar_service = EconomicCalendarService()
