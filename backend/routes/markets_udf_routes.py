"""
TradingView UDF datafeed routes + FXSentinel OHLC API.

Mount base: /api/udf
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from services.markets.market_registry import MARKETS
from services.markets.market_research_service import build_research
from services.markets.udf_datafeed import (
    markets_ohlc_json,
    udf_config,
    udf_history,
    udf_search,
    udf_symbol_info,
)

logger = logging.getLogger(__name__)

markets_udf_bp = Blueprint("markets_udf", __name__, url_prefix="/api/udf")


@markets_udf_bp.route("/config", methods=["GET", "OPTIONS"])
def udf_config_route():
    return jsonify(udf_config())


@markets_udf_bp.route("/symbols", methods=["GET", "OPTIONS"])
def udf_symbols_route():
    symbol = request.args.get("symbol", "")
    return jsonify(udf_symbol_info(symbol))


@markets_udf_bp.route("/search", methods=["GET", "OPTIONS"])
def udf_search_route():
    query = request.args.get("query", "")
    try:
        limit = int(request.args.get("limit", 30))
    except ValueError:
        limit = 30
    return jsonify(udf_search(query, limit=limit))


@markets_udf_bp.route("/history", methods=["GET", "OPTIONS"])
def udf_history_route():
    symbol = request.args.get("symbol", "")
    resolution = request.args.get("resolution", "240")
    try:
        from_ts = int(request.args.get("from", 0))
        to_ts = int(request.args.get("to", 2_000_000_000))
    except ValueError:
        return jsonify({"s": "error", "errmsg": "Invalid from/to timestamps"}), 400

    countback_raw = request.args.get("countback")
    countback = int(countback_raw) if countback_raw and countback_raw.isdigit() else None

    return jsonify(
        udf_history(symbol, resolution, from_ts, to_ts, countback=countback)
    )


@markets_udf_bp.route("/time", methods=["GET", "OPTIONS"])
def udf_time_route():
    """Optional server time for UDF — Unix seconds."""
    import time

    return str(int(time.time()))


# --- FXSentinel-native OHLC (Lightweight Charts / research) ---

markets_api_bp = Blueprint("markets_api", __name__, url_prefix="/api/markets")


@markets_api_bp.route("", methods=["GET", "OPTIONS"])
@markets_api_bp.route("/", methods=["GET", "OPTIONS"])
def markets_list_route():
    return jsonify(
        {
            "markets": [
                {
                    "id": m["id"],
                    "label": m.get("label", m["id"]),
                    "enabled": m.get("enabled", False),
                }
                for m in MARKETS.values()
            ]
        }
    )


@markets_api_bp.route("/<market_id>/research", methods=["GET", "OPTIONS"])
def market_research_route(market_id: str):
    refresh = request.args.get("refresh", "true").lower() != "false"
    payload = build_research(market_id.upper(), refresh=refresh)
    if payload.get("error") == "unknown_market":
        return jsonify(payload), 404
    if payload.get("error") == "market_disabled":
        return jsonify(payload), 403
    return jsonify(payload)


@markets_api_bp.route("/<market_id>/ohlc", methods=["GET", "OPTIONS"])
def market_ohlc_route(market_id: str):
    tf = request.args.get("tf", "4H")
    try:
        limit = int(request.args.get("limit", 200))
    except ValueError:
        limit = 200
    payload = markets_ohlc_json(market_id, tf, limit=limit)
    if payload.get("error"):
        return jsonify(payload), 404
    return jsonify(payload)


def register_markets_routes(app):
    app.register_blueprint(markets_udf_bp)
    app.register_blueprint(markets_api_bp)
    logger.info("Markets UDF + OHLC routes registered")
