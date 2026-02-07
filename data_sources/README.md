# Free Data Sources - No API Keys Required

This directory contains free, high-performance data sources that require **NO API KEYS** and provide **UNLIMITED or HIGH RATE LIMITS**.

## 📊 Available Data Sources

### 1. **Binance Client** (`binance_client.py`)
- **Real-time cryptocurrency prices via WebSocket**
- **Historical OHLCV data via REST API**
- **Rate Limit:** 1200 requests/minute (FREE)
- **Latency:** <100ms for WebSocket updates
- **Coverage:** BTC, ETH, and all major cryptocurrencies
- **Used By:** Bloomberg Terminal, CoinMarketCap, TradingView

**Features:**
- WebSocket for real-time price streams
- REST API fallback for reliability
- 24-hour statistics (volume, price changes, highs/lows)
- Historical candlestick data
- Automatic rate limiting
- Connection health monitoring

**Example:**
```python
from data_sources import BinanceClient

# Initialize client
client = BinanceClient(symbols=['BTCUSDT', 'ETHUSDT'])

# Start WebSocket for real-time prices
client.start_websocket()

# Get current price
btc_price = client.get_price('BTCUSDT')
print(f"BTC: ${btc_price:,.2f}")

# Get 24h statistics
stats = client.get_24h_stats('BTCUSDT')
print(f"24h Change: {stats['price_change_pct_24h']:.2f}%")

# Get historical data
klines = client.get_historical_klines('BTCUSDT', interval='1h', limit=100)
```

### 2. **CoinGecko Client** (`coingecko_client.py`)
- **10,000+ cryptocurrency prices**
- **Market data (market cap, volume, etc.)**
- **Historical charts**
- **Rate Limit:** 10-50 requests/minute (FREE, no key)
- **Used By:** DeFi apps, portfolio trackers, Uniswap

**Features:**
- Simple price lookups
- Detailed market data
- Historical price charts
- Search functionality
- Automatic caching
- Symbol-to-ID conversion

**Example:**
```python
from data_sources import CoinGeckoClient

# Initialize client
client = CoinGeckoClient()

# Get price (auto-converts symbols)
btc_price = client.get_price('BTC')  # or 'bitcoin'
print(f"BTC: ${btc_price:,.2f}")

# Get multiple prices
prices = client.get_prices(['BTC', 'ETH', 'SOL'])

# Get detailed market data
market_data = client.get_market_data('bitcoin')
print(f"Market Cap: ${market_data['market_cap_usd']:,.0f}")
print(f"Volume 24h: ${market_data['volume_24h_usd']:,.0f}")

# Get historical prices
historical = client.get_historical_prices('bitcoin', days=7)
```

### 3. **Polymarket Subgraph** (`polymarket_subgraph.py`)
- **On-chain Polymarket data via The Graph**
- **All prediction markets**
- **Market trades, volumes, and statistics**
- **Rate Limit:** Unlimited (decentralized)
- **Used By:** Polymarket.com frontend itself

**Features:**
- GraphQL queries for on-chain data
- Active markets listing
- Market details and statistics
- Trade history
- Search functionality
- Fallback to Polymarket API

**Example:**
```python
from data_sources import PolymarketSubgraph

# Initialize client
client = PolymarketSubgraph(use_subgraph=True)

# Get active markets
markets = client.get_markets(active_only=True, limit=10)
for market in markets:
    print(f"{market['question']}: ${market['volume']:,.0f} volume")

# Get market details
market = client.get_market('market_id_here')
print(f"Volume: ${market['volume']:,.0f}")
print(f"Liquidity: ${market['liquidity']:,.0f}")

# Get market prices
prices = client.get_market_prices('market_id_here')
print(f"YES: ${prices['yes']:.3f}, NO: ${prices['no']:.3f}")

# Search markets
results = client.search_markets('election')
```

### 4. **Price Aggregator** (`price_aggregator.py`)
- **Multi-source price feeds with automatic fallbacks**
- **Intelligent failover logic**
- **Maximum uptime and reliability**

**Fallback Chain:**
1. **Primary:** Binance WebSocket (real-time, <100ms)
2. **Fallback 1:** Binance REST API
3. **Fallback 2:** CoinGecko API

**Features:**
- Automatic source selection
- Seamless failover
- Statistics tracking
- Symbol normalization
- WebSocket management

**Example:**
```python
from data_sources import PriceAggregator

# Initialize aggregator
aggregator = PriceAggregator(
    symbols=['BTC', 'ETH', 'SOL'],
    enable_websocket=True
)

# Get price (auto-selects best source)
btc_price = aggregator.get_price('BTC')
print(f"BTC: ${btc_price:,.2f}")

# Get multiple prices
prices = aggregator.get_prices(['BTC', 'ETH'])

# Get market data
market_data = aggregator.get_market_data('BTC')
print(f"Source: {market_data['source']}")
print(f"24h Change: {market_data['price_change_pct_24h']:.2f}%")

# Get historical data
historical = aggregator.get_historical_prices('BTC', days=7)

# Check status
status = aggregator.get_status()
print(f"Success Rate: {status['aggregator']['success_rate']:.1f}%")

# Cleanup
aggregator.shutdown()
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - HTTP requests
- `websockets` - WebSocket support for Binance
- `gql[all]` - GraphQL for Polymarket Subgraph

### 2. Configure in `config.yaml`
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
  cache_duration: 60

# Polymarket Subgraph (UNLIMITED - via The Graph)
polymarket:
  use_subgraph: true
  use_api_fallback: true
```

