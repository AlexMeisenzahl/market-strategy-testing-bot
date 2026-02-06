# Core System Modules Documentation

This document provides detailed documentation for the three new core system modules:
- **strategy_manager.py** - Multi-strategy orchestration
- **performance_monitor.py** - Real-time performance tracking
- **performance_optimizer.py** - System-level optimizations

---

## 1. StrategyManager

### Overview
The `StrategyManager` class orchestrates multiple trading strategies running in parallel. Each strategy can be independently enabled/disabled and has its own capital allocation.

### Features
- Run multiple strategies simultaneously (arbitrage, momentum, statistical_arb, news)
- Independent capital allocation per strategy
- Performance tracking and comparison
- Dynamic strategy enable/disable at runtime
- Portfolio management across all strategies

### Basic Usage

```python
import yaml
from strategy_manager import StrategyManager

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize manager
manager = StrategyManager(config)

# Run all strategies on market data
markets = [...]  # List of market data
prices = {...}   # Dict of prices by market_id

opportunities = manager.run_all_strategies(markets, prices)

# Execute best opportunities
trades = manager.execute_best_opportunities(opportunities)

# Compare strategy performance
comparison = manager.compare_strategies()
print(f"Best strategy: {manager.get_best_performing_strategy()}")
```

### Key Methods

#### `__init__(config: Dict[str, Any])`
Initialize the strategy manager with configuration.

**Config parameters:**
- `total_capital`: Total capital to allocate across strategies (default: $100)
- `strategies.enabled`: List of strategy names to enable (default: ['arbitrage'])
- `strategies.capital_allocation`: Dict of strategy → allocation percentage

#### `run_all_strategies(markets, prices_dict) → Dict[str, List]`
Run all enabled strategies on current market data.

**Returns:** Dictionary mapping strategy name to list of opportunities found.

#### `execute_best_opportunities(all_opportunities) → Dict[str, int]`
Execute the best opportunities from each strategy.

**Returns:** Dictionary mapping strategy name to number of trades executed.

#### `compare_strategies() → Dict[str, Any]`
Compare performance metrics across all strategies.

**Returns:** Dictionary with comparative statistics including:
- `opportunities_found`: Total opportunities detected
- `opportunities_taken`: Total trades executed  
- `total_profit`: Cumulative profit
- `roi_percent`: Return on investment percentage
- `win_rate_percent`: Success rate
- `avg_profit_per_trade`: Average profit per trade

#### `get_best_performing_strategy() → Optional[str]`
Identify the best performing strategy based on ROI.

**Returns:** Name of best performing strategy.

#### `enable_strategy(strategy_name: str) → bool`
Enable a strategy at runtime.

#### `disable_strategy(strategy_name: str) → bool`
Disable a strategy at runtime.

#### `rebalance_capital(new_allocation: Dict[str, float]) → bool`
Rebalance capital allocation across strategies.

**Parameters:**
- `new_allocation`: Dictionary mapping strategy name to allocation percentage (must sum to 1.0)

#### `get_statistics() → Dict[str, Any]`
Get overall statistics across all strategies.

**Returns:**
- `enabled_strategies`: List of active strategies
- `total_capital`: Total allocated capital
- `cycles_completed`: Number of trading cycles
- `total_opportunities`: Aggregate opportunities found
- `total_trades`: Aggregate trades executed
- `total_profit`: Total profit across all strategies
- `overall_roi_percent`: Overall return on investment
- `best_strategy`: Name of best performing strategy

### Configuration Example

Add to `config.yaml`:

```yaml
# Strategy configuration
total_capital: 100  # Total capital in USD

strategies:
  enabled:
    - arbitrage
    - momentum
    - statistical_arb
  
  # Optional: Custom capital allocation (must sum to 1.0)
  capital_allocation:
    arbitrage: 0.50       # 50% to arbitrage
    momentum: 0.30        # 30% to momentum
    statistical_arb: 0.20 # 20% to statistical arb
```

---

## 2. PerformanceMonitor

### Overview
The `PerformanceMonitor` class tracks system performance metrics in real-time, providing insights into speed, bottlenecks, and competitive positioning.

### Features
- Real-time timing measurements (detection, decision, execution, network)
- Performance grading (A+ to F)
- Competitive positioning analysis
- Bottleneck identification
- Statistical analysis (min, max, mean, median, p95, p99)
- Comprehensive performance reporting

### Basic Usage

