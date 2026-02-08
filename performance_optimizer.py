"""
Performance Optimizer Module - System-level optimizations for speed

Provides tools and utilities to optimize system performance:
- Configuration optimization suggestions
- Multiprocessing enablement for parallel operations
- Performance profiling and bottleneck identification
- Async operation management with asyncio and aiohttp
- Caching strategies for frequently accessed data
- Memory optimization recommendations

Works in conjunction with PerformanceMonitor to identify and resolve performance issues.
"""

from typing import Dict, List, Any, Optional, Callable
import time
import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
from logger import get_logger


class PerformanceOptimizer:
    """
    System-level performance optimization utilities

    Provides methods to analyze and optimize system performance,
    including parallel processing, async operations, and caching.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize performance optimizer

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()

        # Optimization settings
        self.use_multiprocessing = config.get("use_multiprocessing", False)
        self.use_async = config.get("use_async", True)
        self.use_caching = config.get("use_caching", True)

        # System resources
        self.cpu_count = multiprocessing.cpu_count()
        self.max_workers = config.get("max_workers", min(4, self.cpu_count))

        # Thread/Process pools
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None

        # Performance tracking
        self.optimization_log = []

        # Cache for frequently accessed data
        self.data_cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        self.logger.log_warning(
            f"Performance Optimizer initialized - "
            f"CPU cores: {self.cpu_count}, Max workers: {self.max_workers}"
        )

    def optimize_config(self, current_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimized configuration based on current performance

        Analyzes current performance metrics and suggests configuration changes
        to improve speed and efficiency.

        Args:
            current_performance: Dictionary with current performance metrics

        Returns:
            Dictionary with optimization suggestions
        """
        suggestions = {"config_changes": {}, "system_changes": [], "priority": "medium"}

        # Get median cycle time
        median_cycle = (
            current_performance.get("detailed_metrics", {})
            .get("total_cycle", {})
            .get("median", 0)
        )

        # Get bottlenecks
        bottlenecks = current_performance.get("bottleneck_analysis", {}).get(
            "bottlenecks", []
        )

        # Analyze and suggest optimizations

        # 1. Network optimization
        network_stats = current_performance.get("detailed_metrics", {}).get(
            "network", {}
        )
        if network_stats.get("mean", 0) > 100:
            suggestions["priority"] = "high"
            suggestions["config_changes"]["request_delay_seconds"] = max(
                0.1, self.config.get("request_delay_seconds", 0.5) * 0.5
            )
            suggestions["system_changes"].append(
                {
                    "change": "reduce_request_delay",
                    "reason": "Network latency is acceptable, can increase request frequency",
                    "expected_improvement": "10-20% faster cycle time",
                }
            )

        # 2. Enable async operations if not already enabled
        if not self.use_async and median_cycle > 200:
            suggestions["config_changes"]["use_async"] = True
            suggestions["system_changes"].append(
                {
                    "change": "enable_async_operations",
                    "reason": "Async operations can parallelize I/O-bound tasks",
                    "expected_improvement": "30-50% faster for I/O operations",
                }
            )

        # 3. Enable caching if not already enabled
        if not self.use_caching:
            suggestions["config_changes"]["use_caching"] = True
            suggestions["system_changes"].append(
                {
                    "change": "enable_caching",
                    "reason": "Cache frequently accessed data to reduce computation",
                    "expected_improvement": "15-25% faster for repeated operations",
                }
            )

        # 4. Multiprocessing for CPU-bound tasks
        if not self.use_multiprocessing and median_cycle > 300:
            suggestions["config_changes"]["use_multiprocessing"] = True
            suggestions["config_changes"]["max_workers"] = min(4, self.cpu_count)
            suggestions["system_changes"].append(
                {
                    "change": "enable_multiprocessing",
                    "reason": "CPU-bound operations detected, can benefit from parallelization",
                    "expected_improvement": f"Up to {self.cpu_count}x faster for parallel tasks",
                }
            )

        # 5. Adjust rate limits if we're being too conservative
        rate_usage = current_performance.get("rate_limit_usage", 0)
        if rate_usage < 50:  # Using less than 50% of rate limit
            suggestions["config_changes"]["rate_limit_max"] = int(
                self.config.get("rate_limit_max", 100) * 1.2
            )
            suggestions["system_changes"].append(
                {
                    "change": "increase_rate_limit",
                    "reason": "Currently using only {:.0f}% of rate limit capacity".format(
                        rate_usage
                    ),
                    "expected_improvement": "10-15% more opportunities detected",
                }
            )

        # 6. Optimize market watching
        markets_to_watch = self.config.get("markets_to_watch", [])
        if isinstance(markets_to_watch, list) and len(markets_to_watch) > 10:
            suggestions["config_changes"]["markets_to_watch"] = markets_to_watch[:10]
            suggestions["system_changes"].append(
                {
                    "change": "reduce_market_count",
                    "reason": f"Watching {len(markets_to_watch)} markets - reducing to top 10",
                    "expected_improvement": "20-30% faster detection",
                }
            )

        # Log suggestions
        if suggestions["system_changes"]:
            self.logger.log_warning(
                f"Generated {len(suggestions['system_changes'])} optimization suggestions"
            )
            self.optimization_log.append(
                {
                    "timestamp": time.time(),
                    "suggestions": suggestions,
                    "current_performance": median_cycle,
                }
            )

        return suggestions

    def enable_multiprocessing(self, max_workers: Optional[int] = None) -> bool:
        """
        Enable multiprocessing for parallel operations

        Args:
            max_workers: Maximum number of worker processes (default: CPU count)

        Returns:
            True if successfully enabled, False otherwise
        """
        if self.process_pool is not None:
            self.logger.log_warning("Multiprocessing already enabled")
            return True

        try:
            workers = max_workers or self.max_workers
            self.process_pool = ProcessPoolExecutor(max_workers=workers)
            self.use_multiprocessing = True

            self.logger.log_warning(f"Multiprocessing enabled with {workers} workers")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to enable multiprocessing: {str(e)}")
            return False

    def enable_threading(self, max_workers: Optional[int] = None) -> bool:
        """
        Enable threading for I/O-bound parallel operations

        Args:
            max_workers: Maximum number of worker threads

        Returns:
            True if successfully enabled, False otherwise
        """
        if self.thread_pool is not None:
            self.logger.log_warning("Threading already enabled")
            return True

        try:
            workers = max_workers or self.max_workers * 2  # More threads than processes
            self.thread_pool = ThreadPoolExecutor(max_workers=workers)

            self.logger.log_warning(f"Threading enabled with {workers} workers")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to enable threading: {str(e)}")
            return False

    def parallel_map(
        self, func: Callable, items: List[Any], use_processes: bool = False
    ) -> List[Any]:
        """
        Execute a function on multiple items in parallel

        Args:
            func: Function to execute
            items: List of items to process
            use_processes: Use processes (CPU-bound) vs threads (I/O-bound)

        Returns:
            List of results in same order as input items
        """
        if not items:
            return []

        # Choose appropriate executor
        if use_processes and self.use_multiprocessing:
            if self.process_pool is None:
                self.enable_multiprocessing()
            executor = self.process_pool
        else:
            if self.thread_pool is None:
                self.enable_threading()
            executor = self.thread_pool

        # Execute in parallel
        try:
            if executor:
                results = list(executor.map(func, items))
            else:
                # Fallback to sequential processing
                results = [func(item) for item in items]

            return results

        except Exception as e:
            self.logger.log_error(f"Error in parallel execution: {str(e)}")
            # Fallback to sequential processing
            return [func(item) for item in items]

    async def async_gather(self, *coroutines) -> List[Any]:
        """
        Execute multiple coroutines concurrently

        Args:
            *coroutines: Coroutines to execute

        Returns:
            List of results
        """
        if not self.use_async:
            self.logger.log_warning("Async operations not enabled")
            return []

        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)

            # Check for exceptions
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                self.logger.log_error(f"Async operations had {len(errors)} errors")

            return results

        except Exception as e:
            self.logger.log_error(f"Error in async gather: {str(e)}")
            return []

    def profile_bottlenecks(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Profile a function to identify performance bottlenecks

        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Dictionary with profiling results
        """
        import cProfile
        import pstats
        from io import StringIO

        # Create profiler
        profiler = cProfile.Profile()

        # Profile the function
        profiler.enable()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            self.logger.log_error(f"Error profiling function: {str(e)}")

        execution_time = time.time() - start_time
        profiler.disable()

        # Get profiling stats
        stats_stream = StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats("cumulative")
        stats.print_stats(10)  # Top 10 time consumers

        profile_output = stats_stream.getvalue()

        # Parse top time consumers
        lines = profile_output.split("\n")
        top_consumers = []
        for line in lines[5:15]:  # Skip header lines, get top 10
            if line.strip():
                top_consumers.append(line.strip())

        return {
            "success": success,
            "execution_time_seconds": execution_time,
            "top_time_consumers": top_consumers,
            "full_profile": profile_output,
            "result": result,
        }

    def cache_data(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Cache data for fast retrieval

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (None = no expiry)
        """
        if not self.use_caching:
            return

        cache_entry = {"data": data, "timestamp": time.time(), "ttl": ttl}

        self.data_cache[key] = cache_entry

    def get_cached_data(self, key: str) -> Optional[Any]:
        """
        Retrieve cached data

        Args:
            key: Cache key

        Returns:
            Cached data if available and not expired, None otherwise
        """
        if not self.use_caching:
            self.cache_misses += 1
            return None

        if key not in self.data_cache:
            self.cache_misses += 1
            return None

        cache_entry = self.data_cache[key]

        # Check if expired
        if cache_entry["ttl"] is not None:
            age = time.time() - cache_entry["timestamp"]
            if age > cache_entry["ttl"]:
                del self.data_cache[key]
                self.cache_misses += 1
                return None

        self.cache_hits += 1
        return cache_entry["data"]

    def clear_cache(self, key: Optional[str] = None) -> None:
        """
        Clear cache (specific key or entire cache)

        Args:
            key: Specific key to clear (None = clear all)
        """
        if key is None:
            self.data_cache.clear()
            self.logger.log_warning("Cache cleared")
        elif key in self.data_cache:
            del self.data_cache[key]

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_enabled": self.use_caching,
            "cache_size": len(self.data_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": hit_rate,
            "total_requests": total_requests,
        }

    def create_async_client(self):
        """
        Create an async HTTP client using aiohttp

        Returns:
            aiohttp.ClientSession configured for optimal performance
        """
        try:
            import aiohttp

            # Configure for optimal performance
            connector = aiohttp.TCPConnector(
                limit=100,  # Max concurrent connections
                ttl_dns_cache=300,  # DNS cache for 5 minutes
                use_dns_cache=True,
            )

            timeout = aiohttp.ClientTimeout(
                total=self.config.get("api_timeout_seconds", 5), connect=2, sock_read=3
            )

            session = aiohttp.ClientSession(connector=connector, timeout=timeout)

            self.logger.log_warning("Async HTTP client created with aiohttp")
            return session

        except ImportError:
            self.logger.log_error(
                "aiohttp not installed - install with: pip install aiohttp"
            )
            return None

    async def fetch_multiple_urls_async(self, urls: List[str]) -> List[Any]:
        """
        Fetch multiple URLs concurrently using async operations

        Args:
            urls: List of URLs to fetch

        Returns:
            List of responses (or None for failed requests)
        """
        try:
            import aiohttp
        except ImportError:
            self.logger.log_error("aiohttp not installed")
            return [None] * len(urls)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                tasks.append(self._fetch_url_async(session, url))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

    async def _fetch_url_async(self, session, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single URL asynchronously

        Args:
            session: aiohttp session
            url: URL to fetch

        Returns:
            Response data or None on error
        """
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            self.logger.log_error(f"Error fetching {url}: {str(e)}")
            return None

    def timing_decorator(self, func: Callable) -> Callable:
        """
        Decorator to measure function execution time

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # ms

            self.logger.log_warning(
                f"{func.__name__} executed in {execution_time:.2f}ms"
            )

            return result

        return wrapper

    def batch_operations(
        self, operations: List[Callable], batch_size: int = 10
    ) -> List[Any]:
        """
        Batch multiple operations for more efficient execution

        Args:
            operations: List of callable operations
            batch_size: Number of operations per batch

        Returns:
            List of results
        """
        results = []

        for i in range(0, len(operations), batch_size):
            batch = operations[i : i + batch_size]

            # Execute batch in parallel
            batch_results = self.parallel_map(lambda op: op(), batch)
            results.extend(batch_results)

            # Small delay between batches to avoid overwhelming the system
            if i + batch_size < len(operations):
                time.sleep(0.01)

        return results

    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization status and recommendations

        Returns:
            Dictionary with optimization summary
        """
        cache_stats = self.get_cache_statistics()

        # Determine optimization level
        enabled_optimizations = []
        if self.use_async:
            enabled_optimizations.append("async_operations")
        if self.use_caching:
            enabled_optimizations.append("caching")
        if self.use_multiprocessing:
            enabled_optimizations.append("multiprocessing")
        if self.thread_pool is not None:
            enabled_optimizations.append("threading")

        optimization_score = len(enabled_optimizations) * 25  # Out of 100

        return {
            "optimization_score": optimization_score,
            "enabled_optimizations": enabled_optimizations,
            "system_resources": {
                "cpu_cores": self.cpu_count,
                "max_workers": self.max_workers,
                "thread_pool_active": self.thread_pool is not None,
                "process_pool_active": self.process_pool is not None,
            },
            "cache_performance": cache_stats,
            "optimization_history": len(self.optimization_log),
            "recommendations": self._get_quick_recommendations(),
        }

    def _get_quick_recommendations(self) -> List[str]:
        """
        Get quick optimization recommendations

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not self.use_async:
            recommendations.append("Enable async operations for better I/O performance")

        if not self.use_caching:
            recommendations.append("Enable caching to reduce redundant computations")

        if not self.use_multiprocessing and self.cpu_count > 2:
            recommendations.append(
                f"Enable multiprocessing to utilize {self.cpu_count} CPU cores"
            )

        cache_stats = self.get_cache_statistics()
        if cache_stats["hit_rate_percent"] < 50 and cache_stats["total_requests"] > 100:
            recommendations.append(
                "Cache hit rate is low - consider caching more data or longer TTL"
            )

        if not recommendations:
            recommendations.append("System is well optimized!")

        return recommendations

    def cleanup(self) -> None:
        """Cleanup resources (call when shutting down)"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
            self.thread_pool = None

        if self.process_pool:
            self.process_pool.shutdown(wait=True)
            self.process_pool = None

        self.clear_cache()
        self.logger.log_warning("Performance optimizer cleaned up")
