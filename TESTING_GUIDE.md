# TESTING CHECKLIST

## Phase 1: Initial Setup (Day 1)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure API keys (paper trading mode)
- [ ] Copy `config.example.yaml` to `config.yaml`
- [ ] Verify `paper_trading: true` in config
- [ ] Verify Polymarket connection
- [ ] Run database migrations (databases auto-initialize)
- [ ] Start dashboard: `python start_dashboard.py`
- [ ] Verify dashboard loads at http://localhost:5000

## Phase 2: Data Validation (Days 2-3)
- [ ] Start bot: `python bot.py`
- [ ] Verify historical data collection
- [ ] Verify real-time data flowing
- [ ] Check data accuracy in logs
- [ ] Verify WebSocket connection stable
- [ ] Check data pipeline health at `/api/emergency/health/summary`

## Phase 3: Strategy Backtesting (Days 4-7)
- [ ] Run backtest: Polymarket Arbitrage
- [ ] Run backtest: Crypto Momentum
- [ ] Run backtest: Mean Reversion
- [ ] Run backtest: Market Sentiment
- [ ] Run backtest: Volume Surge
- [ ] Run backtest: Time-Based
- [ ] Identify strategies with Sharpe > 1.5
- [ ] Review backtest results in dashboard

## Phase 4: Paper Trading (Days 8-37 = 30 days)
### Setup
- [ ] Enable ALL strategies in paper mode via dashboard
- [ ] Verify virtual capital: $10,000 per strategy
- [ ] Confirm NO real money being used (check config: `paper_trading: true`)
- [ ] Access leaderboard at http://localhost:5000/leaderboard

### Daily Monitoring (10 min/day)
- [ ] Check strategy competition leaderboard
- [ ] Review top 3 performers
- [ ] Monitor for auto-disabled strategies
- [ ] Check data pipeline health
- [ ] Review any alerts/notifications
- [ ] Record daily observations

### End of Phase (Day 37)
- [ ] Check graduation eligibility for all strategies
- [ ] Identify strategies ready for micro live
- [ ] Review 30-day performance reports
- [ ] Verify at least ONE strategy meets graduation criteria

## Phase 5: Micro Live Trading (Days 38-44 = 7 days) ⚠️
**ONLY IF paper trading successful!**

### Prerequisites
- [ ] At least ONE strategy graduated from paper trading
- [ ] Strategy meets requirements:
  - [ ] Return > 5%
  - [ ] Sharpe ratio > 1.5
  - [ ] Win rate > 55%
  - [ ] Max drawdown < 15%
  - [ ] Total trades >= 50
- [ ] Data pipeline 100% healthy for past 7 days
- [ ] Emergency kill switch tested successfully
- [ ] Polymarket account funded with $50

### Setup
- [ ] Graduate best strategy to micro live
- [ ] Set allocated capital to $50
- [ ] Verify trading stage = 'micro_live'
- [ ] Enable strategy for live trading
- [ ] Monitor first live trade closely

### Daily Monitoring
- [ ] Check actual vs expected performance
- [ ] Monitor slippage and execution quality
- [ ] Verify trades execute correctly
- [ ] Check balance/positions match expectations
- [ ] Record any issues

## Phase 6: Mini Live Trading (Days 45-58 = 14 days) ⚠️⚠️
**ONLY IF micro live successful!**

### Prerequisites
- [ ] Micro live trading completed successfully
- [ ] Positive return in micro live
- [ ] No critical issues during micro live
- [ ] Polymarket account funded with additional $150 (total $200)

### Setup
- [ ] Graduate strategy to mini live
- [ ] Set allocated capital to $200
- [ ] Continue monitoring

## Phase 7: Full Live Trading (Day 59+) ⚠️⚠️⚠️
**ONLY IF mini live successful!**

### Prerequisites
- [ ] Mini live trading completed successfully
- [ ] Consistent positive returns
- [ ] All systems stable
- [ ] Polymarket account funded with $1000+

### Setup
- [ ] Graduate strategy to full live
- [ ] Set allocated capital to $1000+
- [ ] Implement ongoing monitoring plan

---

## RED FLAGS - STOP IMMEDIATELY IF:

❌ **Data Issues**
- Data pipeline offline > 1 minute
- Stale data (> 10 seconds old)
- Price discrepancies > 1%
- WebSocket disconnects frequently

❌ **Strategy Issues**
- Strategy loses > 10% in one day
- 3+ strategies auto-disabled same day
- Win rate drops below 40%
- Max drawdown exceeds 20%

❌ **System Issues**
- Trade verification failures
- Unexpected errors in logs
- Bot crashes or restarts frequently
- Database errors

❌ **Execution Issues**
- Trades not executing as expected
- Slippage > 5%
- Live performance < 80% of paper performance

---

## Emergency Procedures

### If Kill Switch Needed:
1. Navigate to dashboard
2. Click "🚨 EMERGENCY STOP" button
3. Confirm activation
4. All strategies will be immediately disabled
5. Review logs to understand what triggered the issue
6. DO NOT reactivate until issue is resolved

### If Strategy Auto-Disabled:
1. Check disable reason in dashboard
2. Review strategy performance metrics
3. Analyze what went wrong
4. Fix underlying issue
5. Re-enable manually only after fix confirmed

### If Data Pipeline Fails:
1. Check internet connection
2. Verify Polymarket API status
3. Check WebSocket connection
4. Review data monitor logs
5. Restart bot if necessary

---

## Success Criteria

### Paper Trading Success:
- ✅ At least 1 strategy with > 5% return
- ✅ Sharpe ratio > 1.5
- ✅ Win rate > 55%
- ✅ Max drawdown < 15%
- ✅ 50+ trades executed
- ✅ 30 days completed without critical issues

### Micro Live Success:
- ✅ Positive return
- ✅ No critical errors
- ✅ Execution quality good
- ✅ 7 days completed

### Mini Live Success:
- ✅ Return > 4%
- ✅ Sharpe > 1.2
- ✅ 20+ trades
- ✅ 14 days completed

---

## Checklist Tracking

| Phase | Start Date | End Date | Status | Notes |
|-------|-----------|----------|--------|-------|
| Setup | | | | |
| Data Validation | | | | |
| Backtesting | | | | |
| Paper Trading | | | | |
| Micro Live | | | | |
| Mini Live | | | | |
| Full Live | | | | |

---

## Important Reminders

1. **NEVER** skip phases - follow the progression strictly
2. **ALWAYS** verify paper_trading=true before starting
3. **MONITOR** daily during paper trading (even if brief)
4. **DOCUMENT** all issues and observations
5. **BE PATIENT** - rushing leads to losses
6. **TRUST THE PROCESS** - the graduation system is designed for safety

---

## Support and Questions

If you encounter issues:
1. Check logs in `/logs` directory
2. Review dashboard error messages
3. Check GitHub issues
4. Consult README.md and other documentation

Remember: This bot is for testing strategies safely. Take your time and follow the process.
