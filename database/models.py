"""
Database Models for Trading Bot

SQLite-based models for price history, trade journal, and alerts.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading

# Database file location
DB_FILE = Path(__file__).parent.parent / "data" / "trading.db"

# Thread-local storage for connections
_thread_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get thread-local database connection."""
    if not hasattr(_thread_local, "connection"):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        _thread_local.connection = sqlite3.connect(str(DB_FILE))
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection


def init_trading_db():
    """Initialize trading database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # CryptoPriceHistory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crypto_price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price_usd REAL NOT NULL,
            volume REAL,
            market_cap REAL,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Create index for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_crypto_symbol_timestamp 
        ON crypto_price_history(symbol, timestamp)
    """)

    # PolymarketHistory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polymarket_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id TEXT NOT NULL,
            yes_price REAL NOT NULL,
            no_price REAL NOT NULL,
            volume REAL,
            liquidity REAL,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Create index for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_polymarket_id_timestamp 
        ON polymarket_history(market_id, timestamp)
    """)

    # TradeJournal table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT,
            position_id TEXT,
            entry_reason TEXT,
            confidence_level INTEGER,
            exit_reason TEXT,
            lessons_learned TEXT,
            rating INTEGER,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Alert table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            condition_json TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            last_triggered INTEGER,
            trigger_count INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Position extensions for stop-loss/take-profit
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS position_config (
            position_id TEXT PRIMARY KEY,
            stop_loss_pct REAL DEFAULT -5.0,
            take_profit_pct REAL DEFAULT 10.0,
            max_hold_hours INTEGER DEFAULT 24,
            trailing_stop REAL,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # API Keys (encrypted)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT NOT NULL UNIQUE,
            api_key_encrypted TEXT,
            api_secret_encrypted TEXT,
            passphrase_encrypted TEXT,
            is_connected INTEGER DEFAULT 0,
            last_tested INTEGER,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    conn.commit()


class CryptoPriceHistory:
    """Model for cryptocurrency price history"""

    @staticmethod
    def insert(symbol: str, price_usd: float, volume: float = None, 
               market_cap: float = None, timestamp: int = None) -> int:
        """Insert price history record"""
        conn = get_connection()
        cursor = conn.cursor()
        
        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())
        
        cursor.execute("""
            INSERT INTO crypto_price_history (symbol, price_usd, volume, market_cap, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, price_usd, volume, market_cap, timestamp))
        
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def get_history(symbol: str, start_timestamp: int = None, 
                   end_timestamp: int = None) -> List[Dict]:
        """Get price history for a symbol"""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM crypto_price_history WHERE symbol = ?"
        params = [symbol]
        
        if start_timestamp:
            query += " AND timestamp >= ?"
            params.append(start_timestamp)
        
        if end_timestamp:
            query += " AND timestamp <= ?"
            params.append(end_timestamp)
        
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_latest(symbol: str) -> Optional[Dict]:
        """Get latest price for a symbol"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM crypto_price_history 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol,))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def bulk_insert(records: List[Dict]) -> int:
        """Bulk insert price history records"""
        conn = get_connection()
        cursor = conn.cursor()
        
        data = [
            (r['symbol'], r['price_usd'], r.get('volume'), 
             r.get('market_cap'), r.get('timestamp', int(datetime.utcnow().timestamp())))
            for r in records
        ]
        
        cursor.executemany("""
            INSERT INTO crypto_price_history (symbol, price_usd, volume, market_cap, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        
        conn.commit()
        return cursor.rowcount


class PolymarketHistory:
    """Model for Polymarket price history"""

    @staticmethod
    def insert(market_id: str, yes_price: float, no_price: float,
               volume: float = None, liquidity: float = None, 
               timestamp: int = None) -> int:
        """Insert Polymarket history record"""
        conn = get_connection()
        cursor = conn.cursor()
        
        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())
        
        cursor.execute("""
            INSERT INTO polymarket_history (market_id, yes_price, no_price, volume, liquidity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (market_id, yes_price, no_price, volume, liquidity, timestamp))
        
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def get_history(market_id: str, start_timestamp: int = None,
                   end_timestamp: int = None) -> List[Dict]:
        """Get price history for a market"""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM polymarket_history WHERE market_id = ?"
        params = [market_id]
        
        if start_timestamp:
            query += " AND timestamp >= ?"
            params.append(start_timestamp)
        
        if end_timestamp:
            query += " AND timestamp <= ?"
            params.append(end_timestamp)
        
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


class TradeJournal:
    """Model for trade journal entries"""

    @staticmethod
    def create(trade_id: str = None, position_id: str = None,
               entry_reason: str = None, confidence_level: int = None) -> int:
        """Create journal entry"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trade_journal (trade_id, position_id, entry_reason, confidence_level)
            VALUES (?, ?, ?, ?)
        """, (trade_id, position_id, entry_reason, confidence_level))
        
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def update(journal_id: int, exit_reason: str = None,
               lessons_learned: str = None, rating: int = None):
        """Update journal entry"""
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if exit_reason is not None:
            updates.append("exit_reason = ?")
            params.append(exit_reason)
        
        if lessons_learned is not None:
            updates.append("lessons_learned = ?")
            params.append(lessons_learned)
        
        if rating is not None:
            updates.append("rating = ?")
            params.append(rating)
        
        if updates:
            updates.append("updated_at = strftime('%s', 'now')")
            params.append(journal_id)
            
            query = f"UPDATE trade_journal SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all journal entries"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM trade_journal ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(journal_id: int) -> Optional[Dict]:
        """Get journal entry by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM trade_journal WHERE id = ?", (journal_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


class Alert:
    """Model for custom alerts"""

    @staticmethod
    def create(alert_type: str, condition_json: str, enabled: bool = True) -> int:
        """Create alert"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts (alert_type, condition_json, enabled)
            VALUES (?, ?, ?)
        """, (alert_type, condition_json, 1 if enabled else 0))
        
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def update(alert_id: int, enabled: bool = None, condition_json: str = None):
        """Update alert"""
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        if condition_json is not None:
            updates.append("condition_json = ?")
            params.append(condition_json)
        
        if updates:
            updates.append("updated_at = strftime('%s', 'now')")
            params.append(alert_id)
            
            query = f"UPDATE alerts SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

    @staticmethod
    def record_trigger(alert_id: int):
        """Record alert trigger"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alerts 
            SET last_triggered = strftime('%s', 'now'),
                trigger_count = trigger_count + 1
            WHERE id = ?
        """, (alert_id,))
        
        conn.commit()

    @staticmethod
    def get_enabled() -> List[Dict]:
        """Get all enabled alerts"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM alerts WHERE enabled = 1")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all alerts"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete(alert_id: int):
        """Delete alert"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()


