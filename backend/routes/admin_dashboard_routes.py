"""
Local-only admin user dashboard API.

Requires:
  - Request from localhost (127.0.0.1 / ::1)
  - Firebase Bearer token for a DEVELOPER_EMAILS account
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from services.admin_auth import require_local_developer
from services.admin_user_dashboard import admin_user_dashboard

logger = logging.getLogger(__name__)

admin_dashboard_bp = Blueprint("admin_dashboard", __name__, url_prefix="/api/admin/user-dashboard")


def _guard():
    ok, user, err, status = require_local_developer()
    if not ok:
        return None, (jsonify({"error": err}), status)
    return user, None


@admin_dashboard_bp.route("/summary", methods=["GET"])
def dashboard_summary():
    """Aggregate stats only (lighter payload)."""
    _, err_resp = _guard()
    if err_resp:
        return err_resp

    force = request.args.get("refresh", "").lower() in ("1", "true", "yes")
    try:
        data = admin_user_dashboard.get_dashboard_data(force_refresh=force)
    except (TimeoutError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 504
    except Exception as e:
        logger.exception("Admin dashboard summary failed")
        return jsonify({"error": "Failed to load dashboard", "message": str(e)}), 500

    return jsonify(
        {
            "summary": data["summary"],
            "insights": data.get("insights"),
            "feedback": data["feedback"],
            "sources": data["sources"],
        }
    )


@admin_dashboard_bp.route("/users", methods=["GET"])
def dashboard_users():
    """Full merged user list + summary."""
    _, err_resp = _guard()
    if err_resp:
        return err_resp

    force = request.args.get("refresh", "").lower() in ("1", "true", "yes")
    try:
        data = admin_user_dashboard.get_dashboard_data(force_refresh=force)
    except (TimeoutError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 504
    except Exception as e:
        logger.exception("Admin dashboard users failed")
        return jsonify({"error": "Failed to load dashboard", "message": str(e)}), 500

    return jsonify(data)


def register_admin_dashboard_routes(app):
    app.register_blueprint(admin_dashboard_bp)
    logger.info("Admin user dashboard routes registered (localhost + developer only)")
