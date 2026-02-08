# Strategy Graduation System

## Overview

The Strategy Graduation System is a **safe, methodical approach** to transitioning trading strategies from backtesting to live trading with real money. It ensures strategies are thoroughly tested before risking significant capital.

## The 5 Stages

### 1. BACKTEST (7 days)
**Capital:** $10,000 (virtual)
**Duration:** 7 days minimum
**Purpose:** Test strategy on historical data

**Requirements to Graduate:**
- Backtest must run successfully
- Review historical performance
- Verify strategy logic is sound

### 2. PAPER TRADING (30 days)
**Capital:** $10,000 (virtual)
**Duration:** 30 days minimum
**Purpose:** Test strategy on live market data without real money

**Requirements to Graduate:**
- ✅ 30 days completed
- ✅ Return > 5%
- ✅ Sharpe ratio > 1.5
- ✅ Win rate > 55%
- ✅ Max drawdown < 15%
- ✅ Total trades >= 50

**Why 30 days?**
- Captures multiple market conditions
- Identifies edge cases
- Validates consistency
- Proves strategy isn't just lucky

### 3. MICRO LIVE (7 days)
**Capital:** $50 (REAL MONEY)
**Duration:** 7 days minimum
**Purpose:** First real money test with minimal risk

**Requirements to Graduate:**
- ✅ Return > 3%
- ✅ Sharpe ratio > 1.0
- ✅ 10+ trades executed
- ✅ No critical errors
- ✅ Execution quality verified

**Key Focus:**
- Verify real-world execution
- Check for slippage
- Validate order placement
- Test with actual money

### 4. MINI LIVE (14 days)
**Capital:** $200 (REAL MONEY)
**Duration:** 14 days minimum
**Purpose:** Intermediate testing with moderate capital

**Requirements to Graduate:**
- ✅ Return > 4%
- ✅ Sharpe ratio > 1.2
- ✅ 20+ trades executed
- ✅ Consistent performance
- ✅ 14 days completed

**Key Focus:**
- Scale testing
- Sustained performance
- Risk management validation

### 5. FULL LIVE (Ongoing)
**Capital:** $1,000+ (REAL MONEY)
**Duration:** Ongoing
**Purpose:** Full-scale live trading

**Ongoing Monitoring:**
- Continuous performance tracking
- Auto-disable if failing
- Regular graduation eligibility checks
- Capital reallocation based on performance

---

## Graduation Process

### Checking Eligibility

Via API:
```bash
curl http://localhost:5000/api/graduation/check/<strategy_name>
```

Via Dashboard:
1. Go to Strategies page
2. Click on strategy
3. View "Graduation Status" section
4. See requirements checklist

### Manual Graduation

Via API:
```bash
curl -X POST http://localhost:5000/api/graduation/graduate \
  -H "Content-Type: application/json" \
  -d '{"strategy_name": "Polymarket Arbitrage"}'
```

Via Dashboard:
1. Go to strategy page
2. Click "Graduate to Next Stage" button (when enabled)
3. Confirm graduation
4. Monitor post-graduation performance

### Automatic Graduation

Set `auto_graduation: true` in config to enable automatic progression when requirements are met.

**Recommended:** Keep manual graduation during initial testing.

---

## Capital Allocation Strategy

### Competition-Based Allocation

When multiple strategies are in FULL LIVE:

**Top Strategy:** 70% of capital
**Second Strategy:** 20% of capital
**Third Strategy:** 10% of capital

Example with $10,000 total:
- Best Strategy: $7,000
- Second Best: $2,000
- Third Best: $1,000

This allocation:
- Focuses capital on proven winners
- Diversifies across top performers
- Maintains exposure to promising alternatives

### Reallocation Schedule

**Weekly:** Capital reallocated based on recent performance

**Metrics Used:**
- Return percentage (40% weight)
- Sharpe ratio (30% weight)
- Win rate (20% weight)
- Max drawdown inverted (10% weight)

---

## Safety Guardrails

### Auto-Disable Triggers

A strategy will be **automatically disabled** if:

1. **Daily Loss > 10%**
   - Immediate protection against catastrophic losses
   
2. **5 Consecutive Losses**
   - Indicates strategy may be broken
   
3. **Max Drawdown > 20%**
   - Risk management threshold
   
4. **Win Rate < 40%** (after 20+ trades)
   - Strategy no longer profitable

### Manual Disable

You can manually disable any strategy at any time:

Via Dashboard:
1. Navigate to strategy
2. Click "Disable Strategy"
3. Provide reason
4. Confirm

### Emergency Stop

