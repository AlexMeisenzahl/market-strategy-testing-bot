# Free API Clients Documentation

## Overview

This bot now uses **100% free public data sources** with **no API keys required**. The implementation provides:

- **Binance Public API** - Real-time crypto prices (1200 req/min)
- **CoinGecko API** - Market data, trends, 13,000+ cryptocurrencies (50 req/min)
- **Polymarket Subgraph** - Prediction market data via GraphQL (unlimited)
- **Intelligent Fallback** - Automatic switching between sources
- **Smart Caching** - Reduces API calls and improves performance

## Architecture

```
┌─────────────────┐
│   Monitor.py    │
│   (Main Bot)    │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  FreeDataAggregator     │
│  (Combines all sources) │
└────────┬────────────────┘
         │
    ┌────┴────┬────────┬──────────┐
    v         v        v          v
┌─────────┐ ┌────────┐ ┌────────────┐
│ Binance │ │CoinGecko│ │ Polymarket │
│ Client  │ │ Client  │ │  Subgraph  │
└─────────┘ └────────┘ └────────────┘
     │          │            │
     v          v            v
  Binance    CoinGecko   The Graph
   API         API       Subgraph
```

## API Clients

### 1. BinanceClient (`apis/binance_client.py`)

Free Binance API client for real-time cryptocurrency prices.

**Features:**
- No authentication required
- 1200 requests per minute
- Real-time price data
- 24-hour ticker statistics
- Automatic rate limiting

**Usage:**
```python
from apis.binance_client import BinanceClient

client = BinanceClient()

# Get single crypto price
btc_price = client.get_price('BTC')  # Returns: 43521.50

# Get 24-hour ticker data
eth_ticker = client.get_ticker_24h('ETH')
# Returns: {
#   'price': 2345.67,
#   'volume': 1234567,
#   'price_change': 45.23,
#   'price_change_percent': 1.97
# }

# Get multiple prices efficiently
prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
# Returns: {'BTCUSDT': 43521.50, 'ETHUSDT': 2345.67, 'SOLUSDT': 98.32}

# Check connectivity
is_healthy = client.ping()  # Returns: True/False
```

**Rate Limiting:**
- Automatically enforced within the client
- Waits when approaching limit
- No manual intervention needed

### 2. CoinGeckoClient (`apis/coingecko_client.py`)

CoinGecko API client for comprehensive crypto market data.

**Features:**
- No authentication required
- 50 requests per minute (free tier)
- 13,000+ cryptocurrencies
- Market cap, volume, price changes
- Automatic rate limiting

**Usage:**
```python
from apis.coingecko_client import CoinGeckoClient

client = CoinGeckoClient()

# Get single crypto price
btc_price = client.get_price('BTC')  # Returns: 43521.50

# Get comprehensive market data
eth_data = client.get_market_data('ETH')
# Returns: {
#   'price': 2345.67,
#   'market_cap': 281000000000,
#   'volume_24h': 12345678900,
#   'price_change_24h': 45.23,
#   'price_change_percentage_24h': 1.97,
#   'high_24h': 2400.00,
#   'low_24h': 2300.00
# }

# Get multiple prices
prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
# Returns: {'BTC': 43521.50, 'ETH': 2345.67, 'SOL': 98.32}

# Search for a coin
results = client.search_coin('bitcoin')

# Check connectivity
is_healthy = client.ping()  # Returns: True/False
```

**Supported Symbols:**
- BTC, ETH, SOL, USDT, USDC, BNB, ADA, DOGE, XRP, DOT, MATIC, AVAX, LINK, UNI, ATOM
- Automatically maps symbols to CoinGecko IDs

### 3. PolymarketSubgraph (`apis/polymarket_subgraph.py`)

GraphQL client for Polymarket prediction market data.

**Features:**
- No authentication required
- Unlimited rate limits (decentralized)
- Real-time market data
- GraphQL queries for flexibility

