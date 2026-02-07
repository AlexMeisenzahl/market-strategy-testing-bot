# Polymarket API Integration Guide

## Overview

The Market-strategy-testing-bot now integrates with the live Polymarket API to fetch real market data instead of using simulated prices. This document explains how the integration works and how to configure it.

## Features

### 1. Live Market Data
- **Real-time market prices**: Fetches actual YES/NO prices from Polymarket
- **Active markets discovery**: Automatically discovers and filters active markets
- **Market metadata**: Gets liquidity, volume, and other market details
- **Graceful fallback**: Continues operating with simulated data if API is unavailable

### 2. Rate Limiting & Error Handling
- **Exponential backoff**: Automatically retries failed requests with increasing delays
- **Rate limit compliance**: Respects Polymarket's rate limits
- **Connection health monitoring**: Tracks API health and connection status
- **Error recovery**: Gracefully handles API errors and timeouts

### 3. Market Filtering
- **Keyword filtering**: Filter markets by keywords (e.g., "Bitcoin", "Election")
- **Liquidity filtering**: Only scan markets above minimum liquidity threshold
- **Volume filtering**: Only scan markets above minimum 24h volume
- **Category filtering**: Filter by market categories (crypto, politics, sports, etc.)

## Configuration

### Enabling Live API

In your `config.yaml`:

```yaml
polymarket:
  api:
    enabled: true              # Set to true to use live API
    base_url: "https://clob.polymarket.com"
    rate_limit: 60            # Requests per minute
    timeout: 10               # Request timeout in seconds
    retry_attempts: 3         # Retry attempts on failure
```

### Market Filtering

Filter which markets to monitor:

```yaml
polymarket:
  market_filters:
    min_liquidity: 1000       # Minimum liquidity in USD
    min_volume_24h: 5000      # Minimum 24h volume in USD
    categories: []            # Empty = all categories
    
# Optional: Specific keywords to filter markets
markets_to_watch: ['Bitcoin', 'Ethereum', 'Trump', 'Election']
```

### Categories

Available market categories:
- `crypto` - Cryptocurrency markets
- `politics` - Political prediction markets
- `sports` - Sports betting markets
- `entertainment` - Entertainment and media markets
- `science` - Science and technology markets
- `business` - Business and finance markets

## API Endpoints Used

The bot uses Polymarket's public CLOB (Central Limit Order Book) API:

### 1. Get Markets
```
GET https://clob.polymarket.com/markets
```
Returns list of active markets with metadata.

### 2. Get Market Details
```
GET https://clob.polymarket.com/markets/{condition_id}
```
Returns detailed information for a specific market.

### 3. Get Market Prices
```
GET https://clob.polymarket.com/price?token_id={token_id}
```
Returns current price for a market token (YES or NO).

### 4. Get Order Book
```
GET https://clob.polymarket.com/book?token_id={token_id}
```
Returns full order book with bids and asks.

### 5. Get Market Trades
```
GET https://clob.polymarket.com/trades?market={condition_id}
```
Returns recent trades for a market.

## Implementation Details

### PolymarketAPI Class

Located in `polymarket_api.py`, this class handles all API communication:

```python
from polymarket_api import PolymarketAPI

# Initialize API client
api = PolymarketAPI(timeout=10, retry_attempts=3)

# Get active markets
markets = api.get_markets(active=True, limit=100)

# Get market prices
prices = api.get_market_prices(condition_id='market-id')
# Returns: {"yes": 0.52, "no": 0.48}

# Get order book
orderbook = api.get_orderbook(token_id='token-id')
# Returns: {'bids': [...], 'asks': [...]}

# Check API health
is_healthy = api.check_health()
```

### PolymarketMonitor Updates

The `monitor.py` module now uses the live API:

```python
from monitor import PolymarketMonitor

# Initialize monitor with config
monitor = PolymarketMonitor(config)

# Get live prices (falls back to simulation if API fails)
prices = monitor.get_market_prices('market-id')
```

### Bot Integration

The `bot.py` now fetches live markets:

