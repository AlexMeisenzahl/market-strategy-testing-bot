# Free API Data Sources

This directory contains **100% FREE** data source clients that require **NO API KEYS**.

## Overview

Replace rate-limited, paid APIs with unlimited free data sources:

- **Binance API** - Real-time crypto prices (1200 req/min, WebSocket support)
- **CoinGecko API** - Fallback crypto prices (50 req/min)
- **Polymarket Subgraph** - On-chain prediction market data (GraphQL, unlimited)
- **Price Aggregator** - Multi-source consensus pricing with outlier detection

## Features

✅ **No API Keys Required** - All endpoints are public  
✅ **No Cost** - $0/month forever  
✅ **High Rate Limits** - Binance: 1200 req/min, effectively unlimited WebSocket  
✅ **Reliable** - Multiple fallback sources  
✅ **Real-Time** - WebSocket streaming for live prices  
✅ **Production Ready** - Error handling, retries, health checks  

## Quick Start

### 1. Basic Price Fetch

```python
from apis.binance_client import BinanceClient

# Get BTC price (no API key needed!)
client = BinanceClient()
price = client.get_price('BTCUSDT')
print(f"BTC: ${price:,.2f}")
```

### 2. Multi-Source Consensus Pricing

```python
from apis.price_aggregator import PriceAggregator

# Get best price from multiple sources
aggregator = PriceAggregator()
result = aggregator.get_best_price('BTC')

print(f"Price: ${result['price']:,.2f}")
print(f"Sources: {', '.join(result['sources'])}")
print(f"Confidence: {result['confidence']*100:.0f}%")
```

### 3. Real-Time WebSocket Streaming

```python
from apis.binance_client import BinanceClient

def on_price_update(data):
    print(f"{data['symbol']}: ${data['price']:,.2f}")

client = BinanceClient()
client.stream_prices(['BTCUSDT', 'ETHUSDT'], on_price_update)
```

### 4. Polymarket Prediction Markets

```python
from apis.polymarket_subgraph import PolymarketSubgraph

# Query active markets (GraphQL, free)
client = PolymarketSubgraph()
markets = client.query_markets(active=True, first=10)

for market in markets:
    print(f"{market['question']}")
    print(f"  Volume: ${float(market['volumeUSD']):,.0f}")
```

## API Clients

### BinanceClient

**Free Binance API client for crypto prices**

- **Endpoint**: `https://api.binance.com/api/v3`
- **Rate Limit**: 1200 requests/minute (no key required)
- **WebSocket**: Unlimited real-time streaming
- **Coverage**: All major cryptocurrencies

**Methods:**
- `get_price(symbol)` - Get current price for a symbol
- `get_multiple_prices(symbols)` - Batch price fetching
- `get_24h_stats(symbol)` - 24-hour statistics
- `stream_prices(symbols, callback)` - Real-time WebSocket stream
- `health_check()` - Check API availability

### CoinGeckoClient

**Free CoinGecko API client (fallback source)**

- **Endpoint**: `https://api.coingecko.com/api/v3`
- **Rate Limit**: 50 requests/minute (free tier)
- **Coverage**: 10,000+ cryptocurrencies
- **No Key Required**: Public endpoints

**Methods:**
- `get_price(coin_id)` - Get price by coin ID or symbol
- `get_multiple_prices(coin_ids)` - Batch price fetching
- `get_market_data(coin_id)` - Market cap, volume, change
- `search_coins(query)` - Search for coins
- `health_check()` - Check API availability

### PolymarketSubgraph

**Polymarket Subgraph client (GraphQL)**

- **Endpoint**: The Graph Protocol (decentralized)
- **Rate Limit**: Effectively unlimited
- **Data**: On-chain prediction market data
- **Cost**: Free (decentralized protocol)

**Methods:**
- `query_markets(active, first, skip)` - Query prediction markets
- `query_market(market_id)` - Get specific market
- `get_market_prices(market_id)` - Get YES/NO prices
- `query_trades(market_id, first)` - Recent trades
- `search_markets_by_topic(topic)` - Search by keyword
- `health_check()` - Check API availability

### PriceAggregator

**Multi-source price aggregation with consensus**

Combines Binance + CoinGecko for reliable pricing:
- Median calculation
- Outlier detection (5% threshold)
- Automatic failover
- Confidence scoring

