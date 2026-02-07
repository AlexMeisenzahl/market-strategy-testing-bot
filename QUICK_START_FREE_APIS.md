# Quick Start: Using Free API Clients

## 🚀 Get Started in 3 Minutes

This guide shows you how to use the new **100% free API clients** with no setup required!

## Prerequisites

- Python 3.8+ installed
- Dependencies installed: `pip install -r requirements.txt`

## Step 1: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

This installs:
- `websocket-client` - For Binance WebSocket support
- `gql` - For Polymarket GraphQL queries
- All other existing dependencies

## Step 2: Verify Configuration (30 seconds)

The `config.yaml` file already has everything configured:

```yaml
apis:
  binance:
    enabled: true
    rate_limit_per_minute: 1200
  
  coingecko:
    enabled: true
    rate_limit_per_minute: 50
  
  polymarket_subgraph:
    enabled: true
    url: "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"
```

**No API keys needed!** ✅

## Step 3: Run Tests (1 minute)

Test that everything works:

```bash
# Run mock tests (no internet required)
python test_free_apis_mock.py

# Run live API tests (requires internet)
python test_free_apis.py

# Run existing safety tests
python test_safety.py
```

Expected output:
```
✓ PASS   - Imports
✓ PASS   - Client Initialization
✓ PASS   - Method Existence
✓ PASS   - Cache Functionality
✓ PASS   - Monitor Integration
✓ PASS   - Configuration Validation
============================================================
Results: 6/6 tests passed
```

## Step 4: Use in Your Code (1 minute)

### Option A: Use Data Aggregator (Recommended)

The data aggregator automatically handles fallback and caching:

```python
from apis.data_aggregator import FreeDataAggregator

# Initialize
aggregator = FreeDataAggregator()

# Get crypto price (tries Binance first, falls back to CoinGecko)
btc_price = aggregator.get_crypto_price('BTC')
print(f"BTC Price: ${btc_price:,.2f}")

# Get multiple prices efficiently
prices = aggregator.get_multiple_crypto_prices(['BTC', 'ETH', 'SOL'])
for symbol, price in prices.items():
    print(f"{symbol}: ${price:,.2f}")

# Check source health
health = aggregator.get_all_source_health()
print(f"Sources: {health}")
```

### Option B: Use Individual Clients

Use clients directly for more control:

```python
from apis.binance_client import BinanceClient
from apis.coingecko_client import CoinGeckoClient
from apis.polymarket_subgraph import PolymarketSubgraph

# Binance for fast crypto prices
binance = BinanceClient()
btc_price = binance.get_price('BTC')
print(f"BTC: ${btc_price:,.2f}")

# CoinGecko for market data
coingecko = CoinGeckoClient()
eth_data = coingecko.get_market_data('ETH')
print(f"ETH Market Cap: ${eth_data['market_cap']:,.0f}")

# Polymarket for prediction markets
polymarket = PolymarketSubgraph()
markets = polymarket.get_active_markets(limit=5)
print(f"Found {len(markets)} active markets")
```

### Option C: Use with Existing Bot

The bot automatically uses free data sources:

```python
from bot import ArbitrageBot

# Initialize bot (automatically loads free APIs)
bot = ArbitrageBot()

# Free APIs are ready to use!
bot.run()
```

## Usage Examples

### Example 1: Get Live Crypto Prices

```python
from apis.binance_client import BinanceClient

client = BinanceClient()

# Single price
btc = client.get_price('BTC')
print(f"Bitcoin: ${btc:,.2f}")

# Multiple prices
prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
for symbol, price in prices.items():
    print(f"{symbol}: ${price:,.2f}")

# 24-hour data
ticker = client.get_ticker_24h('BTC')
print(f"24h Change: {ticker['price_change_percent']:.2f}%")
print(f"24h Volume: ${ticker['volume']:,.0f}")
```

### Example 2: Fallback Logic

```python
from apis.data_aggregator import FreeDataAggregator

aggregator = FreeDataAggregator()

# Automatically tries Binance first, falls back to CoinGecko
price = aggregator.get_crypto_price('BTC')

if price:
    print(f"Got price: ${price:,.2f}")
else:
    print("All sources failed (check internet connection)")
```

### Example 3: Polymarket Markets