**Usage:**
```python
from apis.polymarket_subgraph import PolymarketSubgraph

client = PolymarketSubgraph()

# Get active markets
markets = client.get_active_markets(limit=10)
# Returns list of markets with:
# - id, question, outcomes, outcomePrices
# - liquidityParameter, volume, endDate

# Get specific market by ID
market = client.get_market_by_id('0x1234...')

# Get market odds (YES/NO prices)
odds = client.get_market_odds('0x1234...')
# Returns: {
#   'yes': 0.52,
#   'no': 0.48,
#   'market_id': '0x1234...',
#   'question': 'Will BTC reach $100k?',
#   'volume': 123456.78,
#   'liquidity': 50000.00
# }

# Search markets by text
markets = client.search_markets('bitcoin', limit=10)

# Get high-volume markets
markets = client.get_markets_by_volume(limit=10, min_volume=10000)

# Check connectivity
is_healthy = client.ping()  # Returns: True/False
```

### 4. FreeDataAggregator (`apis/data_aggregator.py`)

Combines all free data sources with intelligent fallback logic.

**Features:**
- Automatic source selection
- Intelligent fallback (Binance → CoinGecko)
- Smart caching (reduces API calls)
- Health monitoring for all sources

**Usage:**
```python
from apis.data_aggregator import FreeDataAggregator

# Initialize with config
config = {
    'binance': {'rate_limit_per_minute': 1200},
    'coingecko': {'rate_limit_per_minute': 50},
    'polymarket_subgraph': {'query_timeout_seconds': 10},
    'cache_ttl_seconds': 10
}

aggregator = FreeDataAggregator(config)

# Get crypto price (tries Binance first, falls back to CoinGecko)
btc_price = aggregator.get_crypto_price('BTC')

# Get comprehensive market data
eth_data = aggregator.get_crypto_market_data('ETH')

# Get multiple prices efficiently
prices = aggregator.get_multiple_crypto_prices(['BTC', 'ETH', 'SOL'])

# Get Polymarket odds
odds = aggregator.get_polymarket_odds('0x1234...')

# Get active Polymarket markets
markets = aggregator.get_polymarket_active_markets(limit=10)

# Check health of all sources
health = aggregator.get_all_source_health()
# Returns: {
#   'binance': True,
#   'coingecko': True,
#   'polymarket': True
# }

# Get cache statistics
stats = aggregator.get_cache_stats()
# Returns: {
#   'total_entries': 15,
#   'valid_entries': 12,
#   'expired_entries': 3,
#   'cache_ttl_seconds': 10
# }

# Clear cache manually
aggregator.clear_cache()
```

## Integration with Monitor

The `PolymarketMonitor` class automatically initializes the `FreeDataAggregator`:

```python
from monitor import PolymarketMonitor
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize monitor (automatically initializes data aggregator)
monitor = PolymarketMonitor(config)

# Get crypto price directly
btc_price = monitor.get_crypto_price('BTC')

# Check data source health
health = monitor.get_data_source_health()

# Get market prices (automatically uses best source)
prices = monitor.get_market_prices('btc-above-100k')
```

## Configuration

Edit `config.yaml` to configure the free APIs:

```yaml
apis:
  # Binance Public API (Free, No Authentication)
  binance:
    enabled: true
    base_url: "https://api.binance.com/api/v3"
    websocket_url: "wss://stream.binance.com:9443/ws"
    rate_limit_per_minute: 1200
  
  # CoinGecko API (Free, No Authentication)
  coingecko:
    enabled: true
    base_url: "https://api.coingecko.com/api/v3"
    rate_limit_per_minute: 50
  
  # Polymarket Subgraph (Free, Unlimited)
  polymarket_subgraph:
    enabled: true
    url: "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"
    query_timeout_seconds: 10

# Data Aggregator Settings
data_aggregator:
  cache_ttl_seconds: 10          # Cache data for 10 seconds
  prefer_binance: true           # Prefer Binance over CoinGecko (faster)
  fallback_enabled: true         # Enable automatic fallback to backup sources
```

## Caching Strategy

The data aggregator implements intelligent caching to minimize API calls:

1. **Cache on First Request**: Data is cached when first fetched
2. **Serve from Cache**: Subsequent requests within TTL are served from cache
3. **Automatic Expiration**: Cache entries expire after `cache_ttl_seconds`
4. **Per-Symbol Caching**: Each symbol/market is cached independently

