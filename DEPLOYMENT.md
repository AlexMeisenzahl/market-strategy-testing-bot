# Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+
- 2GB RAM minimum (4GB recommended)
- 10GB disk space
- Linux/macOS/Windows with WSL2

### 1. Clone and Configure

```bash
git clone <repository-url>
cd market-strategy-testing-bot

# Copy environment template
cp .env.example .env

# Edit configuration with your values
nano .env

# Optional: Copy and customize YAML config
cp config.example.yaml config.yaml
nano config.yaml
```

### 2. Environment Configuration

Edit `.env` file with your production values:

```bash
# CRITICAL: Change these in production!
SECRET_KEY=your-random-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
GRAFANA_ADMIN_PASSWORD=secure-password-here

# Production environment
TRADING_BOT_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database (optional - defaults to SQLite)
# DATABASE_URL=postgresql://user:password@postgres:5432/trading_bot

# Monitoring
SENTRY_DSN=your-sentry-dsn-here  # Optional but recommended
FEATURE_PROMETHEUS_METRICS=true

# API Keys (optional - for notifications)
TELEGRAM_BOT_TOKEN=your-telegram-token
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Deploy with Docker

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f trading-bot
```

### 4. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:5000/health

# Should return: {"overall_status": "healthy", ...}

# Check metrics endpoint
curl http://localhost:5000/metrics

# Should return Prometheus metrics
```

### 5. Access Services

- **Trading Bot Dashboard**: http://localhost:5000
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3000
  - Default credentials: admin/admin (change immediately!)
- **Health Check**: http://localhost:5000/health

## 📋 Configuration Hierarchy

Configuration is loaded with the following precedence (highest to lowest):

1. **Environment Variables** (`.env` file or system environment)
2. **YAML Configuration** (`config.yaml`)
3. **Default Values** (built-in defaults)

This allows flexible deployment across environments without changing code.

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRADING_BOT_ENV` | Environment (development/production) | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `PAPER_TRADING` | Enable paper trading (MUST be true) | `true` |
| `SECRET_KEY` | Flask secret key | (must set in production) |
| `DATABASE_URL` | Database connection string | `sqlite:///data/bot.db` |
| `SENTRY_DSN` | Sentry error tracking DSN | (empty) |
| `FEATURE_PROMETHEUS_METRICS` | Enable Prometheus metrics | `true` |
| `RATE_LIMIT_ENABLED` | Enable API rate limiting | `true` |
| `REQUEST_TIMEOUT` | API request timeout (seconds) | `30` |

See `.env.example` for complete list of environment variables.

## 🔒 Security Features

### Built-in Security

The bot includes comprehensive security features:

1. **Security Headers**
   - XSS Protection (`X-XSS-Protection`)
   - Clickjacking protection (`X-Frame-Options: DENY`)
   - MIME-sniffing prevention (`X-Content-Type-Options: nosniff`)
   - Content Security Policy (CSP)

2. **Rate Limiting**
   - Default: 100 requests/hour per IP
   - Sensitive endpoints: 20 requests/hour
   - Configurable via `RATE_LIMIT_DEFAULT` and `RATE_LIMIT_SENSITIVE`

3. **Error Handling**
   - Global exception handler
   - Graceful API fallbacks
   - Retry logic with exponential backoff
   - Request timeout monitoring

4. **Health Checks**
   - Comprehensive health endpoint (`/health`)
   - Automatic Docker health checks
   - Service dependency monitoring

### JWT Authentication

Protected endpoints require Bearer token:
```bash
# Generate token (implement your auth flow)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/protected
```

### API Key Authentication

Some endpoints require API key:
```bash
curl -H "X-API-Key: <key>" \
  http://localhost:5000/api/admin
```

### Rate Limiting

Rate limits protect against abuse:
- Default: 100 requests/hour per IP
- Configurable in `.env`:
  ```bash
  RATE_LIMIT_ENABLED=true
  RATE_LIMIT_DEFAULT=100/hour
  RATE_LIMIT_SENSITIVE=20/hour
  ```

## 📊 Monitoring

### Prometheus Metrics
Available at `/metrics` endpoint:
- `opportunities_found_total`: Opportunities detected
- `trades_executed_total`: Trades executed
- `paper_profit_total`: Total profit
- `api_calls_total`: API calls made
- `bot_errors_total`: Error count

### Sentry Error Tracking
- Automatic exception capture
- Performance monitoring
- Breadcrumb tracking

### Grafana Dashboards
Pre-configured dashboards for:
- Trading performance
- System metrics
- API health
- Error rates

## 🔄 Operations

### Backup
```bash
./scripts/backup.sh
```

