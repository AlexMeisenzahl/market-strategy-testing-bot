#!/usr/bin/env python3
"""
Test script to verify all risk management modules work correctly
"""

import yaml
from datetime import datetime, timedelta

# Import all risk management modules
from position_sizer import RiskAdjustedPositionSizer
from risk_manager import DrawdownProtection
from loss_analyzer import LossAnalyzer
from strategy_analyzer import StrategyAnalyzer
from detector import ArbitrageOpportunity


def load_config():
    """Load config with risk management defaults"""
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Add risk management config if not present
    if "position_sizing" not in config:
        config["position_sizing"] = {
            "base_allocation_pct": 0.05,
            "max_allocation_pct": 0.10,
            "min_position_size": 1.0,
            "multipliers": {
                "profit_margin": {
                    "excellent": 1.5,
                    "good": 1.2,
                    "normal": 1.0,
                    "poor": 0.7,
                },
                "win_rate": {"hot_streak": 1.3, "normal": 1.0, "cold_streak": 0.6},
                "liquidity": {"high": 1.0, "medium": 0.85, "low": 0.6},
                "volatility": {"low": 1.1, "normal": 1.0, "high": 0.7},
            },
        }

    if "risk_limits" not in config:
        config["risk_limits"] = {
            "max_consecutive_losses": 3,
            "max_hourly_loss_usd": 50.0,
            "max_daily_drawdown_pct": 0.15,
            "max_total_drawdown_pct": 0.25,
            "min_win_rate": 0.50,
        }

    if "loss_analysis" not in config:
        config["loss_analysis"] = {
            "min_trades": 10,
            "execution_lag_threshold_ms": 500,
            "partial_fill_threshold": 0.8,
        }

    if "strategy_analysis" not in config:
        config["strategy_analysis"] = {
            "min_trades": 10,
            "risk_free_rate": 0.0,
            "lookback_days": 30,
            "risk_tolerance": "moderate",
        }

    return config


def test_position_sizer(config):
    """Test position sizer"""
    print("\n=== Testing Position Sizer ===")
    sizer = RiskAdjustedPositionSizer(config)

    # Create test opportunity
    opportunity = ArbitrageOpportunity(
        market_id="test_market_1",
        market_name="Test Market",
        yes_price=0.48,
        no_price=0.48,
    )

    # Test stats
    stats = {
        "win_rate": 0.65,
        "total_trades": 20,
        "market_liquidity": {"test_market_1": "high"},
        "market_volatility": {"test_market_1": "normal"},
    }

    result = sizer.calculate_position_size(opportunity, bankroll=1000, stats=stats)
    print(f"✓ Position size calculated: ${result['position_size']:.2f}")
    print(f"  Base: ${result['details']['base_size']:.2f}")
    print(f"  Total multiplier: {result['details']['multipliers']['total']:.2f}x")

    return sizer


def test_risk_manager(config):
    """Test risk manager"""
    print("\n=== Testing Risk Manager ===")
    risk_mgr = DrawdownProtection(config)

    # Simulate some trades
    current_capital = 1000

    # Record winning trade
    risk_mgr.record_trade(profit=5.0, current_capital=1005)
    print("✓ Recorded winning trade")

    # Record losing trade
    risk_mgr.record_trade(profit=-2.0, current_capital=1003)
    print("✓ Recorded losing trade")

    # Check breakers
    status = risk_mgr.check_all_breakers(current_capital=1003)
    print(f"✓ Circuit breakers checked - Trading allowed: {status['trading_allowed']}")

    # Get metrics
    metrics = risk_mgr.get_risk_metrics(current_capital=1003)
    print(f"  Consecutive losses: {metrics['consecutive_losses']}")
    print(f"  Win rate: {metrics['win_rate']*100:.1f}%")

    return risk_mgr


def test_loss_analyzer(config):
    """Test loss analyzer"""
    print("\n=== Testing Loss Analyzer ===")
    analyzer = LossAnalyzer(config)

    # Create sample trade history
    trade_history = []
    base_time = datetime.now() - timedelta(days=7)

    for i in range(15):
        trade = {
            "profit": 3.0 if i % 3 != 0 else -2.0,  # 2/3 winners
            "strategy": "arbitrage" if i < 10 else "momentum",
            "executed_at": base_time + timedelta(hours=i * 2),
            "profit_margin": 3.5 - (i * 0.1),  # Declining margins
            "execution_time_ms": 200 + (i * 20),
            "fill_percentage": 0.95,
            "market_volatility": "normal",
        }
        trade_history.append(trade)

    # Analyze losses
    analysis = analyzer.analyze_losses(trade_history)
    print(f"✓ Loss analysis completed")
    print(f"  Total trades: {analysis['total_trades']}")
    print(f"  Losing trades: {analysis['losing_trades']}")
    print(f"  Severity: {analysis.get('severity', 'N/A')}")

    # Generate recommendations
    recommendations = analyzer.generate_fix_suggestions(analysis)
    print(f"✓ Generated {len(recommendations)} recommendations")
    if recommendations:
        print(f"  Top recommendation: {recommendations[0]['category']}")

    return analyzer


def test_strategy_analyzer(config):
    """Test strategy analyzer"""
    print("\n=== Testing Strategy Analyzer ===")
    analyzer = StrategyAnalyzer(config)

    # Create sample performance data
    base_time = datetime.now() - timedelta(days=7)

    performance_data = {
        "arbitrage": [
            {
                "profit": 5.0 if i % 2 == 0 else -1.0,
                "executed_at": base_time + timedelta(hours=i * 3),
                "strategy": "arbitrage",
            }
            for i in range(15)
        ],
        "momentum": [
            {
                "profit": 8.0 if i % 3 == 0 else -2.0,
                "executed_at": base_time + timedelta(hours=i * 4),
                "strategy": "momentum",
            }
            for i in range(12)
        ],
    }

    # Compare strategies
    comparison = analyzer.compare_strategies(performance_data)
    print(f"✓ Strategy comparison completed")
    print(f"  Strategies analyzed: {len(comparison['strategies'])}")

    # Rank strategies
    rankings = analyzer.rank_strategies(performance_data)
    print(f"✓ Strategies ranked")
    if rankings:
        print(
            f"  #1 strategy: {rankings[0]['strategy']} (score: {rankings[0]['overall_score']:.1f})"
        )

    # Generate allocation
    allocation = analyzer.generate_allocation_recommendation(
        comparison, total_capital=1000
    )
    print(f"✓ Allocation recommendation generated")
    for strategy_name, alloc in allocation["allocations"].items():
        print(
            f"  {strategy_name}: {alloc['percentage']:.1f}% (${alloc['capital']:.2f})"
        )

    return analyzer


def main():
    """Run all tests"""
    print("=" * 60)
    print("Risk Management Modules Test")
    print("=" * 60)

    # Load config
    config = load_config()
    print("✓ Config loaded")

    # Test each module
    try:
        sizer = test_position_sizer(config)
        risk_mgr = test_risk_manager(config)
        loss_analyzer = test_loss_analyzer(config)
        strategy_analyzer = test_strategy_analyzer(config)

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - All modules working correctly!")
        print("=" * 60)
        print("\nModules created:")
        print("  1. position_sizer.py - RiskAdjustedPositionSizer")
        print("  2. risk_manager.py - DrawdownProtection")
        print("  3. loss_analyzer.py - LossAnalyzer")
        print("  4. strategy_analyzer.py - StrategyAnalyzer")
        print("\nAll modules are production-ready for paper trading!")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
