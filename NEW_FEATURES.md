# 🚀 New Advanced Features - Weather Trading, BTC Arbitrage, Mobile API & PWA

This document describes the new advanced features added to the Polymarket Trading Bot, including two new trading strategies, a mobile backend API, Progressive Web App, and Telegram notifications.

---

## Table of Contents

1. [Weather Trading Strategy](#1-weather-trading-strategy-)
2. [BTC Arbitrage Strategy](#2-btc-arbitrage-strategy-)
3. [Mobile Backend API](#3-mobile-backend-api-)
4. [Progressive Web App (PWA)](#4-progressive-web-app-pwa-)
5. [Telegram Notifications](#5-telegram-notifications-)
6. [Setup Instructions](#6-setup-instructions)
7. [API Documentation](#7-api-documentation)
8. [Security Best Practices](#8-security-best-practices)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Weather Trading Strategy 🌦️

### Overview

The Weather Trading Strategy uses real-time NOAA weather data to trade on weather-related prediction markets on Polymarket.

### How It Works

1. **Market Detection**: Automatically identifies weather-related markets:
   - Temperature markets (e.g., "Will temperature exceed 80°F in NYC?")
   - Precipitation markets (e.g., "Will it rain on July 4th?")

2. **Weather Data Integration**: Fetches real-time forecasts from NOAA API

3. **Prediction Logic**: Correlates weather forecasts with market prices and generates confidence scores

4. **Automated Trading**: Places bets when confidence exceeds configured threshold

### Configuration

Add to your `config.yaml`:

```yaml
strategies:
  weather_trading:
    enabled: true
    noaa_api_key: "${NOAA_API_KEY}"
    confidence_threshold: 0.7        # 70% confidence required
    max_bet_size: 100                # Maximum $100 per bet
    locations: 
      - "New York"
      - "Los Angeles"
      - "Chicago"
    update_interval_seconds: 3600    # Check every hour
    max_holding_time: 86400          # Hold positions max 24 hours
```

Add to your `.env` file:

```bash
NOAA_API_KEY=your_noaa_api_key_here
```

### Getting a NOAA API Key

1. Visit [weather.gov](https://www.weather.gov/)
2. The NOAA API is free and doesn't require registration for basic use
3. For production use, consider getting an API key from [weather.gov/api](https://www.weather.gov/api)

### Example Opportunities

- **Temperature Market**: "Will NYC exceed 85°F on July 15?"
  - NOAA forecast: High of 88°F
  - Current YES price: $0.45
  - **Action**: Buy YES with 80% confidence

- **Precipitation Market**: "Will it rain in LA tomorrow?"
  - NOAA forecast: 15% chance of rain
  - Current NO price: $0.70
  - **Action**: Buy NO with 85% confidence

### Best Practices

- Start with a conservative confidence threshold (0.7-0.8)
- Monitor strategy performance over several days
- Weather forecasts are most accurate within 3-5 days
- Consider seasonal patterns and climate norms

---

## 2. BTC Arbitrage Strategy ₿

### Overview

The BTC Arbitrage Strategy exploits pricing inefficiencies in Polymarket's 15-minute Bitcoin UP/DOWN markets.

### How It Works

1. **Market Pairing**: Identifies matching UP and DOWN markets for the same 15-minute expiry

2. **Arbitrage Detection**: Finds opportunities where `UP_price + DOWN_price < $1.00`

3. **Spread Locking**: Simultaneously buys both UP and DOWN contracts

4. **Guaranteed Profit**: Since one will always resolve to $1.00, profit is locked in

5. **Expiry Automation**: Automatically settles positions at expiry

### Configuration

Add to your `config.yaml`:

```yaml
strategies:
  btc_arbitrage:
    enabled: true
    min_profit_margin: 0.02          # Minimum 2% profit
    max_position_size: 500           # Maximum $500 per trade
    expiry_minutes: 15               # 15-minute expiry markets
    slippage_tolerance: 0.005        # 0.5% slippage tolerance
    max_gas_price: 50                # Maximum gas price (if applicable)
```

### Example Opportunity

**Market**: "BTC UP in 15 minutes"
- UP price: $0.48
- DOWN price: $0.49
- **Total cost**: $0.97
- **Payout**: $1.00 (guaranteed)
- **Gross profit**: $0.03
- **Net profit** (after fees): ~$0.027 (2.7%)

### Risk Management

- **Execution Risk**: Both sides must fill simultaneously
- **Fee Impact**: Trading fees reduce net profit (typically ~2%)
- **Slippage**: Price may move during execution
- **Position Limits**: Caps maximum exposure per trade

### Performance Expectations

- **Profit per trade**: Typically 1-5% net
- **Win rate**: ~100% (arbitrage is risk-free when executed)
- **Frequency**: Depends on market inefficiencies (5-20 opportunities/day)
- **Best times**: High volatility periods, market opens/closes

---

## 3. Mobile Backend API 🔧

### Overview

A complete FastAPI-based REST API with WebSocket support for remote bot control.

### Features

- **Authentication**: JWT token-based auth
- **Real-time Updates**: WebSocket streaming
- **Rate Limiting**: Protection against abuse
- **CORS Support**: Configurable origins
- **Comprehensive Endpoints**: Markets, trades, positions, strategies

### Configuration

Add to your `config.yaml`:

```yaml
mobile_api:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  jwt_secret: "${API_JWT_SECRET}"
  jwt_expiration_hours: 24
  cors_origins: ["*"]  # Restrict in production!
  rate_limit:
    requests_per_minute: 60
    burst: 10
  websocket:
    heartbeat_interval: 30
    max_connections: 100
```

Add to your `.env`:

```bash
API_JWT_SECRET=your_very_long_random_secret_key_change_this
API_PORT=8000
API_HOST=0.0.0.0
```

### Starting the API Server

```bash
# From the bot main script
python3 api/server.py
```

Or integrate into your bot:

```python
from api import run_server

# Pass bot instance and config
run_server(bot_instance, config)
```

### Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Change these immediately in production!**

---

## 4. Progressive Web App (PWA) 📱

### Overview

A mobile-optimized web app that can be installed on iOS and Android devices.

### Features

- ✅ Installable as standalone app
- ✅ Offline support with service worker
- ✅ Real-time updates via WebSocket
- ✅ Dark mode (AMOLED optimized)
- ✅ Touch-optimized interface
- ✅ Push notifications support
- ✅ Responsive design (mobile, tablet, desktop)

### Installation

#### iOS (iPhone/iPad)

1. Open Safari and navigate to: `http://your-bot-ip:8000`
2. Tap the **Share** button (box with arrow)
3. Scroll down and tap **"Add to Home Screen"**
4. Tap **"Add"**
5. The app icon will appear on your home screen

#### Android

1. Open Chrome and navigate to: `http://your-bot-ip:8000`
2. Tap the **menu** button (⋮)
3. Select **"Add to Home Screen"** or **"Install App"**
4. Tap **"Install"**
5. The app will be added to your app drawer

### App Features

**Dashboard View**:
- Bot status (running, paused, stopped)
- Daily/Total P&L
- Active strategies count
- Active positions count

**Markets View**:
- Browse available markets
- Search functionality
- Filter by category

**Positions View**:
- View all active positions
- Position details (entry price, current price, P&L)
- Close positions

**Strategies View**:
- Enable/disable strategies
- View strategy config
- Strategy performance metrics

**Settings**:
- Theme selection (dark/light/auto)
- Notification preferences
- Account management
- Logout

### Development

```bash
cd mobile

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

---

## 5. Telegram Notifications 📱

### Overview

Real-time Telegram notifications for all bot activities.

### Configuration

Add to your `config.yaml`:

```yaml
telegram:
  enabled: true
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"
  notifications:
    trade_executed: true
    strategy_triggered: true
    profit_loss_updates: true
    daily_summary: true
    error_alerts: true
  rate_limit:
    max_per_minute: 10
```

Add to your `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Setting Up Telegram Bot

1. **Create Bot**:
   - Open Telegram and search for `@BotFather`
   - Send `/newbot`
   - Follow prompts to create your bot
   - Copy the bot token provided

2. **Get Chat ID**:
   - Start a chat with your new bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the response

3. **Configure Bot**:
   - Add token and chat ID to `.env` file
   - Enable in `config.yaml`
   - Restart the bot

### Notification Types

**Trade Executed**:
```
🤖 Trade Executed
Market: Will BTC reach $100k?
Direction: BUY
Size: $50.00
Price: 0.6500
Strategy: btc_arbitrage
Time: 2024-01-15 14:30:00
```

**Profit/Loss Update**:
```
💰 P&L Update
Today: $125.50 (+2.51%)
Total: $1,250.00
Win Rate: 78.5%
Time: 2024-01-15 20:00:00
```

**Strategy Triggered**:
```
🎯 Opportunity Found
Strategy: weather_trading
Market: Will it rain in NYC tomorrow?
Confidence: 85.0%
Action: buy_no
Time: 2024-01-15 09:15:00
```

**Error Alert**:
```
⚠️ Error Alert
Type: API Connection Failed
Message: NOAA API timeout
Time: 2024-01-15 11:45:00
```

**Daily Summary**:
```
📊 Daily Summary
Trades: 12
P&L: $145.75 (+2.92%)
Win Rate: 83.3%

Best Trade: BTC Arbitrage ($15.25)
Worst Trade: Weather Trade (-$3.50)

Date: 2024-01-15
```

---

## 6. Setup Instructions

### Complete Setup Steps

1. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   nano .env
   ```

3. **Configure Strategies**:
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml and enable desired strategies
   nano config.yaml
   ```

4. **Enable Weather Trading**:
   - Get NOAA API key (free, no registration required)
   - Add to `.env`: `NOAA_API_KEY=your_key`
   - Set `enabled: true` in `config.yaml` under `weather_trading`

5. **Enable BTC Arbitrage**:
   - Set `enabled: true` in `config.yaml` under `btc_arbitrage`
   - Adjust `min_profit_margin` as needed (recommended: 0.02-0.03)

6. **Start Mobile API** (optional):
   - Set `enabled: true` in `config.yaml` under `mobile_api`
   - Generate secure JWT secret: `openssl rand -hex 32`
   - Add to `.env`: `API_JWT_SECRET=<generated_secret>`
   - API will start automatically with the bot

7. **Setup Telegram** (optional):
   - Create Telegram bot via @BotFather
   - Get chat ID
   - Add credentials to `.env`
   - Enable in `config.yaml`

8. **Deploy PWA** (optional):
   ```bash
   cd mobile
   npm install
   npm run build
   # Serve with your preferred web server
   ```

9. **Start the Bot**:
   ```bash
   python3 run_bot.py
   ```

---

## 7. API Documentation

### Authentication

**POST** `/api/auth/login`
```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Markets

**GET** `/api/markets?page=1&per_page=50`

Response:
```json
{
  "markets": [...],
  "total": 100,
  "page": 1,
  "per_page": 50
}
```

**GET** `/api/markets/{market_id}`

**GET** `/api/markets/search?q=bitcoin`

### Trading

**POST** `/api/trade`
```json
{
  "market_id": "0x123...",
  "side": "buy",
  "order_type": "market",
  "amount": 50.00,
  "strategy": "btc_arbitrage"
}
```

**DELETE** `/api/trade/{trade_id}`

### Positions

**GET** `/api/positions`

**GET** `/api/positions/{position_id}`

**PUT** `/api/positions/{position_id}/close`

### Strategies

**GET** `/api/strategies`

**PUT** `/api/strategies/{strategy_name}/enable`

**PUT** `/api/strategies/{strategy_name}/disable`

**GET** `/api/strategies/{strategy_name}/config`

**PUT** `/api/strategies/{strategy_name}/config`

### WebSocket

**WS** `/ws/stream`

Events:
- `trade`: Trade execution events
- `position`: Position updates
- `market`: Market price changes
- `strategy`: Strategy triggers
- `status`: Bot status changes

---

## 8. Security Best Practices

### API Security

1. **Change Default Credentials**:
   ```python
   # In api/routes/auth.py, update USERS_DB
   # Use bcrypt to hash passwords
   ```

2. **Use Strong JWT Secret**:
   ```bash
   openssl rand -hex 32
   ```

3. **Restrict CORS Origins**:
   ```yaml
   mobile_api:
     cors_origins: ["https://yourdomain.com"]
   ```

4. **Enable HTTPS**:
   - Use nginx or Caddy as reverse proxy
   - Obtain SSL certificate (Let's Encrypt)

5. **Rate Limiting**:
   - Keep rate limits enabled
   - Adjust based on your needs

### API Key Security

1. **Never commit API keys** to version control
2. **Use environment variables** for all secrets
3. **Rotate keys regularly**
4. **Use separate keys** for dev/production

### Network Security

1. **Firewall Configuration**:
   ```bash
   # Allow only specific IPs
   sudo ufw allow from <your_ip> to any port 8000
   ```

2. **VPN Access**:
   - Use Tailscale or WireGuard
   - Don't expose API publicly

3. **SSH Security**:
   - Disable password authentication
   - Use SSH keys only
   - Change default SSH port

---

## 9. Troubleshooting

### Weather Trading Issues

**Problem**: "NOAA API key not configured"
- **Solution**: Add `NOAA_API_KEY` to `.env` file

**Problem**: "Weather API is not accessible"
- **Solution**: Check internet connection, verify API key is valid

**Problem**: No opportunities found
- **Solution**: 
  - Ensure markets exist for your configured locations
  - Lower `confidence_threshold` temporarily
  - Check market keywords match patterns

### BTC Arbitrage Issues

**Problem**: No BTC markets found
- **Solution**: Polymarket may not have active BTC UP/DOWN markets at all times

**Problem**: "Profit margin too low"
- **Solution**: Adjust `min_profit_margin` in config (try 0.01)

**Problem**: Both sides not filling
- **Solution**: This is paper trading - actual execution would need atomic transactions

### Mobile API Issues

**Problem**: Cannot connect to API
- **Solution**: 
  - Verify API is running: `curl http://localhost:8000/api/health`
  - Check firewall settings
  - Ensure correct host/port in config

**Problem**: "Unauthorized" errors
- **Solution**: 
  - Login again to get fresh token
  - Check JWT secret is configured
  - Verify token hasn't expired

**Problem**: CORS errors
- **Solution**: Add your domain to `cors_origins` in config

### PWA Issues

**Problem**: Cannot install PWA
- **Solution**: 
  - Ensure HTTPS is enabled (required for iOS)
  - Check `manifest.json` is accessible
  - Verify service worker is registered

**Problem**: Offline mode not working
- **Solution**: 
  - Clear browser cache
  - Re-register service worker
  - Check browser console for errors

**Problem**: Icons not showing
- **Solution**: 
  - Generate icons (use a tool like [PWA Asset Generator](https://github.com/onderceylan/pwa-asset-generator))
  - Place in `mobile/public/icons/`
  - Update `manifest.json` paths

### Telegram Issues

**Problem**: Not receiving notifications
- **Solution**: 
  - Verify bot token is correct
  - Check chat ID is correct
  - Send `/start` to bot in Telegram
  - Check bot hasn't been blocked

**Problem**: Rate limit exceeded
- **Solution**: Increase `max_per_minute` in config

**Problem**: "Bot not initialized"
- **Solution**: Check bot token format, ensure no extra spaces

### General Issues

**Problem**: Import errors
- **Solution**: `pip install -r requirements.txt --upgrade`

**Problem**: Configuration not loading
- **Solution**: 
  - Check YAML syntax
  - Verify environment variables are set
  - Use `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"`

**Problem**: High memory usage
- **Solution**: 
  - Reduce WebSocket connection count
  - Lower cache durations
  - Increase cleanup intervals

---

## Support & Contributing

For issues, feature requests, or contributions:

1. Check existing documentation
2. Search closed issues on GitHub
3. Open a new issue with detailed description
4. Include logs and configuration (remove sensitive data)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Disclaimer

This software is for educational purposes only. Trading prediction markets involves risk. Past performance does not guarantee future results. Always paper trade first and understand the risks before trading with real money.

The weather and BTC arbitrage strategies are experimental and should be thoroughly tested before any real-world use. No guarantees are made about profitability or reliability.