```python
from performance_monitor import PerformanceMonitor
import time

# Initialize monitor
monitor = PerformanceMonitor(config)

# Start a trading cycle
monitor.start_cycle()

# Measure detection speed
detection_start = time.time()
opportunities = find_opportunities()
monitor.measure_detection_speed(detection_start, len(opportunities))

# Measure network latency
network_start = time.time()
response = api_call()
monitor.measure_network_latency(network_start, "markets_endpoint")

# End cycle
total_time = monitor.end_cycle()
print(f"Cycle completed in {total_time:.0f}ms")

# Get performance grade
grade, details = monitor.get_performance_grade()
print(f"Performance Grade: {grade}")

# Analyze bottlenecks
analysis = monitor.analyze_bottlenecks()
for bottleneck in analysis['bottlenecks']:
    print(f"Bottleneck: {bottleneck['component']} - {bottleneck['issue']}")

# Compare to competition
competitive = monitor.compare_to_competition()
print(f"Position: {competitive['competitive_position']}")
```

### Key Methods

#### `start_cycle()`
Mark the start of a new trading cycle.

#### `end_cycle() → float`
Mark the end of a trading cycle.

**Returns:** Total cycle time in milliseconds.

#### `measure_detection_speed(start_time, opportunities_found=0) → float`
Measure how fast opportunities were detected.

**Parameters:**
- `start_time`: Time when detection started (from `time.time()`)
- `opportunities_found`: Number of opportunities detected

**Returns:** Detection time in milliseconds.

#### `measure_decision_speed(start_time) → float`
Measure how fast trading decisions were made.

#### `measure_execution_speed(start_time) → float`
Measure how fast trades were executed.

#### `measure_network_latency(start_time, endpoint="unknown") → float`
Measure network latency for API calls.

#### `get_statistics(metric='total_cycle') → Dict[str, float]`
Get statistical analysis of a performance metric.

**Metrics:** 'detection', 'decision', 'execution', 'network', 'total_cycle'

**Returns:**
- `min`: Minimum time
- `max`: Maximum time
- `mean`: Average time
- `median`: Median time
- `p95`: 95th percentile
- `p99`: 99th percentile
- `count`: Number of measurements

#### `analyze_bottlenecks() → Dict[str, Any]`
Identify performance bottlenecks and provide recommendations.

**Returns:**
- `bottlenecks`: List of identified bottlenecks with severity
- `recommendations`: List of optimization suggestions
- `critical_component`: Most critical bottleneck component

#### `get_performance_grade() → Tuple[str, Dict[str, Any]]`
Calculate overall performance grade.

**Grade Thresholds:**
- A+: < 50ms (Elite)
- A: < 100ms (Excellent)
- B: < 250ms (Good)
- C: < 500ms (Average)
- D: < 1000ms (Below average)
- F: > 1000ms (Poor)

**Returns:** Tuple of (grade, details dictionary)

#### `compare_to_competition() → Dict[str, Any]`
Compare performance to competitive benchmarks.

**Benchmarks:**
- Professional bots: ~50ms
- Amateur bots: ~500ms
- Human traders: ~5000ms

**Returns:**
- `our_median_speed_ms`: Our median cycle time
- `competitive_position`: 'elite', 'competitive', 'amateur', or 'slow'
- `tier_description`: Human-readable tier description
- `comparisons`: Detailed comparison to each benchmark
- `estimated_market_percentile`: Estimated market position

#### `generate_performance_report() → Dict[str, Any]`
Generate comprehensive performance report.

**Returns:** Complete performance analysis including:
- Overall grade
- Competitive position
- Bottleneck analysis
- Detailed metrics for all components
- Performance trends
- Reliability metrics

### Performance Targets

Default targets (configurable in `config.yaml`):

```yaml
# Performance targets
target_cycle_time_ms: 200      # Target total cycle time
target_network_latency_ms: 100 # Target network latency
performance_history_size: 100  # Number of measurements to keep
```

---

## 3. PerformanceOptimizer

### Overview
The `PerformanceOptimizer` class provides system-level optimizations to improve speed and efficiency.

### Features
- Configuration optimization suggestions
- Multiprocessing enablement for parallel operations
- Threading support for I/O-bound tasks
- Async operations with asyncio/aiohttp
- Data caching with TTL support
- Performance profiling
- Batch operations
- Resource cleanup

### Basic Usage

```python
from performance_optimizer import PerformanceOptimizer

# Initialize optimizer
optimizer = PerformanceOptimizer(config)

# Get optimization suggestions
performance_report = monitor.generate_performance_report()
suggestions = optimizer.optimize_config(performance_report)

print(f"Priority: {suggestions['priority']}")
for change in suggestions['system_changes']:
    print(f"Suggestion: {change['change']}")
    print(f"Expected improvement: {change['expected_improvement']}")

# Enable optimizations
optimizer.enable_multiprocessing(max_workers=4)
optimizer.enable_threading(max_workers=8)

# Use caching
optimizer.cache_data('expensive_calculation', result, ttl=60)
cached_result = optimizer.get_cached_data('expensive_calculation')

# Parallel processing
def process_item(item):
    return item * 2

items = [1, 2, 3, 4, 5]
results = optimizer.parallel_map(process_item, items)

# Get optimization summary
summary = optimizer.get_optimization_summary()
print(f"Optimization score: {summary['optimization_score']}/100")

# Cleanup when done
optimizer.cleanup()
```

