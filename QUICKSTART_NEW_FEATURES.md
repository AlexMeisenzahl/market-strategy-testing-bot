# Quick Start Guide - New Features

This guide helps you get started with the new advanced features quickly.

## Prerequisites

- Python 3.8+
- pip
- Node.js 16+ (for PWA development)
- Internet connection

## 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# (Optional) Install mobile app dependencies
cd mobile && npm install && cd ..
```

## 2. Configure Environment

```bash
# Copy example files
cp .env.example .env
cp config.example.yaml config.yaml

# Edit .env to add your API keys (optional)
nano .env
```

## 3. Enable Strategies

Edit `config.yaml` and enable desired strategies:

### For Weather Trading:
```yaml
strategies:
  weather_trading:
    enabled: true
    confidence_threshold: 0.7
```

### For BTC Arbitrage:
```yaml
strategies:
  btc_arbitrage:
    enabled: true
    min_profit_margin: 0.02
```

## 4. Start the Bot

```bash
# Run the bot (this will also start the API if enabled)
python3 run_bot.py
```

## 5. Access Mobile App

1. Ensure `mobile_api.enabled: true` in `config.yaml`
2. Open browser: `http://localhost:8000`
3. Login with:
   - Username: `admin`
   - Password: `admin123`

## 6. Install PWA (Optional)

### On iOS:
1. Open in Safari
2. Tap Share → "Add to Home Screen"

### On Android:
1. Open in Chrome
2. Tap ⋮ → "Install App"

## 7. Setup Telegram (Optional)

1. Create bot via [@BotFather](https://t.me/BotFather)
2. Get chat ID
3. Add to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```
4. Enable in `config.yaml`:
   ```yaml
   telegram:
     enabled: true
   ```

## 8. Monitor & Control

- **Dashboard**: http://localhost:5000 (existing)
- **Mobile API**: http://localhost:8000 (new)
- **Telegram**: Receive notifications in Telegram

## Testing the Bot

```bash
# Test imports
python3 -c "from strategies.weather_trading import WeatherTradingStrategy; print('Weather trading OK')"
python3 -c "from strategies.btc_arbitrage import BTCArbitrageStrategy; print('BTC arbitrage OK')"
python3 -c "from telegram_bot import create_telegram_bot; print('Telegram OK')"

# Test API health
curl http://localhost:8000/api/health
```

## Troubleshooting

See [NEW_FEATURES.md](NEW_FEATURES.md#9-troubleshooting) for detailed troubleshooting guide.

## Next Steps

1. Review [NEW_FEATURES.md](NEW_FEATURES.md) for complete documentation
2. Customize strategy parameters in `config.yaml`
3. Monitor bot performance
4. Adjust confidence thresholds based on results
5. Set up remote access via Tailscale or ngrok (see existing docs)

## Security Reminders

- ⚠️ Change default API credentials
- ⚠️ Generate secure JWT secret
- ⚠️ Don't expose API publicly without authentication
- ⚠️ Never commit API keys to version control
- ⚠️ Keep paper_trading: true until thoroughly tested

## Support

For issues or questions:
1. Check [NEW_FEATURES.md](NEW_FEATURES.md)
2. Review [Troubleshooting](#troubleshooting)
3. Open a GitHub issue

Happy Trading! 🚀
