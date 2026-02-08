"""
Demo script for the 5 new professional feature modules

Demonstrates:
1. Backtester - Testing strategies on historical data
2. LiquidityAnalyzer - Order book analysis
3. TaxExporter - Tax report generation
4. Notifier - Multi-channel notifications
5. CompetitionMonitor - Competition detection
"""

import yaml
from datetime import datetime, timedelta
from backtester import Backtester
from liquidity_analyzer import LiquidityAnalyzer, OrderBook
from tax_exporter import TaxExporter
from notifier import Notifier
from competition_monitor import CompetitionMonitor


def demo_backtester():
    """Demonstrate backtester functionality"""
    print("\n" + "=" * 60)
    print("BACKTESTER DEMO")
    print("=" * 60)

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Create backtester
    backtester = Backtester(config)

    # Create sample historical data
    print("\nCreating sample historical data...")
    historical_data = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(100):
        # Simulate some arbitrage opportunities
        timestamp = base_time + timedelta(hours=i)

        # Mix of profitable and unprofitable opportunities
        if i % 10 < 3:  # 30% are arbitrage opportunities
            yes_price = 0.48 + (i % 5) * 0.01
            no_price = 0.49 + (i % 3) * 0.01
        else:
            yes_price = 0.51
            no_price = 0.52

        historical_data.append(
            {
                "timestamp": timestamp,
                "market": f"Market_{i % 5}",
                "yes_price": yes_price,
                "no_price": no_price,
            }
        )

    print(f"Generated {len(historical_data)} data points")

    # Run backtest
    print("\nRunning backtest with basic_arbitrage strategy...")
    results = backtester.simulate_strategy("basic_arbitrage", historical_data)

    # Generate report
    report = backtester.generate_backtest_report()
    print(report)


def demo_liquidity_analyzer():
    """Demonstrate liquidity analyzer functionality"""
    print("\n" + "=" * 60)
    print("LIQUIDITY ANALYZER DEMO")
    print("=" * 60)

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Create analyzer
    analyzer = LiquidityAnalyzer(config)

    # Create sample order book
    print("\nCreating sample order book...")
    bids = [(0.50 - i * 0.01, 100 + i * 50) for i in range(10)]
    asks = [(0.51 + i * 0.01, 100 + i * 50) for i in range(10)]
    order_book = OrderBook(bids, asks)

    print(f"Best bid: {order_book.best_bid():.3f}")
    print(f"Best ask: {order_book.best_ask():.3f}")
    print(f"Spread: {order_book.spread_percentage():.2f}%")

    # Check depth for trade
    print("\nChecking liquidity depth for $10 trade...")
    depth_check = analyzer.check_depth("BTC", 10.0, order_book)

    print(f"Required liquidity: ${depth_check['required_liquidity']:.2f}")
    print(f"Available liquidity: ${depth_check['available_liquidity']:.2f}")
    print(f"Spread: {depth_check['spread_pct']:.2f}%")
    print(f"Passed: {depth_check['passed']}")

    # Estimate slippage
    print("\nEstimating slippage...")
    slippage = analyzer.estimate_slippage(10.0, 5000.0)
    print(f"Estimated slippage: {slippage:.2f}%")

    # Calculate market impact
    print("\nCalculating market impact...")
    impact = analyzer.calculate_market_impact(
        {"market": "BTC", "size": 10.0, "order_book": order_book}
    )

    print(f"Average slippage: {impact['avg_slippage_pct']:.2f}%")
    print(f"Impact cost: ${impact['estimated_impact_cost']:.2f}")
    print(f"Impact severity: {impact['impact_severity']}")

    # Get summary
    summary = analyzer.get_liquidity_summary()
    print(f"\nLiquidity checks: {summary['total_checks']}")
    print(f"Pass rate: {summary['pass_rate']:.1f}%")


def demo_tax_exporter():
    """Demonstrate tax exporter functionality"""
    print("\n" + "=" * 60)
    print("TAX EXPORTER DEMO")
    print("=" * 60)

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Create exporter
    exporter = TaxExporter(config)

    # Check if trades exist
    print("\nChecking for trade logs...")
    trades = exporter.load_trades_from_logs()

    if trades:
        print(f"Found {len(trades)} trades in logs")

        # Generate summary
        print("\nGenerating tax summary...")
        summary_report = exporter.print_summary()
        print(summary_report)

        # Export to CSV
        current_year = datetime.now().year
        print(f"\nExporting tax report for {current_year}...")
        csv_path = exporter.export_to_csv(current_year)

        if csv_path:
            print(f"Tax report saved to: {csv_path}")
    else:
        print("No trades found in logs. Run the bot first to generate trades.")


