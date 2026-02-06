# Risk Management Modules

Comprehensive risk management system for the arbitrage bot with dynamic position sizing, multi-layer circuit breakers, loss analysis, and strategy comparison.

## Overview

This directory contains four production-ready risk management modules that work together to protect capital and optimize trading performance:

1. **position_sizer.py** - Dynamic position sizing based on risk factors
2. **risk_manager.py** - Multi-layer circuit breakers for capital protection
3. **loss_analyzer.py** - Root cause analysis when losses occur
4. **strategy_analyzer.py** - Strategy comparison and capital allocation

## Modules

### 1. Position Sizer (`position_sizer.py`)

**Class:** `RiskAdjustedPositionSizer`

Dynamically calculates position size based on multiple risk factors.

#### Features

- **Base Allocation:** 5% of bankroll (configurable)
- **Dynamic Adjustments:**
  - Profit margin quality (higher margin → bigger size)
  - Recent win rate (hot streak → bigger, cold → smaller)
  - Market liquidity (thin markets → smaller size)
  - Market volatility (high vol → smaller size)
- **Hard Limits:**
  - Maximum: 10% of bankroll
  - Minimum: $1 per trade
- **Detailed Logging:** Logs reasoning for each sizing decision

#### Usage

```python
from position_sizer import RiskAdjustedPositionSizer

# Initialize
sizer = RiskAdjustedPositionSizer(config)

# Calculate position size
result = sizer.calculate_position_size(
    opportunity=opportunity,
    bankroll=1000.0,
    stats={
        'win_rate': 0.65,
        'total_trades': 50,
        'market_liquidity': {'market_id': 'high'},
        'market_volatility': {'market_id': 'normal'}
    }
)

position_size = result['position_size']
details = result['details']  # Detailed breakdown
```

#### Configuration

Add to `config.yaml`:

```yaml
position_sizing:
  base_allocation_pct: 0.05      # 5% of bankroll
  max_allocation_pct: 0.10       # Max 10% per trade
  min_position_size: 1.0         # Min $1 per trade
  
  multipliers:
    profit_margin:
      excellent: 1.5   # >5% margin
      good: 1.2        # 3-5% margin
      normal: 1.0      # 2-3% margin
      poor: 0.7        # <2% margin
    
    win_rate:
      hot_streak: 1.3  # >70% win rate
      normal: 1.0      # 50-70% win rate
      cold_streak: 0.6 # <50% win rate
    
    liquidity:
      high: 1.0        # High volume
      medium: 0.85     # Medium volume
      low: 0.6         # Low volume (thin)
    
    volatility:
      low: 1.1         # Stable prices
      normal: 1.0      # Normal volatility
      high: 0.7        # High volatility
```

---

### 2. Risk Manager (`risk_manager.py`)

**Class:** `DrawdownProtection`

Multi-layer circuit breaker system to automatically pause trading when risk thresholds are exceeded.

#### Circuit Breakers

1. **Consecutive Losses** - Stop after 3 losses in a row
2. **Hourly Loss Limit** - Stop if lose >$X in 1 hour
3. **Daily Drawdown** - Stop if lose >15% in 1 day
4. **Total Drawdown** - Stop if down >25% from peak
5. **Win Rate Degradation** - Stop if win rate drops below 50%

#### Features

- Automatic pause with specific reasons
- Detailed alerts and logging
- Manual force resume option
- Real-time risk metrics tracking

#### Usage

```python
from risk_manager import DrawdownProtection

# Initialize
risk_mgr = DrawdownProtection(config)

# Record each trade
risk_mgr.record_trade(profit=-5.0, current_capital=995.0)

# Check all circuit breakers before trading
status = risk_mgr.check_all_breakers(current_capital=995.0)

if status['trading_allowed']:
    # Execute trade
    pass
else:
    # Trading paused
    print(f"Trading paused: {status['pause_reason']}")
    print(f"Triggered breakers: {status['triggered_breakers']}")

# Get current risk metrics
metrics = risk_mgr.get_risk_metrics(current_capital=995.0)

# Force resume (use with caution!)
risk_mgr.resume_trading(force=True)
```

#### Configuration

Add to `config.yaml`:

```yaml
risk_limits:
  max_consecutive_losses: 3          # Stop after 3 losses in a row
  max_hourly_loss_usd: 50.0          # Stop if lose >$50/hour
  max_daily_drawdown_pct: 0.15       # Stop if lose >15% in 1 day
  max_total_drawdown_pct: 0.25       # Stop if down >25% from peak
  min_win_rate: 0.50                 # Stop if win rate <50%
```

---

### 3. Loss Analyzer (`loss_analyzer.py`)

**Class:** `LossAnalyzer`

Analyzes WHY the bot is losing money when circuit breakers trigger.

