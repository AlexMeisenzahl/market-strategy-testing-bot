# User Guide - Market Strategy Testing Bot

## Quick Start

1. **Start the Dashboard:**
   ```bash
   python start_dashboard.py
   ```
   Access at: http://localhost:5000

2. **Start the Bot:**
   ```bash
   python bot.py
   ```

3. **Access Key Features:**
   - Main Dashboard: http://localhost:5000
   - Leaderboard: http://localhost:5000/leaderboard
   - Analytics: http://localhost:5000/analytics
   - Settings: http://localhost:5000/settings

---

## Dashboard Overview

### Main Dashboard
- **Real-time Performance:** Portfolio value, P&L, return %
- **Active Opportunities:** Current trading opportunities
- **Recent Trades:** Trade history
- **Market Data:** Live crypto prices and Polymarket markets

### Strategy Leaderboard
Shows all strategies competing in real-time:
- **Rankings:** Ordered by performance
- **Metrics:** Value, Return %, Sharpe Ratio, Win Rate
- **Status:** Winning ✅, Marginal ⚠️, or Losing ❌
- **Charts:** Equity curves comparison

---

## Understanding the Leaderboard

### Medals
- 🥇 **Gold:** #1 strategy
- 🥈 **Silver:** #2 strategy
- 🥉 **Bronze:** #3 strategy

### Status Indicators
- **✅ WINNING:** Return > 5%, performing excellently
- **⚠️ MARGINAL:** Return > 0% but < 5%, acceptable
- **❌ LOSING:** Negative return, needs attention

### Metrics Explained

**Current Value:** Total portfolio value including cash and positions

**Return %:** Total profit/loss as percentage
- Positive (green) = profitable
- Negative (red) = losing money

**Sharpe Ratio:** Risk-adjusted return
- \> 2.0 = Excellent
- 1.5 - 2.0 = Good
- 1.0 - 1.5 = Acceptable
- < 1.0 = Poor

**Trades:** Total number of trades executed

**Win Rate:** Percentage of profitable trades
- \> 60% = Excellent
- 55-60% = Good
- 50-55% = Acceptable
- < 50% = Poor

---

## Strategy Management

### Viewing Strategy Details
1. Go to leaderboard
2. Click on strategy name
3. View detailed metrics and charts

### Pausing a Strategy
To temporarily stop a strategy without disabling:

**Via Dashboard:**
1. Navigate to strategy
2. Click "Pause Strategy"
3. Enter reason (optional)
4. Confirm

**Via API:**
```bash
curl -X POST http://localhost:5000/api/emergency/strategy/pause \
  -H "Content-Type: application/json" \
  -d '{"strategy_name": "Polymarket Arbitrage", "reason": "Reviewing logic"}'
```

### Resuming a Strategy
1. Go to paused strategy
2. Click "Resume Strategy"
3. Confirm

### Enabling/Disabling Strategies

**Enable:**
```bash
curl -X POST http://localhost:5000/api/emergency/strategy/enable \
  -H "Content-Type: application/json" \
  -d '{"strategy_name": "Polymarket Arbitrage"}'
```

**Disable:**
```bash
curl -X POST http://localhost:5000/api/emergency/strategy/disable \
  -H "Content-Type: application/json" \
  -d '{"strategy_name": "Polymarket Arbitrage", "reason": "Underperforming"}'
```

---

## Data Health Monitoring

### Indicators

**WebSocket Status:**
- 🟢 **Healthy:** Receiving data normally
- 🟡 **Degraded:** Slow updates or intermittent
- 🔴 **Down:** No data being received

**API Status:**
- 🟢 **Healthy:** Response times < 2 seconds
- 🟡 **Degraded:** Response times 2-5 seconds
- 🔴 **Down:** Not responding or > 5 seconds

**Data Freshness:**
- 🟢 **Fresh:** < 5 seconds old
- 🟡 **Aging:** 5-10 seconds old
- 🔴 **Stale:** > 10 seconds old

### Checking Data Health

**Via Dashboard:**
- Look at header status indicators
- Click for detailed health information

**Via API:**
```bash
curl http://localhost:5000/api/emergency/health/summary
```

---

## Emergency Controls

### Kill Switch 🚨

**When to Use:**
- Critical system error
- Unexpected market behavior
- Need to immediately stop all trading
- Data pipeline failure
- Strategy behaving erratically

**How to Activate:**

**Via Dashboard:**
1. Locate red "🚨 EMERGENCY STOP" button (usually at top)
2. Click button
3. Confirm in dialog box
4. Optionally choose to close positions
5. All strategies will be immediately disabled

**Via API:**
```bash
curl -X POST http://localhost:5000/api/emergency/kill-switch/activate \
  -H "Content-Type: application/json" \
  -d '{"reason": "Data pipeline failure", "close_positions": false}'
```

**What Happens:**
1. All strategies immediately disabled
2. No new trades will be placed
3. Pending orders cancelled (when implemented)
4. Positions kept open (unless close_positions=true)
5. Bot continues running but won't trade

**Deactivating:**
```bash
curl -X POST http://localhost:5000/api/emergency/kill-switch/deactivate \
  -H "Content-Type: application/json" \
  -d '{"admin_password": "optional"}'
```

⚠️ **Important:** After deactivation, strategies remain disabled. You must manually review and re-enable each strategy.

---

## Strategy Graduation

