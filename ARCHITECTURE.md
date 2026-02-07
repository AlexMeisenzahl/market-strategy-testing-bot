# Free API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Market Strategy Bot                          │
│                   (Paper Trading Edition)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PolymarketMonitor                          │
│                     (monitor.py)                                │
│                                                                 │
│  • get_active_markets()      - Uses Subgraph                   │
│  • get_market_prices()       - Uses Subgraph + Cache           │
│  • get_crypto_price()        - Uses PriceAggregator            │
│  • search_markets_by_topic() - Uses Subgraph                   │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           │                    │                    │
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ PriceAggregator  │  │ Polymarket       │  │  Cache Layer     │
│                  │  │ Subgraph         │  │                  │
│ • Consensus      │  │                  │  │ • Market Data    │
│ • Outlier Det.   │  │ • GraphQL        │  │ • TTL: 60s       │
│ • Failover       │  │ • On-chain       │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
     │          │              │
     │          │              │
     ▼          ▼              ▼
┌─────────┐ ┌─────────┐  ┌────────────────────────────┐
│ Binance │ │CoinGecko│  │      The Graph Network     │
│  API    │ │   API   │  │  (Decentralized GraphQL)   │
│         │ │         │  │                            │
│ FREE    │ │ FREE    │  │ polymarket.thegraph.com    │
│ 1200/m  │ │  50/m   │  │                            │
│ WS: ∞   │ │         │  │         FREE               │
└─────────┘ └─────────┘  └────────────────────────────┘
     │          │                    │
     │          │                    │
     ▼          ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│            External Data Sources (All FREE)             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  • Binance Exchange     - Real-time crypto prices      │
│  • CoinGecko Platform   - Aggregated crypto data       │
│  • Ethereum Blockchain  - On-chain market data         │
│                                                         │
│  NO API KEYS • NO COST • HIGH LIMITS                   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Crypto Price Fetching
```
User Request
    │
    ▼
PriceAggregator.get_best_price('BTC')
    │
    ├─────► BinanceClient.get_price('BTCUSDT') ───► $98,432.50
    │
    └─────► CoinGeckoClient.get_price('BTC')   ───► $98,450.00
                │
                ▼
         Consensus Calculation
                │
                ├─ Median: $98,441.25
                ├─ Outlier Check: ✓ Pass
                ├─ Confidence: 95%
                └─ Sources: ['binance', 'coingecko']
                        │
                        ▼
                   Return Result
```

### Market Data Fetching
```
User Request
    │
    ▼
PolymarketMonitor.get_active_markets(10)
    │
    ├─ Check Cache? ─► Cache Miss
    │
    ▼
PolymarketSubgraph.query_markets(active=True, first=10)
    │
    ▼
POST https://api.thegraph.com/subgraphs/name/tokenunion/polymarket
{
  markets(first: 10, where: {active: true}) {
    id, question, outcomes, volumeUSD, ...
  }
}
    │
    ▼
GraphQL Response (JSON)
    │
    ├─ Validate Response
    ├─ Parse Markets
    └─ Update Cache
         │
         ▼
    Return Markets
```

### WebSocket Real-Time Streaming
```
Client Request
    │
    ▼
BinanceClient.stream_prices(['BTCUSDT'], callback)
    │
    ▼
Connect WebSocket
wss://stream.binance.com:9443/ws/btcusdt@ticker
    │
    ├─ Connection Opened ✓
    │
    ▼
Continuous Stream
    │
    ├─► Price Update: $98,432.50 ─► callback()
    ├─► Price Update: $98,435.20 ─► callback()
    ├─► Price Update: $98,431.80 ─► callback()
    │
    └─► Auto-reconnect on disconnect
```

## Component Responsibilities

### BinanceClient
- Primary crypto price source
- HTTP API: Single/batch price requests
- WebSocket: Real-time price streaming
- Health monitoring
- Rate limit: 1200 req/min

### CoinGeckoClient
- Fallback crypto price source
- 10,000+ cryptocurrency support
- Symbol-to-ID mapping
- Market statistics (volume, cap, change)
- Rate limit: 50 req/min (with built-in limiter)

