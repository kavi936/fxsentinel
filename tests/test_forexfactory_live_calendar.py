#!/usr/bin/env python3
"""Tests for automated ForexFactory calendar feed (Step 1)."""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.global_economic_calendar import global_economic_calendar
from services.economic_calendar_service import economic_calendar_service


def test_ff_feed_refresh():
    ok = global_economic_calendar.refresh_feed(force=True)
    assert ok, "FF feed refresh should succeed"
    meta = global_economic_calendar.get_feed_metadata()
    assert meta.get("event_count", 0) > 0, "Should have events after refresh"


def test_event_schema():
    global_economic_calendar.refresh_feed(force=True)
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    events = global_economic_calendar.get_economic_events(start, end)
    assert events, "Should return events for current week"
    e = events[0]
    assert e.get("time", "").endswith(" UTC"), "Time must include UTC suffix for Overview"
    assert "expected" in e, "API field is expected not forecast"
    assert "raw_data" in e, "Frontend sort uses raw_data"
    assert e.get("id", "").startswith("ff_"), "Stable FF ids"


def test_unified_service_primary():
    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    events, source = economic_calendar_service.get_economic_events(start, end)
    assert events, "Unified service should return events"
    assert "ForexFactory" in source or "Hybrid" in source


if __name__ == "__main__":
    test_ff_feed_refresh()
    print("✅ test_ff_feed_refresh")
    test_event_schema()
    print("✅ test_event_schema")
    test_unified_service_primary()
    print("✅ test_unified_service_primary")
    print("All Step 1 calendar tests passed")
