# Polymarket Arbitrage Bot - Paper Trading Edition

A complete, production-ready arbitrage bot for Polymarket with **live API integration**, **professional web dashboard**, and comprehensive safety features. **PAPER TRADING ONLY - NO REAL MONEY IS USED.**

## 🚀 NEW: Live Polymarket API Integration

**The bot now connects to the real Polymarket API** for live market data and prices!

### Live API Features:
- 🔴 **Live Market Data** - Fetches real-time YES/NO prices from Polymarket
- 📊 **Active Markets Discovery** - Automatically finds and filters active markets
- 🎯 **Smart Filtering** - Filter by liquidity, volume, keywords, and categories
- 🛡️ **Graceful Fallback** - Continues with simulated data if API is unavailable
- ⚡ **Rate Limiting** - Respects API limits with exponential backoff
- 🔄 **Auto-Retry** - Automatically retries failed requests

👉 **[See API Integration Guide](API_INTEGRATION.md)**

### Enhanced Notification System:
- 📱 **Granular Controls** - Configure notifications per event type and channel
- ⏰ **Quiet Hours** - Set hours when notifications are suppressed
- 🚦 **Rate Limiting** - Prevent notification spam with smart rate limiting
- 📧 **Multiple Channels** - Desktop, Email, and Telegram notifications
- 🎯 **Smart Triggers** - Configurable triggers for high-value opportunities

## 📊 Professional Web Dashboard

**Access a beautiful, modern web interface** to monitor and control your trading bot!

### Dashboard Features:
- 📈 **Real-time Performance Metrics** - Total P&L, Win Rate, Active Trades
- 📊 **Interactive Charts** - Cumulative P&L, Daily P&L, Strategy Performance
- 💼 **Trading History** - Browse and filter all your trades
- 🔔 **Notification Center** - Configure email, desktop, and Telegram alerts
- 🎛️ **Bot Control** - Start, stop, and monitor your bot from the web
- 🎨 **Professional Design** - Dark theme, responsive, smooth animations
- 📥 **CSV Export** - Export trade history for external analysis
- 📈 **Advanced Analytics** - Opportunity trends, profit distribution, and more

### 📱 Mobile & Progressive Web App (PWA):
- 📲 **Install as iPhone App** - Add to home screen for native app experience
- 🎯 **Mobile-Optimized UI** - Bottom navigation, touch-friendly buttons, card layouts
- 📴 **Offline Support** - View cached data without internet connection
- 🔄 **Pull-to-Refresh** - Swipe down to refresh data on mobile
- 👆 **Touch Gestures** - Swipe to open/close menu, haptic feedback on iOS
- 📱 **Responsive Design** - Works perfectly on iPhone, iPad, and desktop
- 🌐 **Remote Access** - Access via Tailscale or ngrok from anywhere
- 🔒 **Secure** - HTTPS support, service worker caching, safe area support

👉 **[Mobile Setup Guide](docs/MOBILE_SETUP.md)** | **[Remote Access Guide](docs/REMOTE_ACCESS_GUIDE.md)**

### Quick Start Dashboard:

**Option 1: Quick Start Script (Recommended)**
```bash
# Automated setup and launch
python3 start_dashboard.py
```

**Option 2: Manual Start**
```bash
# Start the web dashboard
python3 dashboard/app.py

# Open in your browser
http://localhost:5000
```

👉 **[See Full Dashboard Documentation](dashboard/README.md)**

---

## 🎯 What This Bot Does (In Plain English)

This bot watches Polymarket prediction markets and looks for arbitrage opportunities. An arbitrage opportunity happens when you can buy BOTH the "YES" and "NO" contracts for less than $1.00 combined. Since one of them will always pay out $1.00, you make a guaranteed profit.

**Example:**
- YES contract costs $0.48
- NO contract costs $0.49
- Total cost: $0.97
- One will pay out: $1.00
- Your profit: $0.03 (3% return)

This bot finds these opportunities automatically and can now use **real live data from Polymarket** while still simulating trades (paper trading) so you can learn how arbitrage works without risking any money.

## ⚠️ IMPORTANT SAFETY WARNINGS