Backups stored in `backups/` directory.

### Restore
```bash
./scripts/restore.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

### Health Check
```bash
./scripts/health-check.sh
```

### View Logs
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f trading-bot
```

### Update
```bash
git pull
docker-compose build
docker-compose up -d
```

## 🎚️ Feature Flags

Feature flags can be controlled via:
1. Environment variables: `FEATURE_NAME=true`
2. Config file: `feature_flags` section
3. Runtime API (admin access required)

Available flags:
- `prometheus_metrics`: Enable Prometheus metrics
- `sentry_error_tracking`: Enable Sentry integration
- `telegram_notifications`: Enable Telegram alerts
- `jwt_authentication`: Enable JWT auth

## 🔧 Troubleshooting

### Bot won't start
1. Check Docker logs: `docker-compose logs trading-bot`
2. Verify config.yaml syntax: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
3. Ensure .env file exists and is properly formatted
4. Check health endpoint: `curl http://localhost:5000/health`

### Metrics not appearing
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify bot is exposing `/metrics`: `curl http://localhost:5000/metrics`
3. Verify `FEATURE_PROMETHEUS_METRICS=true` in `.env`
4. Check network connectivity between containers

### High memory usage
1. Check position count
2. Review log file sizes: `du -sh logs/*`
3. Clear old data: `find logs/ -name "*.log.old" -delete`
4. Check for memory leaks: `docker stats polymarket-bot`

### Health check failing
1. Check individual services: `curl http://localhost:5000/health | jq`
2. Verify API keys are configured
3. Check rate limits haven't been exceeded
4. Review error logs: `docker-compose logs trading-bot | grep ERROR`

### Environment variables not taking effect
1. Verify `.env` file is in project root
2. Restart containers: `docker-compose down && docker-compose up -d`
3. Check precedence: ENV > YAML > DEFAULT
4. Verify variable names match exactly (case-sensitive)

## 🆕 Production Features

### Error Handling & Resilience

**Retry Logic with Exponential Backoff**
```python
from utils.error_handlers import with_retry

@with_retry(max_retries=3, backoff_factor=2.0)
def fetch_data():
    return api.get_data()
```

**Safe Data Client Wrapper**
```python
from utils.safe_data_client import SafeDataClient, DataClientFactory

# Create safe client with fallback
safe_client = DataClientFactory.create_market_client(
    primary=polymarket_client,
    fallback=mock_client,
    enable_caching=True
)

# Calls automatically retry and fallback on failure
data = safe_client.safe_call('get_markets', cache_key='markets_list')
```

### Health & Monitoring

**Comprehensive Health Checks**
```bash
# Get full health status
curl http://localhost:5000/health | jq

# Check specific service
curl http://localhost:5000/health | jq '.services.crypto_apis'
```

**Metrics Collection**
```python
from monitoring.metrics import get_metrics_collector

metrics = get_metrics_collector()

# Record API call
metrics.record_api_call('coingecko', 'ping', latency=0.123)

# Record trade
metrics.record_trade('arbitrage', success=True, profit=5.0)

# Get statistics
stats = metrics.get_comprehensive_stats()
```

### Configuration Management

**Environment-First Configuration**
```python
from config.config_loader import get_config

# Load with precedence: ENV > YAML > DEFAULT
config = get_config(config_path='config.yaml')

# Get values
debug = config.get('debug', False)
timeout = config.get('request_timeout', 30)

# Check feature flags
if config.is_feature_enabled('prometheus_metrics'):
    # Enable metrics
    pass
```

## 📈 Performance Tuning

### Worker Configuration
```yaml
# docker-compose.yml
environment:
  - WORKERS=4  # Increase for more throughput
```

### Caching
Enable Redis caching for API calls:
```yaml
feature_flags:
  caching: true
```

### Database Optimization
- Regular backups
- Vacuum/cleanup old data
- Index optimization

## 🚨 Production Checklist

Before deploying to production:

- [ ] Set unique `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure Sentry DSN
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable automated backups
- [ ] Set up monitoring alerts
- [ ] Review and set rate limits
- [ ] Test notification channels
- [ ] Verify `paper_trading: true`
- [ ] Document API keys securely

## 🔐 Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Enable HTTPS** in production
5. **Keep dependencies updated**
6. **Monitor for vulnerabilities**
7. **Restrict network access**
8. **Use strong passwords**

## 📞 Support

For issues or questions:
1. Check logs first
2. Review documentation
3. Search existing issues
4. Open a new issue with:
   - Error messages
   - Configuration (redacted)
   - Steps to reproduce

## 📝 License

See LICENSE file for details.
