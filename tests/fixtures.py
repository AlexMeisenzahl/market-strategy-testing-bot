"""
Test Fixtures for Market Strategy Testing Bot

Provides reusable test data generators using factory_boy.
"""

import factory
from factory import Faker, LazyAttribute
from datetime import datetime, timedelta
import random


class UserSettingsFactory(factory.Factory):
    """Factory for generating user settings test data."""
    
    class Meta:
        model = dict
    
    user_id = 1
    theme = factory.Iterator(['dark', 'light'])
    timezone = factory.Iterator(['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'])
    currency = 'USD'
    date_format = 'YYYY-MM-DD'
    time_format = factory.Iterator(['24h', '12h'])
    trading_mode = factory.Iterator(['paper', 'live'])
    require_confirmation = True
    default_timeframe = factory.Iterator(['1h', '4h', '24h', '7d'])
    auto_refresh_interval = factory.Faker('random_int', min=10, max=60)
    show_notifications = True
    notifications_enabled = True
    notification_sound = True


class NotificationChannelFactory(factory.Factory):
    """Factory for generating notification channel test data."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    user_id = 1
    channel_type = factory.Iterator(['discord', 'slack', 'email', 'telegram', 'webhook'])
    enabled = True
    webhook_url = factory.LazyAttribute(
        lambda obj: f"https://hooks.example.com/{obj.channel_type}/{factory.Faker('uuid4').generate({})}"
        if obj.channel_type in ['discord', 'slack', 'webhook'] else None
    )
    api_key = None
    email_address = factory.LazyAttribute(
        lambda obj: factory.Faker('email').generate({}) if obj.channel_type == 'email' else None
    )
    phone_number = None
    config_json = None


class TradeFactory(factory.Factory):
    """Factory for generating trade test data."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    timestamp = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    strategy = factory.Iterator([
        'Polymarket Arbitrage',
        'Crypto-Polymarket Arbitrage',
        'Cross-Exchange Arbitrage',
        'News-Based Trading',
        'Technical Analysis',
        'Sentiment Analysis'
    ])
    market = factory.Faker('sentence', nb_words=6)
    entry_price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    exit_price = factory.LazyAttribute(
        lambda obj: obj.entry_price * (1 + random.uniform(-0.1, 0.2))
    )
    quantity = factory.Faker('pydecimal', left_digits=2, right_digits=4, positive=True)
    pnl_usd = factory.LazyAttribute(
        lambda obj: float((obj.exit_price - obj.entry_price) * obj.quantity)
    )
    pnl_percentage = factory.LazyAttribute(
        lambda obj: ((obj.exit_price - obj.entry_price) / obj.entry_price) * 100
    )
    confidence = factory.Iterator(['low', 'medium', 'high', 'very_high'])
    status = factory.Iterator(['completed', 'pending', 'failed'])


class OpportunityFactory(factory.Factory):
    """Factory for generating opportunity test data."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    timestamp = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    strategy = factory.Iterator([
        'Polymarket Arbitrage',
        'Crypto-Polymarket Arbitrage',
        'Cross-Exchange Arbitrage'
    ])
    market = factory.Faker('sentence', nb_words=6)
    profit_usd = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    profit_percentage = factory.LazyAttribute(
        lambda obj: float(obj.profit_usd) * random.uniform(1.0, 5.0)
    )
    confidence = factory.Iterator(['low', 'medium', 'high', 'very_high'])
    expiry = factory.LazyAttribute(
        lambda obj: (datetime.fromisoformat(obj.timestamp) + timedelta(hours=random.randint(1, 48))).isoformat()
    )
    liquidity_usd = factory.Faker('pydecimal', left_digits=5, right_digits=0, positive=True)


class CryptoPriceFactory(factory.Factory):
    """Factory for generating crypto price test data."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    symbol = factory.Iterator(['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOT'])
    price_usd = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    timestamp = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    source = factory.Iterator(['binance', 'coingecko', 'coinbase'])
    volume_24h = factory.Faker('pydecimal', left_digits=10, right_digits=0, positive=True)
    market_cap = factory.Faker('pydecimal', left_digits=12, right_digits=0, positive=True)


class AuditLogFactory(factory.Factory):
    """Factory for generating audit log test data."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    user_id = 1
    action = factory.Iterator([
        'settings_updated',
        'strategy_enabled',
        'strategy_disabled',
        'notification_created',
        'notification_updated',
        'trading_mode_changed'
    ])
    entity_type = factory.Iterator([
        'user_settings',
        'strategy',
        'notification_channel',
        'system_config'
    ])
    entity_id = factory.Faker('uuid4')
    old_value = None
    new_value = factory.Faker('sentence')
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    timestamp = factory.LazyFunction(lambda: datetime.utcnow().isoformat())


# Helper functions for creating multiple test objects

def create_user_settings(count=1, **kwargs):
    """Create one or more user settings objects."""
    if count == 1:
        return UserSettingsFactory.create(**kwargs)
    return [UserSettingsFactory.create(**kwargs) for _ in range(count)]


def create_notification_channels(count=1, **kwargs):
    """Create one or more notification channel objects."""
    if count == 1:
        return NotificationChannelFactory.create(**kwargs)
    return [NotificationChannelFactory.create(**kwargs) for _ in range(count)]


def create_trades(count=1, **kwargs):
    """Create one or more trade objects."""
    if count == 1:
        return TradeFactory.create(**kwargs)
    return [TradeFactory.create(**kwargs) for _ in range(count)]


def create_opportunities(count=1, **kwargs):
    """Create one or more opportunity objects."""
    if count == 1:
        return OpportunityFactory.create(**kwargs)
    return [OpportunityFactory.create(**kwargs) for _ in range(count)]


def create_crypto_prices(count=1, **kwargs):
    """Create one or more crypto price objects."""
    if count == 1:
        return CryptoPriceFactory.create(**kwargs)
    return [CryptoPriceFactory.create(**kwargs) for _ in range(count)]


def create_audit_logs(count=1, **kwargs):
    """Create one or more audit log objects."""
    if count == 1:
        return AuditLogFactory.create(**kwargs)
    return [AuditLogFactory.create(**kwargs) for _ in range(count)]
