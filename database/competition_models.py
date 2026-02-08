"""
Database Models for Strategy Competition System

SQLite-based models for strategy performance snapshots, competition tracking,
and strategy configurations.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from decimal import Decimal
import threading

# Database file location
DB_FILE = Path(__file__).parent.parent / "data" / "competition.db"

# Thread-local storage for connections
_thread_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get thread-local database connection."""
    if not hasattr(_thread_local, "connection"):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        _thread_local.connection = sqlite3.connect(str(DB_FILE))
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection


def init_competition_db():
    """Initialize competition database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Strategies table - extended with new fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            strategy_type TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            trading_stage TEXT DEFAULT 'paper',
            allocated_capital REAL DEFAULT 10000.0,
            auto_disabled INTEGER DEFAULT 0,
            disable_reason TEXT,
            emergency_disabled INTEGER DEFAULT 0,
            paused INTEGER DEFAULT 0,
            pause_reason TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Strategy Performance Snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_performance_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            
            portfolio_value REAL NOT NULL,
            total_return_pct REAL,
            daily_pnl REAL,
            
            sharpe_ratio REAL,
            sortino_ratio REAL,
            max_drawdown REAL,
            volatility REAL,
            
            total_trades INTEGER DEFAULT 0,
            win_rate REAL,
            avg_trade_profit REAL,
            
            open_positions INTEGER DEFAULT 0,
            total_exposure REAL,
            
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            
            FOREIGN KEY (strategy_id) REFERENCES strategies(id)
        )
    """)

    # Create indexes for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_strategy_timestamp 
        ON strategy_performance_snapshots(strategy_id, timestamp DESC)
    """)

    # Config table for global settings (kill switch, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Initialize kill switch to false
    cursor.execute("""
        INSERT OR IGNORE INTO config (key, value) VALUES ('kill_switch_active', 'false')
    """)

    # Initialize default strategies if they don't exist
    default_strategies = [
        ('Polymarket Arbitrage', 'arbitrage'),
        ('Crypto Momentum', 'momentum'),
        ('Mean Reversion', 'mean_reversion'),
        ('Market Sentiment', 'sentiment'),
        ('Volume Surge', 'volume'),
        ('Time-Based', 'time_based'),
    ]
    
    for name, strategy_type in default_strategies:
        cursor.execute("""
            INSERT OR IGNORE INTO strategies (name, strategy_type, allocated_capital)
            VALUES (?, ?, 10000.0)
        """, (name, strategy_type))

    conn.commit()


class Strategy:
    """Model for strategy configurations"""

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all strategies"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strategies ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_enabled() -> List[Dict]:
        """Get enabled strategies"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM strategies 
            WHERE enabled = 1 
              AND auto_disabled = 0 
              AND emergency_disabled = 0
              AND paused = 0
            ORDER BY id
        """)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(strategy_id: int) -> Optional[Dict]:
        """Get strategy by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_name(name: str) -> Optional[Dict]:
        """Get strategy by name"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strategies WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(strategy_id: int, **kwargs):
        """Update strategy fields"""
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        allowed_fields = [
            'enabled', 'trading_stage', 'allocated_capital', 'auto_disabled',
            'disable_reason', 'emergency_disabled', 'paused', 'pause_reason'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if updates:
            updates.append("updated_at = strftime('%s', 'now')")
            params.append(strategy_id)
            
            query = f"UPDATE strategies SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()


class StrategyPerformanceSnapshot:
    """Model for hourly snapshots of strategy performance"""

    @staticmethod
    def create(
        strategy_id: int,
        portfolio_value: float,
        total_return_pct: float = None,
        daily_pnl: float = None,
        sharpe_ratio: float = None,
        sortino_ratio: float = None,
        max_drawdown: float = None,
        volatility: float = None,
        total_trades: int = 0,
        win_rate: float = None,
        avg_trade_profit: float = None,
        open_positions: int = 0,
        total_exposure: float = None,
        timestamp: int = None,
    ) -> int:
        """Create performance snapshot"""
        conn = get_connection()
        cursor = conn.cursor()

        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())

        cursor.execute("""
            INSERT INTO strategy_performance_snapshots (
                strategy_id, timestamp, portfolio_value, total_return_pct,
                daily_pnl, sharpe_ratio, sortino_ratio, max_drawdown,
                volatility, total_trades, win_rate, avg_trade_profit,
                open_positions, total_exposure
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            strategy_id, timestamp, portfolio_value, total_return_pct,
            daily_pnl, sharpe_ratio, sortino_ratio, max_drawdown,
            volatility, total_trades, win_rate, avg_trade_profit,
            open_positions, total_exposure
        ))

        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def get_latest(strategy_id: int) -> Optional[Dict]:
        """Get latest snapshot for strategy"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM strategy_performance_snapshots
            WHERE strategy_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (strategy_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_history(strategy_id: int, hours: int = 24) -> List[Dict]:
        """Get performance history for strategy"""
        conn = get_connection()
        cursor = conn.cursor()
        
        start_timestamp = int(datetime.utcnow().timestamp()) - (hours * 3600)
        
        cursor.execute("""
            SELECT * FROM strategy_performance_snapshots
            WHERE strategy_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (strategy_id, start_timestamp))
        
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all_latest() -> List[Dict]:
        """Get latest snapshot for all strategies"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s1.* 
            FROM strategy_performance_snapshots s1
            INNER JOIN (
                SELECT strategy_id, MAX(timestamp) as max_timestamp
                FROM strategy_performance_snapshots
                GROUP BY strategy_id
            ) s2 ON s1.strategy_id = s2.strategy_id 
                AND s1.timestamp = s2.max_timestamp
        """)
        
        return [dict(row) for row in cursor.fetchall()]


class Config:
    """Model for global configuration"""

    @staticmethod
    def get(key: str) -> Optional[str]:
        """Get config value"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None

    @staticmethod
    def set(key: str, value: str):
        """Set config value"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, strftime('%s', 'now'))
        """, (key, value))
        conn.commit()

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get boolean config value"""
        value = Config.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes')

    @staticmethod
    def set_bool(key: str, value: bool):
        """Set boolean config value"""
        Config.set(key, 'true' if value else 'false')


# Initialize database on module import
init_competition_db()