**Benefits:**
- Reduced API calls (respects rate limits)
- Faster response times
- Lower latency for repeated queries

**Example:**
```python
# First call fetches from API (takes ~100ms)
price1 = aggregator.get_crypto_price('BTC')

# Second call within 10 seconds uses cache (takes <1ms)
price2 = aggregator.get_crypto_price('BTC')

# After 10 seconds, cache expires and fetches fresh data
time.sleep(11)
price3 = aggregator.get_crypto_price('BTC')  # Fresh from API
```

## Fallback Logic

The aggregator implements automatic fallback:

1. **Try Primary Source** (Binance for crypto)
2. **Check Health**: If primary fails, check health status
3. **Try Secondary Source** (CoinGecko for crypto)
4. **Return Cached Data**: If all sources fail, return cached data if available
5. **Return None**: If no data available, return None

**Example Flow:**
```
get_crypto_price('BTC')
  └─> Try Binance
       ├─> Success? Return price
       └─> Failed?
            └─> Try CoinGecko
                 ├─> Success? Return price
                 └─> Failed?
                      └─> Check cache
                           ├─> Found? Return cached price
                           └─> Not found? Return None
```

## Rate Limiting

All clients implement automatic rate limiting:

### Binance (1200 req/min)
- Tracks requests per minute
- Automatically waits when approaching limit
- Resets counter every 60 seconds

### CoinGecko (50 req/min)
- Tracks requests per minute
- Automatically waits when approaching limit
- More conservative buffer (45/50)

### Polymarket Subgraph (Unlimited)
- Minimal rate limiting (0.1s between requests)
- Respects GraphQL endpoint

**No manual rate limit management needed!**

## Error Handling

All clients implement robust error handling:

```python
try:
    price = client.get_price('BTC')
    if price is None:
        print("API call failed or returned no data")
except Exception as e:
    print(f"Error: {e}")
```

**Common scenarios:**
- **Network timeout**: Returns None, tries fallback
- **API rate limit**: Automatically waits and retries
- **Invalid response**: Returns None, logs error
- **API downtime**: Switches to fallback source

## Testing

Two test suites are available:

### 1. Live API Tests (`test_free_apis.py`)
Tests actual API connectivity (requires internet):
```bash
python test_free_apis.py
```

### 2. Mock Tests (`test_free_apis_mock.py`)
Tests code structure and logic (no internet required):
```bash
python test_free_apis_mock.py
```

## Benefits Summary

✅ **100% Free** - No API keys, subscriptions, or costs  
✅ **High Rate Limits** - 1200+ requests/minute  
✅ **Reliable** - Multiple fallback sources  
✅ **Comprehensive** - 13,000+ cryptocurrencies  
✅ **Real-Time** - Live price updates  
✅ **Intelligent** - Automatic fallback and caching  
✅ **Easy to Use** - Simple API, no authentication  
✅ **Production Ready** - Used by major applications  

## Troubleshooting

### "Failed to initialize free data sources"
- Check internet connectivity
- Verify config.yaml has correct API settings
- Check if APIs are accessible from your network

### "All sources returning None"
- APIs may be temporarily down
- Check API status pages
- Enable caching to use cached data during outages

### "Rate limit exceeded"
- Increase `cache_ttl_seconds` in config
- Reduce request frequency
- Use `get_multiple_prices()` for batch requests

## Support

For issues or questions:
1. Check API documentation:
   - Binance: https://binance-docs.github.io/apidocs/spot/en/
   - CoinGecko: https://www.coingecko.com/api/documentation
   - The Graph: https://thegraph.com/docs/
2. Run tests: `python test_free_apis_mock.py`
3. Check logs: `logs/errors.log`

## License & Usage

All APIs used are public and free:
- **Binance**: Public API, no authentication
- **CoinGecko**: Free tier, no key required
- **Polymarket Subgraph**: Decentralized, unlimited

Respectful usage is expected. The clients implement automatic rate limiting to ensure compliance with API terms of service.