Use the **Kill Switch** to immediately stop ALL trading:
1. Disables all strategies
2. Cancels pending orders (when implemented)
3. Logs emergency reason
4. Requires manual review before reactivation

---

## Best Practices

### DO:
✅ Follow the 5-stage progression strictly
✅ Wait for ALL requirements to be met before graduating
✅ Monitor strategies daily during paper trading
✅ Start with ONE strategy in live trading
✅ Keep detailed notes on performance
✅ Use the kill switch if something feels wrong

### DON'T:
❌ Skip stages (tempting but dangerous)
❌ Graduate based on just a few days of good performance
❌ Ignore warning signs (consecutive losses, high drawdown)
❌ Let emotions drive decisions
❌ Trade with money you can't afford to lose
❌ Rush the process

---

## Troubleshooting

### Strategy Not Graduating

**Check Requirements:**
```bash
curl http://localhost:5000/api/graduation/check/<strategy_name>
```

Look for which requirement(s) are not met.

### Common Issues:

**Not Enough Trades:**
- Increase market activity
- Lower opportunity threshold
- Wait longer for more trades

**Poor Win Rate:**
- Review strategy logic
- Adjust parameters
- May not be suitable for live trading

**High Drawdown:**
- Reduce position sizes
- Improve risk management
- Reassess strategy viability

### Performance Degradation After Graduation

If performance drops after graduating to live:

1. **Check Slippage:**
   - Compare paper vs live execution
   - Review order fills
   
2. **Verify Execution Quality:**
   - Check order placement speed
   - Review API latency
   
3. **Consider Market Impact:**
   - Larger orders may move market
   - Adjust position sizing

4. **Downgrade If Necessary:**
   - Not a failure to step back
   - Better to be safe than sorry
   - Can re-graduate after improvements

---

## Metrics Explained

### Sharpe Ratio
**Formula:** (Return - Risk Free Rate) / Volatility
**Threshold:** > 1.5 for paper trading
**Meaning:** Risk-adjusted return. Higher is better.
**Good:** > 2.0
**Acceptable:** 1.0 - 2.0
**Poor:** < 1.0

### Win Rate
**Formula:** (Winning Trades / Total Trades) × 100
**Threshold:** > 55% for paper trading
**Meaning:** Percentage of profitable trades
**Good:** > 60%
**Acceptable:** 50-60%
**Poor:** < 50%

### Max Drawdown
**Formula:** (Peak Value - Trough Value) / Peak Value × 100
**Threshold:** < 15% for paper trading
**Meaning:** Largest peak-to-trough decline
**Good:** < 10%
**Acceptable:** 10-15%
**Risky:** 15-20%
**Dangerous:** > 20%

### Return
**Formula:** (Current Value - Starting Value) / Starting Value × 100
**Threshold:** > 5% for paper trading (30 days)
**Meaning:** Total profit/loss percentage
**Annualized:** ~60% if maintained

---

## Example Graduation Timeline

### Realistic Timeline (Minimum)

**Day 1-7:** Backtesting
**Day 8-37:** Paper Trading (30 days)
**Day 38-44:** Micro Live ($50, 7 days)
**Day 45-58:** Mini Live ($200, 14 days)
**Day 59+:** Full Live ($1000+)

**Total:** ~2 months minimum before full live trading

### With Setbacks (Realistic)

**Day 1-7:** Backtesting
**Day 8-37:** Paper Trading
**Day 38:** Strategy fails paper trading requirements
**Day 39-68:** Another 30 days of paper trading
**Day 69-75:** Micro Live
**Day 76-89:** Mini Live
**Day 90+:** Full Live

**Total:** ~3 months with one setback

---

## Success Stories (Examples)

### Strategy A: Polymarket Arbitrage
- **Paper Trading:** 32 days, +8.2% return, 1.8 Sharpe, 62% win rate
- **Micro Live:** 7 days, +4.1% return, clean execution
- **Mini Live:** 14 days, +5.3% return, consistent
- **Full Live:** Allocated $7000, top performer

### Strategy B: Crypto Momentum
- **Paper Trading:** 45 days (failed first attempt), +6.1% return eventually
- **Micro Live:** 10 days (ran longer for confidence), +3.5% return
- **Mini Live:** 14 days, +4.8% return
- **Full Live:** Allocated $2000, second best performer

---

## Conclusion

The graduation system exists to **protect your capital** while still allowing profitable strategies to scale up. Be patient, follow the process, and trust the data over your emotions.

Remember: **A strategy that can't succeed in paper trading won't succeed with real money.**
