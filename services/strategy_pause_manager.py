"""
Strategy Pause Manager

Pause/resume strategies temporarily without disabling.
"""

import logging
from typing import Dict
from datetime import datetime

from database.competition_models import Strategy
from logger import get_logger

logger = get_logger()


class StrategyPauseManager:
    """Pause/resume strategies temporarily"""

    def __init__(self):
        """Initialize pause manager"""
        pass

    def pause_strategy(self, strategy_name: str, reason: str) -> Dict:
        """
        Pause strategy temporarily
        
        Args:
            strategy_name: Name of the strategy
            reason: Reason for pausing
            
        Returns:
            Pause result
        """
        try:
            strategy = Strategy.get_by_name(strategy_name)
            
            if not strategy:
                return {
                    'success': False,
                    'reason': 'Strategy not found'
                }
            
            if strategy['paused']:
                return {
                    'success': False,
                    'reason': 'Strategy is already paused'
                }
            
            # Pause strategy
            Strategy.update(
                strategy['id'],
                paused=1,
                pause_reason=reason
            )
            
            logger.info(f"⏸️ Paused strategy '{strategy_name}': {reason}")
            
            return {
                'success': True,
                'strategy': strategy_name,
                'reason': reason,
                'paused_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error pausing strategy: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def resume_strategy(self, strategy_name: str) -> Dict:
        """
        Resume paused strategy
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Resume result
        """
        try:
            strategy = Strategy.get_by_name(strategy_name)
            
            if not strategy:
                return {
                    'success': False,
                    'reason': 'Strategy not found'
                }
            
            if not strategy['paused']:
                return {
                    'success': False,
                    'reason': 'Strategy is not paused'
                }
            
            # Resume strategy
            Strategy.update(
                strategy['id'],
                paused=0,
                pause_reason=None
            )
            
            logger.info(f"▶️ Resumed strategy '{strategy_name}'")
            
            return {
                'success': True,
                'strategy': strategy_name,
                'resumed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error resuming strategy: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def is_paused(self, strategy_name: str) -> bool:
        """Check if strategy is paused"""
        try:
            strategy = Strategy.get_by_name(strategy_name)
            return bool(strategy['paused']) if strategy else False
        except Exception as e:
            logger.error(f"Error checking pause status: {e}")
            return False

    def get_paused_strategies(self) -> list:
        """Get list of all paused strategies"""
        try:
            strategies = Strategy.get_all()
            return [
                {
                    'name': s['name'],
                    'reason': s['pause_reason']
                }
                for s in strategies
                if s['paused']
            ]
        except Exception as e:
            logger.error(f"Error getting paused strategies: {e}")
            return []


# Global instance
pause_manager = StrategyPauseManager()
