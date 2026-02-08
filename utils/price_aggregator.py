"""
Price Aggregator Utility

Advanced price aggregation with:
- Multi-source price consensus
- Outlier detection and filtering
- Volume-weighted averaging
- Confidence scoring
- Anomaly detection
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
from decimal import Decimal
import statistics
import math


class PriceAggregator:
    """
    Sophisticated price aggregation system
    
    Features:
    - Weighted consensus from multiple sources
    - Statistical outlier removal
    - Volume weighting
    - Confidence scoring
    - Data quality metrics
    """
    
    def __init__(
        self,
        outlier_threshold: float = 2.0,  # Standard deviations
        min_sources: int = 2,
        volume_weight_factor: float = 0.3
    ):
        """
        Initialize price aggregator
        
        Args:
            outlier_threshold: Z-score threshold for outlier detection
            min_sources: Minimum number of sources required
            volume_weight_factor: Weight given to volume (0-1)
        """
        self.outlier_threshold = outlier_threshold
        self.min_sources = min_sources
        self.volume_weight_factor = volume_weight_factor
        
    def aggregate_prices(
        self,
        prices: Dict[str, Tuple[float, float]]
    ) -> Dict[str, any]:
        """
        Aggregate prices from multiple sources with advanced consensus
        
        Args:
            prices: Dict mapping source name to (price, volume) tuple
            
        Returns:
            Dict with consensus price, confidence, and metadata
        """
        if not prices or len(prices) < self.min_sources:
            return {
                "price": None,
                "confidence": 0,
                "source_count": len(prices) if prices else 0,
                "error": "Insufficient sources"
            }
            
        # Extract price and volume data
        price_list = []
        volume_list = []
        source_names = []
        
        for source, (price, volume) in prices.items():
            if price and price > 0:
                price_list.append(price)
                volume_list.append(volume if volume > 0 else 1)  # Default volume
                source_names.append(source)
                
        if len(price_list) < self.min_sources:
            return {
                "price": None,
                "confidence": 0,
                "source_count": len(price_list),
                "error": "Insufficient valid prices"
            }
            
        # Detect and remove outliers
        cleaned_data = self._remove_outliers(
            list(zip(price_list, volume_list, source_names))
        )
        
        if len(cleaned_data) < self.min_sources:
            # If too many outliers, use median instead
            consensus_price = statistics.median(price_list)
            confidence = 50  # Low confidence
            outliers_removed = len(price_list) - len(cleaned_data)
        else:
            # Calculate weighted consensus
            consensus_price = self._weighted_consensus(cleaned_data)
            confidence = self._calculate_confidence(cleaned_data, price_list)
            outliers_removed = len(price_list) - len(cleaned_data)
            
        # Calculate price spread and dispersion
        price_spread = (max(price_list) - min(price_list)) / consensus_price * 100
        price_std = statistics.stdev(price_list) if len(price_list) > 1 else 0
        
        return {
            "price": consensus_price,
            "confidence": confidence,
            "source_count": len(price_list),
            "sources_used": len(cleaned_data),
            "outliers_removed": outliers_removed,
            "price_spread_pct": price_spread,
            "price_std": price_std,
            "min_price": min(price_list),
            "max_price": max(price_list),
            "median_price": statistics.median(price_list),
            "sources": source_names,
            "timestamp": datetime.now().isoformat(),
        }
        
    def _remove_outliers(
        self,
        data: List[Tuple[float, float, str]]
    ) -> List[Tuple[float, float, str]]:
        """
        Remove statistical outliers using modified Z-score
        
        Args:
            data: List of (price, volume, source) tuples
            
        Returns:
            Filtered list without outliers
        """
        if len(data) < 3:
            return data
            
        prices = [p for p, v, s in data]
        
        # Calculate median and MAD (Median Absolute Deviation)
        median = statistics.median(prices)
        mad = statistics.median([abs(p - median) for p in prices])
        
        if mad == 0:
            # All prices are identical
            return data
            
        # Calculate modified z-scores
        z_scores = [abs((p - median) / (1.4826 * mad)) for p in prices]
        
        # Filter out outliers
        filtered = [
            data[i] for i in range(len(data))
            if z_scores[i] < self.outlier_threshold
        ]
        
        return filtered if filtered else data  # Return original if all filtered
        
    def _weighted_consensus(
        self,
        data: List[Tuple[float, float, str]]
    ) -> float:
        """
        Calculate volume-weighted consensus price
        
        Args:
            data: List of (price, volume, source) tuples
            
        Returns:
            Weighted consensus price
        """
        if not data:
            return 0.0
            
        # Separate equal weight and volume weight components
        prices = [p for p, v, s in data]
        volumes = [v for p, v, s in data]
        
        # Equal weight component
        equal_weight_price = statistics.mean(prices)
        
        # Volume weight component
        total_volume = sum(volumes)
        if total_volume > 0:
            volume_weight_price = sum(
                p * v / total_volume for p, v, _ in data
            )
        else:
            volume_weight_price = equal_weight_price
            
        # Combine with weighting factor
        consensus = (
            equal_weight_price * (1 - self.volume_weight_factor) +
            volume_weight_price * self.volume_weight_factor
        )
        
        return consensus
        
    def _calculate_confidence(
        self,
        cleaned_data: List[Tuple[float, float, str]],
        all_prices: List[float]
    ) -> int:
        """
        Calculate confidence score (0-100) based on:
        - Number of sources
        - Price agreement (low spread)
        - Outlier ratio
        
        Args:
            cleaned_data: Cleaned price data
            all_prices: All prices before filtering
            
        Returns:
            Confidence score (0-100)
        """
        # Source count factor (more sources = higher confidence)
        source_factor = min(len(all_prices) / 5, 1.0) * 40  # Max 40 points
        
        # Price agreement factor (lower spread = higher confidence)
        prices = [p for p, v, s in cleaned_data]
        if len(prices) > 1:
            mean_price = statistics.mean(prices)
            cv = statistics.stdev(prices) / mean_price if mean_price > 0 else 1
            agreement_factor = max(0, (1 - cv)) * 40  # Max 40 points
        else:
            agreement_factor = 20
            
        # Outlier factor (fewer outliers = higher confidence)
        outlier_ratio = (len(all_prices) - len(cleaned_data)) / len(all_prices)
        outlier_factor = max(0, (1 - outlier_ratio)) * 20  # Max 20 points
        
        confidence = int(source_factor + agreement_factor + outlier_factor)
        return max(0, min(100, confidence))
        
    def detect_anomaly(
        self,
        current_price: float,
        historical_prices: List[float],
        threshold: float = 3.0
    ) -> Dict[str, any]:
        """
        Detect if current price is anomalous compared to history
        
        Args:
            current_price: Current price to check
            historical_prices: List of recent historical prices
            threshold: Z-score threshold for anomaly
            
        Returns:
            Dict with anomaly detection results
        """
        if not historical_prices or len(historical_prices) < 3:
            return {
                "is_anomaly": False,
                "reason": "Insufficient history",
                "z_score": 0
            }
            
        mean = statistics.mean(historical_prices)
        std = statistics.stdev(historical_prices)
        
        if std == 0:
            return {
                "is_anomaly": current_price != mean,
                "reason": "Zero standard deviation",
                "z_score": float('inf') if current_price != mean else 0
            }
            
        z_score = abs((current_price - mean) / std)
        is_anomaly = z_score > threshold
        
        if is_anomaly:
            direction = "higher" if current_price > mean else "lower"
            reason = f"Price is {z_score:.2f} std deviations {direction} than average"
        else:
            reason = "Within normal range"
            
        return {
            "is_anomaly": is_anomaly,
            "z_score": z_score,
            "reason": reason,
            "mean": mean,
            "std": std,
            "deviation_pct": ((current_price - mean) / mean * 100) if mean > 0 else 0
        }
        
    def calculate_quality_score(
        self,
        aggregation_result: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Calculate overall data quality score
        
        Args:
            aggregation_result: Result from aggregate_prices
            
        Returns:
            Dict with quality metrics
        """
        if not aggregation_result.get("price"):
            return {
                "quality_score": 0,
                "quality_grade": "F",
                "issues": ["No valid price"]
            }
            
        issues = []
        score = 100
        
        # Check source count
        if aggregation_result["source_count"] < 3:
            issues.append("Low source count")
            score -= 20
            
        # Check outliers
        if aggregation_result["outliers_removed"] > 0:
            issues.append(f"{aggregation_result['outliers_removed']} outliers removed")
            score -= aggregation_result["outliers_removed"] * 10
            
        # Check price spread
        if aggregation_result["price_spread_pct"] > 5:
            issues.append(f"High price spread: {aggregation_result['price_spread_pct']:.1f}%")
            score -= 15
            
        # Check confidence
        if aggregation_result["confidence"] < 70:
            issues.append(f"Low confidence: {aggregation_result['confidence']}")
            score -= 10
            
        score = max(0, score)
        
        # Assign grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
            
        return {
            "quality_score": score,
            "quality_grade": grade,
            "issues": issues,
            "recommendation": self._get_recommendation(score, issues)
        }
        
    def _get_recommendation(self, score: int, issues: List[str]) -> str:
        """Get recommendation based on quality score"""
        if score >= 90:
            return "Excellent data quality - proceed with confidence"
        elif score >= 80:
            return "Good data quality - acceptable for trading"
        elif score >= 70:
            return "Fair data quality - use with caution"
        elif score >= 60:
            return "Poor data quality - avoid high-value trades"
        else:
            return "Critical data quality issues - do not trade"
