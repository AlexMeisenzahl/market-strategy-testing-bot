# Trading Strategies Module

This directory contains 4 production-quality trading strategies for the arbitrage bot.

## Available Strategies

### 1. ArbitrageStrategy (`arbitrage_strategy.py`)
**Type:** Risk-Free Arbitrage  
**Risk Level:** Very Low  
**Expected Return:** 2-10% per trade  

Classic arbitrage where YES + NO < $1.00 creates guaranteed profit.

**Entry Criteria:**
- YES price + NO price < $1.00
- Profit margin >= 2%
- Price sum < 0.98

**Exit Criteria:**
- Hold to expiry (risk-free)
- Early exit if prices improve >5%
- Market about to expire

---

### 2. MomentumStrategy (`momentum_strategy.py`)
**Type:** Trend Following  
**Risk Level:** Medium  
**Expected Return:** 10-30% per trade  

Trades markets with strong directional momentum confirmed by volume.

**Entry Criteria:**
- Price moved >2% in 5 minutes
- Volume increased >50% vs average
- Momentum score >70
- Clear direction (bullish/bearish)

**Exit Criteria:**
- Price reversed >1%
- Momentum score drops <40
- Profit target hit (+10-30%)
- Stop loss triggered (-10%)

---

### 3. NewsStrategy (`news_strategy.py`)
**Type:** Event-Based Trading  
**Risk Level:** High  
**Expected Return:** 15-40% per trade  

Detects breaking news through volume spikes and rapid price movements.

**Entry Criteria:**
- Volume spike >300% in last minute
- Price moved >5% rapidly
- Direction is clear (not choppy)

**Exit Criteria:**
- Profit target hit (+15-40%)
- Stop loss triggered (-15%)
- Reversal signal detected (>3%)
- Max hold time (30 minutes)

---

### 4. StatisticalArbStrategy (`statistical_arb_strategy.py`)
**Type:** Pairs Trading / Mean Reversion  
**Risk Level:** Medium-High  
**Expected Return:** 10-20% per trade  

Finds correlated markets that diverge, bets on convergence.

**Entry Criteria:**
- Historical correlation >0.7
- Current divergence >15%
- Z-score >2.0 (statistical significance)

**Exit Criteria:**
- Convergence achieved (z-score < 0.5)
- Profit target hit (+20%)
- Stop loss triggered (-20%)
- Correlation breakdown (< 0.5)

---

## Common Interface

All strategies implement a consistent interface:

```python
class Strategy:
    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with configuration"""
        
    def analyze(self, market_data: Dict, price_data: Dict) -> Optional[Opportunity]:
        """Analyze a single market for opportunities"""
        
    def find_opportunities(self, markets: List[Dict], prices_dict: Dict) -> List[Opportunity]:
        """Find opportunities across all markets"""
        
    def should_enter(self, opportunity: Opportunity) -> bool:
        """Decision logic for entering a position"""
        
    def should_exit(self, market_id: str, current_prices: Dict) -> Tuple[bool, str]:
        """Decision logic for exiting a position"""
        
    def enter_position(self, opportunity: Opportunity, trade_size: float) -> Dict:
        """Record position entry"""
        
    def exit_position(self, market_id: str, exit_price: float, reason: str) -> Dict:
        """Record position exit"""
        
    def get_statistics(self) -> Dict:
        """Return strategy performance statistics"""
        
    def reset_statistics(self) -> None:
        """Reset performance counters"""
```

## Usage Example

