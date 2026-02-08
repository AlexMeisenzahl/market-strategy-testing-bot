"""
Prometheus Metrics Exporter for Trading Bot
Exposes metrics for monitoring and alerting
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from typing import Dict, Any
import time
import psutil
import os

# Define metrics
bot_info = Info("bot", "Trading bot information")
bot_uptime = Gauge("bot_uptime_seconds", "Bot uptime in seconds")
bot_status = Gauge("bot_status", "Bot status (1=running, 0=stopped)")

# Trading metrics
opportunities_found = Counter(
    "opportunities_found_total", "Total opportunities found", ["strategy"]
)
opportunities_missed = Counter(
    "opportunities_missed_total", "Total opportunities missed", ["reason"]
)
trades_executed = Counter(
    "trades_executed_total", "Total trades executed", ["strategy"]
)
paper_profit = Gauge("paper_profit_total", "Total paper trading profit")
paper_trades_count = Gauge("paper_trades_count", "Number of paper trades")

# API metrics
api_calls = Counter("api_calls_total", "Total API calls", ["service", "endpoint"])
api_failures = Counter(
    "api_failures_total", "Total API failures", ["service", "error_type"]
)
api_latency = Histogram(
    "api_latency_seconds", "API call latency", ["service", "endpoint"]
)

# Rate limiting metrics
rate_limit_hits = Counter("rate_limit_hits_total", "Rate limit hits", ["service"])
rate_limit_usage = Gauge(
    "rate_limit_usage_percent", "Rate limit usage percentage", ["service"]
)

# Health metrics
connection_status = Gauge(
    "connection_status",
    "Connection health status (1=healthy, 0=unhealthy)",
    ["service"],
)
last_successful_scan = Gauge(
    "last_successful_scan_timestamp", "Timestamp of last successful market scan"
)

# Error metrics
bot_errors = Counter("bot_errors_total", "Total bot errors", ["error_type"])
notification_failures = Counter(
    "notification_failures_total", "Notification failures", ["channel"]
)

# System metrics
memory_usage = Gauge("memory_usage_bytes", "Memory usage in bytes")
cpu_usage = Gauge("cpu_usage_percent", "CPU usage percentage")


class PrometheusMetrics:
    """Prometheus metrics collector for trading bot"""

    def __init__(self):
        self.start_time = time.time()
        self._init_bot_info()

    def _init_bot_info(self):
        """Initialize bot information"""
        bot_info.info(
            {
                "version": "1.0.0",
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
                "environment": os.getenv("TRADING_BOT_ENV", "development"),
            }
        )

    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # Memory usage
            process = psutil.Process()
            memory_usage.set(process.memory_info().rss)

            # CPU usage
            cpu_usage.set(process.cpu_percent(interval=0.1))

            # Uptime
            uptime = time.time() - self.start_time
            bot_uptime.set(uptime)
        except Exception:
            pass

    def record_opportunity(self, strategy: str):
        """Record an opportunity found"""
        opportunities_found.labels(strategy=strategy).inc()

    def record_missed_opportunity(self, reason: str):
        """Record a missed opportunity"""
        opportunities_missed.labels(reason=reason).inc()

    def record_trade(self, strategy: str):
        """Record a trade execution"""
        trades_executed.labels(strategy=strategy).inc()

    def update_profit(self, total_profit: float):
        """Update total profit metric"""
        paper_profit.set(total_profit)

    def update_trades_count(self, count: int):
        """Update trades count"""
        paper_trades_count.set(count)

    def record_api_call(self, service: str, endpoint: str, duration: float):
        """Record API call"""
        api_calls.labels(service=service, endpoint=endpoint).inc()
        api_latency.labels(service=service, endpoint=endpoint).observe(duration)

    def record_api_failure(self, service: str, error_type: str):
        """Record API failure"""
        api_failures.labels(service=service, error_type=error_type).inc()

    def update_rate_limit(self, service: str, usage_percent: float):
        """Update rate limit usage"""
        rate_limit_usage.labels(service=service).set(usage_percent)

    def record_rate_limit_hit(self, service: str):
        """Record rate limit hit"""
        rate_limit_hits.labels(service=service).inc()

    def update_connection_status(self, service: str, healthy: bool):
        """Update connection status"""
        connection_status.labels(service=service).set(1 if healthy else 0)

    def update_last_scan(self):
        """Update last successful scan timestamp"""
        last_successful_scan.set(time.time())

    def record_error(self, error_type: str):
        """Record bot error"""
        bot_errors.labels(error_type=error_type).inc()

    def record_notification_failure(self, channel: str):
        """Record notification failure"""
        notification_failures.labels(channel=channel).inc()

    def set_bot_status(self, running: bool):
        """Set bot running status"""
        bot_status.set(1 if running else 0)

    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        self.update_system_metrics()
        return generate_latest()


# Global instance
metrics = PrometheusMetrics()
