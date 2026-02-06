"""
Demo script showing how to use the new core system modules:
- StrategyManager
- PerformanceMonitor  
- PerformanceOptimizer

This demonstrates basic usage patterns for beginners.
"""

import yaml
import time
from strategy_manager import StrategyManager
from performance_monitor import PerformanceMonitor
from performance_optimizer import PerformanceOptimizer


def demo_strategy_manager():
    """Demonstrate StrategyManager usage"""
    print("\n" + "="*60)
    print("STRATEGY MANAGER DEMO")
    print("="*60)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize strategy manager
    print("\n1. Initializing Strategy Manager...")
    manager = StrategyManager(config)
    
    # Show enabled strategies
    stats = manager.get_statistics()
    print(f"   Enabled strategies: {stats['enabled_strategies']}")
    print(f"   Total capital: ${stats['total_capital']:.2f}")
    
    # Simulate running strategies
    print("\n2. Running strategies on sample data...")
    
    # Create sample market data
    sample_markets = [
        {'id': 'market1', 'question': 'Will BTC hit $100k?'},
        {'id': 'market2', 'question': 'Will ETH hit $5k?'}
    ]
    
    sample_prices = {
        'market1': {'yes': 0.45, 'no': 0.48},  # Arbitrage opportunity!
        'market2': {'yes': 0.55, 'no': 0.50}   # No arbitrage
    }
    
    # Run all strategies
    opportunities = manager.run_all_strategies(sample_markets, sample_prices)
    
    for strategy_name, opps in opportunities.items():
        print(f"   {strategy_name}: Found {len(opps)} opportunities")
    
    # Compare strategies
    print("\n3. Comparing strategy performance...")
    comparison = manager.compare_strategies()
    
    for strategy_name, perf in comparison.items():
        print(f"\n   {strategy_name}:")
        print(f"      Opportunities found: {perf['opportunities_found']}")
        print(f"      ROI: {perf['roi_percent']:.2f}%")
        print(f"      Allocated capital: ${perf['allocated_capital']:.2f}")
    
    # Get portfolio summary
    print("\n4. Portfolio Summary:")
    portfolio = manager.get_portfolio_summary()
    print(f"   Total capital: ${portfolio['total_capital']:.2f}")
    print(f"   Number of strategies: {len(portfolio['strategies'])}")


def demo_performance_monitor():
    """Demonstrate PerformanceMonitor usage"""
    print("\n" + "="*60)
    print("PERFORMANCE MONITOR DEMO")
    print("="*60)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize performance monitor
    print("\n1. Initializing Performance Monitor...")
    monitor = PerformanceMonitor(config)
    
    # Simulate a trading cycle
    print("\n2. Simulating trading cycle with timing measurements...")
    
    # Start cycle
    monitor.start_cycle()
    
    # Simulate detection
    detection_start = time.time()
    time.sleep(0.05)  # Simulate 50ms detection time
    monitor.measure_detection_speed(detection_start, opportunities_found=3)
    
    # Simulate decision making
    decision_start = time.time()
    time.sleep(0.02)  # Simulate 20ms decision time
    monitor.measure_decision_speed(decision_start)
    
    # Simulate execution
    execution_start = time.time()
    time.sleep(0.03)  # Simulate 30ms execution time
    monitor.measure_execution_speed(execution_start)
    
    # End cycle
    cycle_time = monitor.end_cycle()
    print(f"   Total cycle time: {cycle_time:.0f}ms")
    
    # Get performance grade
    print("\n3. Performance Grade:")
    grade, details = monitor.get_performance_grade()
    print(f"   Grade: {grade}")
    print(f"   Description: {details['grade_description']}")
    print(f"   Median cycle time: {details['median_cycle_time_ms']:.0f}ms")
    
    # Compare to competition
    print("\n4. Competitive Analysis:")
    competitive = monitor.compare_to_competition()
    print(f"   Position: {competitive['competitive_position']}")
    print(f"   Tier: {competitive['tier_description']}")
    print(f"   Estimated percentile: Top {100 - competitive['estimated_market_percentile']}%")
    
    # Analyze bottlenecks
    print("\n5. Bottleneck Analysis:")
    analysis = monitor.analyze_bottlenecks()
    if analysis['bottlenecks']:
        print(f"   Found {analysis['total_bottlenecks']} bottlenecks:")
        for bottleneck in analysis['bottlenecks']:
            print(f"      - {bottleneck['component']}: {bottleneck['issue']}")
    else:
        print("   No significant bottlenecks detected!")
    
    # Generate full report
    print("\n6. Generating performance report...")
    report = monitor.generate_performance_report()
    print(f"   Overall grade: {report['overall_grade']['grade']}")
    print(f"   Reliability score: {report['reliability']['consistency_score']:.1f}/100")
    print(f"   Total cycles measured: {report['summary']['total_cycles']}")


