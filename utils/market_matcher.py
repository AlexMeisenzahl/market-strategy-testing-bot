"""
Market Matcher Utility

Matches markets across different exchanges using fuzzy matching.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import difflib


class MarketMatcher:
    """
    Matches markets across exchanges for cross-exchange arbitrage
    
    Uses fuzzy string matching and validates event timing.
    """
    
    def __init__(self, min_similarity: float = 0.85):
        """
        Initialize market matcher
        
        Args:
            min_similarity: Minimum similarity score (0-1) for matching
        """
        self.min_similarity = min_similarity
    
    def find_matches(self, markets1: List[Dict], markets2: List[Dict]) -> List[Tuple[Dict, Dict, float]]:
        """
        Find matching markets between two exchanges
        
        Args:
            markets1: Markets from first exchange
            markets2: Markets from second exchange
            
        Returns:
            List of tuples (market1, market2, similarity_score)
        """
        matches = []
        
        for m1 in markets1:
            for m2 in markets2:
                similarity = self.calculate_similarity(m1, m2)
                
                if similarity >= self.min_similarity:
                    # Verify event times are close
                    if self._verify_event_times(m1, m2):
                        matches.append((m1, m2, similarity))
        
        return matches
    
    def calculate_similarity(self, market1: Dict, market2: Dict) -> float:
        """
        Calculate similarity score between two markets
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Similarity score between 0 and 1
        """
        # Get market questions/names
        q1 = market1.get('question', market1.get('name', '')).lower()
        q2 = market2.get('question', market2.get('name', '')).lower()
        
        if not q1 or not q2:
            return 0.0
        
        # Use SequenceMatcher for fuzzy matching
        similarity = difflib.SequenceMatcher(None, q1, q2).ratio()
        
        return similarity
    
    def _verify_event_times(self, market1: Dict, market2: Dict) -> bool:
        """
        Verify that event close times are within 1 hour
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            True if times are compatible
        """
        # Get end dates
        end1 = market1.get('end_date', market1.get('close_time', ''))
        end2 = market2.get('end_date', market2.get('close_time', ''))
        
        if not end1 or not end2:
            # If no end dates, assume they match
            return True
        
        try:
            # Parse dates (simplified - production would handle multiple formats)
            date1 = datetime.fromisoformat(end1.replace('Z', '+00:00'))
            date2 = datetime.fromisoformat(end2.replace('Z', '+00:00'))
            
            # Check if within 1 hour
            diff = abs((date1 - date2).total_seconds())
            return diff <= 3600  # 1 hour in seconds
            
        except Exception:
            # If parsing fails, assume they match
            return True
