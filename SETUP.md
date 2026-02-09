# Setup Guide - Market Strategy Testing Bot

Complete setup instructions to get your trading bot running in minutes!

---

## Quick Start (0 Minutes - Mock Data)

**Want to try the bot immediately without any configuration?**

```bash
# Clone the repository
git clone https://github.com/AlexMeisenzahl/market-strategy-testing-bot.git
cd market-strategy-testing-bot

# Install dependencies
pip install -r requirements.txt

# Run the bot!
python run_bot.py
```

✅ **That's it!** The bot will automatically run with **mock data** - no API keys needed.

The bot will:
- Generate fake Polymarket markets with realistic arbitrage opportunities
- Simulate crypto price movements
- Execute paper trades
- Log all activities to `logs/activity.json`
- Update dashboard data in real-time

**To view the dashboard:**
```bash
# In a new terminal
python start_dashboard.py
```

Then open: **http://localhost:5000**

---

## Full Setup (10 Minutes - Live Data)

Want to trade with **real market data**? Follow these steps:

### Step 1: Get API Keys (5 minutes)

You'll need API keys for the services you want to use. See [API_KEYS.md](API_KEYS.md) for detailed instructions.

**Required for Live Trading:**
- ✅ **Polymarket API** - For real prediction markets
- ✅ **CoinGecko API** - For crypto prices (FREE, no key needed!)

**Optional:**
- 🔔 **Telegram Bot Token** - For mobile notifications
- 📧 **Email SMTP** - For email alerts

### Step 2: Start the Dashboard

```bash
python start_dashboard.py
```

Dashboard will be available at: **http://localhost:5000**

### Step 3: Configure API Keys in Dashboard

1. Open the dashboard: http://localhost:5000
2. Navigate to **Settings → Data Sources**
3. You'll see the current mode: 🔴 **MOCK DATA**

**Configure Polymarket:**
- Endpoint: `https://clob.polymarket.com` (pre-filled)
- API Key: Enter your key or leave blank for public access
- Click **Test Connection** to verify
- Click **Save**

**Configure CoinGecko:**
- Provider: Select "CoinGecko (Free)"
- Endpoint: `https://api.coingecko.com/api/v3` (pre-filled)
- API Key: Leave blank (not needed for free tier)
- Click **Test Connection** to verify
- Click **Save**

After saving, the indicator will change to: 🟢 **LIVE DATA**

### Step 4: Start the Bot

```bash
python run_bot.py
```

You'll see clear messages indicating data sources:
```
✅ Successfully connected to Polymarket API
📊 Using LIVE Polymarket data

✅ Successfully connected to CoinGecko API (BTC: $45,234.56)
💰 Using LIVE crypto price data
```

### Step 5: Verify It's Working

**Check the logs:**
```bash
tail -f logs/bot.log
```

**Check the dashboard:**
- Open http://localhost:5000
- Navigate to **Opportunities** tab
- You should see real markets with live data

**Verify data mode in dashboard:**
- Settings → Data Sources should show: 🟢 **LIVE DATA**

---

## Configuration Options

### Paper Trading vs Live Trading

The bot runs in **paper trading mode** by default (no real money):

```yaml
# config.yaml
paper_trading: true  # Set to false for live trading (NOT RECOMMENDED without testing)
```

### Strategy Selection

Enable/disable strategies in `config.yaml`:

```yaml
strategies:
  enabled:
    - arbitrage         # Exploit YES + NO < 1.00
    - momentum          # Ride crypto trends
    - news              # React to volume spikes
    - statistical_arb   # Find correlated markets
```

### Risk Management

Configure position sizing and risk limits:

```yaml
risk_management:
  max_position_size: 1000    # Max $ per trade
  max_daily_loss: 500        # Stop trading if down $500
  max_drawdown: 0.15         # 15% max drawdown
```

---

## What Each Strategy Needs