1. **This bot uses PAPER TRADING ONLY** - No real money is involved
2. **Never change `paper_trading: true` in config.yaml** without thorough understanding
3. **This is for educational purposes** - Learn how arbitrage works safely
4. **Real trading requires**: Authentication, real funds, and much more complexity
5. **Always start with paper trading** before considering real money (if ever)

## 📋 Prerequisites

Before you start, make sure you have:

1. **Python 3.8 or newer** installed on your computer
   - Check by running: `python --version` or `python3 --version`
   - Download from: https://www.python.org/downloads/

2. **Basic command line knowledge**
   - How to open a terminal/command prompt
   - How to navigate to folders
   - How to run Python commands

3. **Internet connection** (to fetch market data)

## 🚀 Installation Steps

### Step 1: Download the Bot

Clone or download this repository to your computer:

```bash
git clone https://github.com/AlexMeisenzahl/arbitrage-bot.git
cd arbitrage-bot
```

### Step 2: Install Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Or if you're using Python 3:

```bash
pip3 install -r requirements.txt
```

### Step 3: Configure the Bot

Copy the example configuration and customize it:

```bash
cp config.example.yaml config.yaml
```

Open `config.yaml` in a text editor and verify these settings:

```yaml
# Safety settings (DO NOT CHANGE)
paper_trading: true        # ✓ Must be true
kill_switch: false         # ✓ Should be false to run

# Trading parameters
max_trade_size: 10        # Max $ per trade (paper money)
min_profit_margin: 0.02   # Minimum 2% profit to attempt trade

# Live API settings (NEW!)
polymarket:
  api:
    enabled: true          # Set to true for live data
    timeout: 10
    retry_attempts: 3
  
  market_filters:
    min_liquidity: 1000   # Filter by liquidity
    min_volume_24h: 5000  # Filter by volume

# Optional: Filter by specific markets
markets_to_watch: []      # Leave empty for all markets
# Or specify keywords: ['Bitcoin', 'Ethereum', 'Election']

# Notifications (NEW!)
notifications:
  desktop:
    enabled: true
    event_types:
      trade: true
      opportunity: true
      error: true
  
  rate_limiting:
    enabled: true
    max_per_hour: 20
  
  quiet_hours:
    enabled: false
    start_time: "23:00"
    end_time: "07:00"
```

See [config.example.yaml](config.example.yaml) for all available options.

👉 **[Full API Integration Guide](API_INTEGRATION.md)**

**DO NOT change `paper_trading` to false!**

## 🎮 How to Run the Bot

### Start the Bot

Run this command in your terminal:

```bash
python bot.py
```

Or on some systems:

```bash
python3 bot.py
```

### You Should See

A live dashboard that looks like this:

```
╔════════════════════════════════════════════════════════════════╗
║           POLYMARKET ARBITRAGE BOT - PAPER TRADING             ║
║                    Status: ✓ RUNNING                           ║
╠════════════════════════════════════════════════════════════════╣
║ Runtime: 0h 2m                     Last Update: 10:23:45       ║
╠════════════════════════════════════════════════════════════════╣
║ CONNECTION                                                     ║
║ Status: ✓ Healthy                  Response Time: 120ms       ║
╚════════════════════════════════════════════════════════════════╝
```

### Stop the Bot

Press `Ctrl+C` (or `Cmd+C` on Mac) to stop the bot gracefully.

## 📊 Understanding the Dashboard

### Status Indicators

- **✓ (Green checkmark)**: Everything is working correctly
- **⚠️ (Yellow warning)**: Something needs attention (like rate limits)
- **🚨 (Red alert)**: Critical issue (stopped or error)

### Dashboard Sections

1. **Header**: Shows bot status (RUNNING or PAUSED)

2. **Runtime & Last Update**: 
   - How long the bot has been running
   - When the dashboard was last refreshed

3. **CONNECTION**:
   - Connection status to Polymarket API
   - Response time (lower is better)
   - Last health check time

4. **API RATE LIMIT**:
   - How many API requests you've used
   - Progress bar showing usage percentage
   - Time until rate limit resets

