"""
Smart Alerts Service - AI Pattern Detection
Analyzes trading patterns and suggests alerts based on detected trends
"""

from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from typing import List, Dict, Any, Optional


class SmartAlerts:
    """
    Detects patterns in market data and suggests intelligent alerts.
    Examples:
    - "BTC pumps every Tuesday at 2 PM"
    - "This market is usually mispriced around 4 PM"
    - Volume spikes at specific times
    - Price movements correlating with day of week
    """
    
    def __init__(self):
        self.patterns = []
        self.min_occurrences = 3  # Minimum pattern occurrences to be significant
        self.confidence_threshold = 0.7
        
    def analyze_time_patterns(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze trades for time-based patterns.
        
        Args:
            trades: List of trade dictionaries with 'timestamp', 'price', 'volume', etc.
            
        Returns:
            List of detected patterns with confidence scores
        """
        if not trades or len(trades) < self.min_occurrences:
            return []
        
        patterns = []
        
        # Analyze day-of-week patterns
        dow_patterns = self._analyze_day_of_week(trades)
        patterns.extend(dow_patterns)
        
        # Analyze hour-of-day patterns
        hour_patterns = self._analyze_hour_of_day(trades)
        patterns.extend(hour_patterns)
        
        # Analyze price volatility patterns
        volatility_patterns = self._analyze_volatility_patterns(trades)
        patterns.extend(volatility_patterns)
        
        return [p for p in patterns if p['confidence'] >= self.confidence_threshold]
    
    def _analyze_day_of_week(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns by day of week."""
        day_data = defaultdict(list)
        
        for trade in trades:
            timestamp = trade.get('timestamp')
            if not timestamp:
                continue
                
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    continue
            
            day = timestamp.strftime('%A')  # Monday, Tuesday, etc.
            price_change = trade.get('price_change', 0)
            volume = trade.get('volume', 0)
            
            day_data[day].append({
                'price_change': price_change,
                'volume': volume,
                'profit': trade.get('profit', 0)
            })
        
        patterns = []
        
        for day, data in day_data.items():
            if len(data) < self.min_occurrences:
                continue
            
            avg_price_change = statistics.mean([d['price_change'] for d in data])
            avg_volume = statistics.mean([d['volume'] for d in data if d['volume'] > 0])
            profitable_count = sum(1 for d in data if d['profit'] > 0)
            
            # Detect significant price movement on specific day
            if abs(avg_price_change) > 2:  # More than 2% average movement
                confidence = min(len(data) / 10, 1.0)  # Max at 10 occurrences
                
                direction = "increases" if avg_price_change > 0 else "decreases"
                patterns.append({
                    'type': 'day_of_week_price',
                    'pattern': f"Price typically {direction} on {day}s",
                    'day': day,
                    'avg_change': round(avg_price_change, 2),
                    'occurrences': len(data),
                    'confidence': confidence,
                    'recommendation': f"Consider setting alerts for {day}s"
                })
            
            # Detect high win rate on specific day
            if profitable_count > 0:
                win_rate = profitable_count / len(data)
                if win_rate > 0.7:
                    patterns.append({
                        'type': 'day_of_week_profit',
                        'pattern': f"{day}s show high profitability ({win_rate:.0%} win rate)",
                        'day': day,
                        'win_rate': win_rate,
                        'occurrences': len(data),
                        'confidence': min(len(data) / 10, 1.0),
                        'recommendation': f"Focus trading activity on {day}s"
                    })
        
        return patterns
    
    def _analyze_hour_of_day(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns by hour of day."""
        hour_data = defaultdict(list)
        
        for trade in trades:
            timestamp = trade.get('timestamp')
            if not timestamp:
                continue
                
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    continue
            
            hour = timestamp.hour
            price_change = trade.get('price_change', 0)
            volume = trade.get('volume', 0)
            
            hour_data[hour].append({
                'price_change': price_change,
                'volume': volume,
                'profit': trade.get('profit', 0)
            })
        
        patterns = []
        
        for hour, data in hour_data.items():
            if len(data) < self.min_occurrences:
                continue
            
            avg_volume = statistics.mean([d['volume'] for d in data if d['volume'] > 0])
            avg_price_change = statistics.mean([d['price_change'] for d in data])
            
            # Detect high volume at specific hour
            all_volumes = [d['volume'] for trade_hour in hour_data.values() 
                          for d in trade_hour if d['volume'] > 0]
            if all_volumes and avg_volume > statistics.mean(all_volumes) * 1.5:
                confidence = min(len(data) / 10, 1.0)
                
                patterns.append({
                    'type': 'hour_of_day_volume',
                    'pattern': f"High trading volume around {hour:02d}:00 UTC",
                    'hour': hour,
                    'avg_volume': round(avg_volume, 2),
                    'occurrences': len(data),
                    'confidence': confidence,
                    'recommendation': f"Monitor markets closely around {hour:02d}:00 UTC"
                })
            
            # Detect significant price movement at specific hour
            if abs(avg_price_change) > 1.5:
                direction = "increase" if avg_price_change > 0 else "decrease"
                patterns.append({
                    'type': 'hour_of_day_price',
                    'pattern': f"Price {direction} typically occurs around {hour:02d}:00 UTC",
                    'hour': hour,
                    'avg_change': round(avg_price_change, 2),
                    'occurrences': len(data),
                    'confidence': min(len(data) / 10, 1.0),
                    'recommendation': f"Set alerts for {hour:02d}:00 UTC"
                })
        
        return patterns
    
    def _analyze_volatility_patterns(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect volatility patterns."""
        if len(trades) < 10:
            return []
        
        patterns = []
        
        # Calculate volatility (standard deviation of price changes)
        price_changes = [t.get('price_change', 0) for t in trades if 'price_change' in t]
        
        if len(price_changes) < 5:
            return []
        
        volatility = statistics.stdev(price_changes)
        avg_change = statistics.mean(price_changes)
        
        # High volatility detection
        if volatility > 5:  # High volatility threshold
            patterns.append({
                'type': 'high_volatility',
                'pattern': f"High price volatility detected (σ={volatility:.2f}%)",
                'volatility': round(volatility, 2),
                'avg_change': round(avg_change, 2),
                'confidence': 0.8,
                'recommendation': "Use wider stop-losses and position sizing"
            })
        
        # Low volatility detection
        elif volatility < 1:  # Low volatility threshold
            patterns.append({
                'type': 'low_volatility',
                'pattern': f"Low price volatility detected (σ={volatility:.2f}%)",
                'volatility': round(volatility, 2),
                'avg_change': round(avg_change, 2),
                'confidence': 0.8,
                'recommendation': "Market may be consolidating; breakout possible"
            })
        
        return patterns
    
    def generate_alert_suggestions(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate actionable alert suggestions based on detected patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            List of suggested alerts with configuration
        """
        suggestions = []
        
        for pattern in patterns:
            if pattern['type'] == 'day_of_week_price':
                suggestions.append({
                    'alert_type': 'time_based',
                    'trigger': f"{pattern['day']} 00:00 UTC",
                    'message': pattern['pattern'],
                    'confidence': pattern['confidence'],
                    'action': 'Monitor price movements'
                })
            
            elif pattern['type'] == 'hour_of_day_volume':
                suggestions.append({
                    'alert_type': 'time_based',
                    'trigger': f"Daily at {pattern['hour']:02d}:00 UTC",
                    'message': pattern['pattern'],
                    'confidence': pattern['confidence'],
                    'action': 'Check for trading opportunities'
                })
            
            elif pattern['type'] == 'high_volatility':
                suggestions.append({
                    'alert_type': 'condition_based',
                    'trigger': 'Price change > 3%',
                    'message': pattern['pattern'],
                    'confidence': pattern['confidence'],
                    'action': 'Adjust risk management'
                })
        
        return suggestions


# Example usage
if __name__ == '__main__':
    # Create sample trades for testing
    sample_trades = [
        {
            'timestamp': '2024-01-01T14:00:00Z',
            'price_change': 2.5,
            'volume': 1000,
            'profit': 50
        },
        {
            'timestamp': '2024-01-08T14:00:00Z',  # Same day of week, same hour
            'price_change': 2.3,
            'volume': 1100,
            'profit': 45
        },
        {
            'timestamp': '2024-01-15T14:00:00Z',  # Pattern repeats
            'price_change': 2.7,
            'volume': 950,
            'profit': 55
        },
    ]
    
    alerts = SmartAlerts()
    patterns = alerts.analyze_time_patterns(sample_trades)
    suggestions = alerts.generate_alert_suggestions(patterns)
    
    print("Detected Patterns:")
    for pattern in patterns:
        print(f"  - {pattern['pattern']} (confidence: {pattern['confidence']:.0%})")
    
    print("\nSuggested Alerts:")
    for suggestion in suggestions:
        print(f"  - {suggestion['message']}")