#### Loss Categories

1. **Partial Fills** - Execution issues (orders not fully filled)
2. **Edge Lost During Execution** - Speed/latency issues
3. **Strategy Not Working** - Logic flaws or outdated assumptions
4. **Market Conditions Changed** - External factors (volatility, events)
5. **Competition Increased** - More bots competing for same opportunities

#### Features

- Root cause analysis of losses
- Specific, actionable recommendations for each category
- Priority-ranked fix suggestions
- Tracks patterns across trade history

#### Usage

```python
from loss_analyzer import LossAnalyzer

# Initialize
analyzer = LossAnalyzer(config)

# Analyze trade history
analysis = analyzer.analyze_losses(trade_history)

print(f"Primary issue: {analysis['primary_issue']}")
print(f"Severity: {analysis['severity']}")

# Generate fix recommendations
recommendations = analyzer.generate_fix_suggestions(analysis)

for rec in recommendations:
    print(f"[{rec['priority']}] {rec['category']}")
    print(f"Recommendation: {rec['recommendation']}")
    for action in rec['actions']:
        print(f"  - {action}")
```

#### Example Recommendations

**Partial Fills:**
- Lower max_trade_size in config (try 50% of current)
- Avoid thin/low-liquidity markets
- Add liquidity checks before trading

**Edge Lost During Execution:**
- Reduce request_delay_seconds in config
- Optimize network latency
- Use limit orders instead of market orders

**Strategy Failure:**
- Disable failing strategy temporarily
- Review and adjust strategy parameters
- Backtest with recent data

#### Configuration

Add to `config.yaml`:

```yaml
loss_analysis:
  min_trades: 10                     # Min trades for reliable analysis
  execution_lag_threshold_ms: 500    # >500ms = slow execution
  partial_fill_threshold: 0.8        # <80% filled = partial fill issue
```

---

### 4. Strategy Analyzer (`strategy_analyzer.py`)

**Class:** `StrategyAnalyzer`

Analyzes and compares multiple trading strategies, providing capital allocation recommendations.

#### Metrics Analyzed

1. **Total Profit** - Absolute returns
2. **Win Rate** - Percentage of winning trades
3. **Average Profit Per Trade** - Mean trade profitability
4. **Risk-Adjusted Returns** - Sharpe ratio
5. **Consistency** - Volatility of returns
6. **Opportunity Frequency** - Trades per day

#### Features

- Multi-dimensional strategy comparison
- Risk-tolerance-based capital allocation
- Strategy rankings with overall scores
- Detailed performance breakdowns

#### Usage

```python
from strategy_analyzer import StrategyAnalyzer

# Initialize
analyzer = StrategyAnalyzer(config)

# Prepare performance data
performance_data = {
    'arbitrage': [trade1, trade2, ...],
    'momentum': [trade1, trade2, ...],
    'statistical_arb': [trade1, trade2, ...]
}

# Compare all strategies
comparison = analyzer.compare_strategies(performance_data)

# Rank strategies
rankings = analyzer.rank_strategies(performance_data)
for rank in rankings:
    print(f"#{rank['rank']} {rank['strategy']}: {rank['overall_score']:.1f}")

# Get allocation recommendation
allocation = analyzer.generate_allocation_recommendation(
    analysis=comparison,
    total_capital=1000.0
)

for strategy, alloc in allocation['allocations'].items():
    print(f"{strategy}: {alloc['percentage']:.1f}% (${alloc['capital']:.2f})")
    print(f"  {alloc['reasoning']}")
```

#### Configuration

Add to `config.yaml`:

```yaml
strategy_analysis:
  min_trades: 10                    # Min trades for reliable metrics
  risk_free_rate: 0.0               # For Sharpe ratio calculation
  lookback_days: 30                 # How far back to analyze
  risk_tolerance: moderate          # conservative, moderate, aggressive
```

#### Risk Tolerance Impact

**Conservative:**
- Prioritizes win rate and consistency
- Lower allocation to volatile strategies
- Focuses on capital preservation

**Moderate:**
- Balanced approach
- Equal weight to profit and risk metrics
- Default recommendation

**Aggressive:**
- Prioritizes total profit
- Higher allocation to high-return strategies
- Less weight on consistency

---

## Integration Example

Complete integration with existing bot:

