"""
Dashboard routes for PX Solver API
Admin panel + API key management + usage tracking
"""

from flask import Blueprint, request, jsonify, send_from_directory
from functools import wraps
import os
import logging

from db import (
    generate_api_key, validate_api_key, list_api_keys,
    toggle_api_key, delete_api_key, update_api_key,
    log_request, get_overview_stats, get_key_stats
)

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "pxadmin2024")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token") or request.args.get("admin_token")
        if token != ADMIN_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/dashboard')
@admin_required
def dashboard_page():
    public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
    return send_from_directory(public_dir, 'dashboard.html')


@dashboard_bp.route('/api/keys', methods=['GET'])
@admin_required
def api_keys_list():
    return jsonify({"keys": list_api_keys()})


@dashboard_bp.route('/api/keys', methods=['POST'])
@admin_required
def api_keys_create():
    data = request.get_json() or {}
    result = generate_api_key(
        name=data.get("name", "Unnamed Key"),
        daily_limit=data.get("daily_limit", 1000),
        rate_limit=data.get("rate_limit", 100),
        expires_days=data.get("expires_days"),
        notes=data.get("notes", "")
    )
    return jsonify({"status": "created", **result}), 201


@dashboard_bp.route('/api/keys/<key_id>', methods=['PUT'])
@admin_required
def api_keys_update(key_id):
    update_api_key(key_id, **(request.get_json() or {}))
    return jsonify({"status": "updated"})


@dashboard_bp.route('/api/keys/<key_id>', methods=['DELETE'])
@admin_required
def api_keys_delete(key_id):
    delete_api_key(key_id)
    return jsonify({"status": "deleted"})


@dashboard_bp.route('/api/keys/<key_id>/toggle', methods=['POST'])
@admin_required
def api_keys_toggle(key_id):
    data = request.get_json() or {}
    active = data.get("active", True)
    toggle_api_key(key_id, active)
    return jsonify({"status": "toggled", "active": active})


@dashboard_bp.route('/api/keys/<key_id>/stats', methods=['GET'])
@admin_required
def api_keys_stats(key_id):
    return jsonify(get_key_stats(key_id))


@dashboard_bp.route('/api/stats', methods=['GET'])
@admin_required
def api_stats():
    return jsonify(get_overview_stats())