5. **TRADING ACTIVITY**:
   - Opportunities Found: Number of arbitrage opportunities detected
   - Paper Trades Executed: Number of simulated trades
   - Paper Profit: Total profit from paper trades

6. **LATEST ACTIVITY**:
   - Real-time log of what the bot is doing
   - Shows scanned markets and opportunities found
   - Displays paper trade executions

7. **ALERTS**:
   - Important warnings or errors
   - Shows rate limit warnings
   - Connection issues

## 📁 Log Files

The bot creates several log files in the `logs/` directory:

### logs/trades.csv
Records of all paper trades executed:
```csv
timestamp,market,yes_price,no_price,sum,profit_pct,profit_usd,status
2026-02-05 10:23:35,Trump-wins-2024,0.48,0.49,0.97,3.1,0.60,executed
```

### logs/opportunities.csv
All arbitrage opportunities found (traded or skipped):
```csv
timestamp,market,yes_price,no_price,sum,profit_pct,action_taken
2026-02-05 10:23:35,Trump-wins-2024,0.48,0.49,0.97,3.1,traded
```

### logs/errors.log
Error messages and warnings:
```
[2026-02-05 10:23:30] WARNING: Rate limit at 85%
[2026-02-05 10:25:00] ERROR: Connection timeout - retrying
```

### logs/connection.log
Connection health monitoring:
```
[2026-02-05 10:23:01] ✓ Connection healthy - 120ms
[2026-02-05 10:23:21] ⚠️ Connection slow - 2500ms
```

## ⚙️ Configuration Guide

Edit `config.yaml` to customize bot behavior:

### Trading Controls

```yaml
max_trade_size: 10              # Maximum $ per paper trade
min_profit_margin: 0.02         # Minimum 2% profit to trade
max_trades_per_hour: 10         # Limit trading frequency
```

### Safety Controls

```yaml
paper_trading: true             # MUST be true
kill_switch: false              # Set to true to stop immediately
```

### Market Selection

```yaml
markets_to_watch:               # Markets to monitor
  - "BTC"                       # Add market names here
  - "ETH"
```

### Rate Limits

```yaml
rate_limit_max: 100                   # Max requests per minute
rate_limit_warning_threshold: 0.80    # Warn at 80%
rate_limit_pause_threshold: 0.95      # Pause at 95%
```

## 🔧 Troubleshooting

### Bot Won't Start

**Problem**: `ModuleNotFoundError: No module named 'rich'`
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Problem**: `FileNotFoundError: config.yaml`
**Solution**: Make sure you're in the correct directory with `config.yaml` present

### Connection Errors

**Problem**: Dashboard shows "🚨 Connection timeout"
**Solution**: 
1. Check your internet connection
2. Wait a few seconds - the bot will retry automatically
3. If persistent, the Polymarket API might be down

### Rate Limit Warnings

**Problem**: "⚠️ Rate limit at 85%"
**Solution**: 
- This is normal - the bot will automatically slow down
- The bot pauses automatically at 95%
- Wait for rate limit to reset (shown in dashboard)

### No Opportunities Found

**Problem**: Bot runs but finds no opportunities
**Solution**:
- This is normal! Arbitrage opportunities are rare
- Lower `min_profit_margin` in config.yaml to find more (but smaller) opportunities
- Add more markets to `markets_to_watch` in config.yaml

## ❓ Frequently Asked Questions

### Q: Is this bot safe?
**A:** Yes! It only does paper trading (simulated trades). No real money is involved.

### Q: Can I make real money with this?
**A:** Not with this version. This is for learning only. Real trading requires:
- Authentication with Polymarket
- Real funds deposited
- Much more complex order execution
- Legal and regulatory compliance

### Q: Why am I not finding opportunities?
**A:** Real arbitrage opportunities are rare because:
- Markets are efficient - others find them quickly
- This is a simplified demo version
- The bot uses simulated prices for demonstration

### Q: How do I stop the bot?
**A:** Press `Ctrl+C` (or `Cmd+C` on Mac). Or set `kill_switch: true` in config.yaml.

### Q: Can I run this 24/7?
**A:** Yes, but:
- It's paper trading, so there's no real benefit
- Watch for rate limits if running long-term
- Your computer needs to stay on

