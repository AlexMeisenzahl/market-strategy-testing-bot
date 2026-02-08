"""
Strategy Competition System

Run multiple strategies simultaneously and track which performs best.
Each strategy starts with same virtual capital and competes in real-time.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
from collections import defaultdict

from database.competition_models import (
    Strategy,
    StrategyPerformanceSnapshot,
    get_connection
)

logger = logging.getLogger(__name__)


class StrategyCompetition:
    """
    Run multiple strategies simultaneously and track winners
    """

    def __init__(self, starting_capital: float = 10000.0):
        """
        Initialize strategy competition
        
        Args:
            starting_capital: Starting capital for each strategy
        """
        self.starting_capital = starting_capital
        self.virtual_portfolios = {}
        self.trade_history = defaultdict(list)
        self.performance_cache = {}
        
        # Initialize virtual portfolios for all strategies
        self._initialize_portfolios()

    def _initialize_portfolios(self):
        """Initialize virtual portfolios for all strategies"""
        strategies = Strategy.get_all()
        for strategy in strategies:
            strategy_id = strategy['id']
            self.virtual_portfolios[strategy_id] = {
                'cash': self.starting_capital,
                'positions': [],
                'total_value': self.starting_capital,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'pnl_history': []
            }

    def run_competition(self, market_data: Dict) -> Dict:
        """
        Run all strategies on same market data
        
        Args:
            market_data: Latest market data to evaluate
            
        Returns:
            Competition results with performance metrics
        """
        try:
            enabled_strategies = Strategy.get_enabled()
            
            if not enabled_strategies:
                logger.warning("No enabled strategies to run")
                return {'status': 'no_strategies', 'results': []}
            
            results = []
            
            for strategy in enabled_strategies:
                strategy_id = strategy['id']
                strategy_name = strategy['name']
                
                try:
                    # Get or create portfolio
                    if strategy_id not in self.virtual_portfolios:
                        self.virtual_portfolios[strategy_id] = {
                            'cash': self.starting_capital,
                            'positions': [],
                            'total_value': self.starting_capital,
                            'trades': 0,
                            'wins': 0,
                            'losses': 0,
                            'pnl_history': []
                        }
                    
                    # Evaluate strategy (placeholder - integrate with actual strategy execution)
                    opportunity = self._evaluate_strategy(strategy, market_data)
                    
                    if opportunity:
                        # Execute trade in virtual portfolio
                        self._execute_virtual_trade(strategy_id, opportunity)
                    
                    # Calculate performance metrics
                    metrics = self._calculate_performance_metrics(strategy_id)
                    results.append({
                        'strategy_id': strategy_id,
                        'strategy_name': strategy_name,
                        'metrics': metrics
                    })
                    
                except Exception as e:
                    logger.error(f"Error running strategy {strategy_name}: {e}")
                    continue
            
            return {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in competition run: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _evaluate_strategy(self, strategy: Dict, market_data: Dict) -> Optional[Dict]:
        """
        Evaluate strategy against market data
        
        This is a placeholder that should be integrated with actual strategy logic
        """
        # TODO: Integrate with actual strategy evaluation
        # For now, return None (no opportunity)
        return None

    def _execute_virtual_trade(self, strategy_id: int, opportunity: Dict):
        """
        Execute trade in virtual portfolio
        
        Args:
            strategy_id: ID of the strategy
            opportunity: Trade opportunity details
        """
        try:
            portfolio = self.virtual_portfolios[strategy_id]
            
            # Extract trade details
            side = opportunity.get('side', 'buy')
            size = opportunity.get('size', 100)
            price = opportunity.get('price', 0.5)
            
            if side == 'buy':
                cost = size * price
                if portfolio['cash'] >= cost:
                    portfolio['cash'] -= cost
                    portfolio['positions'].append({
                        'size': size,
                        'entry_price': price,
                        'entry_time': datetime.utcnow(),
                        'market_id': opportunity.get('market_id'),
                        'side': 'long'
                    })
                    portfolio['trades'] += 1
                    
            elif side == 'sell':
                # Find matching position to close
                if portfolio['positions']:
                    position = portfolio['positions'].pop(0)
                    exit_value = size * price
                    entry_value = position['size'] * position['entry_price']
                    pnl = exit_value - entry_value
                    
                    portfolio['cash'] += exit_value
                    portfolio['pnl_history'].append(pnl)
                    
                    if pnl > 0:
                        portfolio['wins'] += 1
                    else:
                        portfolio['losses'] += 1
            
            # Update total value
            positions_value = sum(
                p['size'] * p['entry_price'] 
                for p in portfolio['positions']
            )
            portfolio['total_value'] = portfolio['cash'] + positions_value
            
            # Record trade
            self.trade_history[strategy_id].append({
                'timestamp': datetime.utcnow(),
                'opportunity': opportunity,
                'portfolio_value': portfolio['total_value']
            })
            
        except Exception as e:
            logger.error(f"Error executing virtual trade: {e}")

    def _calculate_performance_metrics(self, strategy_id: int) -> Dict:
        """Calculate performance metrics for strategy"""
        portfolio = self.virtual_portfolios.get(strategy_id, {})
        
        if not portfolio:
            return {}
        
        current_value = portfolio.get('total_value', self.starting_capital)
        total_return_pct = ((current_value - self.starting_capital) / self.starting_capital) * 100
        
        # Calculate win rate
        total_closed_trades = portfolio['wins'] + portfolio['losses']
        win_rate = (portfolio['wins'] / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        # Calculate Sharpe ratio
        sharpe_ratio = self._calculate_sharpe(portfolio)
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(strategy_id)
        
        return {
            'current_value': round(current_value, 2),
            'return_pct': round(total_return_pct, 2),
            'total_trades': portfolio['trades'],
            'win_rate': round(win_rate, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'open_positions': len(portfolio['positions'])
        }

    def _calculate_sharpe(self, portfolio: Dict) -> float:
        """Calculate Sharpe ratio for portfolio"""
        try:
            pnl_history = portfolio.get('pnl_history', [])
            
            if len(pnl_history) < 2:
                return 0.0
            
            returns = np.array(pnl_history)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            
            # Annualized Sharpe (assuming daily returns)
            sharpe = (mean_return / std_return) * np.sqrt(252)
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def _calculate_max_drawdown(self, strategy_id: int) -> float:
        """Calculate maximum drawdown for strategy"""
        try:
            trades = self.trade_history.get(strategy_id, [])
            
            if not trades:
                return 0.0
            
            values = [t['portfolio_value'] for t in trades]
            peak = values[0]
            max_dd = 0.0
            
            for value in values:
                if value > peak:
                    peak = value
                dd = ((peak - value) / peak) * 100
                max_dd = max(max_dd, dd)
            
            return max_dd
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0

    def get_leaderboard(self) -> List[Dict]:
        """
        Return strategy rankings
        
        Returns:
            List of strategies sorted by performance
        """
        try:
            strategies = Strategy.get_all()
            leaderboard = []
            
            for strategy in strategies:
                strategy_id = strategy['id']
                strategy_name = strategy['name']
                
                # Get latest snapshot or calculate current metrics
                snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
                
                if snapshot:
                    metrics = {
                        'current_value': snapshot['portfolio_value'],
                        'return_pct': snapshot['total_return_pct'] or 0,
                        'sharpe_ratio': snapshot['sharpe_ratio'] or 0,
                        'total_trades': snapshot['total_trades'] or 0,
                        'win_rate': snapshot['win_rate'] or 0,
                        'max_drawdown': snapshot['max_drawdown'] or 0
                    }
                else:
                    # Calculate from virtual portfolio
                    metrics = self._calculate_performance_metrics(strategy_id)
                    if not metrics:
                        metrics = {
                            'current_value': self.starting_capital,
                            'return_pct': 0,
                            'sharpe_ratio': 0,
                            'total_trades': 0,
                            'win_rate': 0,
                            'max_drawdown': 0
                        }
                
                # Determine status
                return_pct = metrics.get('return_pct', 0)
                if return_pct > 5:
                    status = '✅ WINNING'
                elif return_pct > 0:
                    status = '⚠️ MARGINAL'
                else:
                    status = '❌ LOSING'
                
                leaderboard.append({
                    'strategy_id': strategy_id,
                    'strategy': strategy_name,
                    'current_value': metrics.get('current_value', self.starting_capital),
                    'return_pct': metrics.get('return_pct', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'total_trades': metrics.get('total_trades', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'status': status,
                    'enabled': strategy['enabled'],
                    'paused': strategy['paused'],
                    'auto_disabled': strategy['auto_disabled']
                })
            
            # Sort by return percentage (descending)
            leaderboard.sort(key=lambda x: x['return_pct'], reverse=True)
            
            # Add ranks
            for i, entry in enumerate(leaderboard, 1):
                entry['rank'] = i
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error generating leaderboard: {e}", exc_info=True)
            return []

    def get_competition_summary(self) -> Dict:
        """Get overall competition summary"""
        leaderboard = self.get_leaderboard()
        
        if not leaderboard:
            return {
                'total_strategies': 0,
                'active_strategies': 0,
                'top_performer': None,
                'avg_return': 0
            }
        
        enabled_strategies = [s for s in leaderboard if s['enabled']]
        
        avg_return = np.mean([s['return_pct'] for s in leaderboard]) if leaderboard else 0
        
        return {
            'total_strategies': len(leaderboard),
            'active_strategies': len(enabled_strategies),
            'top_performer': leaderboard[0] if leaderboard else None,
            'avg_return': round(avg_return, 2),
            'timestamp': datetime.utcnow().isoformat()
        }


# Global instance
competition = StrategyCompetition()
