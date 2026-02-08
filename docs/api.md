# API Documentation

Complete documentation for all API endpoints in the Market Strategy Testing Bot dashboard.

## Base URL

```
http://localhost:5000
```

## Response Format

All API endpoints return responses in the following standardized format:

```json
{
    "success": true,
    "data": { ... },
    "error": null,
    "message": "Optional message",
    "timestamp": "2026-02-08T10:30:00.000Z",
    "meta": {
        "version": "1.0",
        "execution_time_ms": 12.34
    }
}
```

## Error Response Format

```json
{
    "success": false,
    "data": null,
    "error": {
        "message": "Error description",
        "code": "ERROR_CODE"
    },
    "timestamp": "2026-02-08T10:30:00.000Z",
    "meta": {
        "version": "1.0"
    }
}
```

---

## Health & Status

### GET /health
Basic health check for the dashboard service.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2026-02-08T10:30:00",
    "logs_directory": "/path/to/logs",
    "logs_exist": true,
    "services": {
        "data_parser": "ready",
        "analytics": "ready",
        "chart_data": "ready"
    }
}
```

### GET /api/health
Comprehensive health check for all external services.

**Response:**
```json
{
    "timestamp": "2026-02-08T10:30:00Z",
    "overall_status": "healthy",
    "services": {
        "crypto_apis": {
            "coingecko": {
                "status": "healthy",
                "response_time_ms": 123.45,
                "last_checked": "2026-02-08T10:30:00Z"
            },
            "binance": { ... },
            "coinbase": { ... }
        },
        "prediction_markets": {
            "polymarket": { ... },
            "kalshi": { ... }
        },
        "database": {
            "status": "healthy",
            "response_time_ms": 5.23
        }
    }
}
```

**Status Values:**
- `healthy` - Service is operational
- `degraded` - Service is slow or partially working
- `down` - Service is not responding

---

## Analytics

### GET /api/analytics/overview
Get overall trading performance metrics.

**Query Parameters:**
- `start_date` (optional) - ISO 8601 date string
- `end_date` (optional) - ISO 8601 date string

**Response:**
```json
{
    "success": true,
    "data": {
        "total_pnl": 1234.56,
        "total_trades": 150,
        "win_rate": 0.73,
        "average_profit": 8.23,
        "total_opportunities": 250,
        "active_strategies": 6
    }
}
```

### GET /api/analytics/strategy_performance
Get performance metrics per strategy.

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
    "success": true,
    "data": {
        "strategies": [
            {
                "name": "Polymarket Arbitrage",
                "total_pnl": 456.78,
                "trades": 45,
                "win_rate": 0.82,
                "avg_profit": 10.15,
                "sharpe_ratio": 2.34
            },
            ...
        ]
    }
}
```

### GET /api/analytics/risk_metrics
Get risk analysis metrics.

**Response:**
```json
{
    "success": true,
    "data": {
        "sharpe_ratio": 2.45,
        "sortino_ratio": 3.12,
        "max_drawdown": -0.05,
        "var_95": 12.34,
        "cvar_95": 15.67
    }
}
```

---

## Trading Data

### GET /api/trades
Get trading history.

**Query Parameters:**
- `page` (default: 1) - Page number
- `per_page` (default: 50, max: 100) - Items per page
- `strategy` (optional) - Filter by strategy name
- `status` (optional) - Filter by status (completed, pending, failed)
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "timestamp": "2026-02-08T10:30:00Z",
            "strategy": "Polymarket Arbitrage",
            "market": "Will Bitcoin be above $100k?",
            "entry_price": 0.48,
            "exit_price": 1.00,
            "pnl_usd": 52.00,
            "pnl_percentage": 108.33,
            "status": "completed"
        },
        ...
    ],
    "meta": {
        "pagination": {
            "page": 1,
            "per_page": 50,
            "total": 150,
            "total_pages": 3,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

### GET /api/opportunities
Get detected opportunities.

**Query Parameters:** Same as /api/trades

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "timestamp": "2026-02-08T10:30:00Z",
            "strategy": "Polymarket Arbitrage",
            "market": "Market name",
            "profit_usd": 25.00,
            "confidence": "high",
            "expiry": "2026-02-10T10:30:00Z"
        },
        ...
    ]
}
```

---

## Settings

### GET /api/settings
Get user settings.

**Query Parameters:**
- `user_id` (default: 1)

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "theme": "dark",
        "timezone": "UTC",
        "currency": "USD",
        "trading_mode": "paper",
        "notifications_enabled": true,
        ...
    }
}
```

### PUT /api/settings
Update user settings.

**Request Body:**
```json
{
    "theme": "light",
    "timezone": "America/New_York",
    "notifications_enabled": false
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "updated": true
    },
    "message": "Settings updated successfully"
}
```

### GET /api/settings/export
Export all settings as JSON file.

**Query Parameters:**
- `user_id` (default: 1)

**Response:** JSON file download containing:
- User settings
- Notification channels
- Notification preferences

**Note:** Sensitive data (API keys, passwords) is redacted in exports.

### POST /api/settings/import
Import settings from JSON file.

**Request:** multipart/form-data with `file` field or JSON body

**Response:**
```json
{
    "success": true,
    "results": {
        "user_settings": true,
        "notification_channels": 3,
        "notification_preferences": 10,
        "errors": []
    }
}
```

---

## Notifications

### GET /api/notifications/channels
Get all notification channels.

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "channel_type": "discord",
            "enabled": true,
            "webhook_url": "https://...",
            ...
        },
        ...
    ]
}
```

### POST /api/notifications/channels
Create or update a notification channel.

**Request Body:**
```json
{
    "channel_type": "discord",
    "enabled": true,
    "webhook_url": "https://discord.com/api/webhooks/..."
}
```

### POST /api/notifications/test
Test a notification channel.

**Request Body:**
```json
{
    "channel_type": "discord",
    "config": {
        "webhook_url": "https://..."
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "Test notification sent successfully"
}
```

---

## Chart Data

### GET /api/charts/cumulative_pnl
Get cumulative P&L chart data.

**Response:**
```json
{
    "success": true,
    "data": {
        "labels": ["2026-02-01", "2026-02-02", ...],
        "values": [0, 45.23, 78.91, ...]
    }
}
```

### GET /api/charts/strategy_comparison
Get strategy comparison chart data.

**Response:**
```json
{
    "success": true,
    "data": {
        "strategies": [
            {
                "name": "Polymarket Arbitrage",
                "data": [10, 15, 23, ...]
            },
            ...
        ]
    }
}
```

---

## Bot Control

### GET /api/bot/status
Get bot status.

**Response:**
```json
{
    "success": true,
    "data": {
        "running": true,
        "paused": false,
        "uptime": 3600,
        "mode": "paper",
        "active_strategies": 6,
        "connected_symbols": 10
    }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `NOT_FOUND` | 404 | Resource not found |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `INTERNAL_ERROR` | 500 | Server error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- 100 requests per minute per IP
- 1000 requests per hour per IP

When rate limit is exceeded, you'll receive a 429 status code with:
```json
{
    "success": false,
    "error": {
        "message": "Rate limit exceeded",
        "code": "RATE_LIMIT_EXCEEDED"
    }
}
```

---

## Authentication

Currently, the API does not require authentication as it's designed for local use only.

**Security Note:** Do not expose the dashboard to the public internet without implementing proper authentication.

---

## WebSocket API (Coming Soon)

Real-time updates via WebSocket will be available in a future release:
- Live price updates
- Real-time opportunity notifications
- Live P&L updates
