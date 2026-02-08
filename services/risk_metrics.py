"""
Risk Metrics Service

Calculate advanced risk metrics including Sharpe, Sortino, VaR, Calmar.
Uses numpy for statistical calculations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import numpy as np


class RiskMetrics:
    """Calculate advanced risk metrics for trading strategies"""
    
    def __init__(self, data_parser):
        """
        Initialize risk metrics
        
        Args:
            data_parser: DataParser instance for accessing trade data
        """
        self.data_parser = data_parser
        self.risk_free_rate = 0.0001  # Daily risk-free rate (~4% annual / 252)
    
    def calculate_all_risk_metrics(
        self,
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate all risk metrics for a strategy or all strategies combined
        
        Args:
            strategy_name: Strategy to analyze (None for all strategies)
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            Dictionary with all risk metrics
        """
        # Get trades
        trades_data = self.data_parser.get_trades(
            strategy=strategy_name,
            start_date=start_date,
            end_date=end_date,
            per_page=10000  # Get all trades
        )
        trades = trades_data['trades']
        
        if len(trades) < 2:
            return self._empty_risk_metrics()
        
        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t['entry_time'])
        
        # Extract returns array
        returns = np.array([float(t['pnl_usd']) for t in sorted_trades])
        
        # Calculate metrics
        mean_return = np.mean(returns)
        std_dev = np.std(returns, ddof=1)  # Sample std dev
        
        # Sharpe Ratio
        if std_dev > 0:
            sharpe_ratio = (mean_return - self.risk_free_rate) / std_dev
        else:
            sharpe_ratio = 0.0
        
        # Downside deviation (std dev of negative returns only)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_deviation = np.std(negative_returns, ddof=1)
        else:
            downside_deviation = 0.0
        
        # Sortino Ratio
        if downside_deviation > 0:
            sortino_ratio = (mean_return - self.risk_free_rate) / downside_deviation
        else:
            sortino_ratio = 0.0
        
        # VaR (Value at Risk)
        var_95 = np.percentile(returns, 5)  # 95% VaR
        var_99 = np.percentile(returns, 1)  # 99% VaR
        
        # Max Drawdown
        cumulative_pnl = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative_pnl)
        drawdown = peak - cumulative_pnl
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0
        
        # Max Drawdown %
        peak_value_at_max_dd = peak[np.argmax(drawdown)] if len(drawdown) > 0 else 0
        if peak_value_at_max_dd > 0:
            max_drawdown_pct = (max_drawdown / peak_value_at_max_dd) * 100
        else:
            max_drawdown_pct = 0.0
        
        # Annualized return
        total_return = float(np.sum(returns))
        days_traded = self._calculate_days_traded(sorted_trades)
        if days_traded > 0:
            annualized_return = (total_return / days_traded) * 365
        else:
            annualized_return = 0.0
        
        # Calmar Ratio
        if max_drawdown > 0:
            calmar_ratio = annualized_return / max_drawdown
        else:
            calmar_ratio = 0.0
        
        return {
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'var_95': round(var_95, 2),
            'var_99': round(var_99, 2),
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'std_deviation': round(std_dev, 2),
            'downside_deviation': round(downside_deviation, 2),
            'annualized_return': round(annualized_return, 2),
            'total_return': round(total_return, 2),
            'mean_return': round(mean_return, 2)
        }
    
    def calculate_rolling_sharpe(
        self,
        window_days: int = 30,
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate rolling Sharpe ratio over time
        
        Args:
            window_days: Rolling window size in days
            strategy_name: Strategy to analyze
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary with dates and rolling Sharpe values
        """
        # Get trades
        trades_data = self.data_parser.get_trades(
            strategy=strategy_name,
            start_date=start_date,
            end_date=end_date,
            per_page=10000
        )
        trades = trades_data['trades']
        
        if len(trades) < window_days:
            return {'dates': [], 'sharpe_values': []}
        
        # Sort by date
        sorted_trades = sorted(trades, key=lambda t: t['entry_time'])
        
        dates = []
        sharpe_values = []
        
        for i in range(window_days, len(sorted_trades)):
            window_trades = sorted_trades[i-window_days:i]
            returns = np.array([float(t['pnl_usd']) for t in window_trades])
            
            mean_return = np.mean(returns)
            std_dev = np.std(returns, ddof=1)
            
            if std_dev > 0:
                sharpe = (mean_return - self.risk_free_rate) / std_dev
            else:
                sharpe = 0.0
            
            dates.append(sorted_trades[i]['entry_time'])
            sharpe_values.append(round(sharpe, 2))
        
        return {
            'dates': dates,
            'sharpe_values': sharpe_values
        }
    
    def calculate_drawdown_history(
        self,
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate drawdown over time for visualization
        
        Args:
            strategy_name: Strategy to analyze
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dictionary with dates and drawdown percentages
        """
        # Get trades
        trades_data = self.data_parser.get_trades(
            strategy=strategy_name,
            start_date=start_date,
            end_date=end_date,
            per_page=10000
        )
        trades = trades_data['trades']
        
        if not trades:
            return {'dates': [], 'drawdown_pct': [], 'drawdown_usd': []}
        
        # Sort by date
        sorted_trades = sorted(trades, key=lambda t: t['entry_time'])
        
        # Calculate cumulative P&L and drawdown
        returns = np.array([float(t['pnl_usd']) for t in sorted_trades])
        cumulative_pnl = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative_pnl)
        drawdown_usd = peak - cumulative_pnl
        
        # Calculate drawdown percentage
        drawdown_pct = np.zeros_like(drawdown_usd)
        mask = peak > 0
        drawdown_pct[mask] = (drawdown_usd[mask] / peak[mask]) * 100
        
        dates = [t['entry_time'] for t in sorted_trades]
        
        return {
            'dates': dates,
            'drawdown_pct': [round(float(d), 2) for d in drawdown_pct],
            'drawdown_usd': [round(float(d), 2) for d in drawdown_usd]
        }
    
    def _calculate_days_traded(self, trades: List[Dict]) -> int:
        """Calculate the number of days between first and last trade"""
        if not trades or len(trades) < 2:
            return 0
        
        try:
            first_date = datetime.fromisoformat(trades[0]['entry_time'])
            last_date = datetime.fromisoformat(trades[-1]['entry_time'])
            days = (last_date - first_date).days
            return max(1, days)  # At least 1 day
        except (ValueError, KeyError):
            return 1
    
    def _empty_risk_metrics(self) -> Dict[str, Any]:
        """Return empty risk metrics when there's insufficient data"""
        return {
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'var_95': 0.0,
            'var_99': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'calmar_ratio': 0.0,
            'std_deviation': 0.0,
            'downside_deviation': 0.0,
            'annualized_return': 0.0,
            'total_return': 0.0,
            'mean_return': 0.0
        }
