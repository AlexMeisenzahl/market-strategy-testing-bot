# Quick Start Guide: Core System Modules

This guide will help you quickly integrate the new core system modules into your arbitrage bot.

## What Was Added

Three powerful new modules have been added to enhance your bot:

1. **strategy_manager.py** - Run multiple strategies in parallel
2. **performance_monitor.py** - Track speed and performance
3. **performance_optimizer.py** - Optimize system performance

## Quick Test (5 minutes)

Run the demo to see everything in action:

```bash
python3 demo_core_modules.py
```

This will demonstrate:
- Strategy management with multiple strategies
- Performance monitoring with grading
- Performance optimization suggestions
- All modules working together

## Basic Integration (10 minutes)

### Step 1: Update config.yaml

Add these sections to your `config.yaml`:

```yaml
# Strategy Management
total_capital: 100  # Total capital in USD

strategies:
  enabled:
    - arbitrage    # Start with just arbitrage

# Performance Monitoring
target_cycle_time_ms: 200
target_network_latency_ms: 100
performance_history_size: 100

# Performance Optimization
use_multiprocessing: false
use_async: true
use_caching: true
max_workers: 4
```

### Step 2: Initialize Modules in Your Bot

Add to your main bot file (e.g., `bot.py`):

```python
from strategy_manager import StrategyManager
from performance_monitor import PerformanceMonitor
from performance_optimizer import PerformanceOptimizer

# Initialize modules
strategy_manager = StrategyManager(config)
performance_monitor = PerformanceMonitor(config)
performance_optimizer = PerformanceOptimizer(config)
```

### Step 3: Use in Trading Loop

Replace your existing detection/trading code with:

```python
# Start performance tracking
performance_monitor.start_cycle()

# Fetch markets (with timing)
network_start = time.time()
markets = monitor.get_active_markets()
performance_monitor.measure_network_latency(network_start)

# Get prices
prices = {market['id']: monitor.get_market_prices(market['id']) 
          for market in markets}

# Run strategies (with timing)
detection_start = time.time()
opportunities = strategy_manager.run_all_strategies(markets, prices)
performance_monitor.measure_detection_speed(detection_start)

# Execute trades
execution_start = time.time()
trades = strategy_manager.execute_best_opportunities(opportunities)
performance_monitor.measure_execution_speed(execution_start)

# End cycle
cycle_time = performance_monitor.end_cycle()
print(f"Cycle completed in {cycle_time:.0f}ms")
```

### Step 4: Monitor Performance

Every 10 cycles, check performance:

```python
if performance_monitor.total_cycles % 10 == 0:
    # Get grade
    grade, details = performance_monitor.get_performance_grade()
    print(f"Performance: {grade} - {details['grade_description']}")
    
    # Get optimization suggestions if needed
    if grade in ['C', 'D', 'F']:
        report = performance_monitor.generate_performance_report()
        suggestions = performance_optimizer.optimize_config(report)
        print(f"Optimization suggestions: {len(suggestions['system_changes'])}")
```

## Common Use Cases

### Enable Multiple Strategies

Edit `config.yaml`:

```yaml
strategies:
  enabled:
    - arbitrage
    - momentum
    - statistical_arb
  
  # Optional: Custom allocation
  capital_allocation:
    arbitrage: 0.50
    momentum: 0.30
    statistical_arb: 0.20
```

### Improve Performance

If your grade is below B:

```python
# Get optimization suggestions
report = performance_monitor.generate_performance_report()
suggestions = performance_optimizer.optimize_config(report)

# Apply suggestions
for change in suggestions['system_changes']:
    print(f"Suggestion: {change['change']}")
    print(f"Expected improvement: {change['expected_improvement']}")

# Enable optimizations
performance_optimizer.enable_multiprocessing()
performance_optimizer.enable_threading()
```

### Compare Strategies

See which strategy performs best:

```python
comparison = strategy_manager.compare_strategies()

for strategy_name, stats in comparison.items():
    print(f"{strategy_name}:")
    print(f"  ROI: {stats['roi_percent']:.2f}%")
    print(f"  Win Rate: {stats['win_rate_percent']:.1f}%")
    print(f"  Avg Profit: ${stats['avg_profit_per_trade']:.2f}")

best = strategy_manager.get_best_performing_strategy()
print(f"\nBest strategy: {best}")
```

### Cache Frequently Used Data

Speed up repeated operations:

```python
# Cache market data for 60 seconds
market_data = optimizer.get_cached_data('markets')
if market_data is None:
    market_data = fetch_market_data()  # Expensive operation
    optimizer.cache_data('markets', market_data, ttl=60)
```

## Troubleshooting

### Import Errors

Make sure all strategy files exist in `strategies/` directory:
- arbitrage_strategy.py
- momentum_strategy.py
- statistical_arb_strategy.py
- news_strategy.py

### Performance Grade is N/A

Ensure you're calling both `start_cycle()` and `end_cycle()`:

```python
monitor.start_cycle()
# ... do work ...
monitor.end_cycle()
```

### Strategies Not Finding Opportunities

Check your thresholds in config.yaml:

```yaml
min_profit_margin: 0.02  # 2% minimum profit
```

Lower this value to find more opportunities (but with less profit).

## Next Steps

1. **Read the full documentation**: `CORE_MODULES_README.md`
2. **Review the demo code**: `demo_core_modules.py`
3. **Explore strategies**: Check files in `strategies/` directory
4. **Customize configuration**: Adjust `config.yaml` to your needs
5. **Monitor performance**: Regularly check grades and optimize

## Getting Help

If you encounter issues:

1. Check the logs in `logs/` directory
2. Review error messages in `logs/errors.log`
3. Run the demo to verify basic functionality
4. Check that config.yaml is properly formatted
5. Ensure all dependencies are installed: `pip install -r requirements.txt`

## Performance Tips

1. **Start simple**: Begin with just arbitrage strategy
2. **Monitor first**: Track performance for a while before optimizing
3. **Optimize gradually**: Enable one optimization at a time
4. **Cache wisely**: Cache data that's expensive to compute and stable
5. **Review regularly**: Check performance reports weekly

## Safety Reminders

- Paper trading is ALWAYS enabled in config.yaml
- No real money is ever used
- All trades are simulated
- Safe to experiment and test

---

**Congratulations!** You now have professional-grade strategy management, performance monitoring, and optimization capabilities. Happy trading! 🚀
