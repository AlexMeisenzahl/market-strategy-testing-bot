"""
Metrics Collector for Production Monitoring

Comprehensive metrics collection for API calls, latency, trades, and system health.
Integrates with Prometheus for monitoring and alerting.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, Info
except ImportError:
    # Graceful fallback if prometheus_client not installed
    Counter = Gauge = Histogram = Summary = Info = None

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring trading bot performance.
    Provides both Prometheus integration and in-memory statistics.
    """

    def __init__(self, enable_prometheus: bool = True):
        """
        Initialize metrics collector.

        Args:
            enable_prometheus: Whether to enable Prometheus metrics export
        """
        self.enable_prometheus = enable_prometheus and Counter is not None
        self._lock = Lock()
        
        # In-memory statistics
        self._api_calls: Dict[str, int] = defaultdict(int)
        self._api_latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._api_errors: Dict[str, int] = defaultdict(int)
        self._trade_metrics: Dict[str, Any] = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0.0,
            "trades_by_strategy": defaultdict(int),
        }
        self._opportunities: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
        
        # Initialize Prometheus metrics if enabled
        if self.enable_prometheus:
            self._init_prometheus_metrics()

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metric collectors."""
        if not Counter:
            logger.warning("Prometheus client not available, metrics export disabled")
            self.enable_prometheus = False
            return

        # API metrics
        self.prom_api_calls = Counter(
            'bot_api_calls_total',
            'Total API calls made',
            ['service', 'endpoint', 'status']
        )
        self.prom_api_latency = Histogram(
            'bot_api_latency_seconds',
            'API call latency in seconds',
            ['service', 'endpoint']
        )
        
        # Trading metrics
        self.prom_trades = Counter(
            'bot_trades_total',
            'Total trades executed',
            ['strategy', 'status']
        )
        self.prom_opportunities = Counter(
            'bot_opportunities_total',
            'Total opportunities detected',
            ['strategy']
        )
        self.prom_profit = Gauge(
            'bot_total_profit',
            'Total profit/loss'
        )
        
        # System metrics
        self.prom_uptime = Gauge(
            'bot_uptime_seconds',
            'Bot uptime in seconds'
        )
        self.prom_health = Gauge(
            'bot_health_status',
            'Bot health status (1=healthy, 0=unhealthy)'
        )

    def record_api_call(
        self,
        service: str,
        endpoint: str,
        latency: float,
        status: str = "success",
        error: Optional[str] = None
    ):
        """
        Record an API call with latency and status.

        Args:
            service: Service name (e.g., "coingecko", "polymarket")
            endpoint: Endpoint path or method name
            latency: Call latency in seconds
            status: Call status ("success", "error", "timeout", etc.)
            error: Error message if failed
        """
        with self._lock:
            key = f"{service}:{endpoint}"
            self._api_calls[key] += 1
            self._api_latencies[key].append(latency)
            
            if status != "success":
                self._api_errors[key] += 1
                if error:
                    logger.warning(f"API call failed: {key} - {error}")
            
            # Prometheus metrics
            if self.enable_prometheus:
                self.prom_api_calls.labels(
                    service=service,
                    endpoint=endpoint,
                    status=status
                ).inc()
                self.prom_api_latency.labels(
                    service=service,
                    endpoint=endpoint
                ).observe(latency)

    def record_trade(
        self,
        strategy: str,
        success: bool,
        profit: float = 0.0,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Record a trade execution.

        Args:
            strategy: Strategy name
            success: Whether trade was successful
            profit: Profit/loss amount
            details: Additional trade details
        """
        with self._lock:
            self._trade_metrics["total_trades"] += 1
            self._trade_metrics["trades_by_strategy"][strategy] += 1
            
            if success:
                self._trade_metrics["successful_trades"] += 1
                self._trade_metrics["total_profit"] += profit
            else:
                self._trade_metrics["failed_trades"] += 1
            
            # Prometheus metrics
            if self.enable_prometheus:
                status = "success" if success else "failed"
                self.prom_trades.labels(strategy=strategy, status=status).inc()
                self.prom_profit.set(self._trade_metrics["total_profit"])

    def record_opportunity(self, strategy: str, details: Optional[Dict[str, Any]] = None):
        """
        Record an opportunity detection.

        Args:
            strategy: Strategy name that detected the opportunity
            details: Additional opportunity details
        """
        with self._lock:
            self._opportunities[strategy] += 1
            
            # Prometheus metrics
            if self.enable_prometheus:
                self.prom_opportunities.labels(strategy=strategy).inc()

    def get_api_stats(self) -> Dict[str, Any]:
        """
        Get API call statistics.

        Returns:
            Dictionary with API statistics
        """
        with self._lock:
            stats = {
                "total_calls": sum(self._api_calls.values()),
                "total_errors": sum(self._api_errors.values()),
                "calls_by_endpoint": dict(self._api_calls),
                "errors_by_endpoint": dict(self._api_errors),
                "average_latencies": {},
            }
            
            # Calculate average latencies
            for key, latencies in self._api_latencies.items():
                if latencies:
                    stats["average_latencies"][key] = sum(latencies) / len(latencies)
            
            return stats

    def get_trade_stats(self) -> Dict[str, Any]:
        """
        Get trading statistics.

        Returns:
            Dictionary with trading statistics
        """
        with self._lock:
            return {
                "total_trades": self._trade_metrics["total_trades"],
                "successful_trades": self._trade_metrics["successful_trades"],
                "failed_trades": self._trade_metrics["failed_trades"],
                "success_rate": (
                    self._trade_metrics["successful_trades"] / self._trade_metrics["total_trades"]
                    if self._trade_metrics["total_trades"] > 0 else 0.0
                ),
                "total_profit": self._trade_metrics["total_profit"],
                "trades_by_strategy": dict(self._trade_metrics["trades_by_strategy"]),
            }

    def get_opportunity_stats(self) -> Dict[str, Any]:
        """
        Get opportunity detection statistics.

        Returns:
            Dictionary with opportunity statistics
        """
        with self._lock:
            return {
                "total_opportunities": sum(self._opportunities.values()),
                "opportunities_by_strategy": dict(self._opportunities),
            }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.

        Returns:
            Dictionary with system statistics
        """
        uptime = time.time() - self._start_time
        
        # Update Prometheus uptime
        if self.enable_prometheus:
            self.prom_uptime.set(uptime)
        
        return {
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "start_time": datetime.fromtimestamp(self._start_time).isoformat(),
        }

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get all statistics in one call.

        Returns:
            Dictionary with all statistics
        """
        return {
            "system": self.get_system_stats(),
            "api": self.get_api_stats(),
            "trading": self.get_trade_stats(),
            "opportunities": self.get_opportunity_stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def set_health_status(self, healthy: bool):
        """
        Set bot health status.

        Args:
            healthy: Whether bot is healthy
        """
        if self.enable_prometheus:
            self.prom_health.set(1 if healthy else 0)

    def reset_stats(self):
        """Reset all statistics (useful for testing)."""
        with self._lock:
            self._api_calls.clear()
            self._api_latencies.clear()
            self._api_errors.clear()
            self._opportunities.clear()
            self._trade_metrics = {
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "total_profit": 0.0,
                "trades_by_strategy": defaultdict(int),
            }
            self._start_time = time.time()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(enable_prometheus: bool = True) -> MetricsCollector:
    """
    Get global metrics collector instance.

    Args:
        enable_prometheus: Whether to enable Prometheus metrics

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(enable_prometheus=enable_prometheus)
    
    return _metrics_collector
