"""
Strategy Auto-Selection

Automatically identify best performing strategy and allocate capital.
"""

from typing import Dict, Optional, List
from datetime import datetime

from database.competition_models import Strategy, StrategyPerformanceSnapshot
from logger import get_logger

logger = get_logger()

# Constants
SHARPE_SCALING_FACTOR = 10  # Scale Sharpe ratio in scoring formula


class StrategySelector:
    """Automatically select best performing strategy"""

    def __init__(
        self,
        min_return_pct: float = 0.0,
        min_sharpe: float = 1.5,
        min_win_rate: float = 55.0,
        max_drawdown_pct: float = 15.0,
        min_trades: int = 20
    ):
        """
        Initialize strategy selector
        
        Args:
            min_return_pct: Minimum return percentage
            min_sharpe: Minimum Sharpe ratio
            min_win_rate: Minimum win rate percentage
            max_drawdown_pct: Maximum drawdown percentage
            min_trades: Minimum number of trades
        """
        self.min_return_pct = min_return_pct
        self.min_sharpe = min_sharpe
        self.min_win_rate = min_win_rate
        self.max_drawdown_pct = max_drawdown_pct
        self.min_trades = min_trades

    def select_best_strategy(self) -> Optional[str]:
        """
        Select best strategy based on recent performance
        
        Returns:
            Strategy name or None if no strategy qualifies
        """
        try:
            strategies = Strategy.get_enabled()
            qualified_strategies = []
            
            for strategy in strategies:
                strategy_id = strategy['id']
                strategy_name = strategy['name']
                
                # Get latest performance
                snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
                
                if not snapshot:
                    continue
                
                # Check qualification criteria
                return_pct = snapshot.get('total_return_pct') or 0
                sharpe = snapshot.get('sharpe_ratio') or 0
                win_rate = snapshot.get('win_rate') or 0
                drawdown = snapshot.get('max_drawdown') or 0
                trades = snapshot.get('total_trades') or 0
                
                # Must meet ALL criteria
                if (
                    return_pct >= self.min_return_pct and
                    sharpe >= self.min_sharpe and
                    win_rate >= self.min_win_rate and
                    drawdown <= self.max_drawdown_pct and
                    trades >= self.min_trades
                ):
                    score = self._calculate_score({
                        'return_pct': return_pct,
                        'sharpe': sharpe,
                        'win_rate': win_rate,
                        'drawdown': drawdown
                    })
                    
                    qualified_strategies.append({
                        'name': strategy_name,
                        'score': score,
                        'metrics': {
                            'return_pct': return_pct,
                            'sharpe': sharpe,
                            'win_rate': win_rate,
                            'drawdown': drawdown,
                            'trades': trades
                        }
                    })
            
            if not qualified_strategies:
                logger.info("No strategies meet qualification criteria")
                return None
            
            # Sort by score (highest first)
            qualified_strategies.sort(key=lambda x: x['score'], reverse=True)
            
            best_strategy = qualified_strategies[0]
            logger.info(
                f"Best strategy selected: {best_strategy['name']} "
                f"(score: {best_strategy['score']:.2f})"
            )
            
            return best_strategy['name']
            
        except Exception as e:
            logger.error(f"Error selecting best strategy: {e}", exc_info=True)
            return None

    def _calculate_score(self, performance: Dict) -> float:
        """
        Calculate composite score for strategy
        
        Scoring formula:
        - Return: 40% weight
        - Sharpe: 30% weight
        - Win Rate: 20% weight
        - Drawdown: 10% weight (inverted)
        """
        try:
            return_score = performance['return_pct'] * 0.4
            sharpe_score = performance['sharpe'] * SHARPE_SCALING_FACTOR * 0.3  # Scale sharpe
            winrate_score = performance['win_rate'] * 0.2
            drawdown_score = (100 - performance['drawdown']) * 0.1  # Invert drawdown
            
            total_score = return_score + sharpe_score + winrate_score + drawdown_score
            return total_score
            
        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return 0.0

    def auto_allocate_capital(self, total_capital: float = 10000.0) -> Dict:
        """
        Allocate capital based on strategy performance
        70% to winner, 20% to 2nd, 10% to 3rd
        
        Args:
            total_capital: Total capital to allocate
            
        Returns:
            Capital allocations
        """
        try:
            strategies = Strategy.get_enabled()
            ranked_strategies = []
            
            for strategy in strategies:
                strategy_id = strategy['id']
                strategy_name = strategy['name']
                
                snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
                
                if not snapshot:
                    continue
                
                performance = {
                    'return_pct': snapshot.get('total_return_pct') or 0,
                    'sharpe': snapshot.get('sharpe_ratio') or 0,
                    'win_rate': snapshot.get('win_rate') or 0,
                    'drawdown': snapshot.get('max_drawdown') or 0
                }
                
                score = self._calculate_score(performance)
                
                ranked_strategies.append({
                    'id': strategy_id,
                    'name': strategy_name,
                    'score': score
                })
            
            # Sort by score
            ranked_strategies.sort(key=lambda x: x['score'], reverse=True)
            
            # Allocate capital
            allocations = {}
            allocation_percentages = [0.70, 0.20, 0.10]  # Top 3 strategies
            
            for i, strategy in enumerate(ranked_strategies[:3]):
                if i < len(allocation_percentages):
                    allocation = total_capital * allocation_percentages[i]
                    allocations[strategy['name']] = allocation
                    
                    # Update in database
                    Strategy.update(
                        strategy['id'],
                        allocated_capital=allocation
                    )
                    
                    logger.info(
                        f"Allocated ${allocation:.2f} to {strategy['name']} "
                        f"({allocation_percentages[i]*100:.0f}%)"
                    )
            
            return {
                'allocations': allocations,
                'total_allocated': sum(allocations.values()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error auto-allocating capital: {e}", exc_info=True)
            return {
                'allocations': {},
                'total_allocated': 0,
                'error': str(e)
            }

    def get_qualified_strategies(self) -> List[Dict]:
        """Get list of strategies that meet qualification criteria"""
        try:
            strategies = Strategy.get_enabled()
            qualified = []
            
            for strategy in strategies:
                strategy_id = strategy['id']
                snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
                
                if not snapshot:
                    continue
                
                return_pct = snapshot.get('total_return_pct') or 0
                sharpe = snapshot.get('sharpe_ratio') or 0
                win_rate = snapshot.get('win_rate') or 0
                drawdown = snapshot.get('max_drawdown') or 0
                trades = snapshot.get('total_trades') or 0
                
                meets_criteria = (
                    return_pct >= self.min_return_pct and
                    sharpe >= self.min_sharpe and
                    win_rate >= self.min_win_rate and
                    drawdown <= self.max_drawdown_pct and
                    trades >= self.min_trades
                )
                
                if meets_criteria:
                    qualified.append({
                        'name': strategy['name'],
                        'return_pct': return_pct,
                        'sharpe': sharpe,
                        'win_rate': win_rate,
                        'drawdown': drawdown,
                        'trades': trades
                    })
            
            return qualified
            
        except Exception as e:
            logger.error(f"Error getting qualified strategies: {e}")
            return []


# Global instance
strategy_selector = StrategySelector()
