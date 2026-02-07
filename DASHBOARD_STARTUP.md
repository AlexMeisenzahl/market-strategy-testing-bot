# Dashboard Startup Guide

## Quick Start

Use the optimized startup script for the best experience:

```bash
./start_bot_optimized.sh
```

This script will:
- ✅ Check Python version (3.8+ required)
- ✅ Verify all dependencies are installed
- ✅ Create config.yaml from example if missing
- ✅ Check for port conflicts
- ✅ Start the dashboard server
- ✅ Wait for health check to pass
- ✅ Automatically open your browser
- ✅ Show clear error messages if anything fails

## Manual Start

If you prefer to start manually:

```bash
# 1. Create config file (if not exists)
cp config.example.yaml config.yaml

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Start the dashboard
cd dashboard
python3 app.py
```

Then open http://localhost:5000 in your browser.

## Features

### Performance
- **Fast Startup**: <5 seconds from script launch to browser open
- **Health Checks**: Server verified ready before opening browser
- **Optimized Refresh**: 30-second auto-refresh interval (configurable)
- **Smart Caching**: 5-second cache for CSV data

### UI Controls
- **Manual Refresh**: Click the refresh button in navigation bar
- **Auto-Refresh Toggle**: Enable/disable auto-refresh (default: enabled)
- **Connection Status**: Real-time server connection indicator
- **Loading States**: Visual feedback during data loading

### Advanced Metrics
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Gross profit divided by gross loss
- **Win/Loss Ratio**: Average win size vs average loss size
- **Win Rate**: Percentage of profitable trades

### Data Sources
The dashboard reads from these CSV files in the `logs/` directory:
- `trades.csv` - Completed trades with P&L
- `opportunities.csv` - Detected trading opportunities

**Fallback**: If CSV files don't exist, sample data is used for demonstration.

## CSV File Format

### trades.csv
```csv
id,symbol,strategy,entry_time,exit_time,duration_minutes,entry_price,exit_price,pnl_usd,pnl_pct,status
1,AAPL,RSI Scalp,2024-01-01T10:00:00,2024-01-01T12:15:00,135,150.00,151.50,15.00,1.00,closed
```

### opportunities.csv
```csv
id,timestamp,symbol,strategy,signal_type,confidence,action_taken,outcome,pnl_usd
1,2024-01-01T10:00:00,AAPL,RSI Scalp,BUY,0.85,true,win,15.00
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill <PID>
```

### Dependencies Missing
```bash
pip3 install -r requirements.txt
```

### Config File Missing
```bash
cp config.example.yaml config.yaml
# Then edit config.yaml with your settings
```

### Charts Not Loading
Charts require internet access for CDN resources:
- Tailwind CSS
- Chart.js
- Font Awesome

If offline, charts won't render but data is still accessible via API.

## API Endpoints

### Health Check
```bash
curl http://localhost:5000/health
```

Returns server status and service availability.

### Overview Metrics
```bash
curl http://localhost:5000/api/overview
```

Returns comprehensive trading statistics.

### Chart Data
```bash
# Cumulative P&L
curl "http://localhost:5000/api/charts/cumulative-pnl?range=1M"

# Daily P&L
curl http://localhost:5000/api/charts/daily-pnl

# Strategy Performance
curl http://localhost:5000/api/charts/strategy-performance
```

### Trades
```bash
# All trades (paginated)
curl "http://localhost:5000/api/trades?page=1&per_page=25"

# Filtered trades
curl "http://localhost:5000/api/trades?strategy=RSI+Scalp&outcome=win"
```

### Bot Control
```bash
# Get bot status
curl http://localhost:5000/api/bot/status

# Start bot
curl -X POST http://localhost:5000/api/bot/start

# Stop bot
curl -X POST http://localhost:5000/api/bot/stop

# Restart bot
curl -X POST http://localhost:5000/api/bot/restart
```

## Configuration

Edit `config.yaml` to configure:
- Trading strategies
- Risk management
- Notification settings
- API keys (if needed)

## Performance Tips

1. **Disable Auto-Refresh**: Toggle off if you don't need real-time updates
2. **Use Manual Refresh**: Click refresh button only when needed
3. **Close Unused Tabs**: Each open dashboard tab polls the server
4. **Monitor Logs**: Check `logs/dashboard.log` for errors

## Security Notes

- Dashboard runs on `0.0.0.0:5000` by default (accessible on local network)
- For production use, consider:
  - Running behind a reverse proxy (nginx)
  - Adding authentication
  - Using HTTPS
  - Setting up firewall rules

## Development

### Enable Debug Mode
```bash
export FLASK_DEBUG=true
cd dashboard
python3 app.py
```

Debug mode enables:
- Auto-reload on code changes
- Detailed error pages
- Request logging

**⚠️ Never use debug mode in production!**

## Support

For issues or questions:
1. Check `logs/dashboard.log` for errors
2. Verify config.yaml is valid YAML
3. Ensure Python 3.8+ is installed
4. Check all dependencies are installed
5. Review this README for common solutions
