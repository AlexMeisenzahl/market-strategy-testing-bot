# Free Data Integration Guide

## 🎯 Overview

This guide explains how to use the new **FREE** data sources that require **NO API KEYS**.

**What's New:**
- ✅ **Binance WebSocket** - Real-time crypto prices (1200 req/min)
- ✅ **CoinGecko API** - Free backup (50 req/min, no key)
- ✅ **Polymarket Subgraph** - On-chain data (unlimited)
- ✅ **Price Aggregator** - Multi-source with smart fallbacks

**Total Cost: $0/month | No API Keys | High Rate Limits**

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `websockets` - For Binance WebSocket
- `gql[all]` - For Polymarket Subgraph
- All existing dependencies

### Step 2: Configure Data Sources

Copy the example config:
```bash
cp config.example.yaml config.yaml
```

The default configuration is ready to use:
```yaml
# Binance WebSocket & REST API (FREE - 1200 req/min)
binance:
  enable_websocket: true
  symbols:
    - BTC
    - ETH
    - BNB
    - SOL

# CoinGecko API (FREE - 50 req/min, no key)
coingecko:
  enabled: true

# Polymarket Subgraph (UNLIMITED)
polymarket:
  use_subgraph: true
```

### Step 3: Run the Bot

```bash
python3 bot.py
```

The bot will now use:
- **Binance** for real-time crypto prices
- **CoinGecko** as backup
- **Polymarket Subgraph** for prediction markets

---

## 📊 New Dashboard Features

The bot dashboard now shows:

### Data Sources Status Panel
```
┌─ FREE DATA SOURCES ─────────────────┐
│ Binance:        ✓ Connected          │
│ CoinGecko:      12/50 req/min        │
│ Success Rate:   99.8%                │
└──────────────────────────────────────┘
```

This shows:
- **Binance connection status** - WebSocket or REST
- **CoinGecko usage** - Requests used / limit
- **Success rate** - Percentage of successful requests

---

## 🔧 Advanced Usage

### Using the Monitor in Your Code

```python
import yaml
from monitor import PolymarketMonitor

# Load config
config = yaml.safe_load(open('config.yaml'))

# Initialize monitor
monitor = PolymarketMonitor(config)

# Get crypto price
btc_price = monitor.get_crypto_price('BTC')
print(f"BTC: ${btc_price:,.2f}")

# Get multiple crypto prices
prices = monitor.get_crypto_prices(['BTC', 'ETH', 'SOL'])
for symbol, price in prices.items():
    print(f"{symbol}: ${price:,.2f}")

# Get detailed market data
market_data = monitor.get_crypto_market_data('BTC')
print(f"24h Volume: ${market_data['volume_24h']:,.0f}")
print(f"24h Change: {market_data['price_change_pct_24h']:.2f}%")

# Get Polymarket markets
markets = monitor.get_active_markets()
for market in markets[:5]:
    print(f"Market: {market['question']}")

# Get market prices
prices = monitor.get_market_prices('btc-above-100k')
print(f"YES: ${prices['yes']:.3f}, NO: ${prices['no']:.3f}")

# Check data source status
status = monitor.get_data_source_status()
print(f"Binance: {status['binance']['connected']}")
print(f"Success Rate: {status['aggregator']['success_rate']:.1f}%")

# Cleanup
monitor.shutdown()
```

### Direct Access to Data Sources

```python
from data_sources import BinanceClient, CoinGeckoClient, PolymarketSubgraph

# Use Binance directly
binance = BinanceClient(symbols=['BTCUSDT', 'ETHUSDT'])
binance.start_websocket()  # Real-time updates
btc = binance.get_price('BTCUSDT')

# Use CoinGecko directly
coingecko = CoinGeckoClient()
btc = coingecko.get_price('bitcoin')
market_data = coingecko.get_market_data('bitcoin')

# Use Polymarket Subgraph directly
polymarket = PolymarketSubgraph(use_subgraph=True)
markets = polymarket.get_markets(active_only=True)
prices = polymarket.get_market_prices('market_id')
```

### WebSocket Callback for Real-Time Updates

```python
from data_sources import BinanceClient

def on_price_update(symbol, price, data):
    """Called on each WebSocket price update"""
    print(f"{symbol}: ${price:,.2f}")
    print(f"24h Change: {data.get('P', 0)}%")

# Start WebSocket with callback
client = BinanceClient(symbols=['BTCUSDT'])
client.start_websocket(callback=on_price_update)

# Prices update automatically in real-time
# Press Ctrl+C to stop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.stop_websocket()
```

---

## 🎛️ Configuration Options

### Binance Settings

```yaml
binance:
  enable_websocket: true      # Use WebSocket for real-time
  symbols:                    # Symbols to track
    - BTC
    - ETH
    - BNB
    - SOL
    - XRP
    - ADA
    - AVAX
    - DOGE
  rest_fallback: true         # Fall back to REST if WebSocket fails
```

### CoinGecko Settings

```yaml
coingecko:
  enabled: true               # Enable CoinGecko as backup
  cache_duration: 60          # Cache prices for N seconds
```

Caching reduces API calls and improves performance.

### Polymarket Settings

```yaml
polymarket:
  use_subgraph: true          # Use The Graph subgraph (unlimited)
  use_api_fallback: true      # Fall back to Polymarket API
```

The Graph subgraph is preferred (unlimited) but API works too.

