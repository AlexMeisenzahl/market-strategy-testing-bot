"""
Performance Monitor Module - Real-time speed and latency tracking

Measures and tracks system performance metrics:
- Detection speed (how fast opportunities are found)
- Decision speed (how fast trading decisions are made)
- Execution speed (how fast trades are executed)
- Network latency (API response times)
- Total cycle time (end-to-end processing)

Provides performance grades and competitive position estimates.
Identifies bottlenecks and suggests optimizations.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import statistics
from logger import get_logger


class PerformanceMonitor:
    """
    Tracks and analyzes system performance in real-time
    
    Measures critical timing metrics and provides insights into
    system speed, bottlenecks, and competitive positioning.
    """
    
    # Performance grade thresholds (in milliseconds)
    # Based on industry standards for high-frequency trading bots
    GRADE_THRESHOLDS = {
        'A+': 50,    # Elite: < 50ms total cycle time
        'A':  100,   # Excellent: < 100ms
        'B':  250,   # Good: < 250ms
        'C':  500,   # Average: < 500ms
        'D':  1000,  # Below average: < 1000ms
        'F':  float('inf')  # Poor: > 1000ms
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize performance monitor
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Timing measurements (lists to track history)
        self.detection_times: List[float] = []  # Time to find opportunities
        self.decision_times: List[float] = []   # Time to make trading decision
        self.execution_times: List[float] = []  # Time to execute trade
        self.network_latencies: List[float] = []  # API response times
        self.total_cycle_times: List[float] = []  # End-to-end processing time
        
        # Keep last N measurements (sliding window)
        self.history_size = config.get('performance_history_size', 100)
        
        # Current cycle tracking
        self.current_cycle_start: Optional[float] = None
        self.current_detection_start: Optional[float] = None
        
        # Statistics
        self.total_cycles = 0
        self.slow_cycles = 0  # Cycles that exceeded target time
        
        # Performance targets (milliseconds)
        self.target_cycle_time = config.get('target_cycle_time_ms', 200)
        self.target_network_latency = config.get('target_network_latency_ms', 100)
        
        # Competitive benchmarks (estimated from market research)
        self.competitive_benchmarks = {
            'pro_bot_avg': 50,      # Professional bots: ~50ms
            'amateur_bot_avg': 500, # Amateur bots: ~500ms
            'human_avg': 5000       # Human traders: ~5 seconds
        }
        
        self.logger.log_warning("Performance Monitor initialized")
    
    def start_cycle(self) -> None:
        """Mark the start of a new trading cycle"""
        self.current_cycle_start = time.time()
    
    def end_cycle(self) -> float:
        """
        Mark the end of a trading cycle and record the time
        
        Returns:
            Total cycle time in milliseconds
        """
        if self.current_cycle_start is None:
            return 0.0
        
        cycle_time_ms = (time.time() - self.current_cycle_start) * 1000
        
        # Record the measurement
        self._record_measurement(self.total_cycle_times, cycle_time_ms)
        
        # Track statistics
        self.total_cycles += 1
        if cycle_time_ms > self.target_cycle_time:
            self.slow_cycles += 1
        
        # Reset cycle tracking
        self.current_cycle_start = None
        
        return cycle_time_ms
    
    def measure_detection_speed(self, start_time: float, 
                               opportunities_found: int = 0) -> float:
        """
        Measure how fast the system detected arbitrage opportunities
        
        Args:
            start_time: Time when detection started (from time.time())
            opportunities_found: Number of opportunities found
            
        Returns:
            Detection time in milliseconds
        """
        detection_time_ms = (time.time() - start_time) * 1000
        
        # Record the measurement
        self._record_measurement(self.detection_times, detection_time_ms)
        
        # Log if detection was slow
        if detection_time_ms > 100:  # More than 100ms is concerning
            self.logger.log_warning(
                f"Slow detection: {detection_time_ms:.0f}ms "
                f"({opportunities_found} opportunities)"
            )
        
        return detection_time_ms
    
    def measure_decision_speed(self, start_time: float) -> float:
        """
        Measure how fast trading decisions were made
        
        Args:
            start_time: Time when decision process started
            
        Returns:
            Decision time in milliseconds
        """
        decision_time_ms = (time.time() - start_time) * 1000
        
        # Record the measurement
        self._record_measurement(self.decision_times, decision_time_ms)
        
        return decision_time_ms
    
    def measure_execution_speed(self, start_time: float) -> float:
        """
        Measure how fast trades were executed
        
        Args:
            start_time: Time when execution started
            
        Returns:
            Execution time in milliseconds
        """
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Record the measurement
        self._record_measurement(self.execution_times, execution_time_ms)
        
        return execution_time_ms
    
    def measure_network_latency(self, start_time: float, 
                               endpoint: str = "unknown") -> float:
        """
        Measure network latency for API calls
        
        Args:
            start_time: Time when API call was made
            endpoint: API endpoint called (for logging)
            
        Returns:
            Network latency in milliseconds
        """
        latency_ms = (time.time() - start_time) * 1000
        
        # Record the measurement
        self._record_measurement(self.network_latencies, latency_ms)
        
        # Log if latency is high
        if latency_ms > self.target_network_latency:
            self.logger.log_warning(
                f"High network latency: {latency_ms:.0f}ms to {endpoint}"
            )
        
        return latency_ms
    
    def _record_measurement(self, measurement_list: List[float], value: float) -> None:
        """
        Record a measurement and maintain sliding window
        
        Args:
            measurement_list: List to store measurement in
            value: Measurement value to record
        """
        measurement_list.append(value)
        
        # Maintain sliding window (keep only last N measurements)
        if len(measurement_list) > self.history_size:
            measurement_list.pop(0)
    
    def get_statistics(self, metric: str = 'total_cycle') -> Dict[str, float]:
        """
        Get statistical analysis of a performance metric
        
        Args:
            metric: Which metric to analyze ('detection', 'decision', 'execution', 
                   'network', 'total_cycle')
            
        Returns:
            Dictionary with min, max, mean, median, p95, p99 values
        """
        # Select the appropriate measurement list
        metric_map = {
            'detection': self.detection_times,
            'decision': self.decision_times,
            'execution': self.execution_times,
            'network': self.network_latencies,
            'total_cycle': self.total_cycle_times
        }
        
        measurements = metric_map.get(metric, self.total_cycle_times)
        
        if not measurements:
            return {
                'min': 0.0,
                'max': 0.0,
                'mean': 0.0,
                'median': 0.0,
                'p95': 0.0,
                'p99': 0.0,
                'count': 0
            }
        
        sorted_measurements = sorted(measurements)
        
        # Calculate percentiles
        p95_index = int(len(sorted_measurements) * 0.95)
        p99_index = int(len(sorted_measurements) * 0.99)
        
        return {
            'min': min(measurements),
            'max': max(measurements),
            'mean': statistics.mean(measurements),
            'median': statistics.median(measurements),
            'p95': sorted_measurements[p95_index] if p95_index < len(sorted_measurements) else sorted_measurements[-1],
            'p99': sorted_measurements[p99_index] if p99_index < len(sorted_measurements) else sorted_measurements[-1],
            'count': len(measurements)
        }
    
    def analyze_bottlenecks(self) -> Dict[str, Any]:
        """
        Analyze performance data to identify bottlenecks
        
        Returns:
            Dictionary with bottleneck analysis and recommendations
        """
        bottlenecks = []
        recommendations = []
        
        # Get statistics for each metric
        detection_stats = self.get_statistics('detection')
        decision_stats = self.get_statistics('decision')
        execution_stats = self.get_statistics('execution')
        network_stats = self.get_statistics('network')
        
        # Analyze detection speed
        if detection_stats['mean'] > 100:
            bottlenecks.append({
                'component': 'detection',
                'severity': 'high' if detection_stats['mean'] > 200 else 'medium',
                'avg_time_ms': detection_stats['mean'],
                'issue': 'Slow opportunity detection'
            })
            recommendations.append(
                "Optimize detection algorithm: Consider using numpy for faster calculations, "
                "implement early-exit conditions, or reduce the number of markets scanned."
            )
        
        # Analyze decision speed
        if decision_stats['mean'] > 50:
            bottlenecks.append({
                'component': 'decision',
                'severity': 'medium',
                'avg_time_ms': decision_stats['mean'],
                'issue': 'Slow trading decisions'
            })
            recommendations.append(
                "Simplify decision logic: Pre-compute conditions, cache frequently accessed data, "
                "or use lookup tables instead of complex calculations."
            )
        
        # Analyze execution speed
        if execution_stats['mean'] > 100:
            bottlenecks.append({
                'component': 'execution',
                'severity': 'high',
                'avg_time_ms': execution_stats['mean'],
                'issue': 'Slow trade execution'
            })
            recommendations.append(
                "Optimize execution: Use async operations, batch multiple trades, "
                "or reduce validation overhead."
            )
        
        # Analyze network latency
        if network_stats['mean'] > self.target_network_latency:
            bottlenecks.append({
                'component': 'network',
                'severity': 'high' if network_stats['mean'] > 300 else 'medium',
                'avg_time_ms': network_stats['mean'],
                'issue': 'High network latency'
            })
            recommendations.append(
                "Reduce network overhead: Use connection pooling, enable HTTP/2, "
                "consider using a CDN or closer API endpoints, implement request batching."
            )
        
        return {
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'total_bottlenecks': len(bottlenecks),
            'critical_component': bottlenecks[0]['component'] if bottlenecks else None
        }
    
    def get_performance_grade(self) -> Tuple[str, Dict[str, Any]]:
        """
        Calculate overall performance grade based on total cycle time
        
        Returns:
            Tuple of (grade, details dictionary)
        """
        if not self.total_cycle_times:
            return 'N/A', {'reason': 'No data available'}
        
        # Use median cycle time for grading (more robust than mean)
        stats = self.get_statistics('total_cycle')
        median_time = stats['median']
        
        # Determine grade
        grade = 'F'
        for grade_level, threshold in self.GRADE_THRESHOLDS.items():
            if median_time < threshold:
                grade = grade_level
                break
        
        # Calculate consistency (lower is better)
        consistency = (stats['p95'] - stats['median']) / stats['median'] * 100 if stats['median'] > 0 else 0
        
        details = {
            'grade': grade,
            'median_cycle_time_ms': median_time,
            'p95_cycle_time_ms': stats['p95'],
            'consistency_pct': consistency,
            'total_cycles_measured': stats['count'],
            'grade_description': self._get_grade_description(grade)
        }
        
        return grade, details
    
    def _get_grade_description(self, grade: str) -> str:
        """Get human-readable description for a grade"""
        descriptions = {
            'A+': 'Elite performance - Competitive with professional trading systems',
            'A': 'Excellent performance - Suitable for active trading',
            'B': 'Good performance - Adequate for most opportunities',
            'C': 'Average performance - May miss fast-moving opportunities',
            'D': 'Below average - Significant optimization needed',
            'F': 'Poor performance - Critical optimization required',
            'N/A': 'No data available'
        }
        return descriptions.get(grade, 'Unknown')
    
    def compare_to_competition(self) -> Dict[str, Any]:
        """
        Compare system performance to competitive benchmarks
        
        Returns:
            Dictionary with competitive positioning analysis
        """
        if not self.total_cycle_times:
            return {
                'status': 'no_data',
                'message': 'Insufficient data for competitive analysis'
            }
        
        stats = self.get_statistics('total_cycle')
        our_speed = stats['median']
        
        # Calculate competitive positioning
        comparisons = {}
        for competitor, benchmark_time in self.competitive_benchmarks.items():
            speed_ratio = our_speed / benchmark_time
            
            if speed_ratio < 0.8:
                status = 'faster'
                advantage = 'significant'
            elif speed_ratio < 1.0:
                status = 'faster'
                advantage = 'slight'
            elif speed_ratio < 1.2:
                status = 'slower'
                advantage = 'slight'
            else:
                status = 'slower'
                advantage = 'significant'
            
            comparisons[competitor] = {
                'benchmark_ms': benchmark_time,
                'our_speed_ms': our_speed,
                'speed_ratio': speed_ratio,
                'status': status,
                'advantage': advantage
            }
        
        # Determine overall competitive position
        if our_speed < self.competitive_benchmarks['pro_bot_avg']:
            position = 'elite'
            tier = 'Top 10% - Competitive with professional systems'
        elif our_speed < self.competitive_benchmarks['amateur_bot_avg']:
            position = 'competitive'
            tier = 'Top 50% - Better than average retail bots'
        elif our_speed < self.competitive_benchmarks['human_avg']:
            position = 'amateur'
            tier = 'Better than human traders but slower than bots'
        else:
            position = 'slow'
            tier = 'Slower than human traders - needs optimization'
        
        return {
            'our_median_speed_ms': our_speed,
            'competitive_position': position,
            'tier_description': tier,
            'comparisons': comparisons,
            'estimated_market_percentile': self._estimate_percentile(our_speed)
        }
    
    def _estimate_percentile(self, our_speed: float) -> int:
        """
        Estimate what percentile we're in compared to all market participants
        
        Args:
            our_speed: Our median cycle time in milliseconds
            
        Returns:
            Estimated percentile (0-100)
        """
        # Rough estimation based on competitive benchmarks
        if our_speed < 50:
            return 95  # Top 5%
        elif our_speed < 100:
            return 80  # Top 20%
        elif our_speed < 250:
            return 60  # Top 40%
        elif our_speed < 500:
            return 40  # Middle 40%
        elif our_speed < 1000:
            return 20  # Bottom 20%
        else:
            return 10  # Bottom 10%
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Dictionary with complete performance analysis
        """
        # Get grade and details
        grade, grade_details = self.get_performance_grade()
        
        # Get competitive analysis
        competitive_analysis = self.compare_to_competition()
        
        # Get bottleneck analysis
        bottleneck_analysis = self.analyze_bottlenecks()
        
        # Get all metric statistics
        all_stats = {
            'detection': self.get_statistics('detection'),
            'decision': self.get_statistics('decision'),
            'execution': self.get_statistics('execution'),
            'network': self.get_statistics('network'),
            'total_cycle': self.get_statistics('total_cycle')
        }
        
        # Calculate performance trends (improving/degrading)
        trend = self._calculate_trend()
        
        # Calculate uptime and reliability
        reliability = self._calculate_reliability()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_grade': grade_details,
            'competitive_position': competitive_analysis,
            'bottleneck_analysis': bottleneck_analysis,
            'detailed_metrics': all_stats,
            'performance_trend': trend,
            'reliability': reliability,
            'summary': {
                'total_cycles': self.total_cycles,
                'slow_cycles': self.slow_cycles,
                'slow_cycle_rate': (self.slow_cycles / self.total_cycles * 100) 
                                  if self.total_cycles > 0 else 0
            }
        }
    
    def _calculate_trend(self) -> Dict[str, str]:
        """
        Calculate if performance is improving or degrading over time
        
        Returns:
            Dictionary with trend analysis
        """
        if len(self.total_cycle_times) < 20:
            return {'status': 'insufficient_data'}
        
        # Compare first half vs second half of recent measurements
        mid_point = len(self.total_cycle_times) // 2
        first_half = self.total_cycle_times[:mid_point]
        second_half = self.total_cycle_times[mid_point:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change_pct = ((avg_second - avg_first) / avg_first) * 100
        
        if change_pct < -5:
            trend = 'improving'
            description = f'Performance improved by {abs(change_pct):.1f}%'
        elif change_pct > 5:
            trend = 'degrading'
            description = f'Performance degraded by {change_pct:.1f}%'
        else:
            trend = 'stable'
            description = 'Performance is stable'
        
        return {
            'status': trend,
            'change_percent': change_pct,
            'description': description
        }
    
    def _calculate_reliability(self) -> Dict[str, Any]:
        """
        Calculate system reliability metrics
        
        Returns:
            Dictionary with reliability metrics
        """
        if self.total_cycles == 0:
            return {'status': 'no_data'}
        
        # Success rate (cycles that completed within target time)
        success_rate = ((self.total_cycles - self.slow_cycles) / self.total_cycles) * 100
        
        # Consistency score (based on standard deviation)
        if len(self.total_cycle_times) > 1:
            stdev = statistics.stdev(self.total_cycle_times)
            mean = statistics.mean(self.total_cycle_times)
            consistency_score = max(0, 100 - (stdev / mean * 100))
        else:
            consistency_score = 100
        
        return {
            'success_rate_percent': success_rate,
            'consistency_score': consistency_score,
            'total_cycles': self.total_cycles,
            'successful_cycles': self.total_cycles - self.slow_cycles,
            'slow_cycles': self.slow_cycles
        }
    
    def reset_statistics(self) -> None:
        """Reset all performance statistics (use carefully)"""
        self.detection_times.clear()
        self.decision_times.clear()
        self.execution_times.clear()
        self.network_latencies.clear()
        self.total_cycle_times.clear()
        self.total_cycles = 0
        self.slow_cycles = 0
        self.logger.log_warning("Performance statistics reset")
