"""
Contrarian Trading Strategy
Trades against prevailing market sentiment
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContrarianStrategy:
    """
    Contrarian strategy that takes positions opposite to market sentiment.
    
    Strategy Logic:
    - When market is extremely bullish (>70% buying) → SHORT
    - When market is extremely bearish (<30% buying) → LONG
    - Uses sentiment indicators, volume, and price action
    """
    
    def __init__(self, sentiment_threshold: float = 0.7):
        self.name = "Contrarian"
        self.sentiment_threshold = sentiment_threshold
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data for contrarian opportunities.
        
        Args:
            market_data: Dict with 'price', 'volume', 'sentiment', 'buying_pressure'
            
        Returns:
            Dict with 'signal', 'confidence', 'reason'
        """
        try:
            sentiment = market_data.get('sentiment', 0.5)
            buying_pressure = market_data.get('buying_pressure', 0.5)
            volume = market_data.get('volume', 0)
            
            # Contrarian signal when sentiment is extreme
            if buying_pressure > self.sentiment_threshold:
                # Market too bullish → SHORT
                return {
                    'signal': 'SHORT',
                    'confidence': min(buying_pressure, 0.95),
                    'reason': f'Extreme bullish sentiment ({buying_pressure:.1%}) - expect reversal',
                    'size': self._calculate_position_size(buying_pressure)
                }
            elif buying_pressure < (1 - self.sentiment_threshold):
                # Market too bearish → LONG
                return {
                    'signal': 'LONG',
                    'confidence': min(1 - buying_pressure, 0.95),
                    'reason': f'Extreme bearish sentiment ({buying_pressure:.1%}) - expect bounce',
                    'size': self._calculate_position_size(1 - buying_pressure)
                }
            else:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.5,
                    'reason': 'Sentiment not extreme enough for contrarian trade'
                }
                
        except Exception as e:
            self.logger.error(f"Error in contrarian analysis: {e}")
            return {'signal': 'HOLD', 'confidence': 0, 'reason': f'Error: {e}'}
    
    def _calculate_position_size(self, sentiment_strength: float) -> float:
        """Calculate position size based on sentiment extremity"""
        # More extreme sentiment = larger position
        return min(sentiment_strength * 1.5, 1.0)
    
    def get_description(self) -> str:
        return "Contrarian strategy trading against extreme market sentiment"
