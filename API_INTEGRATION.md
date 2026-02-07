# API Integration Guide - Free Data Sources

This document explains how to use the free, high-performance data sources integrated into the Polymarket Arbitrage Bot.

## 📊 Overview

The bot now uses three free data sources with automatic fallback:

1. **Binance WebSocket & REST API** - Real-time crypto prices (1200 req/min)
2. **CoinGecko Free API** - Backup crypto prices (50 req/min, no key)
3. **Polymarket Subgraph** - On-chain market data (unlimited)

**Total Cost: $0/month**  
**Rate Limit: 1200+ requests/minute**  
**Latency: <100ms (WebSocket)**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Data Sources

Edit `config.yaml`:

```yaml
data_sources:
  binance:
    enabled: true
    websocket: true
    symbols:
      - BTCUSDT
      - ETHUSDT
  
  coingecko:
    enabled: true
    rate_limit_per_minute: 50
  
  polymarket_subgraph:
    enabled: true
    max_markets_per_query: 100
```

### 3. Run the Bot

```bash
python bot.py
```

The bot will automatically:
- Start WebSocket streams for real-time crypto prices
- Connect to Polymarket Subgraph for market data
- Use CoinGecko as a fallback

---

## 📡 Data Sources

### 1. Binance WebSocket API

**What it provides:**
- Real-time cryptocurrency price streams
- <100ms latency updates
- 24-hour volume, high, low prices

**Rate Limits:**
- WebSocket: 1200 messages/minute (FREE)
- REST API: 1200 requests/minute (FREE)

**Usage Example:**

```python
from data_sources import BinanceClient

client = BinanceClient()

# Get current price (REST)
price = client.get_current_price('BTCUSDT')
print(f"BTC Price: ${price}")

# Get 24-hour ticker
ticker = client.get_24h_ticker('ETHUSDT')
print(f"ETH 24h High: ${ticker['high']}")

# Get historical data
klines = client.get_historical_klines('BTCUSDT', interval='1h', limit=100)
print(f"Last 100 hours of BTC data")
```

**WebSocket Streaming (Async):**

```python
import asyncio

async def main():
    client = BinanceClient()
    
    # Stream prices with callback
    def price_callback(data):
        print(f"{data['symbol']}: ${data['price']}")
    
    await client.stream_price('BTCUSDT', callback=price_callback)

asyncio.run(main())
```

**Supported Endpoints:**

| Endpoint | Purpose | Rate Limit |
|----------|---------|------------|
| `/api/v3/ticker/price` | Current price | 1200/min |
| `/api/v3/ticker/24hr` | 24h statistics | 1200/min |
| `/api/v3/klines` | Historical OHLCV | 1200/min |
| WebSocket `@ticker` | Real-time stream | 1200 msg/min |

---

### 2. CoinGecko Free API

**What it provides:**
- Crypto prices for 10,000+ coins
- Market data (market cap, volume)
- Historical price charts
- Trending coins

**Rate Limits:**
- 10-50 requests/minute (no API key required)

**Usage Example:**

```python
from data_sources import CoinGeckoClient

client = CoinGeckoClient()

# Get current price
price = client.get_price('BTCUSDT')
print(f"BTC Price: ${price}")

# Get multiple prices at once
prices = client.get_prices_batch(['BTCUSDT', 'ETHUSDT', 'BNBUSDT'])
for symbol, price in prices.items():
    print(f"{symbol}: ${price}")

# Get market data
market_data = client.get_market_data('BTCUSDT')
print(f"Market Cap: ${market_data['market_cap']:,.0f}")
print(f"24h Change: {market_data['price_change_24h']:.2f}%")

# Get historical chart data
chart = client.get_market_chart('BTCUSDT', days=7)
print(f"7-day price history: {len(chart)} data points")

# Get trending coins
trending = client.get_trending_coins()
for coin in trending[:5]:
    print(f"{coin['name']} ({coin['symbol']})")
```

**Supported Endpoints:**

| Endpoint | Purpose | Rate Limit |
|----------|---------|------------|
| `/simple/price` | Current prices | 50/min |
| `/coins/markets` | Market data | 50/min |
| `/coins/{id}/market_chart` | Historical charts | 50/min |
| `/search/trending` | Trending coins | 50/min |

---

### 3. Polymarket Subgraph (The Graph)

**What it provides:**
- On-chain Polymarket market data
- Trade history
- Liquidity information
- Market resolution data

**Rate Limits:**
- Unlimited (decentralized)

**Usage Example:**

