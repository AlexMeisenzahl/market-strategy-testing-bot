"""
Competition Monitor Module - Detect other arbitrage bots

Detects when other bots are competing for the same opportunities by:
- Tracking opportunity lifespan
- Measuring fill success rates
- Detecting snipe patterns (instant disappearance)
- Estimating competition level

Helps adapt strategy to competitive environment.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from logger import get_logger


class OpportunityTracker:
    """Tracks individual opportunity lifecycle"""
    
    def __init__(self, opportunity_id: str, market: str, detected_at: datetime):
        """
        Initialize opportunity tracker
        
        Args:
            opportunity_id: Unique identifier for opportunity
            market: Market name
            detected_at: When opportunity was first detected
        """
        self.opportunity_id = opportunity_id
        self.market = market
        self.detected_at = detected_at
        self.disappeared_at: Optional[datetime] = None
        self.traded: bool = False
        self.filled: bool = False
        
    @property
    def lifespan(self) -> float:
        """
        Get opportunity lifespan in seconds
        
        Returns:
            Lifespan in seconds
        """
        end_time = self.disappeared_at or datetime.now()
        return (end_time - self.detected_at).total_seconds()
    
    def mark_disappeared(self) -> None:
        """Mark opportunity as disappeared"""
        self.disappeared_at = datetime.now()
    
    def mark_traded(self, filled: bool = True) -> None:
        """
        Mark opportunity as traded
        
        Args:
            filled: Whether order was successfully filled
        """
        self.traded = True
        self.filled = filled


class CompetitionMonitor:
    """
    Monitor trading competition from other bots
    
    Analyzes market behavior to detect presence of competing bots
    and estimate competition intensity.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize competition monitor
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Competition thresholds
        comp_config = config.get('competition_monitoring', {})
        
        self.high_competition_threshold = comp_config.get('high_competition_lifespan', 1.0)  # < 1s
        self.low_competition_threshold = comp_config.get('low_competition_lifespan', 5.0)   # > 5s
        self.snipe_threshold = comp_config.get('snipe_threshold', 0.5)  # < 0.5s = snipe
        self.history_window = comp_config.get('history_window_minutes', 60)  # 60 minutes
        
        # Tracking data structures
        self.opportunities: Dict[str, OpportunityTracker] = {}
        self.lifespan_history: deque = deque(maxlen=1000)  # Last 1000 opportunities
        self.fill_history: deque = deque(maxlen=100)  # Last 100 trade attempts
        self.snipe_count = 0
        self.total_opportunities = 0
        
        # Competition metrics
        self.current_competition_level = "unknown"
        self.last_analysis = None
        
        self.logger.log_warning(
            f"CompetitionMonitor initialized - "
            f"Snipe threshold: {self.snipe_threshold}s, "
            f"History window: {self.history_window}min"
        )
    
    def track_opportunity(self, opportunity_id: str, market: str) -> OpportunityTracker:
        """
        Start tracking a new opportunity
        
        Args:
            opportunity_id: Unique identifier for opportunity
            market: Market name
            
        Returns:
            OpportunityTracker object
        """
        tracker = OpportunityTracker(
            opportunity_id=opportunity_id,
            market=market,
            detected_at=datetime.now()
        )
        
        self.opportunities[opportunity_id] = tracker
        self.total_opportunities += 1
        
        return tracker
    
    def mark_opportunity_disappeared(self, opportunity_id: str) -> None:
        """
        Mark opportunity as disappeared from market
        
        Args:
            opportunity_id: Unique identifier for opportunity
        """
        if opportunity_id not in self.opportunities:
            return
        
        tracker = self.opportunities[opportunity_id]
        tracker.mark_disappeared()
        
        # Record lifespan
        lifespan = tracker.lifespan
        self.lifespan_history.append(lifespan)
        
        # Check if it was a snipe (disappeared very quickly)
        if lifespan < self.snipe_threshold:
            self.snipe_count += 1
            self.logger.log_warning(
                f"Possible snipe detected: {tracker.market} disappeared in {lifespan:.3f}s"
            )
    
    def mark_trade_attempted(self, opportunity_id: str, filled: bool) -> None:
        """
        Mark that we attempted to trade an opportunity
        
        Args:
            opportunity_id: Unique identifier for opportunity
            filled: Whether the order was successfully filled
        """
        if opportunity_id not in self.opportunities:
            return
        
        tracker = self.opportunities[opportunity_id]
        tracker.mark_traded(filled)
        
        # Record fill result
        self.fill_history.append({
            'timestamp': datetime.now(),
            'filled': filled,
            'lifespan': tracker.lifespan
        })
    
    def track_opportunity_lifespan(self) -> Dict[str, Any]:
        """
        Analyze how long opportunities last
        
        Returns:
            Dictionary with lifespan analysis
        """
        if not self.lifespan_history:
            return {
                'avg_lifespan': 0,
                'median_lifespan': 0,
                'min_lifespan': 0,
                'max_lifespan': 0,
                'competition_indicator': 'unknown'
            }
        
        # Calculate statistics
        lifespans = list(self.lifespan_history)
        avg_lifespan = sum(lifespans) / len(lifespans)
        median_lifespan = sorted(lifespans)[len(lifespans) // 2]
        min_lifespan = min(lifespans)
        max_lifespan = max(lifespans)
        
        # Determine competition level based on average lifespan
        if avg_lifespan < self.high_competition_threshold:
            competition_indicator = 'high'
        elif avg_lifespan > self.low_competition_threshold:
            competition_indicator = 'low'
        else:
            competition_indicator = 'medium'
        
        return {
            'avg_lifespan': avg_lifespan,
            'median_lifespan': median_lifespan,
            'min_lifespan': min_lifespan,
            'max_lifespan': max_lifespan,
            'samples': len(lifespans),
            'competition_indicator': competition_indicator
        }
    
    def measure_fill_success_rate(self) -> Dict[str, Any]:
        """
        Measure how often our trades get filled
        
        Returns:
            Dictionary with fill rate analysis
        """
        if not self.fill_history:
            return {
                'total_attempts': 0,
                'successful_fills': 0,
                'failed_fills': 0,
                'fill_rate': 0,
                'competition_indicator': 'unknown'
            }
        
        # Count fills
        total_attempts = len(self.fill_history)
        successful_fills = sum(1 for trade in self.fill_history if trade['filled'])
        failed_fills = total_attempts - successful_fills
        fill_rate = (successful_fills / total_attempts) if total_attempts > 0 else 0
        
        # Determine competition level based on fill rate
        if fill_rate < 0.5:  # < 50% fill rate
            competition_indicator = 'high'
        elif fill_rate > 0.8:  # > 80% fill rate
            competition_indicator = 'low'
        else:
            competition_indicator = 'medium'
        
        return {
            'total_attempts': total_attempts,
            'successful_fills': successful_fills,
            'failed_fills': failed_fills,
            'fill_rate': fill_rate,
            'fill_rate_pct': fill_rate * 100,
            'competition_indicator': competition_indicator
        }
    
    def detect_snipe_patterns(self) -> Dict[str, Any]:
        """
        Detect if opportunities are being sniped by faster bots
        
        Returns:
            Dictionary with snipe pattern analysis
        """
        if not self.lifespan_history:
            return {
                'total_opportunities': 0,
                'snipes_detected': 0,
                'snipe_rate': 0,
                'avg_snipe_time': 0,
                'competition_indicator': 'unknown'
            }
        
        # Count snipes (very fast disappearances)
        snipe_times = [
            lifespan for lifespan in self.lifespan_history 
            if lifespan < self.snipe_threshold
        ]
        
        snipe_rate = len(snipe_times) / len(self.lifespan_history) if self.lifespan_history else 0
        avg_snipe_time = sum(snipe_times) / len(snipe_times) if snipe_times else 0
        
        # Determine competition level based on snipe rate
        if snipe_rate > 0.3:  # > 30% of opportunities sniped
            competition_indicator = 'high'
        elif snipe_rate > 0.1:  # 10-30% sniped
            competition_indicator = 'medium'
        else:
            competition_indicator = 'low'
        
        return {
            'total_opportunities': len(self.lifespan_history),
            'snipes_detected': len(snipe_times),
            'snipe_rate': snipe_rate,
            'snipe_rate_pct': snipe_rate * 100,
            'avg_snipe_time': avg_snipe_time,
            'competition_indicator': competition_indicator
        }
    
    def analyze_competition_level(self) -> str:
        """
        Analyze overall competition level
        
        Returns:
            Competition level: 'low', 'medium', 'high', or 'unknown'
        """
        # Get all indicators
        lifespan_analysis = self.track_opportunity_lifespan()
        fill_analysis = self.measure_fill_success_rate()
        snipe_analysis = self.detect_snipe_patterns()
        
        # Count votes for each level
        indicators = [
            lifespan_analysis['competition_indicator'],
            fill_analysis['competition_indicator'],
            snipe_analysis['competition_indicator']
        ]
        
        # Remove unknowns
        indicators = [i for i in indicators if i != 'unknown']
        
        if not indicators:
            self.current_competition_level = 'unknown'
        else:
            # Use majority vote
            high_count = indicators.count('high')
            medium_count = indicators.count('medium')
            low_count = indicators.count('low')
            
            if high_count >= 2:
                self.current_competition_level = 'high'
            elif low_count >= 2:
                self.current_competition_level = 'low'
            else:
                self.current_competition_level = 'medium'
        
        self.last_analysis = datetime.now()
        
        return self.current_competition_level
    
    def get_competition_report(self) -> str:
        """
        Generate comprehensive competition report
        
        Returns:
            Formatted report string
        """
        # Analyze competition
        competition_level = self.analyze_competition_level()
        lifespan_analysis = self.track_opportunity_lifespan()
        fill_analysis = self.measure_fill_success_rate()
        snipe_analysis = self.detect_snipe_patterns()
        
        report = "\n" + "="*60 + "\n"
        report += "COMPETITION MONITORING REPORT\n"
        report += "="*60 + "\n\n"
        
        report += f"OVERALL COMPETITION LEVEL: {competition_level.upper()}\n\n"
        
        report += "OPPORTUNITY LIFESPAN:\n"
        report += f"  Total Opportunities Tracked: {lifespan_analysis['samples']}\n"
        report += f"  Average Lifespan: {lifespan_analysis['avg_lifespan']:.2f}s\n"
        report += f"  Median Lifespan: {lifespan_analysis['median_lifespan']:.2f}s\n"
        report += f"  Min/Max: {lifespan_analysis['min_lifespan']:.2f}s / {lifespan_analysis['max_lifespan']:.2f}s\n"
        report += f"  Competition Indicator: {lifespan_analysis['competition_indicator']}\n"
        
        if lifespan_analysis['avg_lifespan'] < 1.0:
            report += "  ⚠️ Very short lifespans - HIGH competition detected\n"
        elif lifespan_analysis['avg_lifespan'] > 5.0:
            report += "  ✓ Good lifespans - LOW competition\n"
        report += "\n"
        
        report += "FILL SUCCESS RATE:\n"
        report += f"  Total Trade Attempts: {fill_analysis['total_attempts']}\n"
        report += f"  Successful Fills: {fill_analysis['successful_fills']}\n"
        report += f"  Failed Fills: {fill_analysis['failed_fills']}\n"
        report += f"  Fill Rate: {fill_analysis['fill_rate_pct']:.1f}%\n"
        report += f"  Competition Indicator: {fill_analysis['competition_indicator']}\n"
        
        if fill_analysis['fill_rate'] < 0.5:
            report += "  ⚠️ Low fill rate - orders being front-run\n"
        elif fill_analysis['fill_rate'] > 0.8:
            report += "  ✓ High fill rate - executing well\n"
        report += "\n"
        
        report += "SNIPE DETECTION:\n"
        report += f"  Total Opportunities: {snipe_analysis['total_opportunities']}\n"
        report += f"  Snipes Detected: {snipe_analysis['snipes_detected']}\n"
        report += f"  Snipe Rate: {snipe_analysis['snipe_rate_pct']:.1f}%\n"
        if snipe_analysis['avg_snipe_time'] > 0:
            report += f"  Average Snipe Time: {snipe_analysis['avg_snipe_time']:.3f}s\n"
        report += f"  Competition Indicator: {snipe_analysis['competition_indicator']}\n"
        
        if snipe_analysis['snipe_rate'] > 0.3:
            report += "  ⚠️ High snipe rate - very fast bots active\n"
        elif snipe_analysis['snipe_rate'] < 0.1:
            report += "  ✓ Low snipe rate - good opportunity access\n"
        report += "\n"
        
        report += "RECOMMENDATIONS:\n"
        if competition_level == 'high':
            report += "  - Consider faster execution methods\n"
            report += "  - Lower profit thresholds to compete\n"
            report += "  - Focus on less popular markets\n"
            report += "  - Optimize order routing\n"
        elif competition_level == 'medium':
            report += "  - Current execution speed is adequate\n"
            report += "  - Monitor for changes in competition\n"
            report += "  - Continue current strategy\n"
        else:  # low
            report += "  - Competition is minimal\n"
            report += "  - Can be more selective with opportunities\n"
            report += "  - Good time for larger position sizes\n"
        
        report += "\n"
        report += "="*60 + "\n"
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get competition monitoring statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_opportunities': self.total_opportunities,
            'active_opportunities': len(self.opportunities),
            'current_competition_level': self.current_competition_level,
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None,
            'lifespan_samples': len(self.lifespan_history),
            'fill_samples': len(self.fill_history),
            'total_snipes': self.snipe_count
        }
    
    def reset_statistics(self) -> None:
        """Reset all tracking data"""
        self.opportunities.clear()
        self.lifespan_history.clear()
        self.fill_history.clear()
        self.snipe_count = 0
        self.total_opportunities = 0
        self.current_competition_level = "unknown"
        self.last_analysis = None
        
        self.logger.log_warning("Competition monitoring statistics reset")
