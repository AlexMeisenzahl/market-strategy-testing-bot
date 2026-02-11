"""
SQLite store for trades and opportunities.

Replaces unbounded CSV growth for 6+ month unattended runtime.
Single DB file in logs dir; bounded row counts; dashboard reads last N only.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# Bounded row counts for unattended runtime
TRADES_MAX_ROWS = 500_000
OPPORTUNITIES_MAX_ROWS = 500_000

DB_FILENAME = "trades.db"


def _get_db_path(log_dir: Path) -> Path:
    return Path(log_dir) / DB_FILENAME


def init_db(log_dir: Path) -> Path:
    """Ensure DB and tables exist. Returns path to DB file."""
    path = _get_db_path(log_dir)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                market TEXT NOT NULL,
                yes_price REAL,
                no_price REAL,
                sum_price REAL,
                profit_pct REAL,
                profit_usd REAL,
                status TEXT,
                strategy TEXT,
                arbitrage_type TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                market TEXT NOT NULL,
                yes_price REAL,
                no_price REAL,
                sum_price REAL,
                profit_pct REAL,
                action_taken TEXT,
                strategy TEXT,
                arbitrage_type TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_ts ON trades(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_ts ON opportunities(timestamp)")
        conn.commit()
    finally:
        conn.close()
    return path


def _prune_trades(conn: sqlite3.Connection) -> None:
    """Keep only the last TRADES_MAX_ROWS rows."""
    row = conn.execute(
        "SELECT id FROM (SELECT id FROM trades ORDER BY id DESC LIMIT ?) AS t ORDER BY id ASC LIMIT 1",
        (TRADES_MAX_ROWS,),
    ).fetchone()
    if row:
        conn.execute("DELETE FROM trades WHERE id < ?", (row[0],))
    conn.commit()


def _prune_opportunities(conn: sqlite3.Connection) -> None:
    """Keep only the last OPPORTUNITIES_MAX_ROWS rows."""
    row = conn.execute(
        "SELECT id FROM (SELECT id FROM opportunities ORDER BY id DESC LIMIT ?) AS t ORDER BY id ASC LIMIT 1",
        (OPPORTUNITIES_MAX_ROWS,),
    ).fetchone()
    if row:
        conn.execute("DELETE FROM opportunities WHERE id < ?", (row[0],))
    conn.commit()


def insert_trade(
    log_dir: Path,
    timestamp: str,
    market: str,
    yes_price: float,
    no_price: float,
    profit_pct: float,
    profit_usd: float,
    status: str = "executed",
    strategy: str = "Unknown",
    arbitrage_type: str = "Unknown",
) -> None:
    """Append one trade row. Prunes old rows if over cap."""
    path = _get_db_path(log_dir)
    if not path.exists():
        init_db(log_dir)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            INSERT INTO trades (timestamp, market, yes_price, no_price, sum_price, profit_pct, profit_usd, status, strategy, arbitrage_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                market,
                yes_price,
                no_price,
                yes_price + no_price,
                profit_pct,
                profit_usd,
                status,
                strategy,
                arbitrage_type,
            ),
        )
        conn.commit()
        cur = conn.execute("SELECT COUNT(*) FROM trades")
        if cur.fetchone()[0] > TRADES_MAX_ROWS:
            _prune_trades(conn)
    finally:
        conn.close()


def insert_opportunity(
    log_dir: Path,
    timestamp: str,
    market: str,
    yes_price: float,
    no_price: float,
    profit_pct: float,
    action_taken: str,
    strategy: str = "Unknown",
    arbitrage_type: str = "Unknown",
) -> None:
    """Append one opportunity row. Prunes old rows if over cap."""
    path = _get_db_path(log_dir)
    if not path.exists():
        init_db(log_dir)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            INSERT INTO opportunities (timestamp, market, yes_price, no_price, sum_price, profit_pct, action_taken, strategy, arbitrage_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                market,
                yes_price,
                no_price,
                yes_price + no_price,
                profit_pct,
                action_taken,
                strategy,
                arbitrage_type,
            ),
        )
        conn.commit()
        cur = conn.execute("SELECT COUNT(*) FROM opportunities")
        if cur.fetchone()[0] > OPPORTUNITIES_MAX_ROWS:
            _prune_opportunities(conn)
    finally:
        conn.close()


def get_trades(
    log_dir: Path,
    limit: int = 50_000,
    offset: int = 0,
    year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return trades, newest first. If year is set, filter by timestamp year (no limit)."""
    path = _get_db_path(log_dir)
    if not path.exists():
        return []
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        if year is not None:
            # Tax/export: all trades for year
            rows = conn.execute(
                """
                SELECT id, timestamp, market, yes_price, no_price, sum_price, profit_pct, profit_usd, status, strategy, arbitrage_type
                FROM trades
                WHERE strftime('%Y', timestamp) = ?
                ORDER BY id ASC
                """,
                (str(year),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, timestamp, market, yes_price, no_price, sum_price, profit_pct, profit_usd, status, strategy, arbitrage_type
                FROM trades
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [_row_to_trade_dict(r) for r in rows]
    finally:
        conn.close()


def _row_to_trade_dict(r: sqlite3.Row) -> Dict[str, Any]:
    """Map DB row to data_parser-style trade dict."""
    return {
        "id": r["id"],
        "symbol": r["market"] or "",
        "strategy": r["strategy"] or "Unknown",
        "arbitrage_type": r["arbitrage_type"] if "arbitrage_type" in r.keys() else "Unknown",
        "timestamp": r["timestamp"] or "",
        "entry_time": r["timestamp"],
        "exit_time": r["timestamp"],
        "duration_minutes": 0,
        "entry_price": float(r["yes_price"] or 0),
        "exit_price": float(r["no_price"] or 0),
        "pnl_usd": float(r["profit_usd"] or 0),
        "pnl_pct": float(r["profit_pct"] or 0),
        "status": r["status"] or "closed",
        "outcome": "win" if (float(r["profit_usd"] or 0) > 0) else ("loss" if (float(r["profit_usd"] or 0) < 0) else "breakeven"),
    }


def get_opportunities(
    log_dir: Path,
    limit: int = 50_000,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Return opportunities, newest first."""
    path = _get_db_path(log_dir)
    if not path.exists():
        return []
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, timestamp, market, yes_price, no_price, profit_pct, action_taken, strategy, arbitrage_type
            FROM opportunities
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [_row_to_opportunity_dict(r) for r in rows]
    finally:
        conn.close()


def _row_to_opportunity_dict(r: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": r["id"],
        "timestamp": r["timestamp"] or "",
        "symbol": r["market"] or "",
        "strategy": r["strategy"] or "",
        "signal_type": "BUY",
        "confidence": 0,
        "action_taken": (r["action_taken"] or "").lower() in ("true", "1", "traded", "yes"),
        "outcome": None,
        "pnl_usd": None,
    }


def migrate_csv_to_db(log_dir: Path) -> int:
    """If trades.csv exists and DB has no trades, backfill from CSV. Returns number of trades imported."""
    path = _get_db_path(log_dir)
    csv_path = Path(log_dir) / "trades.csv"
    if not csv_path.exists():
        return 0
    init_db(log_dir)
    conn = sqlite3.connect(str(path))
    try:
        n = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        if n > 0:
            return 0
        count = 0
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = row.get("timestamp", "")
                    market = row.get("market", "")
                    y = float(row.get("yes_price", 0) or 0)
                    no = float(row.get("no_price", 0) or 0)
                    pct = float(row.get("profit_pct", 0) or 0)
                    usd = float(row.get("profit_usd", 0) or 0)
                    status = row.get("status", "executed")
                    strategy = row.get("strategy", "Unknown")
                    arb = row.get("arbitrage_type", "Unknown")
                    conn.execute(
                        "INSERT INTO trades (timestamp, market, yes_price, no_price, sum_price, profit_pct, profit_usd, status, strategy, arbitrage_type) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (ts, market, y, no, y + no, pct, usd, status, strategy, arb),
                    )
                    count += 1
                except (ValueError, KeyError):
                    continue
        conn.commit()
        if count > TRADES_MAX_ROWS:
            _prune_trades(conn)
        return count
    finally:
        conn.close()


def migrate_opportunities_csv_to_db(log_dir: Path) -> int:
    """If opportunities.csv exists and DB has no opportunities, backfill. Returns number imported."""
    path = _get_db_path(log_dir)
    csv_path = Path(log_dir) / "opportunities.csv"
    if not csv_path.exists():
        return 0
    init_db(log_dir)
    conn = sqlite3.connect(str(path))
    try:
        n = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        if n > 0:
            return 0
        count = 0
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = row.get("timestamp", "")
                    market = row.get("market", "")
                    y = float(row.get("yes_price", 0) or 0)
                    no = float(row.get("no_price", 0) or 0)
                    pct = float(row.get("profit_pct", 0) or 0)
                    action = row.get("action_taken", "")
                    strategy = row.get("strategy", "Unknown")
                    arb = row.get("arbitrage_type", "Unknown")
                    conn.execute(
                        "INSERT INTO opportunities (timestamp, market, yes_price, no_price, sum_price, profit_pct, action_taken, strategy, arbitrage_type) VALUES (?,?,?,?,?,?,?,?,?)",
                        (ts, market, y, no, y + no, pct, action, strategy, arb),
                    )
                    count += 1
                except (ValueError, KeyError):
                    continue
        conn.commit()
        if count > OPPORTUNITIES_MAX_ROWS:
            _prune_opportunities(conn)
        return count
    finally:
        conn.close()