class PositionConfig:
    """Model for position-specific configurations"""

    @staticmethod
    def set_config(position_id: str, stop_loss_pct: float = -5.0,
                  take_profit_pct: float = 10.0, max_hold_hours: int = 24,
                  trailing_stop: float = None):
        """Set or update position config"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO position_config 
            (position_id, stop_loss_pct, take_profit_pct, max_hold_hours, trailing_stop, updated_at)
            VALUES (?, ?, ?, ?, ?, strftime('%s', 'now'))
        """, (position_id, stop_loss_pct, take_profit_pct, max_hold_hours, trailing_stop))
        
        conn.commit()

    @staticmethod
    def get_config(position_id: str) -> Optional[Dict]:
        """Get position config"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM position_config WHERE position_id = ?", (position_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


class APIKey:
    """Model for encrypted API keys"""

    @staticmethod
    def save_key(exchange: str, api_key_encrypted: str, 
                api_secret_encrypted: str, passphrase_encrypted: str = None):
        """Save encrypted API key"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO api_keys 
            (exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted, updated_at)
            VALUES (?, ?, ?, ?, strftime('%s', 'now'))
        """, (exchange, api_key_encrypted, api_secret_encrypted, passphrase_encrypted))
        
        conn.commit()

    @staticmethod
    def get_key(exchange: str) -> Optional[Dict]:
        """Get encrypted API key"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM api_keys WHERE exchange = ?", (exchange,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_connection_status(exchange: str, is_connected: bool):
        """Update connection status"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE api_keys 
            SET is_connected = ?, 
                last_tested = strftime('%s', 'now')
            WHERE exchange = ?
        """, (1 if is_connected else 0, exchange))
        
        conn.commit()

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all API keys"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM api_keys")
        return [dict(row) for row in cursor.fetchall()]


# Initialize database on module import
init_trading_db()