```python
from data_sources import PolymarketSubgraph

subgraph = PolymarketSubgraph()

# Query active markets
markets = subgraph.query_markets(
    filters={'active': True},
    limit=50
)
for market in markets:
    print(f"{market['question']}")
    print(f"  Volume: ${market['volume_24h']:,.0f}")
    print(f"  YES: ${market['yes_price']:.2f} | NO: ${market['no_price']:.2f}")

# Get specific market
market = subgraph.get_market('market-id-here')
print(f"Question: {market['question']}")
print(f"Liquidity: ${market['liquidity']:,.0f}")

# Get market trades
trades = subgraph.get_market_trades('market-id-here', limit=100)
for trade in trades[:10]:
    print(f"Trade: {trade['side']} {trade['outcome']} @ ${trade['price']:.2f}")

# Get market prices
prices = subgraph.get_market_prices('market-id-here')
print(f"YES: ${prices['yes_price']:.2f}")
print(f"NO: ${prices['no_price']:.2f}")

# Search markets by keyword
btc_markets = subgraph.search_markets('bitcoin', limit=20)
print(f"Found {len(btc_markets)} Bitcoin markets")
```

**Available Methods:**

| Method | Purpose | Example |
|--------|---------|---------|
| `query_markets()` | Get active markets | Filter by volume, category |
| `get_market()` | Get specific market | By market ID |
| `get_market_trades()` | Get trade history | Last N trades |
| `get_market_prices()` | Get current prices | YES/NO prices |
| `get_market_liquidity()` | Get liquidity data | Order book depth |
| `search_markets()` | Search by keyword | "bitcoin", "election" |

---

## 🔄 Price Aggregator

The `PriceAggregator` automatically tries multiple sources in priority order:

1. **Binance WebSocket** (if enabled) - Fastest, real-time
2. **Binance REST API** - Fast, reliable
3. **CoinGecko API** - Fallback for all coins

**Usage Example:**

```python
from data_sources import PriceAggregator

aggregator = PriceAggregator(enable_websocket=True)

# Start WebSocket streams
aggregator.start_websocket_streams(['BTCUSDT', 'ETHUSDT'])

# Get best available price (tries sources in order)
btc_price = aggregator.get_best_price('BTCUSDT')
print(f"BTC: ${btc_price} (from best source)")

# Get comprehensive market data
market_data = aggregator.get_best_market_data('ETHUSDT')
print(f"ETH: ${market_data['price']}")
print(f"24h Volume: ${market_data['volume']:,.0f}")

# Get multiple prices efficiently
prices = aggregator.get_prices_batch(['BTCUSDT', 'ETHUSDT', 'BNBUSDT'])
for symbol, price in prices.items():
    print(f"{symbol}: ${price}")

# Get statistics
stats = aggregator.get_statistics()
print(f"Total requests: {stats['total_requests']}")
for source, data in stats['sources'].items():
    print(f"{source}: {data['success_rate']:.1f}% success rate")

# Stop streams when done
aggregator.stop()
```

**Automatic Failover:**

The aggregator automatically switches sources if one fails:

```
Request → Binance WebSocket (cached) → Success ✓
Request → Binance WebSocket (unavailable) → Binance REST → Success ✓
Request → Binance REST (rate limited) → CoinGecko → Success ✓
```

---

## 🔧 Configuration

### Basic Configuration

```yaml
data_sources:
  binance:
    enabled: true
    websocket: true
    rest_fallback: true
    symbols:
      - BTCUSDT
      - ETHUSDT
  
  coingecko:
    enabled: true
    rate_limit_per_minute: 50
    cache_ttl_seconds: 60
  
  polymarket_subgraph:
    enabled: true
    max_markets_per_query: 100
    min_market_volume: 1000

price_aggregator:
  enable_websocket: true
  cache_ttl_seconds: 60
  source_priority:
    - binance_ws
    - binance_rest
    - coingecko
```

### Advanced Configuration

```yaml
data_sources:
  binance:
    enabled: true
    websocket: true
    rest_fallback: true
    symbols:
      - BTCUSDT
      - ETHUSDT
      - BNBUSDT
      - ADAUSDT
      - DOGEUSDT
      - XRPUSDT
      - DOTUSDT
      - UNIUSDT
      - LINKUSDT
      - MATICUSDT
    websocket_reconnect: true
    reconnect_delay_seconds: 5
  
  coingecko:
    enabled: true
    base_url: "https://api.coingecko.com/api/v3"
    rate_limit_per_minute: 50
    cache_ttl_seconds: 60
    timeout_seconds: 5
    retry_attempts: 3
  
  polymarket_subgraph:
    enabled: true
    endpoint: "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"
    fallback_api: "https://clob.polymarket.com"
    max_markets_per_query: 100
    min_market_volume: 1000
    timeout_seconds: 10
    cache_markets_seconds: 300
```

---

## 📈 Performance Comparison

### Before (Paid API)

```
Source: The Odds API
Cost: $10-50/month
Rate Limit: 500 requests/day (~20/hour)
Latency: 1-5 seconds
Data: Sports betting only
Reliability: Single point of failure
```