```python
from strategies import ArbitrageStrategy, MomentumStrategy

# Initialize strategies with config
config = {
    'min_profit_margin': 0.02,
    'max_trade_size': 10,
    'momentum_min_score': 70,
}

arb_strategy = ArbitrageStrategy(config)
mom_strategy = MomentumStrategy(config)

# Find opportunities
markets = [...]  # List of markets from API
prices_dict = {...}  # Dictionary of current prices

arb_opps = arb_strategy.find_opportunities(markets, prices_dict)
mom_opps = mom_strategy.find_opportunities(markets, prices_dict)

# Evaluate and enter positions
for opp in arb_opps:
    if arb_strategy.should_enter(opp):
        position = arb_strategy.enter_position(opp, trade_size=10)
        print(f"Entered position: {position}")

# Check exit conditions
for market_id in list(arb_strategy.active_positions.keys()):
    should_exit, reason = arb_strategy.should_exit(market_id, current_prices)
    if should_exit:
        exit_info = arb_strategy.exit_position(market_id, exit_price, reason)
        print(f"Exited position: {exit_info}")

# Get performance statistics
stats = arb_strategy.get_statistics()
print(f"Strategy stats: {stats}")
```

## Configuration

All strategies can be configured via `config.yaml`. Common parameters:

```yaml
# Arbitrage Strategy
min_profit_margin: 0.02          # 2% minimum profit
max_price_sum: 0.98              # Only consider if sum < 0.98

# Momentum Strategy
momentum_min_score: 70           # Minimum momentum score
momentum_min_price_change_5m: 2.0  # 2% price change in 5 min
momentum_min_volume_change: 50.0   # 50% volume increase
momentum_profit_target_min: 10.0   # 10% profit target
momentum_stop_loss: 10.0          # 10% stop loss

# News Strategy
news_min_volume_spike: 300.0     # 300% volume spike
news_min_price_movement: 5.0     # 5% rapid price movement
news_profit_target_min: 15.0     # 15% profit target
news_stop_loss: 15.0             # 15% stop loss
news_max_hold_time: 30           # 30 minutes max hold

# Statistical Arbitrage Strategy
stat_arb_min_correlation: 0.7    # 0.7 minimum correlation
stat_arb_min_divergence: 15.0    # 15% divergence threshold
stat_arb_min_z_score: 2.0        # 2.0 z-score threshold
stat_arb_profit_target: 20.0     # 20% profit target
stat_arb_stop_loss: 20.0         # 20% stop loss
```

## Integration with Existing Codebase

All strategies integrate seamlessly with existing modules:

1. **Logger Module** (`logger.py`):
   - All strategies use `get_logger()` for consistent logging
   - Trade entries/exits logged to `logs/trades.csv`
   - Opportunities logged to `logs/opportunities.csv`

2. **Monitor Module** (`monitor.py`):
   - Strategies receive market data from `PolymarketMonitor`
   - Work with rate limiting and connection health checks

3. **Detector Module** (`detector.py`):
   - `ArbitrageStrategy` provides same functionality as `ArbitrageDetector`
   - Can be used as drop-in replacement or in parallel

4. **Paper Trader** (`paper_trader.py`):
   - All strategies designed for paper trading
   - Track expected vs actual profits
   - Work with simulated market conditions

## Safety Features

All strategies include:

- **Division by zero protection**: All calculations check for zero denominators
- **Price validation**: Prices must be between 0 and 1
- **Error handling**: Graceful handling of invalid or missing data
- **Position limits**: Respect maximum trade size and position limits
- **Stop losses**: All non-arbitrage strategies have stop loss protection
- **Logging**: All activities logged for audit trail

## Testing

All strategies have been tested for:

- ✓ Import and instantiation
- ✓ Interface consistency
- ✓ Integration with existing codebase
- ✓ Error handling and edge cases
- ✓ Division by zero vulnerabilities
- ✓ Performance tracking
- ✓ Position management
- ✓ Security vulnerabilities (CodeQL scan passed)

## Next Steps

These strategies are designed to work with a `StrategyManager` that will:
- Orchestrate multiple strategies simultaneously
- Handle position sizing and risk management
- Aggregate statistics across all strategies
- Provide a unified interface for the bot

## License

Part of the Polymarket Arbitrage Bot project.
