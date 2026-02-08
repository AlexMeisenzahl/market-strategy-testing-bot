"""
Strategy Health Monitor

Monitor all enabled strategies and auto-disable failures.
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

from database.competition_models import Strategy, StrategyPerformanceSnapshot
from logger import get_logger

logger = get_logger()


class StrategyHealthMonitor:
    """Monitor strategies and auto-disable failures"""

    def __init__(
        self,
        max_daily_loss_pct: float = 10.0,
        max_consecutive_losses: int = 5,
        max_drawdown_pct: float = 20.0,
        min_win_rate: float = 40.0,
        min_trades_for_winrate: int = 20
    ):
        """
        Initialize health monitor
        
        Args:
            max_daily_loss_pct: Maximum daily loss before auto-disable
            max_consecutive_losses: Max consecutive losses before auto-disable
            max_drawdown_pct: Maximum drawdown before auto-disable
            min_win_rate: Minimum win rate (after min trades)
            min_trades_for_winrate: Minimum trades before checking win rate
        """
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown_pct = max_drawdown_pct
        self.min_win_rate = min_win_rate
        self.min_trades_for_winrate = min_trades_for_winrate
        
        # Track consecutive losses per strategy
        self.consecutive_losses = defaultdict(int)

    def check_strategy_health(self, strategy: Dict) -> Dict:
        """
        Check if strategy should be auto-disabled
        
        Args:
            strategy: Strategy dict from database
            
        Returns:
            Health check result
        """
        try:
            strategy_id = strategy['id']
            strategy_name = strategy['name']
            
            # Skip if already disabled
            if not strategy['enabled'] or strategy['auto_disabled']:
                return {
                    'status': 'disabled',
                    'strategy': strategy_name
                }
            
            # Get latest performance
            snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
            
            if not snapshot:
                return {
                    'status': 'ok',
                    'strategy': strategy_name,
                    'message': 'No performance data yet'
                }
            
            # Check daily loss limit
            daily_pnl = snapshot.get('daily_pnl', 0) or 0
            portfolio_value = snapshot.get('portfolio_value', 10000) or 10000
            daily_loss_pct = abs(daily_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
            
            if daily_pnl < 0 and daily_loss_pct > self.max_daily_loss_pct:
                reason = f"Daily loss {daily_loss_pct:.2f}% exceeds limit {self.max_daily_loss_pct}%"
                self._auto_disable_strategy(strategy, reason)
                return {
                    'status': 'disabled',
                    'strategy': strategy_name,
                    'reason': reason
                }
            
            # Check max drawdown
            max_drawdown = snapshot.get('max_drawdown', 0) or 0
            if max_drawdown > self.max_drawdown_pct:
                reason = f"Max drawdown {max_drawdown:.2f}% exceeds limit {self.max_drawdown_pct}%"
                self._auto_disable_strategy(strategy, reason)
                return {
                    'status': 'disabled',
                    'strategy': strategy_name,
                    'reason': reason
                }
            
            # Check win rate collapse (after minimum trades)
            total_trades = snapshot.get('total_trades', 0) or 0
            win_rate = snapshot.get('win_rate', 0) or 0
            
            if total_trades >= self.min_trades_for_winrate and win_rate < self.min_win_rate:
                reason = f"Win rate {win_rate:.2f}% below minimum {self.min_win_rate}% after {total_trades} trades"
                self._auto_disable_strategy(strategy, reason)
                return {
                    'status': 'disabled',
                    'strategy': strategy_name,
                    'reason': reason
                }
            
            # TODO: Check consecutive losses (requires tracking individual trades)
            # For now, we'll skip this check
            
            return {
                'status': 'healthy',
                'strategy': strategy_name,
                'metrics': {
                    'daily_pnl': daily_pnl,
                    'daily_loss_pct': daily_loss_pct,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'total_trades': total_trades
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking strategy health: {e}", exc_info=True)
            return {
                'status': 'error',
                'strategy': strategy.get('name', 'unknown'),
                'message': str(e)
            }

    def _auto_disable_strategy(self, strategy: Dict, reason: str):
        """Auto-disable failing strategy"""
        try:
            strategy_id = strategy['id']
            strategy_name = strategy['name']
            
            logger.warning(f"🚫 Auto-disabling strategy '{strategy_name}': {reason}")
            
            Strategy.update(
                strategy_id,
                enabled=0,
                auto_disabled=1,
                disable_reason=reason
            )
            
            # TODO: Send notification when implemented
            
        except Exception as e:
            logger.error(f"Error auto-disabling strategy: {e}", exc_info=True)

    def check_all_strategies(self) -> List[Dict]:
        """Check health of all enabled strategies"""
        try:
            strategies = Strategy.get_enabled()
            results = []
            
            for strategy in strategies:
                result = self.check_strategy_health(strategy)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking all strategies: {e}", exc_info=True)
            return []

    def get_health_summary(self) -> Dict:
        """Get overall health summary"""
        try:
            strategies = Strategy.get_all()
            
            total = len(strategies)
            enabled = len([s for s in strategies if s['enabled']])
            auto_disabled = len([s for s in strategies if s['auto_disabled']])
            paused = len([s for s in strategies if s['paused']])
            
            return {
                'total_strategies': total,
                'enabled': enabled,
                'auto_disabled': auto_disabled,
                'paused': paused,
                'healthy': enabled,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                'total_strategies': 0,
                'enabled': 0,
                'auto_disabled': 0,
                'paused': 0,
                'healthy': 0,
                'error': str(e)
            }


# Global instance
health_monitor = StrategyHealthMonitor()