### Q: What's the difference between paper and real trading?
**A:** 
- **Paper trading**: Simulated, no real money, safe to learn
- **Real trading**: Uses real money, requires authentication, has risk

## 🌐 Live Market Data Integration

### Overview

The bot now supports **live, real-time data from the Polymarket API**! This allows you to test strategies against actual market conditions while remaining in safe paper trading mode.

## 🏆 Strategy Competition System

The bot now includes a comprehensive **Strategy Competition System** that runs multiple trading strategies simultaneously and tracks which ones perform best.

### Competition Features:

- **📊 Real-Time Leaderboard** - View strategy rankings updated every second
  - Access at: http://localhost:5000/leaderboard
  - Medal rankings (🥇🥈🥉) for top 3 performers
  - Status indicators: ✅ WINNING, ⚠️ MARGINAL, ❌ LOSING

- **🎯 Performance Tracking** - Comprehensive metrics for each strategy
  - Portfolio value and return percentage
  - Sharpe ratio (risk-adjusted returns)
  - Win rate and total trades
  - Max drawdown monitoring

- **🛡️ Safety Controls**
  - **Emergency Kill Switch** - Stop all trading immediately
  - **Auto-Disable System** - Automatically stops failing strategies
  - **Strategy Health Monitoring** - Continuous performance checking
  - **Data Pipeline Monitoring** - Real-time data quality validation

- **📈 Strategy Graduation System** - Safe progression from paper to live trading
  - 5 stages: Backtest → Paper → Micro Live → Mini Live → Full Live
  - Strict requirements at each stage
  - Automatic eligibility checking
  - See [STRATEGY_GRADUATION.md](STRATEGY_GRADUATION.md) for details

- **💰 Capital Allocation** - Intelligent capital distribution
  - Top strategy gets 70% of capital
  - Second best gets 20%
  - Third best gets 10%
  - Weekly reallocation based on performance

### Quick Access:

- **Main Dashboard:** http://localhost:5000
- **Strategy Leaderboard:** http://localhost:5000/leaderboard
- **API Documentation:** See [USER_GUIDE.md](USER_GUIDE.md)

👉 **[Complete Testing Guide](TESTING_GUIDE.md)** - Step-by-step testing checklist
👉 **[User Guide](USER_GUIDE.md)** - How to use all features
👉 **[Strategy Graduation](STRATEGY_GRADUATION.md)** - Safe path to live trading

---

### Features

- **Real Market Data**: Fetches live markets from Polymarket
- **Actual Prices**: Uses real bid/ask spreads from the order book
- **Smart Caching**: Reduces API calls with 15-second cache
- **Rate Limiting**: Respects API limits (60 requests/minute)
- **Market Filtering**: Focus on specific categories and liquidity levels
- **Fallback Mode**: Automatically uses simulated data if API fails

### Configuration

Edit `config.yaml` (or `config.example.yaml`) to configure live data:

```yaml
polymarket:
  use_live_data: true              # Enable live data (set false for testing)
  api_base_url: "https://gamma-api.polymarket.com"
  clob_api_url: "https://clob.polymarket.com"
  rate_limit_per_minute: 60        # Max API requests per minute
  cache_duration_seconds: 15       # Cache market data for this long
  
  markets:
    max_markets: 50                # Maximum markets to monitor
    min_liquidity: 1000            # Minimum $ liquidity
    categories:                    # Categories to include (empty = all)
      - "Crypto"
      - "Politics"
      - "Sports"
      - "Business"
    exclude_keywords:              # Skip markets with these keywords
      - "test"
      - "demo"
```

### How It Works

1. **Market Fetching**: Bot fetches active markets from Polymarket's Gamma API
2. **Filtering**: Applies category, liquidity, and keyword filters
3. **Price Updates**: Gets real-time bid/ask prices from CLOB API
4. **Opportunity Detection**: Finds arbitrage opportunities in real markets
5. **Paper Trading**: Simulates trades without risking real money

### API Endpoints Used

The bot uses these **public Polymarket APIs** (no authentication required):

- **Markets**: `https://gamma-api.polymarket.com/markets`
  - Returns list of active prediction markets
  