```python
# In bot.py
def _get_live_markets(self):
    """Fetch active markets from Polymarket API"""
    markets = self.monitor.api.get_markets(active=True, limit=100)
    
    # Apply filters
    filtered = [m for m in markets 
                if m['liquidity'] >= min_liquidity
                and m['volume'] >= min_volume]
    
    return filtered[:20]  # Top 20 by volume
```

## Safety Features

### 1. Graceful Degradation
If the API is unavailable or disabled, the bot automatically falls back to simulated data:

```python
if self.live_api_enabled:
    prices = self.api.get_market_prices(market_id)
    if not prices:
        # Fallback to simulated data
        prices = self._generate_simulated_prices()
```

### 2. Rate Limiting
The API client respects rate limits and uses exponential backoff:

```python
# Automatic retry with exponential backoff
wait_time = 2 ** retry_count  # 1s, 2s, 4s, 8s...
time.sleep(wait_time)
```

### 3. Error Handling
All API calls are wrapped in try-catch blocks with comprehensive error logging:

```python
try:
    response = self.session.get(url, timeout=self.timeout)
    if response.status_code == 200:
        return response.json()
except requests.exceptions.Timeout:
    self.logger.log_error("API timeout")
    return None
```

### 4. Connection Health Monitoring
The monitor tracks API health and connection status:

```python
# Check connection health
is_healthy = self.monitor.check_connection_health()

# Auto-pause on connection loss
if not is_healthy and config['auto_pause_on_connection_loss']:
    self.paused = True
```

## Testing

### Test Live API Connection

```python
from polymarket_api import PolymarketAPI

# Test API health
api = PolymarketAPI()
is_healthy = api.check_health()
print(f"API Health: {'✓ OK' if is_healthy else '✗ Failed'}")

# Test fetching markets
markets = api.get_markets(active=True, limit=5)
print(f"Found {len(markets)} active markets")
```

### Test with Live API Disabled

Set `polymarket.api.enabled: false` in config to test with simulated data.

## Performance Considerations

### Request Delays
The bot adds delays between API requests to avoid rate limiting:

```yaml
request_delay_seconds: 0.5  # 500ms delay between requests
```

### Caching
Consider implementing caching for:
- Market metadata (refresh every 5 minutes)
- Price data (refresh every 10-30 seconds)

### Batch Requests
For multiple markets, fetch prices in batches with delays:

```python
for market in markets:
    prices = monitor.get_market_prices(market['id'])
    time.sleep(0.5)  # Delay between requests
```

## Troubleshooting

### API Not Working

1. **Check configuration**:
   - Ensure `polymarket.api.enabled: true`
   - Verify timeout and retry settings

2. **Check logs**:
   ```bash
   tail -f logs/trading.log | grep "API"
   ```

3. **Test API directly**:
   ```bash
   curl https://clob.polymarket.com/markets?limit=1
   ```

4. **Check rate limits**:
   - Monitor rate limiter usage in dashboard
   - Increase `request_delay_seconds` if hitting limits

### Fallback to Simulated Data

If you see "using fallback data" in logs:
- API may be temporarily unavailable
- Rate limits may be exceeded
- Network connectivity issues

The bot will continue operating with simulated data.

### Connection Timeout

If getting frequent timeouts:
- Increase `timeout` setting (default: 10s)
- Check network connectivity
- Verify Polymarket API status

## Future Enhancements

Potential improvements for the API integration:

1. **WebSocket Support**: Real-time price updates via WebSocket
2. **Advanced Caching**: Redis/Memcached for faster data access
3. **Historical Data**: Fetch and analyze historical market data
4. **Market Analytics**: Calculate implied probabilities and market efficiency
5. **Multi-Exchange**: Support for other prediction market platforms

## References

- **Polymarket API Documentation**: https://docs.polymarket.com/
- **Polymarket CLOB API**: https://clob.polymarket.com/
- **API Status**: Check Polymarket status page for API availability

## Support

For issues with the API integration:

1. Check the logs in `logs/trading.log`
2. Verify configuration in `config.yaml`
3. Test API connectivity with the provided test scripts
4. Open an issue on GitHub with error details
