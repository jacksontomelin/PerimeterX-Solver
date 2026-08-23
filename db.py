"""
Database module for PX Solver API
SQLite-based tracking: API keys, requests, usage stats
"""

import sqlite3
import os
import uuid
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Tentar /app/data primeiro, fallback para diretório local
_default_db = "/app/data/px_solver.db"
try:
    os.makedirs("/app/data", exist_ok=True)
except Exception:
    _default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "px_solver.db")

DB_PATH = os.environ.get("PX_DB_PATH", _default_db)


def get_db():
    """Get database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            key_hash TEXT UNIQUE NOT NULL,
            key_prefix TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            rate_limit INTEGER NOT NULL DEFAULT 100,
            daily_limit INTEGER NOT NULL DEFAULT 1000,
            total_requests INTEGER NOT NULL DEFAULT 0,
            total_success INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            last_used_at TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            site TEXT,
            app_id TEXT,
            status TEXT NOT NULL,
            token_obtained INTEGER NOT NULL DEFAULT 0,
            response_time_ms INTEGER,
            error TEXT,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        );

        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT NOT NULL,
            api_key_id TEXT,
            total_requests INTEGER NOT NULL DEFAULT 0,
            total_success INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            avg_response_ms INTEGER,
            PRIMARY KEY (date, api_key_id),
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        );

        CREATE INDEX IF NOT EXISTS idx_requests_timestamp ON requests(timestamp);
        CREATE INDEX IF NOT EXISTS idx_requests_api_key ON requests(api_key_id);
        CREATE INDEX IF NOT EXISTS idx_requests_site ON requests(site);
        CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized")


# ============================================================
# API KEY MANAGEMENT
# ============================================================

def generate_api_key(name: str, daily_limit: int = 1000, rate_limit: int = 100,
                     expires_days: Optional[int] = None, notes: str = "") -> Dict[str, str]:
    """Generate a new API key"""
    key_id = str(uuid.uuid4())[:8]
    raw_key = f"pxs_{secrets.token_hex(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]
    
    expires_at = None
    if expires_days:
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    
    conn = get_db()
    conn.execute("""
        INSERT INTO api_keys (id, key_hash, key_prefix, name, expires_at, 
                              rate_limit, daily_limit, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (key_id, key_hash, key_prefix, name, expires_at, rate_limit, daily_limit, notes))
    conn.commit()
    conn.close()
    
    logger.info(f"API key created: {key_prefix}... for '{name}'")
    
    return {
        "id": key_id,
        "key": raw_key,
        "prefix": key_prefix,
        "name": name,
        "daily_limit": daily_limit,
        "rate_limit": rate_limit,
        "expires_at": expires_at,
    }


