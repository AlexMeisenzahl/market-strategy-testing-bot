"""
Complete database schema migration

This migration creates all tables required for the trading bot system:
- crypto_price_history: Historical cryptocurrency prices
- user_settings: User preferences and configuration
- notification_channels: Communication channels for alerts
- notification_preferences: Per-notification type settings
- workspaces: User workspace management
- favorites: Favorited strategies/markets
- audit_log: System audit trail

Revision ID: 001
Revises:
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create all tables with indexes and constraints.
    """

    # Crypto Price History Table
    op.create_table(
        "crypto_price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("price_usd", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, default="binance"),
        sa.Column("volume_24h", sa.Float(), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes for crypto_price_history
    op.create_index(
        "idx_crypto_symbol_timestamp", "crypto_price_history", ["symbol", "timestamp"]
    )
    op.create_index("idx_crypto_timestamp", "crypto_price_history", ["timestamp"])
    op.create_index("idx_crypto_symbol", "crypto_price_history", ["symbol"])

    # User Settings Table
    op.create_table(
        "user_settings",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("theme", sa.String(20), nullable=False, default="dark"),
        sa.Column("timezone", sa.String(50), nullable=False, default="UTC"),
        sa.Column("currency", sa.String(10), nullable=False, default="USD"),
        sa.Column("date_format", sa.String(20), nullable=False, default="YYYY-MM-DD"),
        sa.Column("time_format", sa.String(10), nullable=False, default="24h"),
        sa.Column("trading_mode", sa.String(20), nullable=False, default="paper"),
        sa.Column("require_confirmation", sa.Boolean(), nullable=False, default=True),
        sa.Column("default_timeframe", sa.String(10), nullable=False, default="24h"),
        sa.Column("auto_refresh_interval", sa.Integer(), nullable=False, default=30),
        sa.Column("show_notifications", sa.Boolean(), nullable=False, default=True),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("notification_sound", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Notification Channels Table
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, default=1),
        sa.Column("channel_type", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("api_key", sa.String(200), nullable=True),
        sa.Column("email_address", sa.String(200), nullable=True),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_settings.user_id"], ondelete="CASCADE"
        ),
    )

    # Create index for notification_channels
    op.create_index(
        "idx_notif_channel_user", "notification_channels", ["user_id", "channel_type"]
    )

    # Notification Preferences Table
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, default=1),
        sa.Column("notification_type", sa.String(100), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("min_profit_threshold", sa.Float(), nullable=True),
        sa.Column("min_confidence", sa.String(20), nullable=True),
        sa.Column("strategies", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_settings.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"], ["notification_channels.id"], ondelete="SET NULL"
        ),
    )

    # Create index for notification_preferences
    op.create_index(
        "idx_notif_pref_user_type",
        "notification_preferences",
        ["user_id", "notification_type"],
    )

    # Workspaces Table
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, default=1),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("layout_config", sa.Text(), nullable=True),
        sa.Column("strategies_config", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_settings.user_id"], ondelete="CASCADE"
        ),
    )

    # Create index for workspaces
    op.create_index("idx_workspace_user", "workspaces", ["user_id"])

    # Favorites Table
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, default=1),
        sa.Column("item_type", sa.String(50), nullable=False),
        sa.Column("item_id", sa.String(200), nullable=False),
        sa.Column("item_name", sa.String(200), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_settings.user_id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for favorites
    op.create_index("idx_favorites_user", "favorites", ["user_id"])
    op.create_index("idx_favorites_user_type", "favorites", ["user_id", "item_type"])

    # Audit Log Table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, default=1),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user_settings.user_id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for audit_log
    op.create_index("idx_audit_user", "audit_log", ["user_id"])
    op.create_index("idx_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("idx_audit_action", "audit_log", ["action"])
    op.create_index("idx_audit_entity", "audit_log", ["entity_type", "entity_id"])


def downgrade():
    """
    Drop all tables in reverse order.
    """
    op.drop_table("audit_log")
    op.drop_table("favorites")
    op.drop_table("workspaces")
    op.drop_table("notification_preferences")
    op.drop_table("notification_channels")
    op.drop_table("user_settings")
    op.drop_table("crypto_price_history")