### Key Methods

#### `optimize_config(current_performance) → Dict[str, Any]`
Generate optimized configuration based on performance.

**Returns:**
- `config_changes`: Suggested configuration changes
- `system_changes`: List of system optimization suggestions
- `priority`: 'high', 'medium', or 'low'

#### `enable_multiprocessing(max_workers=None) → bool`
Enable multiprocessing for CPU-bound parallel operations.

#### `enable_threading(max_workers=None) → bool`
Enable threading for I/O-bound parallel operations.

#### `parallel_map(func, items, use_processes=False) → List[Any]`
Execute a function on multiple items in parallel.

**Parameters:**
- `func`: Function to execute
- `items`: List of items to process
- `use_processes`: Use processes (CPU-bound) vs threads (I/O-bound)

#### `cache_data(key, data, ttl=None)`
Cache data for fast retrieval.

**Parameters:**
- `key`: Cache key
- `data`: Data to cache
- `ttl`: Time-to-live in seconds (None = no expiry)

#### `get_cached_data(key) → Optional[Any]`
Retrieve cached data.

#### `get_cache_statistics() → Dict[str, Any]`
Get cache performance statistics.

**Returns:**
- `cache_hits`: Number of cache hits
- `cache_misses`: Number of cache misses
- `hit_rate_percent`: Cache hit rate percentage
- `cache_size`: Number of cached items

#### `profile_bottlenecks(func, *args, **kwargs) → Dict[str, Any]`
Profile a function to identify bottlenecks.

**Returns:**
- `execution_time_seconds`: Total execution time
- `top_time_consumers`: Top 10 time-consuming operations
- `full_profile`: Complete profiling output

#### `create_async_client()`
Create an async HTTP client using aiohttp.

**Returns:** aiohttp.ClientSession configured for optimal performance.

#### `get_optimization_summary() → Dict[str, Any]`
Get summary of optimization status.

**Returns:**
- `optimization_score`: Score out of 100
- `enabled_optimizations`: List of enabled features
- `system_resources`: CPU cores, workers
- `cache_performance`: Cache statistics
- `recommendations`: Quick optimization suggestions

#### `cleanup()`
Cleanup resources (call when shutting down).

### Optimization Configuration

Add to `config.yaml`:

```yaml
# Performance optimization settings
use_multiprocessing: false  # Enable for CPU-bound tasks
use_async: true            # Enable async operations
use_caching: true          # Enable data caching
max_workers: 4             # Max parallel workers
```

---

## Integration Example

Here's how to use all three modules together in a main trading loop:

```python
import yaml
from strategy_manager import StrategyManager
from performance_monitor import PerformanceMonitor
from performance_optimizer import PerformanceOptimizer
from monitor import PolymarketMonitor
import time

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize all modules
strategy_manager = StrategyManager(config)
performance_monitor = PerformanceMonitor(config)
performance_optimizer = PerformanceOptimizer(config)
market_monitor = PolymarketMonitor(config)

# Main trading loop
while True:
    # Start performance tracking
    performance_monitor.start_cycle()
    
    # Fetch market data with network timing
    network_start = time.time()
    markets = market_monitor.get_active_markets()
    performance_monitor.measure_network_latency(network_start, "markets")
    
    # Fetch prices
    prices = {}
    for market in markets:
        network_start = time.time()
        prices[market['id']] = market_monitor.get_market_prices(market['id'])
        performance_monitor.measure_network_latency(network_start, f"prices_{market['id']}")
    
    # Run strategies with detection timing
    detection_start = time.time()
    opportunities = strategy_manager.run_all_strategies(markets, prices)
    total_opps = sum(len(opps) for opps in opportunities.values())
    performance_monitor.measure_detection_speed(detection_start, total_opps)
    
    # Execute trades with timing
    execution_start = time.time()
    trades = strategy_manager.execute_best_opportunities(opportunities)
    performance_monitor.measure_execution_speed(execution_start)
    
    # End cycle
    cycle_time = performance_monitor.end_cycle()
    
    # Check performance every 10 cycles
    if performance_monitor.total_cycles % 10 == 0:
        # Get performance report
        report = performance_monitor.generate_performance_report()
        grade = report['overall_grade']['grade']
        
        print(f"Performance Grade: {grade}")
        print(f"Median cycle time: {report['overall_grade']['median_cycle_time_ms']:.0f}ms")
        
        # Optimize if needed
        if grade in ['C', 'D', 'F']:
            suggestions = performance_optimizer.optimize_config(report)
            print(f"Generated {len(suggestions['system_changes'])} optimization suggestions")
            
            # Apply automatic optimizations
            if 'use_multiprocessing' in suggestions['config_changes']:
                performance_optimizer.enable_multiprocessing()
    
    # Sleep before next cycle
    time.sleep(config.get('cycle_interval', 10))

# Cleanup
performance_optimizer.cleanup()
```

