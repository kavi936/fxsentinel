"""
Load per-market research profiles (JSON) — wiring diagram for context sources.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_PROFILES_DIR = Path(__file__).resolve().parent / "profiles"


@lru_cache(maxsize=16)
def load_market_profile(market_id: str) -> Optional[Dict[str, Any]]:
    mid = (market_id or "").upper()
    path = _PROFILES_DIR / f"{mid}.json"
    if not path.is_file():
        logger.debug("No profile JSON for %s at %s", mid, path)
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data["market_id"] = mid
            return data
    except Exception as e:
        logger.warning("Failed to load market profile %s: %s", mid, e)
    return None