```python
from apis.polymarket_subgraph import PolymarketSubgraph

client = PolymarketSubgraph()

# Get active markets
markets = client.get_active_markets(limit=10)

for market in markets:
    print(f"Question: {market['question']}")
    print(f"Volume: ${float(market['volume']):,.2f}")
    print(f"Liquidity: ${float(market['liquidityParameter']):,.2f}")
    print()

# Search for specific markets
bitcoin_markets = client.search_markets('bitcoin', limit=5)
print(f"Found {len(bitcoin_markets)} Bitcoin-related markets")
```

### Example 4: Caching for Performance

```python
from apis.data_aggregator import FreeDataAggregator
import time

config = {'cache_ttl_seconds': 10}
aggregator = FreeDataAggregator(config)

# First call fetches from API (slow)
start = time.time()
price1 = aggregator.get_crypto_price('BTC')
elapsed1 = time.time() - start
print(f"First call: {elapsed1:.3f}s")

# Second call uses cache (fast)
start = time.time()
price2 = aggregator.get_crypto_price('BTC')
elapsed2 = time.time() - start
print(f"Cached call: {elapsed2:.3f}s")

# Check cache stats
stats = aggregator.get_cache_stats()
print(f"Cache entries: {stats['valid_entries']}")
```

## Common Tasks

### Check API Health

```python
from apis.data_aggregator import FreeDataAggregator

aggregator = FreeDataAggregator()
health = aggregator.get_all_source_health()

print("API Status:")
print(f"  Binance: {'✓ Healthy' if health['binance'] else '✗ Down'}")
print(f"  CoinGecko: {'✓ Healthy' if health['coingecko'] else '✗ Down'}")
print(f"  Polymarket: {'✓ Healthy' if health['polymarket'] else '✗ Down'}")
```

### Monitor Multiple Cryptos

```python
from apis.binance_client import BinanceClient
import time

client = BinanceClient()
symbols = ['BTC', 'ETH', 'SOL', 'BNB']

while True:
    prices = client.get_multiple_prices(symbols)
    
    print("\n" + "=" * 50)
    for symbol, price in prices.items():
        print(f"{symbol:10} ${price:>12,.2f}")
    
    time.sleep(5)  # Update every 5 seconds
```

### Track Price Changes

```python
from apis.binance_client import BinanceClient

client = BinanceClient()

ticker = client.get_ticker_24h('BTC')

print(f"BTC Price: ${ticker['price']:,.2f}")
print(f"24h Change: {ticker['price_change']:+,.2f} ({ticker['price_change_percent']:+.2f}%)")
print(f"24h High: ${ticker['high']:,.2f}")
print(f"24h Low: ${ticker['low']:,.2f}")
print(f"24h Volume: ${ticker['volume']:,.0f}")
```

## Troubleshooting

### "Failed to initialize free data sources"

**Solution:** Check internet connection and verify APIs are accessible:

```bash
# Test connectivity
curl https://api.binance.com/api/v3/ping
curl https://api.coingecko.com/api/v3/ping
```

### "Rate limit exceeded"

**Solution:** Enable caching or increase cache TTL:

```python
config = {
    'cache_ttl_seconds': 30  # Increase from 10 to 30 seconds
}
aggregator = FreeDataAggregator(config)
```

### "All sources returning None"

**Solution:** Check if APIs are blocked by your network:

```python
from apis.binance_client import BinanceClient
from apis.coingecko_client import CoinGeckoClient

binance = BinanceClient()
coingecko = CoinGeckoClient()

print(f"Binance: {'✓' if binance.ping() else '✗'}")
print(f"CoinGecko: {'✓' if coingecko.ping() else '✗'}")
```

## Best Practices

1. **Use Data Aggregator** - Provides automatic fallback and caching
2. **Enable Caching** - Reduce API calls and improve performance
3. **Check Health** - Monitor source health before making requests
4. **Batch Requests** - Use `get_multiple_prices()` for multiple symbols
5. **Handle Errors** - Always check if returned value is None

## Next Steps

- Read full documentation: `FREE_APIS_README.md`
- Run the bot: `python bot.py`
- View logs: `logs/errors.log`
- Customize config: `config.yaml`

## Need Help?

1. Run tests: `python test_free_apis_mock.py`
2. Check documentation: `FREE_APIS_README.md`
3. View API docs:
   - Binance: https://binance-docs.github.io/apidocs/spot/en/
   - CoinGecko: https://www.coingecko.com/api/documentation
   - The Graph: https://thegraph.com/docs/

---

**Total Setup Time: 3 minutes** ⏱️  
**Cost: $0/month** 💰  
**API Keys Required: 0** 🔑
