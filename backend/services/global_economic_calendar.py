import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

FF_FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
FF_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FXSentinel/1.0; +https://fxsentinel.io)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.forexfactory.com/",
}


class GlobalEconomicCalendar:
    """
    Automated ForexFactory calendar — replaces manual JSON export + hybrid paste.

    Fetches ff_calendar_thisweek.json on a TTL, normalizes to the app canonical schema,
    and persists to backend/cache/ff_calendar_feed.json (not the 27k-line Python file).
    """

    def __init__(self):
        self.forexfactory_url = FF_FEED_URL
        self.feed_file = os.path.join(os.path.dirname(__file__), "..", "cache", "ff_calendar_feed.json")
        self.cache_ttl = 6 * 60 * 60  # 6 hours
        self.last_fetch_succeeded = False
        self._feed_events: List[Dict] = []
        self._last_fetched: Optional[str] = None
        self._load_feed_store()
        print("🚀 Global Economic Calendar initialized (ForexFactory live feed)")

    def _load_feed_store(self) -> None:
        try:
            if not os.path.exists(self.feed_file):
                return
            with open(self.feed_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self._feed_events = payload.get("events") or []
            self._last_fetched = payload.get("last_fetched")
            self.last_fetch_succeeded = bool(self._feed_events)
        except Exception as e:
            print(f"⚠️ Error loading FF feed store: {e}")
            self._feed_events = []
            self._last_fetched = None

    def _save_feed_store(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.feed_file), exist_ok=True)
            with open(self.feed_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "last_fetched": self._last_fetched,
                        "source_url": self.forexfactory_url,
                        "event_count": len(self._feed_events),
                        "events": self._feed_events,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"⚠️ Error saving FF feed store: {e}")

    def get_feed_metadata(self) -> Dict:
        return {
            "last_fetched": self._last_fetched,
            "event_count": len(self._feed_events),
            "source_url": self.forexfactory_url,
            "last_fetch_succeeded": self.last_fetch_succeeded,
        }

    def _feed_is_stale(self) -> bool:
        if not self._last_fetched or not self._feed_events:
            return True
        try:
            fetched = datetime.fromisoformat(self._last_fetched.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - fetched).total_seconds()
            return age >= self.cache_ttl
        except Exception:
            return True

    def refresh_feed(self, force: bool = False) -> bool:
        """Fetch ForexFactory JSON and rebuild the local feed store."""
        if not force and not self._feed_is_stale():
            return True

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.forexfactory_url,
                    headers=FF_REQUEST_HEADERS,
                    timeout=30,
                )
                if response.status_code == 200:
                    raw = response.json()
                    if not isinstance(raw, list):
                        print("⚠️ ForexFactory response is not a list")
                        break
                    self._feed_events = self._parse_all_events(raw)
                    self._last_fetched = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    self.last_fetch_succeeded = True
                    self._save_feed_store()
                    print(f"✅ FF feed refreshed: {len(self._feed_events)} events")
                    return True
                if response.status_code == 429:
                    print(f"⚠️ ForexFactory rate limited (429), attempt {attempt + 1}/{max_retries}")
                else:
                    print(f"⚠️ ForexFactory HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ ForexFactory request error (attempt {attempt + 1}): {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))

        # Keep serving stale store if we have one
        if self._feed_events:
            self.last_fetch_succeeded = False
            print(f"⚠️ Using stale FF feed ({len(self._feed_events)} events)")
            return False

        self.last_fetch_succeeded = False
        return False

    def get_economic_events(self, start_date: str, end_date: str) -> List[Dict]:
        """Return normalized events in [start_date, end_date], refreshing feed if stale."""
        self.refresh_feed(force=False)
        if not self._feed_events:
            return []
        return [
            e
            for e in self._feed_events
            if start_date <= (e.get("date") or "") <= end_date
        ]

    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        self.refresh_feed(force=False)
        for event in self._feed_events:
            if event.get("id") == event_id:
                return event
        return None

    def _parse_all_events(self, data: List[Dict]) -> List[Dict]:
        events: List[Dict] = []
        for item in data:
            parsed = self._parse_ff_item(item)
            if parsed:
                events.append(parsed)
        events.sort(key=lambda e: (e.get("date") or "", e.get("time") or ""))
        return events

    def _parse_ff_item(self, item: Dict) -> Optional[Dict]:
        title = (item.get("title") or "").strip()
        date_str = item.get("date") or ""
        currency = (item.get("country") or "USD").strip()
        impact_raw = item.get("impact") or "Low"

        if not title or not date_str:
            return None
        if str(impact_raw).lower() == "holiday":
            return None

        event_date, event_time = self._parse_ff_datetime(date_str)
        impact = self._map_impact_level(impact_raw)
        forecast = item.get("forecast") or ""
        previous = item.get("previous") or ""
        actual_raw = item.get("actual")
        actual = str(actual_raw).strip() if actual_raw not in (None, "", "null") else "TBD"

        stable_key = f"{title}|{date_str}|{currency}"
        event_id = "ff_" + hashlib.sha256(stable_key.encode()).hexdigest()[:16]

        return {
            "id": event_id,
            "title": title,
            "date": event_date,
            "time": event_time,
            "country": self._get_country_from_currency(currency),
            "currency": currency,
            "impact": impact,
            "actual": actual,
            "expected": forecast if forecast != "" else "N/A",
            "previous": previous if previous != "" else "N/A",
            "source": "ForexFactory",
            "status": self._get_status_from_date(event_date),
            "type": self._get_event_type_from_title(title),
            "currencyPairs": self._get_currency_pairs(currency),
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "raw_data": {"date": event_date, "time": event_time},
        }

    def _parse_ff_datetime(self, date_str: str) -> Tuple[str, str]:
        """ISO FF datetime → (YYYY-MM-DD, HH:MM UTC)."""
        try:
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is not None:
                dt_utc = dt.astimezone(timezone.utc)
            else:
                dt_utc = dt.replace(tzinfo=timezone.utc)
            return dt_utc.strftime("%Y-%m-%d"), dt_utc.strftime("%H:%M UTC")
        except Exception:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d"), "12:00 UTC"

    def _get_country_from_currency(self, currency: str) -> str:
        currency_country_map = {
            "USD": "US",
            "EUR": "EU",
            "GBP": "GB",
            "JPY": "JP",
            "CAD": "CA",
            "AUD": "AU",
            "CHF": "CH",
            "NZD": "NZ",
            "CNY": "CN",
            "BRL": "BR",
            "SEK": "SE",
            "NOK": "NO",
            "HKD": "HK",
            "SGD": "SG",
            "KRW": "KR",
            "INR": "IN",
            "MXN": "MX",
            "ZAR": "ZA",
            "RUB": "RU",
            "TRY": "TR",
            "All": "ALL",
        }
        return currency_country_map.get(currency, currency)

    def _map_impact_level(self, impact: str) -> str:
        impact_lower = str(impact).lower()
        if impact_lower in ["high", "red", "3", "critical"]:
            return "high"
        if impact_lower in ["medium", "orange", "2", "yellow"]:
            return "medium"
        return "low"

    def _get_status_from_date(self, date_str: str) -> str:
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            if event_date < today:
                return "completed"
            if event_date == today:
                return "today"
            return "upcoming"
        except Exception:
            return "upcoming"

    def _get_event_type_from_title(self, title: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ["interest rate", "fed", "ecb", "boe", "rate decision", "cash rate"]):
            return "Interest Rate"
        if any(w in title_lower for w in ["unemployment", "employment", "payroll", "jobs", "claims"]):
            return "Employment"
        if any(w in title_lower for w in ["speaks", "speech", "testimony"]):
            return "Central Bank Speech"
        if any(w in title_lower for w in ["pmi", "confidence", "sentiment"]):
            return "Business Sentiment"
        return "Economic Indicator"

    def _get_currency_pairs(self, currency: str) -> List[str]:
        currency_pairs = {
            "USD": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"],
            "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF"],
            "GBP": ["GBPUSD", "EURGBP", "GBPJPY", "GBPCHF"],
            "JPY": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"],
            "CHF": ["USDCHF", "EURCHF", "GBPCHF", "AUDCHF"],
            "CAD": ["USDCAD", "EURCAD", "GBPCAD", "AUDCAD"],
            "AUD": ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY"],
            "NZD": ["NZDUSD", "EURNZD", "GBPNZD", "NZDJPY"],
            "CNY": ["USDCNY", "EURCNY", "GBPCNY", "JPYCNY"],
        }
        return currency_pairs.get(currency, ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"])

    def get_event_summary(self, start_date: str, end_date: str) -> Dict:
        events = self.get_economic_events(start_date, end_date)
        if not events:
            return {
                "total_events": 0,
                "countries": {},
                "impact_levels": {},
                "event_types": {},
                "high_impact_events": [],
            }

        countries: Dict[str, int] = {}
        impact_levels: Dict[str, int] = {}
        event_types: Dict[str, int] = {}
        high_impact_events = []

        for event in events:
            countries[event["country"]] = countries.get(event["country"], 0) + 1
            impact_levels[event["impact"]] = impact_levels.get(event["impact"], 0) + 1
            event_types[event["type"]] = event_types.get(event["type"], 0) + 1
            if event.get("impact") == "high":
                high_impact_events.append(
                    {
                        "title": event["title"],
                        "date": event["date"],
                        "time": event["time"],
                        "country": event["country"],
                        "currency": event["currency"],
                    }
                )

        return {
            "total_events": len(events),
            "countries": dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)),
            "impact_levels": dict(sorted(impact_levels.items(), key=lambda x: x[1], reverse=True)),
            "event_types": dict(sorted(event_types.items(), key=lambda x: x[1], reverse=True)),
            "high_impact_events": high_impact_events,
        }

    def clear_cache(self) -> None:
        self._feed_events = []
        self._last_fetched = None
        if os.path.exists(self.feed_file):
            os.remove(self.feed_file)
        print("🗑️ ForexFactory calendar feed store cleared")


global_economic_calendar = GlobalEconomicCalendar()
