# Arbitrage Tracking Documentation

## Overview

The arbitrage tracking system provides comprehensive performance metrics for arbitrage trading strategies. It tracks opportunities found, executions performed, profit/loss statistics, win rates, and provides detailed performance analytics.

## Components

### ArbitrageTracker

The `ArbitrageTracker` class is the core metrics tracking component that maintains statistics on arbitrage strategy performance.

**Location:** `strategies/arbitrage_tracker.py`

#### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `opportunities_found` | int | Total number of arbitrage opportunities detected |
| `opportunities_executed` | int | Number of opportunities that were actually executed |
| `total_profit` | float | Cumulative profit from all profitable executions (USD) |
| `total_loss` | float | Cumulative losses from all losing executions (USD) |
| `win_rate` | float | Percentage of profitable executions (0-100) |
| `average_profit` | float | Average profit per execution (USD) |
| `start_time` | datetime | When tracking started |
| `execution_history` | List[Dict] | Detailed history of all executions |

#### Methods

##### `record_opportunity(opportunity: Dict) -> None`

Records when an arbitrage opportunity is detected.

**Parameters:**
- `opportunity`: Dictionary containing opportunity details (market_id, market_name, yes_price, no_price, etc.)

**Example:**
```python
opportunity = {
    'market_id': 'market_123',
    'market_name': 'Presidential Election 2024',
    'yes_price': 0.45,
    'no_price': 0.48
}
tracker.record_opportunity(opportunity)
```

##### `record_execution(result: Dict) -> None`

Records the result of an arbitrage execution.

**Parameters:**
- `result`: Dictionary containing execution results with keys:
  - `profit`: float (profit/loss amount in USD)
  - `market_id`: str
  - `market_name`: str
  - `executed_at`: datetime or str (optional)

**Example:**
```python
result = {
    'market_id': 'market_123',
    'market_name': 'Presidential Election 2024',
    'profit': 12.50,
    'executed_at': datetime.now()
}
tracker.record_execution(result)
```

##### `get_metrics() -> Dict`

Returns a complete snapshot of current metrics.

**Returns:**
Dictionary containing all metrics including:
- opportunities_found
- opportunities_executed
- total_profit
- total_loss
- net_profit
- win_rate
- average_profit
- start_time
- running_time_hours
- running_time_minutes
- execution_history

**Example:**
```python
metrics = tracker.get_metrics()
print(f"Win Rate: {metrics['win_rate']:.2f}%")
print(f"Net Profit: ${metrics['net_profit']:.2f}")
```

##### `reset_metrics() -> None`

Resets all metrics to zero. Useful for starting a new trading session or testing.

**Example:**
```python
tracker.reset_metrics()
# All counters and history now cleared
```

##### `export_summary() -> str`

Generates a human-readable summary of metrics for console output.

**Returns:**
Formatted string containing key performance metrics.

**Example:**
```python
print(tracker.export_summary())
```

**Output:**
```
=== ARBITRAGE PERFORMANCE ===
Opportunities Found: 45
Opportunities Executed: 12
Win Rate: 83.33%
Total Profit: $245.67
Average Profit: $20.47
Running Time: 2h 15m
============================
```

### ArbitrageOrchestrator

The `ArbitrageOrchestrator` class coordinates arbitrage detection and execution with integrated performance tracking.

**Location:** `strategies/arbitrage_orchestrator.py`

#### Methods

##### `detect_opportunity(market_data: Dict, price_data: Dict) -> Optional[ArbitrageOpportunity]`

Detects arbitrage opportunities and automatically records them with the tracker.

**Parameters:**
- `market_data`: Market information dictionary
- `price_data`: Current prices {'yes': float, 'no': float}

**Returns:**
ArbitrageOpportunity object if found, None otherwise

**Example:**
```python
market_data = {
    'id': 'market_123',
    'question': 'Will the market close above $100?'
}
price_data = {'yes': 0.45, 'no': 0.48}

opportunity = orchestrator.detect_opportunity(market_data, price_data)
if opportunity:
    print(f"Found opportunity with {opportunity.profit_margin:.2f}% margin")
```

##### `execute_opportunity(opportunity: ArbitrageOpportunity, trade_size: float) -> Dict`

Executes an arbitrage trade and records the result.

**Parameters:**
- `opportunity`: ArbitrageOpportunity object to execute
- `trade_size`: Amount to invest in USD

**Returns:**
Dictionary containing execution result

**Example:**
```python
result = orchestrator.execute_opportunity(opportunity, trade_size=100.0)
print(f"Executed with profit: ${result['profit']:.2f}")
```

##### `get_performance_metrics() -> Dict`

Returns current performance metrics from the tracker.

**Example:**
```python
metrics = orchestrator.get_performance_metrics()
print(f"Total opportunities: {metrics['opportunities_found']}")
print(f"Execution rate: {metrics['opportunities_executed'] / metrics['opportunities_found'] * 100:.1f}%")
```

##### `print_performance_dashboard() -> None`

Prints a formatted performance dashboard to console.

**Example:**
```python
orchestrator.print_performance_dashboard()
```

## Understanding Metrics