def demo_performance_optimizer():
    """Demonstrate PerformanceOptimizer usage"""
    print("\n" + "="*60)
    print("PERFORMANCE OPTIMIZER DEMO")
    print("="*60)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize optimizer
    print("\n1. Initializing Performance Optimizer...")
    optimizer = PerformanceOptimizer(config)
    
    # Show system resources
    summary = optimizer.get_optimization_summary()
    print(f"   CPU cores: {summary['system_resources']['cpu_cores']}")
    print(f"   Max workers: {summary['system_resources']['max_workers']}")
    print(f"   Optimization score: {summary['optimization_score']}/100")
    
    # Show enabled optimizations
    print("\n2. Enabled Optimizations:")
    for opt in summary['enabled_optimizations']:
        print(f"   ✓ {opt}")
    
    # Show recommendations
    print("\n3. Recommendations:")
    for rec in summary['recommendations']:
        print(f"   → {rec}")
    
    # Demonstrate caching
    print("\n4. Demonstrating caching:")
    
    # Cache some data
    optimizer.cache_data('test_key', {'sample': 'data'}, ttl=60)
    print("   Data cached")
    
    # Retrieve cached data
    cached = optimizer.get_cached_data('test_key')
    print(f"   Data retrieved: {cached}")
    
    # Show cache stats
    cache_stats = optimizer.get_cache_statistics()
    print(f"   Cache hits: {cache_stats['cache_hits']}")
    print(f"   Cache size: {cache_stats['cache_size']}")
    
    # Generate optimization suggestions
    print("\n5. Generating optimization suggestions...")
    
    # Create mock performance data
    mock_performance = {
        'detailed_metrics': {
            'total_cycle': {'median': 300, 'mean': 350, 'p95': 450},
            'network': {'median': 150, 'mean': 180}
        },
        'bottleneck_analysis': {
            'bottlenecks': [
                {'component': 'network', 'avg_time_ms': 180}
            ]
        }
    }
    
    suggestions = optimizer.optimize_config(mock_performance)
    print(f"   Priority: {suggestions['priority']}")
    print(f"   Found {len(suggestions['system_changes'])} suggestions:")
    
    for change in suggestions['system_changes'][:3]:  # Show first 3
        print(f"\n      Change: {change['change']}")
        print(f"      Reason: {change['reason']}")
        print(f"      Expected improvement: {change['expected_improvement']}")
    
    # Cleanup
    print("\n6. Cleaning up resources...")
    optimizer.cleanup()
    print("   Cleanup complete!")


def demo_integrated_usage():
    """Demonstrate using all three modules together"""
    print("\n" + "="*60)
    print("INTEGRATED USAGE DEMO")
    print("="*60)
    print("\nShowing how to use all three modules together in a real trading loop:")
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize all modules
    print("\n1. Initializing all modules...")
    strategy_manager = StrategyManager(config)
    performance_monitor = PerformanceMonitor(config)
    performance_optimizer = PerformanceOptimizer(config)
    print("   All modules initialized!")
    
    # Simulate trading cycle
    print("\n2. Running integrated trading cycle...")
    
    # Start performance monitoring
    performance_monitor.start_cycle()
    
    # Sample data
    markets = [{'id': 'market1', 'question': 'Sample Market'}]
    prices = {'market1': {'yes': 0.45, 'no': 0.48}}
    
    # Run strategies with detection timing
    detection_start = time.time()
    opportunities = strategy_manager.run_all_strategies(markets, prices)
    performance_monitor.measure_detection_speed(detection_start, len(opportunities))
    
    # Execute trades with execution timing
    execution_start = time.time()
    trades = strategy_manager.execute_best_opportunities(opportunities)
    performance_monitor.measure_execution_speed(execution_start)
    
    # End cycle
    cycle_time = performance_monitor.end_cycle()
    
    print(f"   Cycle completed in {cycle_time:.0f}ms")
    print(f"   Total opportunities: {sum(len(o) for o in opportunities.values())}")
    print(f"   Total trades: {sum(trades.values())}")
    
    # Get performance report
    print("\n3. Analyzing performance...")
    perf_report = performance_monitor.generate_performance_report()
    grade = perf_report['overall_grade']['grade']
    print(f"   Performance grade: {grade}")
    
    # Optimize if needed
    if grade in ['C', 'D', 'F']:
        print("\n4. Performance needs improvement - generating optimizations...")
        suggestions = performance_optimizer.optimize_config(perf_report)
        print(f"   Generated {len(suggestions['system_changes'])} suggestions")
    else:
        print("\n4. Performance is good - no immediate optimizations needed!")
    
    # Show strategy comparison
    print("\n5. Strategy Performance:")
    comparison = strategy_manager.compare_strategies()
    best = strategy_manager.get_best_performing_strategy()
    print(f"   Best performing strategy: {best}")
    
    # Cleanup
    performance_optimizer.cleanup()
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CORE SYSTEM MODULES DEMONSTRATION")
    print("="*60)
    print("\nThis demo showcases the three new core system modules:")
    print("  1. StrategyManager - Orchestrates multiple trading strategies")
    print("  2. PerformanceMonitor - Tracks speed and latency metrics")
    print("  3. PerformanceOptimizer - Provides system-level optimizations")
    
    try:
        # Run individual demos
        demo_strategy_manager()
        demo_performance_monitor()
        demo_performance_optimizer()
        
        # Run integrated demo
        demo_integrated_usage()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("  - Review the code in strategy_manager.py")
        print("  - Review the code in performance_monitor.py")
        print("  - Review the code in performance_optimizer.py")
        print("  - Integrate these modules into your main bot.py")
        print("  - Adjust config.yaml to enable/disable strategies")
        
    except Exception as e:
        print(f"\n❌ Error running demos: {str(e)}")
        import traceback
        traceback.print_exc()
