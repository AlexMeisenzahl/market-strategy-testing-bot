# Polymarket Arbitrage Bot - Paper Trading Edition

A complete, production-ready arbitrage bot for Polymarket with real-time dashboard and comprehensive safety features. **PAPER TRADING ONLY - NO REAL MONEY IS USED.**

## 🎯 What This Bot Does (In Plain English)

This bot watches Polymarket prediction markets and looks for arbitrage opportunities. An arbitrage opportunity happens when you can buy BOTH the "YES" and "NO" contracts for less than $1.00 combined. Since one of them will always pay out $1.00, you make a guaranteed profit.

**Example:**
- YES contract costs $0.48
- NO contract costs $0.49
- Total cost: $0.97
- One will pay out: $1.00
- Your profit: $0.03 (3% return)

This bot finds these opportunities automatically and simulates trades (paper trading) so you can learn how arbitrage works without risking any money.

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

### Step 3: Verify Configuration

Open `config.yaml` in a text editor and verify these settings:

```yaml
paper_trading: true        # ✓ Should be true
kill_switch: false         # ✓ Should be false to run
max_trade_size: 10        # Max $ per trade (paper money)
min_profit_margin: 0.02   # Minimum 2% profit to attempt trade
```

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