---

## Best Practices

1. **Strategy Management**
   - Start with one strategy (arbitrage) and add more as you gain confidence
   - Monitor individual strategy performance before allocating significant capital
   - Rebalance capital allocation based on historical performance

2. **Performance Monitoring**
   - Always measure complete cycles (start_cycle → end_cycle)
   - Track network latency separately to identify external factors
   - Review performance reports regularly to identify degradation

3. **Performance Optimization**
   - Enable optimizations gradually (start with caching, then async, then multiprocessing)
   - Profile bottlenecks before optimizing
   - Monitor cache hit rates and adjust TTL accordingly
   - Always call cleanup() when shutting down

4. **Error Handling**
   - All modules include comprehensive error handling
   - Check return values from enable/disable methods
   - Monitor logs for warnings about performance issues

---

## Troubleshooting

### StrategyManager Issues

**Problem:** Strategy not finding any opportunities
- Check that the strategy is properly configured in config.yaml
- Verify market data format matches strategy expectations
- Review strategy-specific thresholds (min_profit_margin, etc.)

**Problem:** Capital allocation doesn't sum to 100%
- Ensure capital_allocation percentages sum to exactly 1.0
- Check for typos in strategy names

### PerformanceMonitor Issues

**Problem:** Grade is always N/A
- Ensure you're calling start_cycle() and end_cycle() for each cycle
- Check that measurements are being recorded

**Problem:** High network latency
- Verify internet connection
- Check if API endpoints are responsive
- Consider using a CDN or closer API endpoints

### PerformanceOptimizer Issues

**Problem:** Multiprocessing not working
- Some operations cannot be pickled for multiprocessing
- Try threading instead for I/O-bound tasks
- Check system resources (CPU availability)

**Problem:** Cache not improving performance
- Verify data is actually being cached (check cache_size)
- Ensure TTL is appropriate for data freshness requirements
- Check cache hit rate - if low, adjust what/how you're caching

---

## Advanced Usage

### Custom Strategy Integration

To add your own strategy:

1. Create a new strategy class in `strategies/` following the existing pattern
2. Implement required methods: `analyze()`, `find_opportunities()`, `should_enter()`, `should_exit()`, `enter_position()`, `exit_position()`, `get_statistics()`
3. Add strategy to StrategyManager._initialize_strategies()
4. Enable in config.yaml

### Async Operations

For advanced users, leverage async operations:

```python
# Create async client
async_client = performance_optimizer.create_async_client()

# Fetch multiple URLs concurrently
urls = [url1, url2, url3]
results = await performance_optimizer.fetch_multiple_urls_async(urls)
```

### Custom Performance Metrics

Add custom timing measurements:

```python
# Measure custom operation
start = time.time()
custom_operation()
custom_time = (time.time() - start) * 1000

# Store in monitor (you can extend the class to track custom metrics)
```

---

## API Reference Summary

### StrategyManager
- `run_all_strategies()` - Execute all strategies
- `execute_best_opportunities()` - Trade best opportunities
- `compare_strategies()` - Compare performance
- `get_best_performing_strategy()` - Identify winner
- `enable_strategy()` / `disable_strategy()` - Runtime control
- `get_statistics()` - Overall statistics
- `get_portfolio_summary()` - Portfolio overview

### PerformanceMonitor
- `start_cycle()` / `end_cycle()` - Track cycles
- `measure_detection_speed()` - Track detection time
- `measure_network_latency()` - Track API latency
- `get_performance_grade()` - Get grade (A+ to F)
- `compare_to_competition()` - Competitive analysis
- `analyze_bottlenecks()` - Identify slow components
- `generate_performance_report()` - Full report

### PerformanceOptimizer
- `optimize_config()` - Get optimization suggestions
- `enable_multiprocessing()` / `enable_threading()` - Parallel processing
- `parallel_map()` - Execute in parallel
- `cache_data()` / `get_cached_data()` - Caching
- `profile_bottlenecks()` - Profile functions
- `get_optimization_summary()` - Status summary
- `cleanup()` - Resource cleanup

---

## Further Reading

- Review existing strategies in `strategies/` directory
- See STRATEGIES_README.md for strategy-specific documentation
- Check config.yaml for all configuration options
- Review demo_core_modules.py for working examples