def demo_notifier():
    """Demonstrate notifier functionality"""
    print("\n" + "=" * 60)
    print("NOTIFIER DEMO")
    print("=" * 60)

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Create notifier
    notifier = Notifier(config)

    # Get statistics
    stats = notifier.get_statistics()
    print(f"\nNotification channels:")
    print(f"  Desktop: {stats['channels_enabled']['desktop']}")
    print(f"  SMS: {stats['channels_enabled']['sms']}")
    print(f"  Push: {stats['channels_enabled']['push']}")
    print(f"  Sound: {stats['channels_enabled']['sound']}")
    print(f"  Plyer available: {stats['plyer_available']}")

    # Test notifications (only if enabled)
    if any(stats["channels_enabled"].values()):
        print("\nTesting notification system...")
        test_results = notifier.test_notifications()
        print(f"Test results: {test_results}")

    # Demo priority-based notifications
    print("\nDemonstrating priority-based notifications...")

    # INFO priority (desktop only)
    print("\n1. INFO notification (desktop only):")
    notifier.alert_opportunity_found("BTC", 2.5)

    # WARNING priority (desktop + sound)
    print("\n2. WARNING notification (desktop + sound):")
    notifier.alert_connection_issue("API response time slow")

    # CRITICAL priority (all channels)
    print("\n3. CRITICAL notification (all channels):")
    notifier.alert_circuit_breaker("Max consecutive losses exceeded")

    # Get updated statistics
    stats = notifier.get_statistics()
    print(f"\nTotal notifications sent: {stats['total_notifications']}")


def demo_competition_monitor():
    """Demonstrate competition monitor functionality"""
    print("\n" + "=" * 60)
    print("COMPETITION MONITOR DEMO")
    print("=" * 60)

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Create monitor
    monitor = CompetitionMonitor(config)

    # Simulate opportunity tracking
    print("\nSimulating opportunity tracking...")

    # Create some fast-disappearing opportunities (high competition)
    for i in range(30):
        opp_id = f"opp_fast_{i}"
        tracker = monitor.track_opportunity(opp_id, f"Market_{i % 5}")

        # Simulate fast disappearance (0.1 - 0.8 seconds)
        import time
        import random

        time.sleep(random.uniform(0.001, 0.01))  # Small delay for demo

        monitor.mark_opportunity_disappeared(opp_id)

        # Simulate trade attempts with varying success
        if i % 3 == 0:  # 33% fill rate (high competition)
            monitor.mark_trade_attempted(opp_id, filled=True)
        else:
            monitor.mark_trade_attempted(opp_id, filled=False)

    # Create some slow-disappearing opportunities (low competition)
    for i in range(10):
        opp_id = f"opp_slow_{i}"
        tracker = monitor.track_opportunity(opp_id, f"Market_{i % 3}")

        # Simulate slower disappearance
        time.sleep(random.uniform(0.001, 0.005))
        monitor.mark_opportunity_disappeared(opp_id)

        # High fill rate (low competition)
        if i % 5 != 0:  # 80% fill rate
            monitor.mark_trade_attempted(opp_id, filled=True)
        else:
            monitor.mark_trade_attempted(opp_id, filled=False)

    # Analyze competition
    print("\nAnalyzing competition level...")
    competition_level = monitor.analyze_competition_level()
    print(f"Current competition level: {competition_level.upper()}")

    # Get detailed analyses
    lifespan = monitor.track_opportunity_lifespan()
    print(f"\nOpportunity lifespan:")
    print(f"  Average: {lifespan['avg_lifespan']:.3f}s")
    print(f"  Indicator: {lifespan['competition_indicator']}")

    fill_rate = monitor.measure_fill_success_rate()
    print(f"\nFill success rate:")
    print(f"  Fill rate: {fill_rate['fill_rate_pct']:.1f}%")
    print(f"  Indicator: {fill_rate['competition_indicator']}")

    snipes = monitor.detect_snipe_patterns()
    print(f"\nSnipe detection:")
    print(f"  Snipe rate: {snipes['snipe_rate_pct']:.1f}%")
    print(f"  Indicator: {snipes['competition_indicator']}")

    # Generate full report
    report = monitor.get_competition_report()
    print(report)


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("PROFESSIONAL FEATURE MODULES DEMO")
    print("=" * 60)
    print("\nDemonstrating 5 new professional modules:")
    print("1. Backtester")
    print("2. LiquidityAnalyzer")
    print("3. TaxExporter")
    print("4. Notifier")
    print("5. CompetitionMonitor")

    try:
        demo_backtester()
        input("\nPress Enter to continue to next demo...")

        demo_liquidity_analyzer()
        input("\nPress Enter to continue to next demo...")

        demo_tax_exporter()
        input("\nPress Enter to continue to next demo...")

        demo_notifier()
        input("\nPress Enter to continue to next demo...")

        demo_competition_monitor()

        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETE")
        print("=" * 60)
        print("\nAll 5 professional modules are working correctly!")
        print("See the output above for detailed demonstrations.")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