### Overview
Strategies progress through 5 stages:
1. **Backtest** (7 days, $10K virtual)
2. **Paper** (30 days, $10K virtual)
3. **Micro Live** (7 days, $50 real)
4. **Mini Live** (14 days, $200 real)
5. **Full Live** ($1000+ real)

### Checking Eligibility

**Via Dashboard:**
1. Go to strategy page
2. View "Graduation Status" section
3. See checklist of requirements

**Via API:**
```bash
curl http://localhost:5000/api/graduation/check/Polymarket%20Arbitrage
```

### Graduating a Strategy

**Via Dashboard:**
1. Ensure strategy meets all requirements
2. Click "Graduate to Next Stage" button
3. Review next stage details
4. Confirm graduation

**Important:** Never skip stages. Each stage is crucial for validation.

---

## Auto-Disable System

Strategies are automatically disabled if they:
- Lose > 10% in one day
- Have 5 consecutive losses
- Max drawdown > 20%
- Win rate < 40% (after 20+ trades)

**Viewing Auto-Disabled Strategies:**
```bash
curl http://localhost:5000/api/emergency/health/summary
```

Look for `auto_disabled` count.

**Re-enabling:**
1. Review why it was disabled
2. Fix the underlying issue
3. Manually re-enable via dashboard or API
4. Monitor closely after re-enabling

---

## Performance Tracking

### Real-Time Updates
- Leaderboard updates every 5 seconds
- Performance snapshots taken every second
- Hourly snapshots saved to database

### Historical Data
View past performance:
```bash
curl http://localhost:5000/api/leaderboard/performance/Polymarket%20Arbitrage?hours=24
```

Returns 24 hours of performance data for charts.

---

## Notifications

### Alert Types
- Strategy disabled (auto or manual)
- Kill switch activated
- Graduation eligibility achieved
- Data pipeline issues
- Performance milestones

### Configuration
1. Go to Settings page
2. Navigate to Notifications section
3. Configure alert preferences
4. Set up notification channels (email, etc.)

---

## Tips for Success

### Daily Routine (5-10 minutes)
1. Check leaderboard rankings
2. Review any auto-disabled strategies
3. Verify data health indicators
4. Check for graduation opportunities
5. Review recent trades

### Weekly Routine (30 minutes)
1. Analyze top 3 performers
2. Review all strategy metrics
3. Check for patterns in failures
4. Assess capital allocation
5. Plan adjustments if needed

### Monthly Routine (1-2 hours)
1. Comprehensive performance review
2. Graduate eligible strategies
3. Adjust strategy parameters if needed
4. Review and improve documentation
5. Backup database and logs

---

## Troubleshooting

### Bot Not Trading
1. Check kill switch status
2. Verify strategies are enabled
3. Check data pipeline health
4. Review logs for errors
5. Ensure markets have liquidity

### Dashboard Not Loading
1. Verify dashboard is running: `python start_dashboard.py`
2. Check port 5000 is available
3. Review dashboard logs
4. Try different browser

### Data Not Updating
1. Check WebSocket connection
2. Verify API connectivity
3. Check internet connection
4. Review data monitor status
5. Restart bot if necessary

### Strategy Underperforming
1. Review recent market conditions
2. Check if strategy logic still valid
3. Compare paper vs live performance
4. Consider pausing while investigating
5. May need to disable if consistently failing

---

## API Reference

### Leaderboard
- `GET /api/leaderboard/` - Get current rankings
- `GET /api/leaderboard/summary` - Competition summary
- `GET /api/leaderboard/performance/<name>?hours=24` - Historical data

### Emergency Controls
- `GET /api/emergency/kill-switch/status` - Check kill switch
- `POST /api/emergency/kill-switch/activate` - Activate kill switch
- `POST /api/emergency/kill-switch/deactivate` - Deactivate kill switch
- `POST /api/emergency/strategy/pause` - Pause strategy
- `POST /api/emergency/strategy/resume` - Resume strategy
- `GET /api/emergency/health/summary` - Health summary

---

## Configuration

### Important Settings

**config.yaml:**
```yaml
# Safety
paper_trading: true  # MUST be true for testing
kill_switch: false   # Set to true to disable trading

# Competition
COMPETITION_STARTING_CAPITAL: 10000
COMPETITION_ENABLED: true

# Health Monitoring
MAX_DAILY_LOSS_PCT: 10
MAX_CONSECUTIVE_LOSSES: 5
MAX_DRAWDOWN_PCT: 20
MIN_WIN_RATE: 40

# Data Validation
DATA_FRESHNESS_THRESHOLD: 5  # seconds
PRICE_DISCREPANCY_THRESHOLD: 1.0  # percent
```

---

## Support

For issues or questions:
1. Check logs in `/logs` directory
2. Review this user guide
3. Consult TESTING_GUIDE.md
4. Read STRATEGY_GRADUATION.md
5. Check GitHub repository issues

---

## Safety Reminders

⚠️ **CRITICAL SAFETY RULES:**

1. **ALWAYS** start with paper trading
2. **NEVER** skip graduation stages
3. **VERIFY** paper_trading=true before starting
4. **MONITOR** strategies daily
5. **USE** kill switch if anything seems wrong
6. **DON'T** trade with money you can't afford to lose
7. **TRUST** the auto-disable system
8. **BE PATIENT** - rushing leads to losses

Remember: The goal is safe, methodical testing. Not quick profits.
