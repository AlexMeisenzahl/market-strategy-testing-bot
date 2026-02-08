"""
Portfolio Rebalancer

Rebalances capital allocation across strategies based on performance.
Allocates more capital to high-performing strategies and reduces allocation
to underperforming ones.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from services.portfolio_manager import portfolio_manager
from services.position_tracker import position_tracker


class PortfolioRebalancer:
    """
    Portfolio rebalancer for strategy allocation
    
    Analyzes strategy performance and adjusts capital allocation:
    - High Sharpe ratio strategies get more capital
    - Losing strategies get reduced allocation
    - Maintains diversification across strategies
    """

    def __init__(self, min_allocation_pct: float = 5.0,
                 max_allocation_pct: float = 40.0):
        """
        Initialize portfolio rebalancer
        
        Args:
            min_allocation_pct: Minimum allocation per strategy (%)
            max_allocation_pct: Maximum allocation per strategy (%)
        """
        self.logger = logging.getLogger(__name__)
        self.min_allocation_pct = min_allocation_pct
        self.max_allocation_pct = max_allocation_pct
        self.rebalance_history = []
        
        self.logger.info("Portfolio Rebalancer initialized")
        self.logger.info(f"  Min allocation: {min_allocation_pct}%")
        self.logger.info(f"  Max allocation: {max_allocation_pct}%")
    
    def rebalance(self, strategies: List[str] = None,
                 lookback_days: int = 30) -> Dict:
        """
        Execute portfolio rebalancing
        
        Args:
            strategies: List of strategy names to rebalance (None = all strategies)
            lookback_days: Days to look back for performance calculation
            
        Returns:
            Dict with rebalancing results
        """
        self.logger.info("Starting portfolio rebalancing...")
        
        # Get strategy performance
        strategy_performance = portfolio_manager.get_strategy_performance()
        
        if not strategy_performance:
            return {
                'success': False,
                'error': 'No strategy performance data available'
            }
        
        # Filter to specified strategies if provided
        if strategies:
            strategy_performance = {
                k: v for k, v in strategy_performance.items()
                if k in strategies
            }
        
        if not strategy_performance:
            return {
                'success': False,
                'error': 'No matching strategies found'
            }
        
        # Calculate performance scores
        performances = self._calculate_strategy_scores(strategy_performance)
        
        # Calculate optimal allocations
        new_allocations = self._calculate_optimal_allocations(performances)
        
        # Get current portfolio value
        portfolio_value = portfolio_manager.get_current_value()
        
        # Generate rebalancing plan
        rebalancing_plan = []
        for strategy, allocation_pct in new_allocations.items():
            current_data = strategy_performance[strategy]
            current_allocation = self._get_current_allocation(strategy, portfolio_value)
            
            target_value = portfolio_value * (allocation_pct / 100.0)
            change = target_value - current_allocation
            
            rebalancing_plan.append({
                'strategy': strategy,
                'current_allocation': current_allocation,
                'current_allocation_pct': (current_allocation / portfolio_value) * 100,
                'target_allocation': target_value,
                'target_allocation_pct': allocation_pct,
                'change': change,
                'change_pct': ((target_value - current_allocation) / current_allocation * 100)
                             if current_allocation > 0 else 0,
                'performance_score': performances[strategy]['score']
            })
        
        # Sort by change (largest changes first)
        rebalancing_plan.sort(key=lambda x: abs(x['change']), reverse=True)
        
        # Record rebalancing
        rebalance_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'lookback_days': lookback_days,
            'strategies_count': len(new_allocations),
            'portfolio_value': portfolio_value,
            'rebalancing_plan': rebalancing_plan
        }
        self.rebalance_history.append(rebalance_record)
        
        # Log results
        self.logger.info("✓ Rebalancing plan generated:")
        for item in rebalancing_plan:
            self.logger.info(
                f"  {item['strategy']}: "
                f"{item['current_allocation_pct']:.1f}% -> {item['target_allocation_pct']:.1f}% "
                f"({item['change']:+.2f})"
            )
        
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'portfolio_value': portfolio_value,
            'strategies_count': len(new_allocations),
            'rebalancing_plan': rebalancing_plan
        }
    
    def _calculate_strategy_scores(self, strategy_performance: Dict) -> Dict:
        """
        Calculate performance scores for strategies
        
        Args:
            strategy_performance: Dict of strategy performance data
            
        Returns:
            Dict of strategy -> performance metrics with scores
        """
        performances = {}
        
        for strategy, data in strategy_performance.items():
            # Calculate Sharpe ratio (simplified)
            closed_positions = data['closed_positions']
            
            if closed_positions == 0:
                sharpe_ratio = 0.0
            else:
                avg_return = data['avg_profit'] / 1000.0  # Normalized
                # Simplified Sharpe (would use actual volatility in production)
                sharpe_ratio = avg_return * 10 if data['win_rate'] > 50 else avg_return * 5
            
            # Calculate combined score
            # Factors: Sharpe ratio (40%), win rate (30%), total P&L (30%)
            win_rate_score = data['win_rate'] / 100.0
            pnl_score = max(0, min(1, data['total_pnl'] / 1000.0))  # Normalized to 0-1
            sharpe_score = max(0, min(1, sharpe_ratio / 2.0))  # Normalized to 0-1
            
            combined_score = (
                sharpe_score * 0.4 +
                win_rate_score * 0.3 +
                pnl_score * 0.3
            )
            
            performances[strategy] = {
                'sharpe_ratio': sharpe_ratio,
                'win_rate': data['win_rate'],
                'total_pnl': data['total_pnl'],
                'avg_profit': data['avg_profit'],
                'closed_positions': closed_positions,
                'score': combined_score
            }
        
        return performances
    
    def _calculate_optimal_allocations(self, performances: Dict) -> Dict[str, float]:
        """
        Calculate optimal allocation percentages based on performance
        
        Args:
            performances: Dict of strategy performance scores
            
        Returns:
            Dict of strategy -> allocation percentage
        """
        if not performances:
            return {}
        
        # Calculate allocation based on relative scores
        total_score = sum(p['score'] for p in performances.values())
        
        if total_score == 0:
            # Equal allocation if all scores are 0
            equal_allocation = 100.0 / len(performances)
            return {strategy: equal_allocation for strategy in performances.keys()}
        
        allocations = {}
        for strategy, perf in performances.items():
            # Allocate proportional to score
            allocation_pct = (perf['score'] / total_score) * 100.0
            
            # Apply min/max constraints
            allocation_pct = max(self.min_allocation_pct, allocation_pct)
            allocation_pct = min(self.max_allocation_pct, allocation_pct)
            
            allocations[strategy] = allocation_pct
        
        # Normalize to 100%
        total_allocation = sum(allocations.values())
        if total_allocation > 0:
            allocations = {
                k: (v / total_allocation) * 100.0
                for k, v in allocations.items()
            }
        
        return allocations
    
    def _get_current_allocation(self, strategy: str, portfolio_value: float) -> float:
        """
        Get current capital allocation for a strategy
        
        Args:
            strategy: Strategy name
            portfolio_value: Current portfolio value
            
        Returns:
            Current allocation in dollars
        """
        # Get open positions for this strategy
        positions = position_tracker.get_positions_by_strategy(strategy)
        open_positions = [p for p in positions if p.status == 'open']
        
        # Sum position sizes
        total_allocated = sum(p.size for p in open_positions)
        
        return total_allocated
    
    def get_allocation_recommendations(self, strategies: List[str] = None) -> Dict:
        """
        Get allocation recommendations without executing rebalancing
        
        Args:
            strategies: List of strategy names (None = all)
            
        Returns:
            Dict with recommendations
        """
        result = self.rebalance(strategies=strategies, lookback_days=30)
        
        if not result['success']:
            return result
        
        # Return recommendations only (don't execute)
        return {
            'success': True,
            'recommendations': result['rebalancing_plan'],
            'timestamp': result['timestamp']
        }
    
    def get_rebalance_history(self, limit: int = 10) -> List[Dict]:
        """
        Get rebalancing history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of rebalancing records
        """
        return self.rebalance_history[-limit:]
    
    def update_constraints(self, min_allocation_pct: float = None,
                          max_allocation_pct: float = None):
        """
        Update allocation constraints
        
        Args:
            min_allocation_pct: New minimum allocation percentage
            max_allocation_pct: New maximum allocation percentage
        """
        if min_allocation_pct is not None:
            self.min_allocation_pct = min_allocation_pct
            self.logger.info(f"Min allocation updated to {min_allocation_pct}%")
        
        if max_allocation_pct is not None:
            self.max_allocation_pct = max_allocation_pct
            self.logger.info(f"Max allocation updated to {max_allocation_pct}%")
    
    def schedule_rebalancing(self, frequency: str = 'weekly',
                           day_of_week: int = 0, hour: int = 0) -> Dict:
        """
        Schedule automatic rebalancing
        
        Args:
            frequency: 'daily', 'weekly', or 'monthly'
            day_of_week: Day of week for weekly (0=Monday, 6=Sunday)
            hour: Hour of day to execute (0-23)
            
        Returns:
            Dict with schedule info
            
        Note: This is a placeholder - actual scheduling would require
        a job scheduler like APScheduler or cron
        """
        schedule_info = {
            'frequency': frequency,
            'day_of_week': day_of_week,
            'hour': hour,
            'next_rebalance': self._calculate_next_rebalance_time(
                frequency, day_of_week, hour
            )
        }
        
        self.logger.info(
            f"Rebalancing scheduled: {frequency} at {hour:02d}:00"
        )
        
        return schedule_info
    
    def _calculate_next_rebalance_time(self, frequency: str,
                                      day_of_week: int, hour: int) -> str:
        """Calculate next rebalancing time"""
        now = datetime.utcnow()
        
        if frequency == 'daily':
            next_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
        
        elif frequency == 'weekly':
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_time = now + timedelta(days=days_ahead)
            next_time = next_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        else:  # monthly
            next_time = now.replace(day=1, hour=hour, minute=0, second=0, microsecond=0)
            if next_time <= now:
                # Next month
                if now.month == 12:
                    next_time = next_time.replace(year=now.year + 1, month=1)
                else:
                    next_time = next_time.replace(month=now.month + 1)
        
        return next_time.isoformat()


# Global instance
portfolio_rebalancer = PortfolioRebalancer()
