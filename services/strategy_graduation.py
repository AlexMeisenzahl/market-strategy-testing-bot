"""
Strategy Graduation Service

Graduate strategies from paper to live trading through 5 stages.
"""

import logging
from typing import Dict
from datetime import datetime, timedelta

from database.competition_models import Strategy, StrategyPerformanceSnapshot
from logger import get_logger

logger = get_logger()


class StrategyGraduation:
    """Graduate strategies from paper to live trading"""

    # Trading stages
    STAGE_BACKTEST = 'backtest'
    STAGE_PAPER = 'paper'
    STAGE_MICRO_LIVE = 'micro_live'
    STAGE_MINI_LIVE = 'mini_live'
    STAGE_FULL_LIVE = 'full_live'

    # Capital per stage
    CAPITAL_BACKTEST = 10000.0
    CAPITAL_PAPER = 10000.0
    CAPITAL_MICRO = 50.0
    CAPITAL_MINI = 200.0
    CAPITAL_FULL = 1000.0

    # Duration requirements (days)
    DURATION_BACKTEST = 7
    DURATION_PAPER = 30
    DURATION_MICRO = 7
    DURATION_MINI = 14

    def __init__(self):
        """Initialize graduation service"""
        pass

    def check_graduation_eligibility(self, strategy_name: str) -> Dict:
        """
        Check if strategy ready to graduate
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Graduation eligibility result
        """
        try:
            strategy = Strategy.get_by_name(strategy_name)
            
            if not strategy:
                return {
                    'eligible': False,
                    'reason': 'Strategy not found'
                }
            
            current_stage = strategy.get('trading_stage', self.STAGE_PAPER)
            
            # Get performance snapshot
            snapshot = StrategyPerformanceSnapshot.get_latest(strategy['id'])
            
            if not snapshot:
                return {
                    'current_stage': current_stage,
                    'ready_for_next': False,
                    'reason': 'No performance data available'
                }
            
            # Check requirements based on current stage
            if current_stage == self.STAGE_PAPER:
                requirements = self._check_paper_graduation(strategy, snapshot)
            elif current_stage == self.STAGE_MICRO_LIVE:
                requirements = self._check_micro_graduation(strategy, snapshot)
            elif current_stage == self.STAGE_MINI_LIVE:
                requirements = self._check_mini_graduation(strategy, snapshot)
            else:
                return {
                    'current_stage': current_stage,
                    'ready_for_next': False,
                    'reason': f'Stage {current_stage} does not have next stage'
                }
            
            next_stage = self._get_next_stage(current_stage)
            ready = all(requirements.values())
            
            return {
                'current_stage': current_stage,
                'ready_for_next': ready,
                'next_stage': next_stage,
                'requirements_met': requirements,
                'recommendation': 'Ready to graduate' if ready else 'Not ready yet'
            }
            
        except Exception as e:
            logger.error(f"Error checking graduation eligibility: {e}", exc_info=True)
            return {
                'eligible': False,
                'error': str(e)
            }

    def _check_paper_graduation(self, strategy: Dict, snapshot: Dict) -> Dict:
        """
        Check paper trading graduation requirements
        """
        # Get strategy age
        created_at = strategy.get('created_at', 0)
        age_days = (datetime.utcnow().timestamp() - created_at) / 86400
        
        return_pct = snapshot.get('total_return_pct') or 0
        sharpe = snapshot.get('sharpe_ratio') or 0
        win_rate = snapshot.get('win_rate') or 0
        drawdown = snapshot.get('max_drawdown') or 0
        trades = snapshot.get('total_trades') or 0
        
        return {
            'duration_met': age_days >= self.DURATION_PAPER,
            'return_met': return_pct > 5.0,
            'sharpe_met': sharpe > 1.5,
            'winrate_met': win_rate > 55.0,
            'drawdown_met': drawdown < 15.0,
            'trades_met': trades >= 50
        }

    def _check_micro_graduation(self, strategy: Dict, snapshot: Dict) -> Dict:
        """Check micro live graduation requirements"""
        # Similar to paper but with micro requirements
        return_pct = snapshot.get('total_return_pct') or 0
        sharpe = snapshot.get('sharpe_ratio') or 0
        trades = snapshot.get('total_trades') or 0
        
        return {
            'return_met': return_pct > 3.0,
            'sharpe_met': sharpe > 1.0,
            'trades_met': trades >= 10
        }

    def _check_mini_graduation(self, strategy: Dict, snapshot: Dict) -> Dict:
        """Check mini live graduation requirements"""
        return_pct = snapshot.get('total_return_pct') or 0
        sharpe = snapshot.get('sharpe_ratio') or 0
        trades = snapshot.get('total_trades') or 0
        
        return {
            'return_met': return_pct > 4.0,
            'sharpe_met': sharpe > 1.2,
            'trades_met': trades >= 20
        }

    def _get_next_stage(self, current_stage: str) -> str:
        """Get next stage in graduation process"""
        stage_progression = {
            self.STAGE_BACKTEST: self.STAGE_PAPER,
            self.STAGE_PAPER: self.STAGE_MICRO_LIVE,
            self.STAGE_MICRO_LIVE: self.STAGE_MINI_LIVE,
            self.STAGE_MINI_LIVE: self.STAGE_FULL_LIVE,
        }
        return stage_progression.get(current_stage, current_stage)

    def graduate_strategy(self, strategy_name: str) -> Dict:
        """
        Graduate strategy to next stage
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Graduation result
        """
        try:
            # Check eligibility first
            eligibility = self.check_graduation_eligibility(strategy_name)
            
            if not eligibility.get('ready_for_next'):
                return {
                    'success': False,
                    'reason': 'Strategy does not meet graduation requirements',
                    'eligibility': eligibility
                }
            
            strategy = Strategy.get_by_name(strategy_name)
            current_stage = strategy.get('trading_stage', self.STAGE_PAPER)
            next_stage = eligibility['next_stage']
            
            # Set capital for next stage
            capital_map = {
                self.STAGE_PAPER: self.CAPITAL_PAPER,
                self.STAGE_MICRO_LIVE: self.CAPITAL_MICRO,
                self.STAGE_MINI_LIVE: self.CAPITAL_MINI,
                self.STAGE_FULL_LIVE: self.CAPITAL_FULL
            }
            new_capital = capital_map.get(next_stage, self.CAPITAL_PAPER)
            
            # Update strategy
            Strategy.update(
                strategy['id'],
                trading_stage=next_stage,
                allocated_capital=new_capital
            )
            
            logger.info(
                f"✅ Graduated strategy '{strategy_name}' from {current_stage} "
                f"to {next_stage} with ${new_capital} capital"
            )
            
            return {
                'success': True,
                'strategy': strategy_name,
                'from_stage': current_stage,
                'to_stage': next_stage,
                'allocated_capital': new_capital,
                'graduated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error graduating strategy: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
strategy_graduation = StrategyGraduation()