### PolymarketSubgraph
- Primary prediction market source
- GraphQL queries via The Graph
- On-chain data (verifiable)
- Market search and filtering
- Trade history
- Effectively unlimited queries

### PriceAggregator
- Orchestrates multiple price sources
- Calculates median (consensus)
- Detects outliers (5% threshold)
- Tracks source health
- Automatic failover
- Confidence scoring

### PolymarketMonitor
- Main integration point
- Uses PriceAggregator for crypto
- Uses Subgraph for markets
- Implements caching layer
- Provides unified API

## Error Handling Flow

```
API Request
    │
    ▼
Try Primary Source (e.g., Binance)
    │
    ├─ Success? ─► Return Data ✓
    │
    └─ Failure
        │
        ├─ Log Error
        ├─ Mark Source Unhealthy
        │
        ▼
    Try Fallback Source (e.g., CoinGecko)
        │
        ├─ Success? ─► Return Data ✓
        │
        └─ Failure
            │
            ├─ Log Critical Error
            └─ Return None/Empty
                │
                ▼
         User Handles Gracefully
```

## Configuration Hierarchy

```
config.yaml
    │
    ├─ data_sources
    │   ├─ crypto_prices
    │   │   ├─ primary: binance
    │   │   ├─ fallback: coingecko
    │   │   └─ use_websocket: true
    │   │
    │   └─ polymarket
    │       ├─ method: subgraph
    │       ├─ url: thegraph.com/...
    │       └─ cache_ttl_seconds: 60
    │
    └─ advanced
        ├─ price_aggregator
        │   ├─ outlier_threshold: 0.05
        │   └─ min_sources: 1
        │
        ├─ websocket
        │   ├─ auto_reconnect: true
        │   └─ reconnect_delay: 5
        │
        └─ graphql
            ├─ batch_size: 10
            └─ timeout: 10
```

## Benefits Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Cost** | $10-50/mo | $0/mo | 100% savings |
| **Rate Limit** | 500/day | 1200/min | 144x more |
| **Real-Time** | Polling | WebSocket | Instant |
| **Sources** | 1 | 3+ | More reliable |
| **Setup Time** | 30+ min | 0 min | Instant |
| **API Keys** | Required | None | Simpler |
| **Data Quality** | Aggregated | Direct | More accurate |

## Network Diagram

```
Internet
    │
    ├──────────────────────┬──────────────────────┬────────────────
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌─────────┐          ┌──────────────┐
│ Binance │          │CoinGecko│          │  The Graph   │
│  REST   │          │  REST   │          │   GraphQL    │
│         │          │         │          │              │
│  HTTP   │          │  HTTP   │          │   HTTPS      │
│  1200/m │          │  50/m   │          │   Unlimited  │
└─────────┘          └─────────┘          └──────────────┘
    │                      │                      │
    │                      │                      │
┌───┴──────────────────────┴──────────────────────┴───┐
│            Bot Application Server                   │
│                                                      │
│  • BinanceClient       • CoinGeckoClient            │
│  • PolymarketSubgraph  • PriceAggregator            │
│  • PolymarketMonitor   • Cache Layer                │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│              Trading Strategy Logic                 │
│                                                     │
│  • Arbitrage Detection  • Position Sizing          │
│  • Risk Management      • Paper Trading            │
└─────────────────────────────────────────────────────┘
```

## Security Model

```
┌──────────────────────────────────────────────┐
│           Security Layers                    │
├──────────────────────────────────────────────┤
│                                              │
│  1. No API Keys                              │
│     • No secrets to leak                     │
│     • No authentication                      │
│                                              │
│  2. Public Endpoints Only                    │
│     • Read-only access                       │
│     • No write operations                    │
│                                              │
│  3. Rate Limiting                            │
│     • Built-in politeness delays             │
│     • Respects API guidelines                │
│                                              │
│  4. Error Handling                           │
│     • Specific exceptions                    │
│     • No data leakage                        │
│                                              │
│  5. Input Validation                         │
│     • Type checking                          │
│     • Range validation                       │
│                                              │
│  6. Dependency Security                      │
│     • All deps checked                       │
│     • 0 vulnerabilities                      │
│                                              │
└──────────────────────────────────────────────┘
```