def validate_api_key(raw_key: str) -> Optional[Dict]:
    """Validate API key and return key info"""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1", (key_hash,)
    ).fetchone()
    
    if not row:
        conn.close()
        return None
    
    # Check expiration
    if row["expires_at"]:
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            conn.close()
            return None
    
    # Check daily limit
    today = datetime.now().strftime("%Y-%m-%d")
    daily = conn.execute(
        "SELECT total_requests FROM daily_stats WHERE date = ? AND api_key_id = ?",
        (today, row["id"])
    ).fetchone()
    
    daily_used = daily["total_requests"] if daily else 0
    
    if daily_used >= row["daily_limit"]:
        conn.close()
        return {"error": "daily_limit_exceeded", "limit": row["daily_limit"], "used": daily_used}
    
    # Update last_used
    conn.execute("UPDATE api_keys SET last_used_at = datetime('now') WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    
    return dict(row)


def list_api_keys() -> List[Dict]:
    """List all API keys"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM api_keys ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_api_key(key_id: str, active: bool) -> bool:
    """Enable/disable API key"""
    conn = get_db()
    conn.execute("UPDATE api_keys SET is_active = ? WHERE id = ?", (1 if active else 0, key_id))
    conn.commit()
    conn.close()
    return True


def delete_api_key(key_id: str) -> bool:
    """Delete API key"""
    conn = get_db()
    conn.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()
    return True


def update_api_key(key_id: str, **kwargs) -> bool:
    """Update API key fields"""
    allowed = {"name", "daily_limit", "rate_limit", "notes", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    
    sets = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [key_id]
    
    conn = get_db()
    conn.execute(f"UPDATE api_keys SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()
    return True


# ============================================================
# REQUEST TRACKING
# ============================================================

def log_request(api_key_id: Optional[str], site: str, app_id: Optional[str],
                status: str, token_obtained: bool, response_time_ms: int = 0,
                error: str = "", ip_address: str = "", user_agent: str = ""):
    """Log an API request"""
    conn = get_db()
    
    conn.execute("""
        INSERT INTO requests (api_key_id, site, app_id, status, token_obtained,
                              response_time_ms, error, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (api_key_id, site, app_id, status, 1 if token_obtained else 0,
          response_time_ms, error, ip_address, user_agent))
    
    # Update API key counters
    if api_key_id:
        conn.execute("""
            UPDATE api_keys SET 
                total_requests = total_requests + 1,
                total_success = total_success + CASE WHEN ? THEN 1 ELSE 0 END,
                total_tokens = total_tokens + CASE WHEN ? THEN 1 ELSE 0 END
            WHERE id = ?
        """, (status == "SUCCESS", token_obtained, api_key_id))
    
    # Update daily stats
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO daily_stats (date, api_key_id, total_requests, total_success, total_tokens, avg_response_ms)
        VALUES (?, ?, 1, ?, ?, ?)
        ON CONFLICT(date, api_key_id) DO UPDATE SET
            total_requests = total_requests + 1,
            total_success = total_success + excluded.total_success,
            total_tokens = total_tokens + excluded.total_tokens,
            avg_response_ms = (avg_response_ms + excluded.avg_response_ms) / 2
    """, (today, api_key_id or "__public__",
          1 if status == "SUCCESS" else 0,
          1 if token_obtained else 0,
          response_time_ms))
    
    conn.commit()
    conn.close()


# ============================================================
# STATISTICS
# ============================================================

def get_overview_stats() -> Dict:
    """Get overall stats for dashboard"""
    conn = get_db()
    
    total = conn.execute("SELECT COUNT(*) as c FROM requests").fetchone()["c"]
    success = conn.execute("SELECT COUNT(*) as c FROM requests WHERE status = 'SUCCESS'").fetchone()["c"]
    tokens = conn.execute("SELECT COUNT(*) as c FROM requests WHERE token_obtained = 1").fetchone()["c"]
    active_keys = conn.execute("SELECT COUNT(*) as c FROM api_keys WHERE is_active = 1").fetchone()["c"]
    total_keys = conn.execute("SELECT COUNT(*) as c FROM api_keys").fetchone()["c"]
    
    # Today
    today = datetime.now().strftime("%Y-%m-%d")
    today_reqs = conn.execute(
        "SELECT COALESCE(SUM(total_requests),0) as c FROM daily_stats WHERE date = ?", (today,)
    ).fetchone()["c"]
    today_tokens = conn.execute(
        "SELECT COALESCE(SUM(total_tokens),0) as c FROM daily_stats WHERE date = ?", (today,)
    ).fetchone()["c"]
    
    # Last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_data = conn.execute("""
        SELECT date, SUM(total_requests) as reqs, SUM(total_success) as success, SUM(total_tokens) as tokens
        FROM daily_stats WHERE date >= ? GROUP BY date ORDER BY date
    """, (week_ago,)).fetchall()
    
    # Top sites
    top_sites = conn.execute("""
        SELECT site, COUNT(*) as total, SUM(token_obtained) as tokens
        FROM requests GROUP BY site ORDER BY total DESC LIMIT 10
    """).fetchall()
    
    # Recent requests
    recent = conn.execute("""
        SELECT r.*, k.name as key_name 
        FROM requests r LEFT JOIN api_keys k ON r.api_key_id = k.id
        ORDER BY r.timestamp DESC LIMIT 20
    """).fetchall()
    
    conn.close()
    
    return {
        "total_requests": total,
        "total_success": success,
        "total_tokens": tokens,
        "success_rate": round(success / total * 100, 1) if total > 0 else 0,
        "active_keys": active_keys,
        "total_keys": total_keys,
        "today_requests": today_reqs,
        "today_tokens": today_tokens,
        "weekly": [dict(r) for r in week_data],
        "top_sites": [dict(r) for r in top_sites],
        "recent_requests": [dict(r) for r in recent],
    }


def get_key_stats(key_id: str) -> Dict:
    """Get stats for a specific API key"""
    conn = get_db()
    
    key = conn.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,)).fetchone()
    if not key:
        conn.close()
        return {}
    
    # Daily usage last 30 days
    month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    daily = conn.execute("""
        SELECT date, total_requests, total_success, total_tokens
        FROM daily_stats WHERE api_key_id = ? AND date >= ? ORDER BY date
    """, (key_id, month_ago)).fetchall()
    
    # Per-site breakdown
    sites = conn.execute("""
        SELECT site, COUNT(*) as total, SUM(token_obtained) as tokens
        FROM requests WHERE api_key_id = ? GROUP BY site ORDER BY total DESC
    """, (key_id,)).fetchall()
    
    conn.close()
    
    return {
        "key": dict(key),
        "daily_usage": [dict(r) for r in daily],
        "site_breakdown": [dict(r) for r in sites],
    }


# Initialize on import
init_db()