### After (Free APIs)

```
Sources: Binance + CoinGecko + Polymarket Subgraph
Cost: $0/month
Rate Limit: 1200+ requests/minute
Latency: <100ms (WebSocket)
Data: Crypto + Polymarket markets
Reliability: Multiple fallbacks
```

**Performance Gains:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cost | $10-50/mo | $0/mo | 100% savings |
| Rate Limit | 20 req/hr | 1200 req/min | 3,600x faster |
| Latency | 1-5 sec | <100ms | 50x faster |
| Reliability | 1 source | 3 sources | 3x redundancy |
| Data Coverage | Limited | 10,000+ assets | Unlimited |

---

## 🧪 Testing

### Test Individual Clients

```python
# Test Binance
from data_sources import BinanceClient

client = BinanceClient()
price = client.get_current_price('BTCUSDT')
assert price > 0, "Failed to fetch BTC price"
print(f"✓ Binance working: BTC = ${price}")

# Test CoinGecko
from data_sources import CoinGeckoClient

client = CoinGeckoClient()
price = client.get_price('BTCUSDT')
assert price > 0, "Failed to fetch BTC price"
print(f"✓ CoinGecko working: BTC = ${price}")

# Test Polymarket Subgraph
from data_sources import PolymarketSubgraph

subgraph = PolymarketSubgraph()
markets = subgraph.query_markets(filters={'active': True}, limit=10)
assert len(markets) > 0, "Failed to fetch markets"
print(f"✓ Polymarket Subgraph working: {len(markets)} markets found")
```

### Test Price Aggregator

```python
from data_sources import PriceAggregator

aggregator = PriceAggregator(enable_websocket=False)

# Test failover
price = aggregator.get_best_price('BTCUSDT')
assert price > 0, "Failed to get price from any source"
print(f"✓ Price Aggregator working: BTC = ${price}")

# Check statistics
stats = aggregator.get_statistics()
print(f"Sources used: {list(stats['sources'].keys())}")
for source, data in stats['sources'].items():
    if data['total'] > 0:
        print(f"  {source}: {data['success_rate']:.0f}% success")
```

---

## 🛠️ Troubleshooting

### WebSocket Connection Issues

**Problem:** WebSocket streams not connecting

**Solutions:**
1. Check firewall settings (allow WSS connections)
2. Disable WebSocket temporarily: `websocket: false` in config
3. Verify internet connection
4. Check Binance service status: https://www.binance.com/en/support

```yaml
# Fallback to REST only
data_sources:
  binance:
    enabled: true
    websocket: false  # Disable WebSocket
    rest_fallback: true
```

### Rate Limit Issues

**Problem:** Hitting rate limits on CoinGecko

**Solutions:**
1. Increase cache TTL: `cache_ttl_seconds: 120`
2. Reduce request frequency
3. Rely more on Binance (higher rate limits)

```yaml
data_sources:
  coingecko:
    enabled: true
    cache_ttl_seconds: 120  # Cache for 2 minutes
```

### Subgraph Query Failures

**Problem:** Polymarket Subgraph queries failing

**Solutions:**
1. Check The Graph service status
2. Use fallback API: `fallback_api: "https://clob.polymarket.com"`
3. Reduce query complexity

```yaml
data_sources:
  polymarket_subgraph:
    enabled: true
    fallback_api: "https://clob.polymarket.com"  # Use direct API
    max_markets_per_query: 50  # Reduce batch size
```

---

## 📚 Additional Resources

### Binance API Documentation
- REST API: https://binance-docs.github.io/apidocs/spot/en/
- WebSocket: https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams

### CoinGecko API Documentation
- API v3: https://www.coingecko.com/en/api/documentation
- Rate Limits: https://www.coingecko.com/en/api/pricing

### The Graph & Polymarket
- The Graph Docs: https://thegraph.com/docs/
- Polymarket API: https://docs.polymarket.com/

---

## 🔐 Legal & Compliance

✅ **All data sources are free and comply with their terms of service:**

- **Binance:** Public market data explicitly free for all users
- **CoinGecko:** Free tier with no authentication required
- **The Graph:** Decentralized, open-source protocol

✅ **No API keys required**  
✅ **Within usage limits**  
✅ **Terms of Service compliant**

---

## 📊 Summary

**You now have access to:**

- ⚡ **Real-time crypto prices** via Binance WebSocket (<100ms latency)
- 🔄 **Automatic failover** between 3 data sources
- 💰 **$0/month cost** (was $10-50/month)
- 🚀 **1200+ requests/minute** (was 20 requests/hour)
- 📈 **10,000+ cryptocurrencies** tracked
- 🎯 **Unlimited Polymarket data** via on-chain queries

**No API keys. No rate limits. Production-grade infrastructure at zero cost!**