### 3. Use in Your Code
```python
import yaml
from data_sources import PriceAggregator, PolymarketSubgraph

# Load config
config = yaml.safe_load(open('config.yaml'))

# Initialize data sources
aggregator = PriceAggregator(
    symbols=config['binance']['symbols'],
    enable_websocket=config['binance']['enable_websocket']
)

polymarket = PolymarketSubgraph(
    use_subgraph=config['polymarket']['use_subgraph']
)

# Get crypto prices
btc = aggregator.get_price('BTC')
eth = aggregator.get_price('ETH')

# Get Polymarket markets
markets = polymarket.get_markets(active_only=True)
```

## 🧪 Testing

Run the test suite to verify all data sources:
```bash
python3 test_data_sources.py
```

This will test:
- Binance REST API (WebSocket requires async)
- CoinGecko API
- Polymarket Subgraph/API
- Price Aggregator

## 📈 Rate Limits

| Source | Free Tier | Rate Limit | Authentication |
|--------|-----------|------------|----------------|
| **Binance WebSocket** | ✅ Yes | 1200 req/min | ❌ None |
| **Binance REST** | ✅ Yes | 1200 req/min | ❌ None |
| **CoinGecko** | ✅ Yes | 10-50 req/min | ❌ None |
| **Polymarket Subgraph** | ✅ Yes | Unlimited* | ❌ None |
| **Polymarket API** | ✅ Yes | ~100 req/min | ❌ None |

*The Graph subgraph is decentralized and has no practical rate limits.

## 🔄 Automatic Fallbacks

The Price Aggregator automatically handles failures:

1. **Binance WebSocket fails** → Falls back to Binance REST
2. **Binance REST fails** → Falls back to CoinGecko
3. **All sources fail** → Returns `None` and logs error

This ensures maximum uptime even if one data source is temporarily unavailable.

## 🛡️ Error Handling

All clients include:
- Automatic retry logic
- Rate limit detection and waiting
- Connection health monitoring
- Graceful degradation
- Detailed error logging

## 📚 API Documentation

### BinanceClient Methods
- `start_websocket(callback)` - Start real-time price stream
- `stop_websocket()` - Stop WebSocket connection
- `get_price(symbol)` - Get current price
- `get_prices(symbols)` - Get multiple prices
- `get_24h_stats(symbol)` - Get 24-hour statistics
- `get_historical_klines(symbol, interval, limit)` - Get OHLCV data
- `get_connection_status()` - Get connection health
- `is_healthy()` - Check if connection is healthy

### CoinGeckoClient Methods
- `get_price(coin_id, vs_currency)` - Get current price
- `get_prices(coin_ids, vs_currency)` - Get multiple prices
- `get_market_data(coin_id)` - Get detailed market data
- `get_historical_prices(coin_id, days)` - Get historical prices
- `search_coins(query)` - Search for coins
- `get_rate_limit_status()` - Get rate limit status

### PolymarketSubgraph Methods
- `get_markets(active_only, limit)` - Get market list
- `get_market(market_id)` - Get market details
- `get_market_prices(market_id)` - Get YES/NO prices
- `get_market_trades(market_id, limit)` - Get trade history
- `search_markets(query, limit)` - Search markets
- `get_stats()` - Get platform statistics

### PriceAggregator Methods
- `get_price(symbol, source)` - Get price with fallbacks
- `get_prices(symbols, source)` - Get multiple prices
- `get_market_data(symbol)` - Get market data
- `get_historical_prices(symbol, days, interval)` - Get history
- `add_symbol(symbol)` - Add symbol to track
- `remove_symbol(symbol)` - Remove symbol
- `get_status()` - Get status of all sources
- `shutdown()` - Close all connections

## 💡 Tips

1. **Use WebSocket for real-time data** - Much faster than polling REST APIs
2. **Enable caching** - Reduces API calls and improves performance
3. **Monitor rate limits** - Use `get_status()` methods to track usage
4. **Handle errors gracefully** - All methods return `None` on failure
5. **Clean up resources** - Call `shutdown()` when done

## 🔗 External Resources

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [CoinGecko API Documentation](https://www.coingecko.com/api/documentation)
- [The Graph Documentation](https://thegraph.com/docs/)
- [Polymarket API Documentation](https://docs.polymarket.com/)

## 📝 License

These data sources use public APIs that are free to use. No API keys or authentication required.

---

**Total Cost: $0/month | Rate Limit: 1200+ req/min | Latency: <100ms**
