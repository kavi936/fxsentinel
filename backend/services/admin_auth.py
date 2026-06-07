#!/usr/bin/env python3
"""
Auth helpers for local-only admin dashboard routes.
"""

import os
from typing import Any, Dict, Optional, Tuple

from flask import request


def _developer_emails() -> set:
    raw = os.getenv("DEVELOPER_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def is_local_request() -> bool:
    """Admin dashboard is intended for localhost only."""
    if os.getenv("ADMIN_DASHBOARD_ALLOW_REMOTE", "").lower() in ("1", "true", "yes"):
        return True
    addr = (request.remote_addr or "").strip()
    return addr in ("127.0.0.1", "::1", "localhost")


def extract_user_from_token() -> Optional[Dict[str, str]]:
    """Extract user from Firebase Bearer token."""
    try:
        from firebase_admin import auth as firebase_auth
    except ImportError:
        return None

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split("Bearer ", 1)[1].strip()
    if not token:
        return None

    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception:
        return None

    uid = decoded.get("uid", "")
    if not uid:
        return None

    return {
        "user_id": uid,
        "user_email": decoded.get("email", "") or "",
        "user_name": decoded.get("name", "") or decoded.get("display_name", "") or "",
    }


def require_local_developer() -> Tuple[bool, Optional[Dict[str, str]], Optional[str], int]:
    """
    Returns (ok, user_info, error_message, http_status).
    """
    if not is_local_request():
        return False, None, "Admin dashboard is only available on localhost", 403

    user = extract_user_from_token()
    if not user:
        return False, None, "Valid Firebase token required", 401

    email = (user.get("user_email") or "").lower()
    if email not in _developer_emails():
        return False, None, "Developer access required", 403

    return True, user, None, 200
