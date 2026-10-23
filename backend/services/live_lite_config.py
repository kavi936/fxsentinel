"""
Live-lite / demo hosting flags.

When LIVE_LITE_MODE=true (Render free tier), alerts, Telegram news ingest,
and Stripe checkout default off unless explicitly re-enabled.
"""

from __future__ import annotations

import os


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def live_lite_mode() -> bool:
    return _env_bool("LIVE_LITE_MODE", False)


def alerts_enabled() -> bool:
    if os.getenv("ALERTS_ENABLED") is not None and os.getenv("ALERTS_ENABLED").strip() != "":
        return _env_bool("ALERTS_ENABLED", False)
    return not live_lite_mode()


def telegram_news_enabled() -> bool:
    if os.getenv("TELEGRAM_NEWS_ENABLED") is not None and os.getenv("TELEGRAM_NEWS_ENABLED").strip() != "":
        return _env_bool("TELEGRAM_NEWS_ENABLED", False)
    return not live_lite_mode()


def stripe_checkout_enabled() -> bool:
    if os.getenv("STRIPE_CHECKOUT_ENABLED") is not None and os.getenv("STRIPE_CHECKOUT_ENABLED").strip() != "":
        return _env_bool("STRIPE_CHECKOUT_ENABLED", False)
    return not live_lite_mode()
