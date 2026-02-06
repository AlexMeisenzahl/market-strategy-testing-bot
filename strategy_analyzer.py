"""
Strategy Analyzer Module - Compare and rank trading strategies

Analyzes each strategy across multiple performance metrics:
- Total profit
- Win rate  
- Average profit per trade
- Risk-adjusted returns (Sharpe ratio)
- Consistency (volatility of returns)
- Opportunity frequency

Provides capital allocation recommendations based on performance,
risk tolerance, and opportunity availability.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import math
from logger import get_logger


class StrategyAnalyzer:
    """
    Analyzes and compares trading strategy performance
    
    Evaluates strategies across multiple dimensions and provides
    recommendations for optimal capital allocation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy analyzer
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Analysis parameters
        analysis_config = config.get('strategy_analysis', {})
        self.min_trades_for_analysis = analysis_config.get('min_trades', 10)
        self.risk_free_rate = analysis_config.get('risk_free_rate', 0.0)  # For Sharpe ratio
        self.lookback_days = analysis_config.get('lookback_days', 30)
        
        # Risk tolerance (for allocation recommendations)
        self.risk_tolerance = analysis_config.get('risk_tolerance', 'moderate')  # conservative, moderate, aggressive
        
        self.logger.log_warning(
            f"Strategy Analyzer initialized - "
            f"Risk tolerance: {self.risk_tolerance}, "
            f"Lookback: {self.lookback_days} days"
        )
    
    def compare_strategies(self, performance_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Compare all strategies across performance metrics
        
        Args:
            performance_data: Dictionary mapping strategy name to list of trades
                             {strategy_name: [trade1, trade2, ...]}
            
        Returns:
            Dictionary with comparative analysis
        """
        if not performance_data:
            return {
                'error': 'No performance data provided',
                'strategies': {}
            }
        
        analysis = {
            'analyzed_at': datetime.now().isoformat(),
            'strategies': {},
            'summary': {}
        }
        
        # Analyze each strategy
        for strategy_name, trades in performance_data.items():
            strategy_metrics = self._analyze_single_strategy(strategy_name, trades)
            analysis['strategies'][strategy_name] = strategy_metrics
        
        # Generate summary statistics
        analysis['summary'] = self._generate_summary(analysis['strategies'])
        
        # Log comparison
        self._log_comparison(analysis)
        
        return analysis
    
    def _analyze_single_strategy(self, strategy_name: str, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a single strategy's performance
        
        Args:
            strategy_name: Name of the strategy
            trades: List of trade dictionaries
            
        Returns:
            Dictionary with strategy metrics
        """
        if len(trades) < self.min_trades_for_analysis:
            return {
                'insufficient_data': True,
                'trade_count': len(trades),
                'message': f'Need at least {self.min_trades_for_analysis} trades'
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(t.get('profit', 0) for t in trades)
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t.get('profit', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.get('profit', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(trades)
        consistency_score = self._calculate_consistency(trades)
        
        # Opportunity frequency
        frequency = self._calculate_frequency(trades)
        
        # Overall score (weighted combination)
        overall_score = self._calculate_overall_score({
            'win_rate': win_rate,
            'total_profit': total_profit,
            'sharpe_ratio': sharpe_ratio,
            'consistency_score': consistency_score,
            'frequency': frequency
        })
        
        return {
            'strategy_name': strategy_name,
            'insufficient_data': False,
            'trade_count': total_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit_per_trade': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(sum(t.get('profit', 0) for t in winning_trades) / sum(t.get('profit', 0) for t in losing_trades)) if losing_trades and sum(t.get('profit', 0) for t in losing_trades) != 0 else float('inf'),
            'sharpe_ratio': sharpe_ratio,
            'consistency_score': consistency_score,
            'opportunity_frequency': frequency,
            'overall_score': overall_score
        }
    
    def _calculate_sharpe_ratio(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted returns)
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Sharpe ratio (higher is better)
        """
        if len(trades) < 2:
            return 0.0
        
        returns = [t.get('profit', 0) for t in trades]
        
        # Calculate mean and std dev
        mean_return = sum(returns) / len(returns)
        
        # Calculate standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.0
        
        # Sharpe = (mean_return - risk_free_rate) / std_dev
        sharpe = (mean_return - self.risk_free_rate) / std_dev
        
        return sharpe
    
    def _calculate_consistency(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate consistency score (inverse of return volatility)
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Consistency score 0-100 (higher is better)
        """
        if len(trades) < 2:
            return 0.0
        
        returns = [t.get('profit', 0) for t in trades]
        
        # Calculate coefficient of variation
        mean_return = sum(returns) / len(returns)
        if mean_return == 0:
            return 0.0
        
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        cv = std_dev / abs(mean_return)
        
        # Convert to 0-100 score (lower CV = higher consistency)
        # CV of 0 = 100, CV of 2+ = 0
        consistency = max(0, min(100, 100 - (cv * 50)))
        
        return consistency
    
    def _calculate_frequency(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate opportunity frequency (trades per day)
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Average trades per day
        """
        if not trades:
            return 0.0
        
        # Get time span
        timestamps = [t.get('executed_at', datetime.now()) for t in trades]
        if not timestamps or len(timestamps) < 2:
            return 0.0
        
        earliest = min(timestamps)
        latest = max(timestamps)
        
        time_span_days = (latest - earliest).total_seconds() / 86400
        if time_span_days == 0:
            time_span_days = 1
        
        frequency = len(trades) / time_span_days
        
        return frequency
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate overall strategy score (0-100)
        
        Args:
            metrics: Dictionary with normalized metrics
            
        Returns:
            Overall score 0-100
        """
        # Weights based on risk tolerance
        if self.risk_tolerance == 'conservative':
            weights = {
                'win_rate': 0.30,
                'total_profit': 0.20,
                'sharpe_ratio': 0.25,
                'consistency_score': 0.20,
                'frequency': 0.05
            }
        elif self.risk_tolerance == 'aggressive':
            weights = {
                'win_rate': 0.15,
                'total_profit': 0.40,
                'sharpe_ratio': 0.15,
                'consistency_score': 0.10,
                'frequency': 0.20
            }
        else:  # moderate
            weights = {
                'win_rate': 0.25,
                'total_profit': 0.25,
                'sharpe_ratio': 0.20,
                'consistency_score': 0.20,
                'frequency': 0.10
            }
        
        # Normalize metrics to 0-100 scale
        normalized = {
            'win_rate': metrics['win_rate'] * 100,
            'total_profit': min(100, max(0, metrics['total_profit'] * 10)),  # Assuming $10 profit = 100 score
            'sharpe_ratio': min(100, max(0, (metrics['sharpe_ratio'] + 2) * 25)),  # Sharpe of 2 = 100 score
            'consistency_score': metrics['consistency_score'],
            'frequency': min(100, metrics['frequency'] * 20)  # 5 trades/day = 100 score
        }
        
        # Calculate weighted score
        score = sum(normalized[key] * weights[key] for key in weights)
        
        return score
    
    def rank_strategies(self, performance_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Rank strategies by overall performance
        
        Args:
            performance_data: Dictionary mapping strategy name to trades
            
        Returns:
            List of strategies ranked by overall score
        """
        # Get comparative analysis
        analysis = self.compare_strategies(performance_data)
        
        # Extract and sort strategies
        strategies = analysis.get('strategies', {})
        
        ranked = []
        for name, metrics in strategies.items():
            if not metrics.get('insufficient_data', False):
                ranked.append({
                    'rank': 0,  # Will be set below
                    'strategy': name,
                    'overall_score': metrics.get('overall_score', 0),
                    'metrics': metrics
                })
        
        # Sort by overall score (descending)
        ranked.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Assign ranks
        for i, strategy in enumerate(ranked, 1):
            strategy['rank'] = i
        
        # Log rankings
        self._log_rankings(ranked)
        
        return ranked
    
    def generate_allocation_recommendation(
        self,
        analysis: Dict[str, Any],
        total_capital: float
    ) -> Dict[str, Any]:
        """
        Generate capital allocation recommendation
        
        Args:
            analysis: Strategy comparison analysis
            total_capital: Total capital to allocate
            
        Returns:
            Dictionary with allocation recommendations
        """
        strategies = analysis.get('strategies', {})
        
        # Filter out strategies with insufficient data
        valid_strategies = {
            name: metrics for name, metrics in strategies.items()
            if not metrics.get('insufficient_data', False)
        }
        
        if not valid_strategies:
            return {
                'error': 'No valid strategies for allocation',
                'allocations': {}
            }
        
        # Calculate allocation weights based on overall scores
        total_score = sum(m.get('overall_score', 0) for m in valid_strategies.values())
        
        if total_score == 0:
            # Equal allocation if all scores are 0
            allocation_pct = 1.0 / len(valid_strategies)
            allocations = {
                name: {
                    'percentage': allocation_pct * 100,
                    'capital': total_capital * allocation_pct,
                    'reasoning': 'Equal allocation (no performance data)'
                }
                for name in valid_strategies
            }
        else:
            # Proportional allocation based on scores
            allocations = {}
            for name, metrics in valid_strategies.items():
                score = metrics.get('overall_score', 0)
                allocation_pct = score / total_score
                
                # Apply minimum/maximum allocation limits
                allocation_pct = max(0.05, min(0.60, allocation_pct))  # 5-60% per strategy
                
                reasoning = self._generate_allocation_reasoning(metrics, allocation_pct)
                
                allocations[name] = {
                    'percentage': allocation_pct * 100,
                    'capital': total_capital * allocation_pct,
                    'reasoning': reasoning
                }
            
            # Normalize to 100%
            total_allocated_pct = sum(a['percentage'] for a in allocations.values()) / 100
            for name in allocations:
                allocations[name]['percentage'] /= total_allocated_pct
                allocations[name]['capital'] /= total_allocated_pct
        
        recommendation = {
            'total_capital': total_capital,
            'allocations': allocations,
            'generated_at': datetime.now().isoformat(),
            'risk_tolerance': self.risk_tolerance
        }
        
        # Log recommendation
        self._log_allocation(recommendation)
        
        return recommendation
    
    def _generate_allocation_reasoning(self, metrics: Dict[str, Any], allocation_pct: float) -> str:
        """
        Generate reasoning for allocation decision
        
        Args:
            metrics: Strategy metrics
            allocation_pct: Allocated percentage
            
        Returns:
            Reasoning string
        """
        reasons = []
        
        # Win rate
        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.7:
            reasons.append(f"high win rate ({win_rate*100:.1f}%)")
        elif win_rate < 0.5:
            reasons.append(f"low win rate ({win_rate*100:.1f}%)")
        
        # Sharpe ratio
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe > 1.5:
            reasons.append(f"excellent risk-adjusted returns (Sharpe: {sharpe:.2f})")
        elif sharpe < 0:
            reasons.append(f"poor risk-adjusted returns (Sharpe: {sharpe:.2f})")
        
        # Consistency
        consistency = metrics.get('consistency_score', 0)
        if consistency > 70:
            reasons.append("very consistent")
        elif consistency < 40:
            reasons.append("inconsistent")
        
        # Frequency
        freq = metrics.get('opportunity_frequency', 0)
        if freq > 5:
            reasons.append(f"high opportunity frequency ({freq:.1f}/day)")
        elif freq < 1:
            reasons.append(f"low opportunity frequency ({freq:.1f}/day)")
        
        if not reasons:
            reasons.append("balanced performance")
        
        return f"{allocation_pct*100:.1f}% allocated due to: " + ", ".join(reasons)
    
    def _generate_summary(self, strategies: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics across all strategies
        
        Args:
            strategies: Dictionary of strategy metrics
            
        Returns:
            Summary statistics dictionary
        """
        valid_strategies = [
            s for s in strategies.values()
            if not s.get('insufficient_data', False)
        ]
        
        if not valid_strategies:
            return {'no_valid_strategies': True}
        
        return {
            'total_strategies': len(strategies),
            'valid_strategies': len(valid_strategies),
            'total_profit': sum(s.get('total_profit', 0) for s in valid_strategies),
            'avg_win_rate': sum(s.get('win_rate', 0) for s in valid_strategies) / len(valid_strategies),
            'avg_sharpe_ratio': sum(s.get('sharpe_ratio', 0) for s in valid_strategies) / len(valid_strategies),
            'best_strategy': max(valid_strategies, key=lambda s: s.get('overall_score', 0))['strategy_name'],
            'worst_strategy': min(valid_strategies, key=lambda s: s.get('overall_score', 0))['strategy_name']
        }
    
    def _log_comparison(self, analysis: Dict[str, Any]) -> None:
        """
        Log strategy comparison results
        
        Args:
            analysis: Analysis results dictionary
        """
        self.logger.log_warning("📊 STRATEGY COMPARISON")
        
        summary = analysis.get('summary', {})
        if summary.get('no_valid_strategies'):
            self.logger.log_warning("No valid strategies to compare")
            return
        
        self.logger.log_warning(
            f"Valid strategies: {summary['valid_strategies']}/{summary['total_strategies']}"
        )
        self.logger.log_warning(
            f"Combined profit: ${summary['total_profit']:.2f}"
        )
        self.logger.log_warning(
            f"Best: {summary['best_strategy']}, Worst: {summary['worst_strategy']}"
        )
        
        # Log individual strategies
        for name, metrics in analysis.get('strategies', {}).items():
            if metrics.get('insufficient_data'):
                self.logger.log_warning(
                    f"  {name}: Insufficient data ({metrics['trade_count']} trades)"
                )
            else:
                self.logger.log_warning(
                    f"  {name}: Score={metrics['overall_score']:.1f}, "
                    f"Profit=${metrics['total_profit']:.2f}, "
                    f"WinRate={metrics['win_rate']*100:.1f}%, "
                    f"Sharpe={metrics['sharpe_ratio']:.2f}"
                )
    
    def _log_rankings(self, ranked: List[Dict[str, Any]]) -> None:
        """
        Log strategy rankings
        
        Args:
            ranked: List of ranked strategies
        """
        self.logger.log_warning("🏆 STRATEGY RANKINGS")
        
        for strategy in ranked:
            self.logger.log_warning(
                f"  #{strategy['rank']} {strategy['strategy']}: "
                f"Score={strategy['overall_score']:.1f}"
            )
    
    def _log_allocation(self, recommendation: Dict[str, Any]) -> None:
        """
        Log allocation recommendation
        
        Args:
            recommendation: Allocation recommendation dictionary
        """
        self.logger.log_warning(
            f"💰 CAPITAL ALLOCATION (Total: ${recommendation['total_capital']:.2f})"
        )
        
        for name, alloc in recommendation['allocations'].items():
            self.logger.log_warning(
                f"  {name}: {alloc['percentage']:.1f}% (${alloc['capital']:.2f})"
            )
            self.logger.log_warning(f"    {alloc['reasoning']}")
