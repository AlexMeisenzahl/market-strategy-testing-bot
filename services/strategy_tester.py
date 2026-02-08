"""
Strategy Tester - Forward Testing Framework

Provides comprehensive forward testing capabilities for trading strategies:
- Live data integration
- Real-time strategy execution
- Performance tracking
- Risk management
- Automated reporting
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv

from logger import get_logger
from services.paper_trading_engine import PaperTradingEngine, OrderSide, OrderType


class StrategyTester:
    """
    Forward testing framework for trading strategies
    
    Features:
    - Multiple strategy testing simultaneously
    - Real-time data feed integration
    - Paper trading execution
    - Performance analytics
    - Risk management
    - Automated reporting
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.001,
        log_dir: str = "logs",
        config: Dict[str, Any] = None,
        logger=None,
    ):
        """
        Initialize strategy tester
        
        Args:
            initial_capital: Starting capital for testing
            commission_rate: Commission rate as decimal
            slippage_rate: Slippage rate as decimal
            log_dir: Directory for logs and results
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger or get_logger()
        self.config = config or {}
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize paper trading engine
        self.trading_engine = PaperTradingEngine(
            initial_balance=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            log_dir=str(self.log_dir),
            logger=self.logger,
        )
        
        # Strategy registry
        self.strategies: Dict[str, Any] = {}
        self.strategy_signals: Dict[str, List[Dict]] = {}
        
        # Testing state
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_running = False
        
        # Data tracking
        self.market_data: Dict[str, List[Dict]] = {}
        self.signal_history: List[Dict] = []
        
        # Results
        self.test_results: Dict[str, Any] = {}
        
    def register_strategy(
        self, strategy_name: str, strategy_instance: Any
    ) -> None:
        """
        Register a strategy for testing
        
        Args:
            strategy_name: Unique name for the strategy
            strategy_instance: Strategy instance with required methods
        """
        required_methods = ["analyze_momentum", "execute_trade"]
        
        # Validate strategy has required methods
        for method in required_methods:
            if not hasattr(strategy_instance, method):
                if self.logger:
                    self.logger.log_error(
                        f"Strategy {strategy_name} missing method: {method}"
                    )
                return
                
        self.strategies[strategy_name] = strategy_instance
        self.strategy_signals[strategy_name] = []
        
        if self.logger:
            self.logger.log_event(f"Registered strategy: {strategy_name}")
            
    def start_test(self) -> Dict[str, Any]:
        """
        Start forward testing
        
        Returns:
            Start status
        """
        if self.is_running:
            return {
                "success": False,
                "error": "Test already running",
            }
            
        if not self.strategies:
            return {
                "success": False,
                "error": "No strategies registered",
            }
            
        self.is_running = True
        self.start_time = datetime.now()
        
        if self.logger:
            self.logger.log_event(
                f"Started forward testing with {len(self.strategies)} strategies"
            )
            
        return {
            "success": True,
            "start_time": self.start_time.isoformat(),
            "strategies": list(self.strategies.keys()),
        }
        
    def stop_test(self) -> Dict[str, Any]:
        """
        Stop forward testing and generate results
        
        Returns:
            Test results
        """
        if not self.is_running:
            return {
                "success": False,
                "error": "Test not running",
            }
            
        self.is_running = False
        self.end_time = datetime.now()
        
        # Generate comprehensive results
        self.test_results = self._generate_results()
        
        # Save results to file
        self._save_results()
        
        if self.logger:
            self.logger.log_event("Stopped forward testing")
            
        return {
            "success": True,
            "end_time": self.end_time.isoformat(),
            "results": self.test_results,
        }
        
    def process_market_data(
        self, symbol: str, price: float, volume: float = 0.0, metadata: Dict = None
    ) -> List[Dict[str, Any]]:
        """
        Process market data and generate signals
        
        Args:
            symbol: Market symbol
            price: Current price
            volume: Current volume
            metadata: Additional market metadata
            
        Returns:
            List of signals generated
        """
        if not self.is_running:
            return []
            
        # Store market data
        if symbol not in self.market_data:
            self.market_data[symbol] = []
            
        data_point = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "metadata": metadata or {},
        }
        self.market_data[symbol].append(data_point)
        
        signals = []
        
        # Run each strategy
        for strategy_name, strategy in self.strategies.items():
            try:
                # Check if strategy should analyze this symbol
                if hasattr(strategy, "symbols") and symbol not in strategy.symbols:
                    continue
                    
                # Generate signal
                signal = None
                if hasattr(strategy, "analyze_momentum"):
                    signal = strategy.analyze_momentum(symbol, price, volume)
                elif hasattr(strategy, "analyze_market"):
                    signal = strategy.analyze_market(
                        {"symbol": symbol, **metadata} if metadata else {"symbol": symbol},
                        {"price": price},
                    )
                    
                if signal:
                    signal["strategy"] = strategy_name
                    signal["timestamp"] = datetime.now()
                    signals.append(signal)
                    
                    # Store signal
                    self.strategy_signals[strategy_name].append(signal)
                    self.signal_history.append(signal)
                    
                    # Auto-execute if enabled
                    if self._should_auto_execute(signal):
                        self._execute_signal(signal, price)
                        
            except Exception as e:
                if self.logger:
                    self.logger.log_error(
                        f"Error processing {strategy_name} for {symbol}: {str(e)}"
                    )
                    
        return signals
        
    def execute_signal_manually(
        self, signal: Dict[str, Any], current_price: float
    ) -> Dict[str, Any]:
        """
        Manually execute a trading signal
        
        Args:
            signal: Signal dictionary
            current_price: Current market price
            
        Returns:
            Execution result
        """
        return self._execute_signal(signal, current_price)
        
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current testing status
        
        Returns:
            Status dictionary with metrics
        """
        current_prices = self._get_latest_prices()
        portfolio_metrics = self.trading_engine.get_performance_metrics(current_prices)
        
        # Calculate per-strategy metrics
        strategy_metrics = {}
        for strategy_name, strategy in self.strategies.items():
            if hasattr(strategy, "get_performance_metrics"):
                strategy_metrics[strategy_name] = strategy.get_performance_metrics()
            else:
                strategy_metrics[strategy_name] = {
                    "signals_generated": len(self.strategy_signals[strategy_name])
                }
                
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_time": (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time
                else 0
            ),
            "strategies_active": len(self.strategies),
            "total_signals": len(self.signal_history),
            "portfolio": portfolio_metrics,
            "strategies": strategy_metrics,
            "positions": self.trading_engine.get_all_positions(current_prices),
        }
        
    def get_results(self) -> Dict[str, Any]:
        """Get test results"""
        if not self.test_results:
            return {"error": "Test not completed yet"}
        return self.test_results
        
    # Private helper methods
    
    def _should_auto_execute(self, signal: Dict[str, Any]) -> bool:
        """Determine if signal should be auto-executed"""
        # Check if auto-execution is enabled
        auto_execute = self.config.get("auto_execute_signals", True)
        if not auto_execute:
            return False
            
        # Check if signal has execution flag
        return signal.get("execution_ready", False)
        
    def _execute_signal(
        self, signal: Dict[str, Any], current_price: float
    ) -> Dict[str, Any]:
        """
        Execute a trading signal
        
        Args:
            signal: Signal dictionary
            current_price: Current market price
            
        Returns:
            Execution result
        """
        symbol = signal.get("symbol", signal.get("market_id", "UNKNOWN"))
        direction = signal.get("direction", "bullish")
        position_size = signal.get("position_size", 10)
        
        # Determine order side
        side = "buy" if direction in ["bullish", "buy"] else "sell"
        
        # Place market order
        order_result = self.trading_engine.place_order(
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=position_size / current_price,  # Convert USD to quantity
        )
        
        if not order_result["success"]:
            if self.logger:
                self.logger.log_error(
                    f"Failed to place order for signal: {order_result.get('error')}"
                )
            return order_result
            
        # Execute the order
        execution_result = self.trading_engine.execute_order(
            order_result["order_id"], current_price
        )
        
        if execution_result["success"] and self.logger:
            self.logger.log_trade(
                market=symbol,
                yes_price=current_price,
                no_price=0,
                profit_usd=0,
                status="executed_from_signal",
                strategy=signal.get("strategy", "unknown"),
                arbitrage_type=direction,
            )
            
        return execution_result
        
    def _get_latest_prices(self) -> Dict[str, float]:
        """Get latest price for each symbol"""
        prices = {}
        for symbol, data_list in self.market_data.items():
            if data_list:
                prices[symbol] = data_list[-1]["price"]
        return prices
        
    def _generate_results(self) -> Dict[str, Any]:
        """Generate comprehensive test results"""
        if not self.start_time or not self.end_time:
            return {}
            
        duration = (self.end_time - self.start_time).total_seconds()
        current_prices = self._get_latest_prices()
        
        # Portfolio performance
        portfolio_metrics = self.trading_engine.get_performance_metrics(current_prices)
        
        # Strategy-specific results
        strategy_results = {}
        for strategy_name, strategy in self.strategies.items():
            signals = self.strategy_signals[strategy_name]
            
            strategy_results[strategy_name] = {
                "signals_generated": len(signals),
                "performance": (
                    strategy.get_performance_metrics()
                    if hasattr(strategy, "get_performance_metrics")
                    else {}
                ),
            }
            
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = 0.0
        if portfolio_metrics["total_trades"] > 0:
            avg_return = portfolio_metrics["total_return_pct"] / 100
            # Simplified Sharpe (would need historical returns for real calculation)
            sharpe_ratio = avg_return * (252 ** 0.5)  # Annualized
            
        return {
            "test_period": {
                "start": self.start_time.isoformat(),
                "end": self.end_time.isoformat(),
                "duration_seconds": duration,
                "duration_hours": duration / 3600,
            },
            "portfolio": portfolio_metrics,
            "strategies": strategy_results,
            "risk_metrics": {
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown_pct": portfolio_metrics["max_drawdown_pct"],
                "win_rate_pct": portfolio_metrics["win_rate_pct"],
            },
            "trading_activity": {
                "total_signals": len(self.signal_history),
                "total_trades": portfolio_metrics["total_trades"],
                "signal_to_trade_ratio": (
                    portfolio_metrics["total_trades"] / len(self.signal_history)
                    if self.signal_history
                    else 0
                ),
            },
        }
        
    def _save_results(self) -> None:
        """Save test results to files"""
        if not self.test_results:
            return
            
        # Save JSON results
        results_file = self.log_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)
            
        # Save CSV trade history
        if self.trading_engine.trade_history:
            csv_file = self.log_dir / f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(csv_file, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=self.trading_engine.trade_history[0].keys()
                )
                writer.writeheader()
                writer.writerows(self.trading_engine.trade_history)
                
        if self.logger:
            self.logger.log_event(f"Saved test results to {results_file}")