| Strategy | Data Required | Works Without API? |
|----------|--------------|-------------------|
| **Arbitrage** | Polymarket markets | ❌ Needs live data |
| **Momentum** | Crypto prices | ❌ Needs live data |
| **News** | Polymarket volume | ❌ Needs live data |
| **Statistical Arb** | Market correlations | ❌ Needs live data |

**Mock mode generates realistic test data but cannot execute real trades.**

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           run_bot.py                    │
│  (Main bot loop - 60s intervals)        │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
    ┌───▼────┐      ┌───▼────┐
    │ Market │      │ Crypto │
    │ Client │      │ Client │
    └───┬────┘      └───┬────┘
        │                │
    ┌───▼────────────────▼───┐
    │   Live or Mock Data    │
    └───────────┬────────────┘
                │
    ┌───────────▼────────────┐
    │  Strategy Manager      │
    │  - Arbitrage           │
    │  - Momentum            │
    │  - News                │
    │  - Statistical Arb     │
    └───────────┬────────────┘
                │
    ┌───────────▼────────────┐
    │  Paper Trading Engine  │
    │  (Simulated execution) │
    └───────────┬────────────┘
                │
    ┌───────────▼────────────┐
    │  Dashboard & Logs      │
    │  (Real-time updates)   │
    └────────────────────────┘
```

---

## Troubleshooting

### Bot Shows "MOCK DATA" After Adding Keys

1. Check that you clicked **Save** after entering credentials
2. Click **Test Connection** to verify keys work
3. Restart the bot: `Ctrl+C` then `python run_bot.py`
4. Check logs for connection errors: `tail -f logs/bot.log`

### "Connection Failed" Error

- **Polymarket**: Check if endpoint is correct and internet is working
- **CoinGecko**: Verify you haven't exceeded rate limits (50 calls/min free)
- **Network**: Try pinging the API: `curl https://api.coingecko.com/api/v3/ping`

### No Opportunities Found

- **Normal**: Real markets may not always have arbitrage opportunities
- **Check markets**: Visit https://polymarket.com to see available markets
- **Adjust filters**: Lower `min_volume` in bot code if markets are filtered out
- **Mock data**: Switch to mock mode to verify bot logic works

### Dashboard Not Loading

```bash
# Check if port 5000 is in use
lsof -i :5000

# Try a different port
export PORT=5001
python start_dashboard.py
```

### Keys Not Saving

- **Permissions**: Ensure `config/` directory is writable
- **Encryption**: Check `config/encryption.key` was created successfully
- **Browser**: Clear cache and try again
- **Logs**: Check dashboard logs for errors

---

## Security Notes

✅ **Credentials are encrypted** using AES-256 (Fernet)
✅ **Encryption key** stored in `config/encryption.key` (keep secure!)
✅ **Keys masked** in dashboard UI (****last6chars)
✅ **Never commit** `config/credentials.json` or `config/encryption.key` to git

**Best practices:**
- Use `.gitignore` to exclude config files (already configured)
- Rotate API keys periodically
- Use read-only keys when possible
- Never share encryption key

---

## Next Steps

1. ✅ **Run with mock data** - Test all features (0 setup)
2. 📚 **Read [API_KEYS.md](API_KEYS.md)** - Learn how to get API keys
3. 🔑 **Add API keys** - Enable live data (10 minutes)
4. 📊 **Monitor dashboard** - Watch opportunities in real-time
5. 🧪 **Paper trade** - Test strategies without risk
6. 📖 **Read [STRATEGIES.md](STRATEGIES.md)** - Understand each strategy
7. ⚡ **Optimize** - Tune parameters for better performance

---

## Getting Help

- 📖 **FAQ**: [FAQ.md](FAQ.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/AlexMeisenzahl/market-strategy-testing-bot/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/AlexMeisenzahl/market-strategy-testing-bot/discussions)
- 📧 **Email**: Check repo for contact info

---

**Happy Trading! 📈🚀**
