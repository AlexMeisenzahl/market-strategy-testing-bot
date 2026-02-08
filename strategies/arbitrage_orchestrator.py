"""
Arbitrage Orchestrator Module

Orchestrates arbitrage detection and execution with integrated performance tracking.
Coordinates between arbitrage strategy detection and execution tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from strategies.arbitrage_tracker import ArbitrageTracker
from strategies.arbitrage_strategy import ArbitrageStrategy, ArbitrageOpportunity
from strategies.arbitrage_executor import ArbitrageExecutor


class ArbitrageOrchestrator:
    """
    Orchestrates arbitrage operations with integrated tracking
    
    Manages the complete arbitrage workflow from opportunity detection
    through execution while maintaining comprehensive performance metrics.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with strategy and tracker
        
        Args:
            config: Configuration dictionary for arbitrage strategy
        """
        self.config = config
        self.strategy = ArbitrageStrategy(config)
        self.tracker = ArbitrageTracker()
        self.executor = ArbitrageExecutor()
    
    def detect_opportunity(self, market_data: Dict[str, Any],
                          price_data: Dict[str, float]) -> Optional[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunity and record it
        
        Args:
            market_data: Market information
            price_data: Current prices {'yes': float, 'no': float}
            
        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        opportunity = self.strategy.analyze(market_data, price_data)
        
        if opportunity:
            # Record opportunity with tracker
            self.tracker.record_opportunity(opportunity.to_dict())
        
        return opportunity
    
    def execute_opportunity(self, opportunity: ArbitrageOpportunity,
                           trade_size: float) -> Dict[str, Any]:
        """
        Execute arbitrage trade and record the result
        
        Args:
            opportunity: ArbitrageOpportunity to execute
            trade_size: Amount to invest in USD
            
        Returns:
            Execution result dictionary
        """
        # Enter position using strategy
        position = self.strategy.enter_position(opportunity, trade_size)
        
        # Calculate profit from position
        profit = position.get('expected_profit', 0.0)
        
        # Record execution with tracker
        execution_result = {
            'market_id': opportunity.market_id,
            'market_name': opportunity.market_name,
            'profit': profit,
            'executed_at': datetime.now()
        }
        
        self.tracker.record_execution(execution_result)
        
        return execution_result
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics from tracker
        
        Returns:
            Dictionary with current performance metrics
        """
        return self.tracker.get_metrics()
    
    def print_performance_dashboard(self) -> None:
        """Print performance metrics to console"""
        print(self.tracker.export_summary())
    
    def reset_performance_tracking(self) -> None:
        """Reset all performance metrics"""
        self.tracker.reset_metrics()
