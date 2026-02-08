# Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+
- 2GB RAM minimum
- 10GB disk space

### 1. Clone and Configure

```bash
git clone <repository-url>
cd market-strategy-testing-bot

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
nano config.yaml
```

### 2. Deploy with Docker

```bash
# Deploy all services
./scripts/deploy.sh

# Or manually:
docker-compose up -d
```

### 3. Access Services

- **Trading Bot Dashboard**: http://localhost:5000
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3000
  - Default credentials: admin/admin

## 📋 Configuration

### Environment Variables (.env)

Key configurations:
- `SENTRY_DSN`: Sentry error tracking DSN
- `JWT_SECRET_KEY`: Secret key for JWT authentication
- `FEATURE_*`: Feature flags to enable/disable features

### Config.yaml

Main bot configuration:
- `paper_trading`: MUST be `true` for safety
- `feature_flags`: Enable/disable features
- Market filters and strategy settings

## 🔒 Security Features

### JWT Authentication
Protected endpoints require Bearer token:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/protected
```

### API Key Authentication
Some endpoints require API key:
```bash
curl -H "X-API-Key: <key>" http://localhost:5000/api/admin
```

### Rate Limiting
- Default: 100 requests/hour per IP
- Configurable in security middleware

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
2. Verify config.yaml syntax
3. Ensure .env file exists

### Metrics not appearing
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify bot is exposing `/metrics`
3. Check network connectivity

### High memory usage
1. Check position count
2. Review log file sizes
3. Clear old data: `rm -rf logs/*.log.old`

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
