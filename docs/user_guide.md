# User Guide

Complete guide for using the Market Strategy Testing Bot.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Monitoring Performance](#monitoring-performance)
4. [Configuring Strategies](#configuring-strategies)
5. [Setting Up Notifications](#setting-up-notifications)
6. [Understanding Analytics](#understanding-analytics)
7. [Exporting Data](#exporting-data)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Time Setup

1. **Install the bot** (see README.md for installation)
2. **Copy configuration**:
   ```bash
   cp config.example.yaml config.yaml
   ```
3. **Start the dashboard**:
   ```bash
   python start_dashboard.py
   ```
4. **Open browser**: http://localhost:5000

### Understanding Paper Trading

⚠️ **Important:** This bot uses **paper trading** by default.

- All trades are simulated
- No real money is involved
- Perfect for learning and testing
- Data is real, execution is simulated

---

## Dashboard Overview

### Main Dashboard (/)

**Top Metrics:**
- **Total P&L**: Your cumulative profit/loss
- **Win Rate**: Percentage of profitable trades
- **Active Trades**: Currently open positions
- **Today's P&L**: Profit/loss for current day

**Charts:**
- **Cumulative P&L**: Your profit over time
- **Daily P&L**: Daily performance breakdown
- **Strategy Performance**: Compare strategy results

**Recent Activity:**
- Latest trades
- New opportunities
- System alerts

### Navigation

- **🏠 Dashboard**: Main overview
- **💎 Opportunities**: View detected opportunities
- **📊 Analytics**: Detailed performance metrics
- **⚙️ Settings**: Configure bot and notifications
- **🔔 Notifications**: Manage alerts
- **📥 Export**: Download data

---

## Monitoring Performance

### Key Metrics to Watch

**Total P&L**
- Your overall profit or loss
- Green = profit, Red = loss
- Target: Positive and growing

**Win Rate**
- Percentage of profitable trades
- Good: >60%
- Excellent: >75%

**Average Profit**
- Average profit per trade
- Higher is better
- Compare across strategies

**Sharpe Ratio**
- Risk-adjusted return
- >1.0 = Good
- >2.0 = Excellent
- >3.0 = Outstanding

**Max Drawdown**
- Largest peak-to-trough decline
- Lower is better
- Target: <10%

### Performance Dashboard

Access: Dashboard → Analytics

View:
- Strategy comparison
- Time-based analysis
- Risk metrics
- Opportunity analysis

---

## Configuring Strategies

### Available Strategies

1. **Polymarket Arbitrage**
   - Finds price discrepancies on Polymarket
   - Buy YES + NO for less than $1.00
   - Most common strategy

2. **Crypto-Polymarket Arbitrage**
   - Exploits crypto price differences
   - Uses real-time crypto prices
   - Requires market correlation

3. **Cross-Exchange Arbitrage**
   - Compares prices across exchanges
   - Advanced strategy
   - Higher profit potential

### Enabling/Disabling Strategies

1. Go to **Settings** → **Strategies**
2. Toggle strategy on/off
3. Adjust profit thresholds
4. Save changes

### Strategy Settings

**Min Profit Margin:**
- Minimum profit to execute trade
- Recommended: 2-3%
- Lower = more trades, higher risk

**Confidence Threshold:**
- Minimum confidence level
- Options: Low, Medium, High, Very High
- Higher = fewer but safer trades

---

## Setting Up Notifications

### Notification Channels

**Desktop Notifications:**
- Built-in system notifications
- No setup required
- Automatic for important events

**Email Notifications:**
1. Go to Settings → Notifications
2. Click "Email" tab
3. Enter SMTP details:
   - Server: smtp.gmail.com
   - Port: 587
   - Username: your-email@gmail.com
   - Password: app-specific password
4. Test connection
5. Enable

**Telegram Notifications:**
1. Create Telegram bot (@BotFather)
2. Get bot token
3. Get your chat ID (@userinfobot)
4. Enter in Settings → Notifications
5. Test connection
6. Enable

**Discord Notifications:**
1. Create webhook in Discord server
2. Copy webhook URL
3. Enter in Settings → Notifications
4. Test connection
5. Enable

### Notification Types

You can configure notifications for:

- **Opportunities**: When new arbitrage found
- **Trades**: When trade executes
- **Price Alerts**: Crypto price thresholds
- **Risk Alerts**: When risk limits breached
- **System**: Bot status changes
- **Performance**: Daily/weekly summaries

### Quiet Hours

Prevent notifications during sleep:

1. Go to Settings → Notifications
2. Enable "Quiet Hours"
3. Set start time (e.g., 10 PM)
4. Set end time (e.g., 8 AM)
5. Select timezone
6. Save

---

## Understanding Analytics

### Strategy Analytics

**Access:** Dashboard → Analytics → Strategy Performance

**Metrics per strategy:**
- Total trades
- Win rate
- Average profit
- Total P&L
- Sharpe ratio
- Max drawdown

**Use this to:**
- Identify best-performing strategies
- Disable underperforming strategies
- Adjust profit thresholds

### Time Analytics

**Access:** Dashboard → Analytics → Time Analysis

**Shows:**
- Best performing hours
- Best performing days
- Seasonal patterns

**Use this to:**
- Schedule bot operation
- Optimize trading hours
- Understand market patterns

### Risk Metrics

**Access:** Dashboard → Analytics → Risk Metrics

**Key metrics:**
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk focus
- **Max Drawdown**: Worst decline
- **Value at Risk (VaR)**: Potential loss
- **Conditional VaR**: Expected loss in worst case

**What they mean:**
- Higher Sharpe/Sortino = Better risk-adjusted returns
- Lower drawdown = More stable performance
- Lower VaR = Less risk exposure

---

## Exporting Data

### Export Options

**CSV Export (Trades):**
1. Go to Dashboard → Export
2. Select date range
3. Click "Export Trades CSV"
4. Open in Excel/Google Sheets

**JSON Export (Settings):**
1. Go to Settings → Export
2. Click "Export Settings"
3. Saves all configuration
4. Use for backup or sharing

**Analytics PDF (Coming Soon):**
- Full performance report
- Charts and metrics
- Professional format

### What to Export

**For tax purposes:**
- All completed trades
- Full year date range
- Include timestamps

**For analysis:**
- Strategy-specific data
- Custom date ranges
- Filter by profit/loss

**For backup:**
- Settings JSON
- All trades CSV
- Configuration files

---

## Troubleshooting

### Bot Not Finding Opportunities

**Possible causes:**
1. Profit margin too high
2. Markets inactive
3. API issues

**Solutions:**
1. Lower min_profit_margin to 1-2%
2. Check market_filters in config
3. Run health check: http://localhost:5000/api/health
4. Check logs directory

### Notifications Not Working

**Email:**
1. Verify SMTP settings
2. Use app-specific password (Gmail)
3. Check spam folder
4. Test connection in settings

**Telegram:**
1. Verify bot token
2. Ensure you've started chat with bot
3. Check chat ID is correct
4. Test in settings

### Dashboard Won't Load

1. Check if service is running:
   ```bash
   ps aux | grep python
   ```
2. Check logs:
   ```bash
   tail -f logs/dashboard.log
   ```
3. Restart dashboard:
   ```bash
   python start_dashboard.py
   ```

### High CPU/Memory Usage

1. Reduce WebSocket connections
2. Lower refresh rate
3. Disable unused strategies
4. Clear old log files

### API Errors

1. Check health endpoint
2. Verify API keys (if used)
3. Check rate limits
4. Test internet connection

---

## Best Practices

### Daily Routine

1. **Morning**: Check overnight performance
2. **Midday**: Review active opportunities
3. **Evening**: Check total P&L
4. **Weekly**: Export and analyze data

### Optimization Tips

1. **Start Conservative**
   - Higher profit margins
   - Fewer strategies
   - Lower trade limits

2. **Monitor and Adjust**
   - Watch performance weekly
   - Adjust based on results
   - Keep detailed notes

3. **Regular Maintenance**
   - Update software monthly
   - Backup configuration weekly
   - Review logs regularly

4. **Safety First**
   - Keep paper_trading: true
   - Test before enabling features
   - Use kill switch if needed

### Common Mistakes to Avoid

❌ **Don't:**
- Set profit margins too low
- Enable all strategies at once
- Ignore risk metrics
- Skip configuration validation
- Disable kill switch
- Turn off paper trading

✅ **Do:**
- Start with defaults
- Enable strategies gradually
- Monitor risk closely
- Validate config changes
- Keep emergency stop ready
- Stay in paper trading mode

---

## Getting Help

### Resources

1. **Documentation**
   - This user guide
   - Configuration guide
   - API documentation
   - Deployment guide

2. **Logs**
   - Dashboard logs: `logs/dashboard.log`
   - Bot logs: `logs/bot.log`
   - Check for errors and warnings

3. **Health Checks**
   - Run: http://localhost:5000/api/health
   - Check all services
   - Verify API connectivity

4. **Community**
   - GitHub Issues
   - Documentation wiki
   - Developer guide

### Reporting Issues

When reporting issues, include:

1. **Error message** (exact text)
2. **Steps to reproduce**
3. **Configuration** (remove sensitive data)
4. **Logs** (relevant sections)
5. **System info** (OS, Python version)
6. **Screenshots** (if UI issue)

---

## Next Steps

1. ✅ Complete initial setup
2. ✅ Start dashboard and explore
3. ✅ Configure notifications
4. ✅ Enable one strategy
5. ✅ Monitor for 24 hours
6. ✅ Review analytics
7. ✅ Adjust settings
8. ✅ Enable more strategies gradually

**Remember:** This is a learning tool. Take your time, understand the metrics, and always use paper trading mode.

Happy trading! 🚀
