"""
Database Models for Settings and Notifications

SQLite-based models for user settings, notification channels, and preferences.
Uses SQLite as a simple, file-based database solution.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading


# Database file location
DB_FILE = Path(__file__).parent.parent / 'data' / 'settings.db'

# Thread-local storage for connections
_thread_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get thread-local database connection."""
    if not hasattr(_thread_local, 'connection'):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        _thread_local.connection = sqlite3.connect(str(DB_FILE))
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # UserSettings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'dark',
            timezone TEXT DEFAULT 'UTC',
            currency TEXT DEFAULT 'USD',
            date_format TEXT DEFAULT 'YYYY-MM-DD',
            time_format TEXT DEFAULT '24h',
            trading_mode TEXT DEFAULT 'paper',
            require_confirmation INTEGER DEFAULT 1,
            default_timeframe TEXT DEFAULT '24h',
            auto_refresh_interval INTEGER DEFAULT 30,
            show_notifications INTEGER DEFAULT 1,
            notifications_enabled INTEGER DEFAULT 1,
            notification_sound INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # NotificationChannel table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            channel_type TEXT NOT NULL,
            enabled INTEGER DEFAULT 0,
            webhook_url TEXT,
            api_key TEXT,
            email_address TEXT,
            phone_number TEXT,
            config_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_settings(user_id)
        )
    ''')
    
    # NotificationPreference table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            notification_type TEXT NOT NULL,
            channel_id INTEGER,
            enabled INTEGER DEFAULT 1,
            min_profit_threshold REAL,
            min_confidence TEXT,
            strategies TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_settings(user_id),
            FOREIGN KEY (channel_id) REFERENCES notification_channels(id)
        )
    ''')
    
    conn.commit()
    
    # Create default user settings if not exists
    cursor.execute('SELECT COUNT(*) FROM user_settings WHERE user_id = 1')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO user_settings (user_id) VALUES (1)
        ''')
        conn.commit()


class UserSettings:
    """User settings model"""
    
    @staticmethod
    def get(user_id: int = 1) -> Dict[str, Any]:
        """
        Get user settings.
        
        Args:
            user_id: User ID (default: 1)
            
        Returns:
            Dictionary of settings
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Return defaults if not found
        return {
            'user_id': user_id,
            'theme': 'dark',
            'timezone': 'UTC',
            'currency': 'USD',
            'date_format': 'YYYY-MM-DD',
            'time_format': '24h',
            'trading_mode': 'paper',
            'require_confirmation': 1,
            'default_timeframe': '24h',
            'auto_refresh_interval': 30,
            'show_notifications': 1,
            'notifications_enabled': 1,
            'notification_sound': 1
        }
    
    @staticmethod
    def update(user_id: int, settings: Dict[str, Any]) -> bool:
        """
        Update user settings.
        
        Args:
            user_id: User ID
            settings: Dictionary of settings to update
            
        Returns:
            True if successful
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build update query
        set_clauses = []
        values = []
        
        for key, value in settings.items():
            if key not in ['user_id', 'created_at']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(user_id)
        
        query = f"UPDATE user_settings SET {', '.join(set_clauses)} WHERE user_id = ?"
        cursor.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0
    
    @staticmethod
    def reset(user_id: int = 1):
        """
        Reset user settings to defaults.
        
        Args:
            user_id: User ID
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_settings WHERE user_id = ?', (user_id,))
        cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))
        conn.commit()


class NotificationChannel:
    """Notification channel model"""
    
    @staticmethod
    def get_all(user_id: int = 1) -> List[Dict[str, Any]]:
        """
        Get all notification channels for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of channel dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notification_channels WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        
        channels = []
        for row in rows:
            channel = dict(row)
            # Parse config_json if present
            if channel.get('config_json'):
                try:
                    channel['config'] = json.loads(channel['config_json'])
                except:
                    channel['config'] = {}
            channels.append(channel)
        
        return channels
    
    @staticmethod
    def get(channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific notification channel.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Channel dictionary or None
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notification_channels WHERE id = ?', (channel_id,))
        row = cursor.fetchone()
        
        if row:
            channel = dict(row)
            if channel.get('config_json'):
                try:
                    channel['config'] = json.loads(channel['config_json'])
                except:
                    channel['config'] = {}
            return channel
        
        return None
    
    @staticmethod
    def get_by_type(channel_type: str, user_id: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get channel by type.
        
        Args:
            channel_type: Type of channel
            user_id: User ID
            
        Returns:
            Channel dictionary or None
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM notification_channels WHERE user_id = ? AND channel_type = ?',
            (user_id, channel_type)
        )
        row = cursor.fetchone()
        
        if row:
            channel = dict(row)
            if channel.get('config_json'):
                try:
                    channel['config'] = json.loads(channel['config_json'])
                except:
                    channel['config'] = {}
            return channel
        
        return None
    
    @staticmethod
    def create_or_update(user_id: int, channel_type: str, data: Dict[str, Any]) -> int:
        """
        Create or update a notification channel.
        
        Args:
            user_id: User ID
            channel_type: Type of channel
            data: Channel data
            
        Returns:
            Channel ID
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if channel exists
        cursor.execute(
            'SELECT id FROM notification_channels WHERE user_id = ? AND channel_type = ?',
            (user_id, channel_type)
        )
        row = cursor.fetchone()
        
        # Prepare config_json
        config = data.get('config', {})
        config_json = json.dumps(config) if config else None
        
        now = datetime.now().isoformat()
        
        if row:
            # Update existing
            channel_id = row['id']
            cursor.execute('''
                UPDATE notification_channels
                SET enabled = ?, webhook_url = ?, api_key = ?, email_address = ?,
                    phone_number = ?, config_json = ?, updated_at = ?
                WHERE id = ?
            ''', (
                data.get('enabled', 0),
                data.get('webhook_url'),
                data.get('api_key'),
                data.get('email_address'),
                data.get('phone_number'),
                config_json,
                now,
                channel_id
            ))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO notification_channels
                (user_id, channel_type, enabled, webhook_url, api_key, email_address,
                 phone_number, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                channel_type,
                data.get('enabled', 0),
                data.get('webhook_url'),
                data.get('api_key'),
                data.get('email_address'),
                data.get('phone_number'),
                config_json,
                now,
                now
            ))
            channel_id = cursor.lastrowid
        
        conn.commit()
        return channel_id
    
    @staticmethod
    def delete(channel_id: int):
        """
        Delete a notification channel.
        
        Args:
            channel_id: Channel ID
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notification_channels WHERE id = ?', (channel_id,))
        conn.commit()


class NotificationPreference:
    """Notification preference model"""
    
    @staticmethod
    def get_all(user_id: int = 1) -> List[Dict[str, Any]]:
        """
        Get all notification preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of preference dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notification_preferences WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_for_type(notification_type: str, user_id: int = 1) -> List[Dict[str, Any]]:
        """
        Get preferences for a specific notification type.
        
        Args:
            notification_type: Type of notification
            user_id: User ID
            
        Returns:
            List of preference dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM notification_preferences WHERE user_id = ? AND notification_type = ?',
            (user_id, notification_type)
        )
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    @staticmethod
    def create_or_update(user_id: int, notification_type: str, channel_id: Optional[int], data: Dict[str, Any]) -> int:
        """
        Create or update a notification preference.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            channel_id: Channel ID (optional)
            data: Preference data
            
        Returns:
            Preference ID
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if preference exists
        if channel_id:
            cursor.execute(
                'SELECT id FROM notification_preferences WHERE user_id = ? AND notification_type = ? AND channel_id = ?',
                (user_id, notification_type, channel_id)
            )
        else:
            cursor.execute(
                'SELECT id FROM notification_preferences WHERE user_id = ? AND notification_type = ? AND channel_id IS NULL',
                (user_id, notification_type)
            )
        
        row = cursor.fetchone()
        now = datetime.now().isoformat()
        
        if row:
            # Update existing
            pref_id = row['id']
            cursor.execute('''
                UPDATE notification_preferences
                SET enabled = ?, min_profit_threshold = ?, min_confidence = ?,
                    strategies = ?, updated_at = ?
                WHERE id = ?
            ''', (
                data.get('enabled', 1),
                data.get('min_profit_threshold'),
                data.get('min_confidence'),
                data.get('strategies'),
                now,
                pref_id
            ))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO notification_preferences
                (user_id, notification_type, channel_id, enabled, min_profit_threshold,
                 min_confidence, strategies, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                notification_type,
                channel_id,
                data.get('enabled', 1),
                data.get('min_profit_threshold'),
                data.get('min_confidence'),
                data.get('strategies'),
                now,
                now
            ))
            pref_id = cursor.lastrowid
        
        conn.commit()
        return pref_id
    
    @staticmethod
    def delete(pref_id: int):
        """
        Delete a notification preference.
        
        Args:
            pref_id: Preference ID
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notification_preferences WHERE id = ?', (pref_id,))
        conn.commit()
    
    @staticmethod
    def bulk_update(user_id: int, preferences: List[Dict[str, Any]]):
        """
        Bulk update notification preferences.
        
        Args:
            user_id: User ID
            preferences: List of preference dictionaries
        """
        for pref in preferences:
            NotificationPreference.create_or_update(
                user_id,
                pref['notification_type'],
                pref.get('channel_id'),
                pref
            )
