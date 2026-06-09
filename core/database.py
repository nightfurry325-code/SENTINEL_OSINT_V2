"""core/database.py — SQLite persistence layer"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, cfg):
        self.db_path = cfg.get("db_path")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS scans (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_type   TEXT NOT NULL,
                    target      TEXT NOT NULL,
                    found_count INTEGER DEFAULT 0,
                    results     TEXT,
                    created_at  TEXT DEFAULT (datetime('now','localtime'))
                );
                CREATE TABLE IF NOT EXISTS cache (
                    key         TEXT PRIMARY KEY,
                    value       TEXT,
                    expires_at  TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_scans_target ON scans(target);
                CREATE INDEX IF NOT EXISTS idx_scans_type   ON scans(scan_type);
            """)

    def save_scan(self, scan_type: str, target: str, results: dict) -> int:
        found = results.get("found_count", 0)
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO scans (scan_type, target, found_count, results) VALUES (?,?,?,?)",
                (scan_type, target, found, json.dumps(results))
            )
            return cur.lastrowid

    def get_scan_by_id(self, scan_id: int):
        with self._conn() as c:
            row = c.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
            return dict(row) if row else None

    def get_all_scans(self, limit=50):
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, scan_type, target, found_count, created_at FROM scans ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_cached(self, key: str):
        with self._conn() as c:
            row = c.execute(
                "SELECT value FROM cache WHERE key=? AND (expires_at IS NULL OR expires_at > datetime('now'))",
                (key,)
            ).fetchone()
            return json.loads(row["value"]) if row else None

    def set_cache(self, key: str, value, ttl_hours: int = 24):
        from datetime import timedelta
        expires = (datetime.now() + timedelta(hours=ttl_hours)).strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?,?,?)",
                (key, json.dumps(value), expires)
            )

    def delete_scan(self, scan_id: int):
        with self._conn() as c:
            c.execute("DELETE FROM scans WHERE id=?", (scan_id,))

    def clear_expired_cache(self):
        with self._conn() as c:
            c.execute("DELETE FROM cache WHERE expires_at < datetime('now')")
