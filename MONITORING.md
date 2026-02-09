# 📊 Monitoring Guide

Comprehensive guide for monitoring the Market Strategy Testing Bot in production.

## Table of Contents

- [Health Checks](#health-checks)
- [Metrics & Dashboards](#metrics--dashboards)
- [Alerting](#alerting)
- [Key Performance Indicators (KPIs)](#key-performance-indicators-kpis)
- [Troubleshooting](#troubleshooting)

---

## Health Checks

### Health Endpoint

The bot exposes a comprehensive health check endpoint at `/health` or `/api/health`:

```bash
curl http://localhost:5000/health
```

### Health Check Response

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "overall_status": "healthy",
  "services": {
    "crypto_apis": {
      "coingecko": {
        "status": "healthy",
        "response_time_ms": 145,
        "last_checked": "2024-01-15T10:30:00Z"
      },
      "binance": {
        "status": "healthy",
        "response_time_ms": 98,
        "last_checked": "2024-01-15T10:30:00Z"
      }
    },
    "prediction_markets": {
      "polymarket": {
        "status": "healthy",
        "response_time_ms": 234,
        "last_checked": "2024-01-15T10:30:00Z"
      }
    },
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "last_checked": "2024-01-15T10:30:00Z"
    }
  },
  "application": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 3600
  }
}
```

### Health Status Values

- **healthy**: Service is operating normally
- **degraded**: Service is operational but experiencing issues
- **down**: Service is unavailable

### Docker Health Checks

Docker automatically monitors container health:

```bash
# Check container health
docker ps

# View health check logs
docker inspect --format='{{json .State.Health}}' polymarket-bot | jq
```

---

## Metrics & Dashboards

### Prometheus Metrics

The bot exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:5000/metrics
```

### Available Metrics

#### Trading Metrics
- `bot_opportunities_total{strategy}` - Total opportunities detected
- `bot_trades_total{strategy,status}` - Total trades executed
- `bot_total_profit` - Total profit/loss
- `bot_api_calls_total{service,endpoint,status}` - API call counts
- `bot_api_latency_seconds{service,endpoint}` - API call latency

#### System Metrics
- `bot_uptime_seconds` - Bot uptime
- `bot_health_status` - Health status (1=healthy, 0=unhealthy)
- `bot_memory_usage_bytes` - Memory usage
- `bot_cpu_usage_percent` - CPU usage

### Accessing Prometheus

Prometheus runs on port 9090:

```bash
# Open Prometheus UI
open http://localhost:9090

# Query example: Total opportunities in last hour
bot_opportunities_total[1h]

# Query example: Average API latency
rate(bot_api_latency_seconds_sum[5m]) / rate(bot_api_latency_seconds_count[5m])
```

### Grafana Dashboards

Grafana runs on port 3000:

```bash
# Open Grafana UI
open http://localhost:3000

# Default credentials
Username: admin
Password: admin (change this!)
```

#### Pre-configured Dashboards

1. **Trading Performance**
   - Opportunities detected over time
   - Trades executed by strategy
   - Profit/loss trends
   - Success rate

2. **System Health**
   - API response times
   - Error rates
   - Service availability
   - Resource usage

3. **API Performance**
   - Request rates by service
   - Latency percentiles (p50, p95, p99)
   - Error rates
   - Rate limit usage

---

## Alerting

### Prometheus Alertmanager

Alerts are configured in `monitoring/alerts.yml`:

#### Critical Alerts

1. **BotDown** - Bot process is not running
   ```yaml
   - alert: BotDown
     expr: up{job="trading-bot"} == 0
     for: 5m
     annotations:
       summary: "Trading bot is down"
   ```

2. **HighErrorRate** - API error rate exceeds threshold
   ```yaml
   - alert: HighErrorRate
     expr: rate(bot_errors_total[5m]) > 0.1
     for: 5m
     annotations:
       summary: "High error rate detected"
   ```

3. **DatabaseDown** - Database connectivity issues
   ```yaml
   - alert: DatabaseDown
     expr: bot_health_status{service="database"} == 0
     for: 2m
   ```

#### Warning Alerts

1. **HighAPILatency** - API response times degraded
2. **LowOpportunityRate** - Fewer opportunities than expected
3. **HighMemoryUsage** - Memory usage exceeds 80%

### Notification Channels

Configure alerts to notify via:
- **Email**: SMTP configuration in `.env`
- **Telegram**: Set `TELEGRAM_BOT_TOKEN` in `.env`
- **Slack**: Set `SLACK_WEBHOOK_URL` in `.env`
- **Discord**: Set `DISCORD_WEBHOOK_URL` in `.env`

---

## Key Performance Indicators (KPIs)

### Trading KPIs

1. **Opportunity Detection Rate**
   - **Target**: > 10 opportunities/hour
   - **Query**: `rate(bot_opportunities_total[1h])`

2. **Trade Success Rate**
   - **Target**: > 95%
   - **Formula**: `successful_trades / total_trades`

3. **Average Profit per Trade**
   - **Target**: > 2%
   - **Formula**: `total_profit / total_trades`

4. **API Availability**
   - **Target**: > 99%
   - **Query**: `avg(up{job="trading-bot"})`

### System KPIs

1. **API Response Time (p95)**
   - **Target**: < 500ms
   - **Query**: `histogram_quantile(0.95, bot_api_latency_seconds)`

2. **Error Rate**
   - **Target**: < 1%
   - **Query**: `rate(bot_errors_total[5m])`

3. **Memory Usage**
   - **Target**: < 2GB
   - **Query**: `bot_memory_usage_bytes`

4. **CPU Usage**
   - **Target**: < 50%
   - **Query**: `bot_cpu_usage_percent`

---

## Troubleshooting

### Common Issues

#### 1. Health Check Failing

**Symptoms**: `/health` returns 503 or "down" status

**Diagnosis**:
```bash
# Check service health
curl http://localhost:5000/health | jq

# Check logs
docker-compose logs trading-bot | tail -50

# Check specific service
curl http://localhost:5000/api/health | jq '.services.crypto_apis'
```

**Solutions**:
- Check API keys are configured correctly
- Verify network connectivity
- Check rate limits haven't been exceeded
- Restart failed services: `docker-compose restart trading-bot`

#### 2. High API Latency

**Symptoms**: Slow response times, timeouts

**Diagnosis**:
```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=bot_api_latency_seconds

# Check specific service latency
curl http://localhost:5000/api/metrics/stats | jq '.api.average_latencies'
```

**Solutions**:
- Enable request caching in config
- Increase API timeout values
- Switch to fallback data sources
- Check network connectivity

#### 3. Memory Leaks

**Symptoms**: Increasing memory usage over time

**Diagnosis**:
```bash
# Monitor memory over time
watch -n 5 'docker stats polymarket-bot --no-stream'

# Check in Prometheus
bot_memory_usage_bytes
```

**Solutions**:
- Restart bot: `docker-compose restart trading-bot`
- Clear cache: Check logs directory size
- Review log rotation settings
- Update to latest version

#### 4. Missing Metrics

**Symptoms**: Grafana dashboards show no data

**Diagnosis**:
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Test metrics endpoint
curl http://localhost:5000/metrics
```

**Solutions**:
- Verify `FEATURE_PROMETHEUS_METRICS=true` in `.env`
- Check bot is exposing metrics: `curl localhost:5000/metrics`
- Verify Prometheus can reach bot (check network)
- Restart Prometheus: `docker-compose restart prometheus`

#### 5. Database Errors

**Symptoms**: Health check shows database down

**Diagnosis**:
```bash
# Check database file exists
ls -lh data/bot.db

# Check database integrity
sqlite3 data/bot.db "PRAGMA integrity_check;"
```

**Solutions**:
- Restore from backup
- Check disk space: `df -h`
- Verify database permissions
- Initialize database: `python -c "from database.settings_models import init_db; init_db()"`

### Getting Help

If issues persist:

1. **Check Logs**:
   ```bash
   docker-compose logs -f trading-bot
   ```

2. **Export Metrics**:
   ```bash
   curl http://localhost:5000/api/metrics/stats > metrics.json
   ```

3. **Health Report**:
   ```bash
   curl http://localhost:5000/health > health.json
   ```

4. **Open Issue**: Include logs, metrics, and health report

---

## Best Practices

### Monitoring Checklist

- [ ] Health checks pass (200 status)
- [ ] All services show "healthy" status
- [ ] Prometheus scraping bot metrics
- [ ] Grafana dashboards displaying data
- [ ] Alert rules configured
- [ ] Notification channels tested
- [ ] Backups configured and tested
- [ ] Log rotation enabled
- [ ] Resource limits set appropriately

### Regular Maintenance

1. **Daily**:
   - Check health endpoint
   - Review error logs
   - Verify trading activity

2. **Weekly**:
   - Review Grafana dashboards
   - Check disk space
   - Update dependencies

3. **Monthly**:
   - Test backup restoration
   - Review and update alerts
   - Optimize database
   - Update to latest version

---

## Additional Resources

- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [README.md](README.md) - General documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