- **Events**: `https://gamma-api.polymarket.com/events`
  - Returns market metadata and details
  
- **Prices**: `https://clob.polymarket.com/price`
  - Returns current bid/ask prices from order book

### Rate Limits & Best Practices

**Rate Limits:**
- Default: 60 requests per minute
- Bot automatically tracks and respects limits
- Implements exponential backoff on errors

**Best Practices:**
1. Use caching (enabled by default)
2. Don't set cache duration too low (< 10 seconds)
3. Limit `max_markets` to reasonable number (50-100)
4. Monitor rate limit warnings in dashboard

### Troubleshooting API Issues

**Problem: "Failed to fetch live markets"**
- **Solution**: Check internet connection, API may be temporarily down
- **Fallback**: Bot automatically uses simulated data

**Problem: "Rate limited"**
- **Solution**: Increase `cache_duration_seconds` in config
- **Solution**: Decrease `max_markets` to reduce API calls
- **Fallback**: Bot waits for rate limit to reset

**Problem: API returns empty data**
- **Cause**: No active markets match your filters
- **Solution**: Broaden category filters or reduce `min_liquidity`

**Problem: Connection timeout**
- **Cause**: Slow network or API latency
- **Solution**: Increase `api_timeout_seconds` in config

### Testing Live Data

To verify live data is working:

1. Start bot with `use_live_data: true`
2. Check dashboard for real market names (not "BTC-above-100k")
3. Verify prices change over time (not static)
4. Check logs for "Fetching markets from" messages

### Switching Between Live and Simulated Data

**Use Live Data** (recommended):
```yaml
polymarket:
  use_live_data: true
```

**Use Simulated Data** (for testing):
```yaml
polymarket:
  use_live_data: false
```

Simulated mode is useful for:
- Testing bot logic without API calls
- Development and debugging
- When API is down or unavailable

### Security Notes

- ✅ **No authentication required** for public data
- ✅ **Read-only access** - bot only fetches data
- ✅ **No wallet needed** - paper trading only
- ✅ **No API keys** - public endpoints are free
- ✅ **Privacy preserved** - no personal data sent

**Important**: Even with live data, **paper trading remains enabled**. Real money is never at risk.

---

## 📚 Learning Resources

To understand arbitrage trading better:

1. **Arbitrage**: https://www.investopedia.com/terms/a/arbitrage.asp
2. **Prediction Markets**: https://polymarket.com/
3. **Risk Management**: Always important in real trading

## 🔐 Security & Privacy

- This bot does NOT require any API keys or authentication
- It does NOT access your wallet or funds
- It only reads public market data
- All trades are simulated (paper trading)

## 🚦 Next Steps (After Paper Trading)

If you want to explore real trading (advanced users only):

1. **Never start with real money** - paper trade for weeks/months first
2. **Understand the risks** - you can lose money
3. **Learn about**:
   - Polymarket API authentication
   - Order book mechanics
   - Slippage and fees
   - Gas costs (on blockchain)
   - Legal requirements in your jurisdiction

4. **Start small** if you eventually trade real money
5. **Use proper risk management**

## 📝 Project Structure

```
arbitrage-bot/
├── config.yaml          # User configuration
├── bot.py              # Main entry point with dashboard
├── monitor.py          # Price monitoring and API handling
├── detector.py         # Arbitrage opportunity detection
├── paper_trader.py     # Paper trading simulator
├── logger.py           # Logging system
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── logs/              # Auto-created log directory
    ├── trades.csv
    ├── opportunities.csv
    ├── errors.log
    └── connection.log
```

## 🤝 Support

If you encounter issues:

1. Check this README's Troubleshooting section
2. Review the log files in `logs/` directory
3. Make sure all dependencies are installed
4. Verify Python version is 3.8 or newer

## ⚖️ License & Disclaimer

This software is for educational purposes only. The authors are not responsible for any financial losses. Always do your own research and never trade with money you can't afford to lose.

**USE AT YOUR OWN RISK**

---

**Remember: This is PAPER TRADING only. Learn, experiment, and understand arbitrage in a safe environment!** 🎓📈
