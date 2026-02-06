"""
Quick Start Guide - Professional Modules

Simple examples to get started with each module.
"""

# ============================================================
# 1. BACKTESTER - Test strategies on historical data
# ============================================================

from backtester import Backtester
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

backtester = Backtester(config)

# Create historical_data.csv with format:
# timestamp,market,yes_price,no_price
# 2024-01-01 10:00:00,BTC,0.48,0.49

data = backtester.load_historical_data(filepath="historical_data.csv")
results = backtester.simulate_strategy('basic_arbitrage', data)
print(backtester.generate_backtest_report())


# ============================================================
# 2. LIQUIDITY ANALYZER - Check liquidity before trading
# ============================================================

from liquidity_analyzer import LiquidityAnalyzer

analyzer = LiquidityAnalyzer(config)

# Before every trade:
is_safe, reason = analyzer.verify_before_execution(opportunity)
if is_safe:
    # Execute trade
    pass
else:
    print(f"Trade blocked: {reason}")


# ============================================================
# 3. TAX EXPORTER - Generate tax reports
# ============================================================

from tax_exporter import TaxExporter

exporter = TaxExporter(config)

# Export annual tax report
csv_path = exporter.export_to_csv(year=2024)
print(f"Tax report: {csv_path}")

# Print summary
print(exporter.print_summary(year=2024))


# ============================================================
# 4. NOTIFIER - Send alerts
# ============================================================

from notifier import Notifier

notifier = Notifier(config)

# Quick alerts
notifier.alert_opportunity_found("BTC", profit_pct=2.5)
notifier.alert_trade_executed("ETH", profit_usd=1.25)
notifier.alert_circuit_breaker("Max losses exceeded")

# Custom notifications
notifier.notify(
    title="Custom Alert",
    message="Something important happened",
    priority="WARNING"  # CRITICAL, WARNING, or INFO
)


# ============================================================
# 5. COMPETITION MONITOR - Detect other bots
# ============================================================

from competition_monitor import CompetitionMonitor

monitor = CompetitionMonitor(config)

# For each opportunity:
tracker = monitor.track_opportunity("opp_123", "BTC")

# When it disappears:
monitor.mark_opportunity_disappeared("opp_123")

# After trade attempt:
monitor.mark_trade_attempted("opp_123", filled=True)

# Analyze competition:
level = monitor.analyze_competition_level()  # 'low', 'medium', 'high'
print(f"Competition: {level}")
print(monitor.get_competition_report())


# ============================================================
# CONFIGURATION
# ============================================================

# Add to config.yaml for full functionality:

"""
# Liquidity settings
liquidity_requirements:
  min_liquidity_multiplier: 5.0
  max_spread_pct: 0.5
  min_daily_volume_usd: 1000.0

# Tax settings
tax_settings:
  short_term_rate: 0.24
  long_term_rate: 0.15

# Notification settings
notifications:
  desktop_enabled: true
  sms_enabled: false
  push_enabled: false
  sound_enabled: true
  sms_phone: "+1234567890"

# Competition monitoring
competition_monitoring:
  high_competition_lifespan: 1.0
  low_competition_lifespan: 5.0
  snipe_threshold: 0.5
"""
