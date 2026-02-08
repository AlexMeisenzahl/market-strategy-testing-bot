# Configuration Guide

Complete guide to configuring the Market Strategy Testing Bot.

## Configuration File Location

The main configuration file is `config.yaml` in the root directory.

**First time setup:** Copy `config.example.yaml` to `config.yaml`:
```bash
cp config.example.yaml config.yaml
```

---

## Safety Settings

### paper_trading
**Type:** Boolean  
**Default:** `true`  
**Description:** When true, all trades are simulated. No real money is used.

```yaml
paper_trading: true  # KEEP THIS TRUE FOR SAFETY
```

⚠️ **WARNING:** Only change to `false` if you fully understand live trading implications.

### kill_switch
**Type:** Boolean  
**Default:** `false`  
**Description:** Emergency stop. When true, bot immediately stops all trading.

```yaml
kill_switch: false  # Set to true to stop bot immediately
```

---

## Data Sources

### Crypto Prices

```yaml
data_sources:
  crypto_prices:
    primary: binance       # Primary data source
    fallback: coingecko   # Fallback if primary fails
    use_websocket: true   # Use WebSocket for real-time prices
```

**Supported sources:**
- `binance` - Free, 1200 req/min, real-time WebSocket
- `coingecko` - Free, 50 req/min, REST API
- `coinbase` - Free, 10 req/sec, REST API

### Polymarket

```yaml
data_sources:
  polymarket:
    method: subgraph           # 'subgraph' (free) or 'api' (requires config)
    cache_ttl_seconds: 60     # Cache duration
```

**Methods:**
- `subgraph` - Free GraphQL endpoint, unlimited requests
- `api` - Official Polymarket API (requires configuration below)

---

## Polymarket API Configuration

```yaml
polymarket:
  api:
    enabled: false              # Enable official API
    base_url: "https://clob.polymarket.com"
    rate_limit: 60             # Requests per minute
    timeout: 10                # Request timeout (seconds)
    retry_attempts: 3          # Number of retries on failure
  
  market_filters:
    min_liquidity: 1000        # Minimum liquidity in USD
    min_volume_24h: 5000       # Minimum 24h volume in USD
    categories: []             # Filter by categories (empty = all)
```

**Available categories:**
- `crypto`
- `politics`
- `sports`
- `entertainment`
- `science`
- `business`

---

## Trading Parameters

### Position Sizing

```yaml
max_trade_size: 10              # Maximum per trade (USD)
```

**Recommendations:**
- Paper trading: 10-100 USD
- Real trading: Start with 5-20 USD

### Profit Requirements

```yaml
min_profit_margin: 0.02         # Minimum 2% profit margin
```

**Recommendations:**
- Conservative: 0.03-0.05 (3-5%)
- Moderate: 0.02-0.03 (2-3%)
- Aggressive: 0.01-0.02 (1-2%)

### Rate Limits

```yaml
max_trades_per_hour: 5          # Hourly trade limit
max_trades_per_day: 50          # Daily trade limit
```

**Recommendations:**
- Conservative: 5/hour, 30/day
- Moderate: 10/hour, 50/day
- Aggressive: 20/hour, 100/day

---

## API Settings

```yaml
api_timeout_seconds: 5          # Request timeout
api_retry_attempts: 3           # Number of retries
```

---

## Notification Settings

### Email Configuration

```yaml
notifications:
  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: your-email@gmail.com
    password: your-app-password    # Use app-specific password
```

**Gmail Setup:**
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate an app-specific password
4. Use that password in config

**Supported SMTP Servers:**
- Gmail: smtp.gmail.com:587
- Outlook: smtp.office365.com:587
- Yahoo: smtp.mail.yahoo.com:587

### Telegram Configuration

```yaml
notifications:
  telegram:
    bot_token: your-bot-token
    default_chat_id: your-chat-id
```

**Telegram Setup:**
1. Message @BotFather on Telegram
2. Create a new bot with /newbot
3. Copy the bot token
4. Start a chat with your bot
5. Get your chat ID from @userinfobot

### Quiet Hours

```yaml
notifications:
  quiet_hours_start: 22   # 10 PM
  quiet_hours_end: 8      # 8 AM
```

Notifications are suppressed during quiet hours.

---

## Market Selection

```yaml
markets_to_watch: []            # Empty = all markets
```

**Examples:**
```yaml
# Watch only crypto markets
markets_to_watch: ["Bitcoin", "Ethereum", "Crypto"]

# Watch only politics
markets_to_watch: ["Trump", "Biden", "Election"]

# Watch specific events
markets_to_watch: ["2024 Election", "Bitcoin ETF"]
```

---

## Strategy Configuration

```yaml
strategies:
  polymarket_arbitrage:
    enabled: true
    min_profit: 0.02
    
  crypto_polymarket_arbitrage:
    enabled: true
    min_profit: 0.03
    
  cross_exchange_arbitrage:
    enabled: false
```

---

## Advanced Settings

### Logging

```yaml
logging:
  level: INFO                   # DEBUG, INFO, WARNING, ERROR
  file: logs/bot.log
  max_size_mb: 10
  backup_count: 5
```

### Performance

```yaml
performance:
  websocket_buffer_size: 1000   # WebSocket message buffer
  cache_size_mb: 100            # Price cache size
  worker_threads: 4             # Concurrent workers
```

---

## Validation

Validate your configuration:
```bash
python -m utils.config_validator config.yaml
```

Expected output:
```
✅ Configuration is valid!
```

If errors are found:
```
❌ ERRORS:
  • Invalid primary crypto source: invalid_source
  • min_profit_margin must be between 0 and 1

⚠️  WARNINGS:
  • max_trade_size is $1000 - consider lowering for safety
```

---

## Environment Variables

Override config values with environment variables:

```bash
export TRADING_MODE=paper
export MAX_TRADE_SIZE=10
export NOTIFICATIONS_ENABLED=true
```

**Supported variables:**
- `TRADING_MODE` - Override trading_mode
- `MAX_TRADE_SIZE` - Override max_trade_size
- `NOTIFICATIONS_ENABLED` - Override notifications
- `LOG_LEVEL` - Override logging level

---

## Best Practices

1. **Always start with paper trading**
2. **Test notifications before going live**
3. **Set conservative profit margins initially**
4. **Monitor performance for 1-2 weeks before adjusting**
5. **Keep rate limits conservative**
6. **Enable quiet hours to avoid night alerts**
7. **Regularly backup your config**
8. **Use version control for config changes**

---

## Troubleshooting

### Bot won't start
- Check config.yaml syntax with validator
- Verify all required sections exist
- Check log files for errors

### No opportunities detected
- Lower min_profit_margin
- Check market_filters aren't too restrictive
- Verify API connections with health check

### Too many notifications
- Enable rate limiting
- Set quiet hours
- Increase min_profit_threshold
- Disable low-confidence alerts

### API errors
- Check API credentials
- Verify rate limits
- Test with health check endpoint
- Check firewall/proxy settings

---

## Support

For configuration help:
1. Check this guide
2. Review config.example.yaml comments
3. Run config validator
4. Check logs directory
5. Review API documentation