```python
import yaml
from position_sizer import RiskAdjustedPositionSizer
from risk_manager import DrawdownProtection
from loss_analyzer import LossAnalyzer
from strategy_analyzer import StrategyAnalyzer

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize all modules
position_sizer = RiskAdjustedPositionSizer(config)
risk_manager = DrawdownProtection(config)
loss_analyzer = LossAnalyzer(config)
strategy_analyzer = StrategyAnalyzer(config)

# Trading loop
current_capital = 1000.0
trade_history = []
strategy_performance = {'arbitrage': [], 'momentum': []}

while True:
    # 1. Check circuit breakers
    risk_status = risk_manager.check_all_breakers(current_capital)
    
    if not risk_status['trading_allowed']:
        # Trading paused - analyze losses
        analysis = loss_analyzer.analyze_losses(trade_history)
        recommendations = loss_analyzer.generate_fix_suggestions(analysis)
        
        # Log and alert
        print(f"PAUSED: {risk_status['pause_reason']}")
        for rec in recommendations:
            print(f"Fix: {rec['recommendation']}")
        
        break
    
    # 2. Find opportunity
    opportunity = find_arbitrage_opportunity()
    
    if opportunity:
        # 3. Calculate position size
        stats = {
            'win_rate': risk_manager.winning_trades / max(1, risk_manager.total_trades),
            'total_trades': risk_manager.total_trades,
            'market_liquidity': get_liquidity_data(),
            'market_volatility': get_volatility_data()
        }
        
        sizing = position_sizer.calculate_position_size(
            opportunity, current_capital, stats
        )
        position_size = sizing['position_size']
        
        # 4. Execute trade
        trade = execute_trade(opportunity, position_size)
        
        # 5. Record results
        risk_manager.record_trade(trade['profit'], current_capital)
        current_capital += trade['profit']
        trade_history.append(trade)
        strategy_performance[trade['strategy']].append(trade)
    
    # 6. Periodically analyze strategies
    if len(trade_history) % 50 == 0:
        comparison = strategy_analyzer.compare_strategies(strategy_performance)
        allocation = strategy_analyzer.generate_allocation_recommendation(
            comparison, current_capital
        )
        
        # Adjust strategy allocations based on recommendation
        update_strategy_allocations(allocation)
```

---

## Testing

Run the comprehensive test suite:

```bash
python3 test_risk_modules.py
```

This tests all four modules with realistic scenarios.

---

## Logging

All modules integrate with the existing logger system (`logger.py`):

- Position sizing decisions logged with full reasoning
- Circuit breaker triggers logged as CRITICAL
- Loss analysis results logged with severity levels
- Strategy comparisons and rankings logged

Check logs in:
- `logs/errors.log` - All risk management events
- `logs/trades.csv` - Individual trades
- `logs/opportunities.csv` - Opportunities evaluated

---

## Best Practices

### Position Sizing

1. Start conservative (5% base) and adjust based on performance
2. Monitor multiplier effectiveness over time
3. Adjust thresholds based on market conditions

### Risk Management

1. Never force resume without understanding the issue
2. Review triggered breakers before resuming
3. Adjust thresholds if too sensitive/lenient
4. Reset daily tracking at start of each day

### Loss Analysis

1. Run analysis after every circuit breaker trigger
2. Implement highest priority recommendations first
3. Track whether fixes improve performance
4. Re-run analysis to verify improvements

### Strategy Analysis

1. Analyze strategies weekly or after 50+ trades
2. Rebalance capital based on recommendations
3. Disable consistently poor-performing strategies
4. Consider risk tolerance when allocating

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Configure all thresholds in `config.yaml`
- [ ] Test with paper trading first
- [ ] Verify logging is working correctly
- [ ] Set up alerts for circuit breaker triggers
- [ ] Document baseline performance metrics
- [ ] Plan response procedures for each circuit breaker

### Monitoring

Monitor these key metrics:

- Position sizes being calculated
- Circuit breaker status (any triggered?)
- Loss categories over time
- Strategy performance rankings
- Capital allocation changes

### Maintenance

- Review and adjust multipliers monthly
- Update risk limits based on capital growth
- Archive old trade data
- Validate loss categorization accuracy
- Benchmark strategy analyzer recommendations

---

## Troubleshooting

**Problem:** Position sizes too small
- Increase `base_allocation_pct` or adjust multipliers

**Problem:** Circuit breakers too sensitive
- Increase thresholds (e.g., `max_consecutive_losses: 5`)

**Problem:** Loss analysis gives generic recommendations
- Ensure trade data includes execution metadata
- Increase `min_trades_for_analysis` for better patterns

**Problem:** Strategy analyzer shows insufficient data
- Continue trading to gather more data per strategy
- Lower `min_trades` threshold (but less reliable)

---

## API Reference

See inline docstrings in each module for complete API documentation:

```python
# View documentation
help(RiskAdjustedPositionSizer)
help(DrawdownProtection)
help(LossAnalyzer)
help(StrategyAnalyzer)
```

---

## License

Part of the arbitrage-bot project. All modules are production-ready for paper trading.

**⚠️ IMPORTANT:** Always use paper trading mode. Never trade real money without thorough testing and review.