### Price Aggregator Settings

```yaml
price_aggregator:
  enable_websocket: true      # Enable WebSocket
  primary_source: binance     # Primary: binance or coingecko
  fallback_enabled: true      # Enable automatic fallbacks
```

---

## 🔄 Fallback Logic

The Price Aggregator uses intelligent fallbacks:

1. **Try Binance WebSocket** (fastest, <100ms)
   - Real-time price from WebSocket cache
   
2. **Try Binance REST API** (if WebSocket unavailable)
   - Fresh price from REST endpoint
   
3. **Try CoinGecko API** (if Binance fails)
   - Backup source with global coverage

4. **Return None** (if all sources fail)
   - Log error for investigation

This ensures maximum uptime and reliability.

---

## 📈 Rate Limits

All sources have generous free tiers:

| Source | Requests/Minute | Authentication | Cost |
|--------|----------------|----------------|------|
| Binance WebSocket | 1200 | ❌ None | $0 |
| Binance REST | 1200 | ❌ None | $0 |
| CoinGecko | 10-50 | ❌ None | $0 |
| Polymarket Subgraph | Unlimited* | ❌ None | $0 |

*Decentralized via The Graph, no practical limit.

### Rate Limit Monitoring

Check rate limit status:
```python
# Monitor level
status = monitor.get_rate_limit_status()
print(f"Used: {status['current']}/{status['max']}")
print(f"Resets in: {status['reset_in']} seconds")

# Data source level
ds_status = monitor.get_data_source_status()
binance_used = ds_status['binance']['rate_limit_used']
coingecko_used = ds_status['coingecko']['rate_limit_used']
```

---

## 🧪 Testing

### Run Test Suite

```bash
python3 test_data_sources.py
```

This tests:
- ✅ Binance REST API
- ✅ CoinGecko API
- ✅ Polymarket Subgraph/API
- ✅ Price Aggregator
- ✅ Fallback logic

**Note:** Tests require internet access. In sandboxed environments, imports and initialization will work but API calls may fail.

### Manual Testing

```python
# Test imports
from data_sources import BinanceClient, CoinGeckoClient, PolymarketSubgraph, PriceAggregator
print("✓ Imports successful")

# Test initialization
binance = BinanceClient()
coingecko = CoinGeckoClient()
polymarket = PolymarketSubgraph()
aggregator = PriceAggregator()
print("✓ All clients initialized")

# Test monitor integration
from monitor import PolymarketMonitor
import yaml
config = yaml.safe_load(open('config.yaml'))
monitor = PolymarketMonitor(config)
print("✓ Monitor initialized with free data sources")
```

---

## 🛠️ Troubleshooting

### "websockets library not installed"

```bash
pip install websockets
```

The bot will work without WebSocket (using REST APIs), but WebSocket provides:
- Real-time updates (<100ms)
- Lower latency
- More efficient

### Rate Limit Errors

If you hit rate limits:
1. **Wait for reset** - Limits reset every 60 seconds
2. **Reduce frequency** - Increase delays between requests
3. **Use caching** - Enable caching in config
4. **Check status** - Monitor rate limit usage

### Connection Errors

If data sources fail to connect:
1. **Check internet** - All sources require internet
2. **Check firewall** - Ensure API domains aren't blocked
3. **Try fallbacks** - Aggregator automatically tries alternatives
4. **Check logs** - See `logs/errors.log` for details

### WebSocket Disconnects

WebSocket may disconnect due to:
- Network issues
- Server maintenance
- Rate limits

The client automatically:
- Retries with exponential backoff (up to 5 times)
- Falls back to REST API
- Logs connection errors

---

## 📚 Additional Resources

- **[Data Sources README](data_sources/README.md)** - Detailed API documentation
- **[Test Suite](test_data_sources.py)** - Example usage patterns
- **[Main README](README.md)** - Bot overview and setup

---

## 💡 Tips & Best Practices

### 1. Use WebSocket for Real-Time Data
```python
# ✅ Good - Real-time updates
aggregator = PriceAggregator(enable_websocket=True)

# ❌ Less efficient - Polling
aggregator = PriceAggregator(enable_websocket=False)
```

### 2. Enable Caching
```yaml
coingecko:
  cache_duration: 60  # Cache for 60 seconds
```

### 3. Monitor Rate Limits
```python
status = monitor.get_data_source_status()
if status['binance']['rate_limit_used'] > 1000:
    print("⚠️ Approaching Binance rate limit")
```

### 4. Handle Errors Gracefully
```python
price = monitor.get_crypto_price('BTC')
if price is None:
    print("Failed to fetch price - using fallback")
    price = fallback_price
```

### 5. Clean Up Resources
```python
try:
    # Use monitor
    price = monitor.get_crypto_price('BTC')
finally:
    # Always cleanup
    monitor.shutdown()
```

---

## ✅ Summary

You now have:
- ✅ **Free crypto prices** from Binance (1200 req/min)
- ✅ **Backup prices** from CoinGecko (50 req/min)
- ✅ **Polymarket data** from The Graph (unlimited)
- ✅ **Smart fallbacks** for maximum reliability
- ✅ **NO API KEYS** required
- ✅ **$0/month** cost

**Total Rate Limit: 1200+ requests/minute**
**Total Cost: $0/month**
**Authentication: None required**

Enjoy trading with free, unlimited data! 🚀
