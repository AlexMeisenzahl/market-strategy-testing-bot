"""
Strategy Manager Module

Coordinates multiple trading strategies and manages their execution.
Loads all enabled strategies from config and runs them together.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from logger import get_logger

# Import all strategy classes
from strategies.arbitrage_strategy import ArbitrageStrategy, ArbitrageOpportunity
from strategies.momentum_strategy import MomentumStrategy, MomentumOpportunity
from strategies.news_strategy import NewsStrategy, NewsOpportunity
from strategies.statistical_arb_strategy import StatisticalArbStrategy, StatisticalArbOpportunity


class StrategyManager:
    """
    Manages multiple trading strategies
    
    Coordinates execution of all enabled strategies, handles errors gracefully,
    and tags each opportunity with its strategy name.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy manager
        
        Args:
            config: Configuration dictionary with strategy settings
        """
        self.config = config
        self.logger = get_logger()
        self.strategies: Dict[str, Any] = {}
        
        # Load strategies from config
        self._load_strategies()
        
        # Log enabled strategies
        enabled = [name for name in self.strategies.keys()]
        if enabled:
            self.logger.log_info(f"Enabled strategies: {', '.join(enabled)}")
        else:
            self.logger.log_warning("No strategies enabled!")
    
    def _load_strategies(self) -> None:
        """Load all enabled strategies from configuration"""
        strategies_config = self.config.get('strategies', {})
        
        # Load Arbitrage Strategy
        arb_config = strategies_config.get('polymarket_arbitrage', {})
        if arb_config.get('enabled', True):
            try:
                # Merge arbitrage config with global config for backward compatibility
                strategy_config = {
                    'min_profit_margin': arb_config.get('min_profit_margin', 
                                                       self.config.get('min_profit_margin', 0.02)),
                    'max_trade_size': self.config.get('max_trade_size', 10),
                    'arbitrage_types': arb_config.get('arbitrage_types', {}),
                }
                
                self.strategies['polymarket_arbitrage'] = ArbitrageStrategy(strategy_config)
                self.logger.log_info("Loaded Polymarket Arbitrage strategy")
            except Exception as e:
                self.logger.log_error(f"Failed to load Arbitrage strategy: {str(e)}")
        
        # Load Momentum Strategy
        momentum_config = strategies_config.get('crypto_momentum', {})
        if momentum_config.get('enabled', False):
            try:
                strategy_config = {
                    'symbols': momentum_config.get('symbols', ['BTC', 'ETH', 'SOL', 'XRP']),
                    'momentum_min_price_change_5m': momentum_config.get('min_price_change_5m', 2.0),
                    'momentum_min_volume_change': momentum_config.get('min_volume_change', 50.0),
                    'momentum_min_score': momentum_config.get('min_score', 70.0),
                }
                
                self.strategies['crypto_momentum'] = MomentumStrategy(strategy_config)
                self.logger.log_info("Loaded Crypto Momentum strategy")
            except Exception as e:
                self.logger.log_error(f"Failed to load Momentum strategy: {str(e)}")
        
        # Load News Strategy
        news_config = strategies_config.get('crypto_news', {})
        if news_config.get('enabled', False):
            try:
                strategy_config = {
                    'news_volume_spike_threshold': news_config.get('volume_spike_threshold', 300.0),
                    'news_min_price_movement': news_config.get('min_price_movement', 5.0),
                    'news_min_confidence': news_config.get('min_confidence', 70.0),
                }
                
                self.strategies['crypto_news'] = NewsStrategy(strategy_config)
                self.logger.log_info("Loaded Crypto News strategy")
            except Exception as e:
                self.logger.log_error(f"Failed to load News strategy: {str(e)}")
        
        # Load Statistical Arbitrage Strategy
        stat_arb_config = strategies_config.get('crypto_statistical_arb', {})
        if stat_arb_config.get('enabled', False):
            try:
                strategy_config = {
                    'stat_arb_min_correlation': stat_arb_config.get('min_correlation', 0.7),
                    'stat_arb_z_score_threshold': stat_arb_config.get('z_score_threshold', 2.0),
                    'stat_arb_max_holding_time': stat_arb_config.get('max_holding_time', 3600),
                }
                
                self.strategies['crypto_statistical_arb'] = StatisticalArbStrategy(strategy_config)
                self.logger.log_info("Loaded Statistical Arbitrage strategy")
            except Exception as e:
                self.logger.log_error(f"Failed to load Statistical Arb strategy: {str(e)}")
    
    def find_opportunities(self, markets: List[Dict[str, Any]],
                          prices_dict: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Find opportunities across all enabled strategies
        
        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data
            
        Returns:
            List of opportunities with strategy tags
        """
        all_opportunities = []
        
        for strategy_name, strategy in self.strategies.items():
            try:
                # Find opportunities for this strategy
                opportunities = strategy.find_opportunities(markets, prices_dict)
                
                # Tag each opportunity with strategy name
                for opp in opportunities:
                    # Convert to dict if it's an object
                    if hasattr(opp, 'to_dict'):
                        opp_dict = opp.to_dict()
                    else:
                        opp_dict = dict(opp)
                    
                    # Add strategy tag
                    opp_dict['strategy'] = strategy_name
                    
                    # Add arbitrage_type if this is an arbitrage opportunity
                    if not opp_dict.get('arbitrage_type'):
                        opp_dict['arbitrage_type'] = self._get_arbitrage_type(opp_dict)
                    
                    all_opportunities.append(opp_dict)
                
                if opportunities:
                    self.logger.log_info(
                        f"{strategy_name}: Found {len(opportunities)} opportunities"
                    )
                    
            except Exception as e:
                # Log error but continue with other strategies
                self.logger.log_error(
                    f"Error running {strategy_name}: {str(e)}"
                )
                continue
        
        return all_opportunities
    
    def _get_arbitrage_type(self, opportunity: Dict[str, Any]) -> str:
        """
        Determine arbitrage type for an opportunity
        
        Args:
            opportunity: Opportunity dictionary
            
        Returns:
            Arbitrage type string
        """
        # Default type based on opportunity_type field
        opp_type = opportunity.get('opportunity_type', '')
        
        if opp_type == 'arbitrage':
            return opportunity.get('arbitrage_type', 'Simple')
        elif opp_type == 'momentum':
            return 'N/A'
        elif opp_type == 'news':
            return 'N/A'
        elif opp_type == 'statistical_arb':
            return 'N/A'
        else:
            return 'Unknown'
    
    def get_enabled_strategies(self) -> List[str]:
        """
        Get list of enabled strategy names
        
        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())
    
    def get_strategy_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all strategies
        
        Returns:
            Dictionary mapping strategy name to statistics
        """
        stats = {}
        
        for strategy_name, strategy in self.strategies.items():
            try:
                if hasattr(strategy, 'get_statistics'):
                    stats[strategy_name] = strategy.get_statistics()
            except Exception as e:
                self.logger.log_error(
                    f"Error getting statistics for {strategy_name}: {str(e)}"
                )
                stats[strategy_name] = {'error': str(e)}
        
        return stats
    
    def reset_all_statistics(self) -> None:
        """Reset statistics for all strategies"""
        for strategy in self.strategies.values():
            if hasattr(strategy, 'reset_statistics'):
                try:
                    strategy.reset_statistics()
                except Exception as e:
                    self.logger.log_error(f"Error resetting strategy stats: {str(e)}")