**Methods:**
- `get_best_price(symbol)` - Get consensus price
- `get_multiple_prices(symbols)` - Batch consensus pricing
- `get_price_comparison(symbol)` - Compare all sources
- `health_check()` - Check all sources
- `get_source_priority()` - Get healthy sources in order

## Configuration

Edit `config.yaml`:

```yaml
data_sources:
  crypto_prices:
    primary: binance       # Free, 1200 req/min
    fallback: coingecko    # Free, 50 req/min
    use_websocket: true    # Real-time streams
    
  polymarket:
    method: subgraph       # Free GraphQL API
    url: "https://api.thegraph.com/subgraphs/name/tokenunion/polymarket"
    cache_ttl_seconds: 60
    use_alternative: false

advanced:
  price_aggregator:
    outlier_threshold: 0.05  # 5% deviation
    min_sources: 1
  
  websocket:
    auto_reconnect: true
    reconnect_delay: 5
```

## Error Handling

All clients include:
- ✅ Automatic retries on failure
- ✅ Connection health monitoring
- ✅ Rate limiting (polite usage)
- ✅ Graceful degradation
- ✅ Detailed logging

Example:
```python
client = BinanceClient()

# Health check before use
if client.health_check():
    price = client.get_price('BTCUSDT')
    if price:
        print(f"BTC: ${price:,.2f}")
    else:
        print("Failed to get price")
else:
    print("Binance API unavailable")
```

## Testing

Run unit tests:
```bash
python test_api_structure.py
```

Run live API tests (requires internet):
```bash
python test_free_apis.py
```

## Integration with Monitor

The `monitor.py` module automatically uses these free data sources:

```python
from monitor import PolymarketMonitor
import yaml

# Load config
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize monitor (uses free APIs automatically)
monitor = PolymarketMonitor(config)

# Get crypto price
btc_price = monitor.get_crypto_price('BTC')
print(f"BTC: ${btc_price['price']:,.2f}")

# Get Polymarket markets
markets = monitor.get_active_markets(limit=10)
for market in markets:
    print(market['question'])

# Search markets by topic
btc_markets = monitor.search_markets_by_topic('Bitcoin')
```

## Advantages Over Paid APIs

| Feature | Paid APIs | Free Solution |
|---------|-----------|---------------|
| **Cost** | $10-50/mo | $0/mo |
| **Setup** | API keys | None |
| **Rate Limit** | 500 req/day | 1200 req/min |
| **Real-Time** | Polling | WebSocket |
| **Reliability** | Single source | Multiple fallbacks |
| **Data Quality** | Aggregated | Direct from source |

## Data Quality

### Binance
- ✅ Largest crypto exchange (50% market share)
- ✅ Sub-second latency
- ✅ 99.99% uptime
- ✅ Used by Bloomberg, CoinMarketCap

### CoinGecko
- ✅ Independent price aggregator
- ✅ 10,000+ cryptocurrencies
- ✅ Community-trusted source

### Polymarket Subgraph
- ✅ On-chain data (can't be manipulated)
- ✅ Same source as Polymarket.com
- ✅ Decentralized (The Graph network)
- ✅ No rate limits

## Legal & Ethical

✅ **Binance**: Public API, explicitly allows usage  
✅ **CoinGecko**: Free tier for personal/educational use  
✅ **The Graph**: Decentralized, open protocol  
✅ **No ToS violations**  
✅ **No scraping** - all official APIs  

## Support

For issues or questions:
1. Check API health: Run `test_api_structure.py`
2. Review logs in `logs/errors.log`
3. Check API documentation:
   - Binance: https://binance-docs.github.io/apidocs/
   - CoinGecko: https://www.coingecko.com/api/documentation
   - The Graph: https://thegraph.com/docs/

## Summary

**You now have access to:**
- ✅ Real-time crypto prices (Binance WebSocket)
- ✅ Fallback pricing (CoinGecko)
- ✅ On-chain prediction markets (Polymarket Subgraph)
- ✅ Multi-source consensus pricing
- ✅ **NO API KEYS REQUIRED**
- ✅ **$0/month cost**
- ✅ **Unlimited rate limits** (with WebSocket)

Enjoy free, unlimited, reliable data! 🎉