### Win Rate

**Formula:** `(Profitable Executions / Total Executions) × 100`

The win rate represents the percentage of executions that resulted in a profit. A win rate of 100% means all executions were profitable, while 0% means all resulted in losses.

**Interpretation:**
- **80-100%**: Excellent performance, strategy is highly effective
- **60-80%**: Good performance, strategy is working well
- **40-60%**: Moderate performance, may need optimization
- **Below 40%**: Poor performance, strategy needs review

### Average Profit

**Formula:** `(Total Profit - Total Loss) / Total Executions`

The average profit represents the mean profit/loss per execution. This includes both winning and losing trades.

**Interpretation:**
- **Positive value**: Strategy is profitable on average
- **Negative value**: Strategy is losing money on average
- **Close to zero**: Strategy is breaking even

### Net Profit

**Formula:** `Total Profit - Total Loss`

The net profit is the total cumulative profit after accounting for all losses.

### Execution Rate

**Formula:** `(Opportunities Executed / Opportunities Found) × 100`

Not all detected opportunities may be executed due to various constraints (liquidity, risk limits, etc.). The execution rate shows what percentage of detected opportunities were actually traded.

## Usage Examples

### Basic Usage

```python
from strategies.arbitrage_orchestrator import ArbitrageOrchestrator

# Initialize orchestrator with configuration
config = {
    'min_profit_margin': 0.02,  # 2% minimum
    'max_trade_size': 100,
    'max_price_sum': 0.98
}

orchestrator = ArbitrageOrchestrator(config)

# Detect and execute opportunities
market_data = {'id': 'market_1', 'question': 'Test Market'}
price_data = {'yes': 0.45, 'no': 0.48}

opportunity = orchestrator.detect_opportunity(market_data, price_data)
if opportunity:
    result = orchestrator.execute_opportunity(opportunity, trade_size=50.0)
    print(f"Profit: ${result['profit']:.2f}")

# View performance
orchestrator.print_performance_dashboard()
```

### Advanced Usage - Monitoring Session

```python
# Initialize orchestrator
orchestrator = ArbitrageOrchestrator(config)

# Trading loop
for market, prices in markets_stream():
    opportunity = orchestrator.detect_opportunity(market, prices)
    
    if opportunity and orchestrator.strategy.should_enter(opportunity):
        result = orchestrator.execute_opportunity(opportunity, trade_size=100.0)
        
        # Check performance after each trade
        metrics = orchestrator.get_performance_metrics()
        
        # Alert on poor performance
        if metrics['opportunities_executed'] >= 10 and metrics['win_rate'] < 50:
            print("⚠️ Warning: Win rate below 50%")
            # Consider adjusting strategy parameters

# End of session summary
print("\n" + "="*50)
print("SESSION SUMMARY")
print("="*50)
orchestrator.print_performance_dashboard()
```

### Programmatic Metrics Access

```python
# Get detailed metrics
metrics = orchestrator.get_performance_metrics()

# Calculate execution rate
if metrics['opportunities_found'] > 0:
    execution_rate = (metrics['opportunities_executed'] / 
                     metrics['opportunities_found']) * 100
    print(f"Execution Rate: {execution_rate:.1f}%")

# Check profitability
if metrics['net_profit'] > 0:
    print(f"✅ Strategy is profitable: ${metrics['net_profit']:.2f}")
else:
    print(f"❌ Strategy is losing: ${metrics['net_profit']:.2f}")

# Review execution history
for execution in metrics['execution_history']:
    print(f"{execution['market_name']}: ${execution['profit']:.2f}")
```

### Resetting Metrics for New Session

```python
# Reset all tracking for a fresh start
orchestrator.reset_performance_tracking()

# Confirm reset
metrics = orchestrator.get_performance_metrics()
assert metrics['opportunities_found'] == 0
assert metrics['opportunities_executed'] == 0
print("Metrics reset successfully")
```

## Testing

Run the test suites to verify functionality:

```bash
# Test ArbitrageTracker
python tests/test_arbitrage_tracker.py

# Test ArbitrageOrchestrator
python tests/test_arbitrage_orchestrator.py

# Run all tests with pytest
pytest tests/test_arbitrage_tracker.py tests/test_arbitrage_orchestrator.py -v
```

## Best Practices

1. **Regular Monitoring**: Check metrics periodically during trading sessions
2. **Performance Thresholds**: Set alerts for win rate below 50% or negative net profit
3. **Session Tracking**: Reset metrics at the start of each trading session
4. **History Analysis**: Review execution_history to identify patterns
5. **Metric Interpretation**: Consider both win rate and average profit together

## Integration Notes

- The tracker is automatically integrated when using `ArbitrageOrchestrator`
- No manual tracking calls needed - orchestrator handles all recording
- Thread-safety is NOT provided (assumes single-threaded execution)
- Metrics are in-memory only (not persisted to database)

## Future Enhancements (Out of Scope)

- Real-time visualization/graphs
- Database persistence
- Multi-strategy comparison
- Alert thresholds with notifications
- Performance heatmaps
- Risk-adjusted returns (Sharpe ratio, etc.)
