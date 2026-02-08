"""
Risk Limit Enforcer

Enforces hard risk limits to prevent losses and implements
circuit breaker functionality for emergency trading halts.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RiskLimits:
    """Risk limit configuration"""
    max_position_size: float = 1000.0  # Max size per position
    max_daily_loss: float = 500.0  # Max loss per day
    max_total_exposure: float = 5000.0  # Max total capital at risk
    max_drawdown_pct: float = 20.0  # Max drawdown from peak (%)
    max_positions: int = 10  # Max open positions


class RiskEnforcer:
    """
    Risk limit enforcer with circuit breaker
    
    Provides hard stops to prevent excessive losses and can
    disable all trading if critical limits are breached.
    """

    def __init__(self, config: Dict = None, risk_limits: RiskLimits = None):
        """
        Initialize risk enforcer
        
        Args:
            config: Bot configuration dict
            risk_limits: Custom risk limits (uses defaults if None)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Set risk limits from config or use defaults
        self.limits = risk_limits or RiskLimits(
            max_position_size=self.config.get('risk', {}).get('max_position_size', 1000.0),
            max_daily_loss=self.config.get('risk', {}).get('max_daily_loss', 500.0),
            max_total_exposure=self.config.get('risk', {}).get('max_total_exposure', 5000.0),
            max_drawdown_pct=self.config.get('risk', {}).get('max_drawdown_pct', 20.0),
            max_positions=self.config.get('risk', {}).get('max_positions', 10)
        )
        
        # Circuit breaker state
        self.circuit_breaker_active = False
        self.circuit_breaker_reason = None
        self.circuit_breaker_time = None
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.utcnow().date()
        
        # Peak tracking for drawdown
        self.peak_portfolio_value = 0.0
        
        self.logger.info("Risk Enforcer initialized with limits:")
        self.logger.info(f"  Max Position Size: ${self.limits.max_position_size:.2f}")
        self.logger.info(f"  Max Daily Loss: ${self.limits.max_daily_loss:.2f}")
        self.logger.info(f"  Max Total Exposure: ${self.limits.max_total_exposure:.2f}")
        self.logger.info(f"  Max Drawdown: {self.limits.max_drawdown_pct}%")
        self.logger.info(f"  Max Positions: {self.limits.max_positions}")
    
    def check_trade_allowed(self, trade_size: float, current_exposure: float,
                          daily_pnl: float, num_positions: int = 0,
                          portfolio_value: float = 10000.0) -> Tuple[bool, str]:
        """
        Check if a trade is allowed under current risk limits
        
        Args:
            trade_size: Size of proposed trade
            current_exposure: Current total exposure across all positions
            daily_pnl: Profit/loss for today
            num_positions: Current number of open positions
            portfolio_value: Current portfolio value
            
        Returns:
            Tuple of (allowed: bool, reason: str)
            
        Example:
            allowed, reason = risk_enforcer.check_trade_allowed(
                trade_size=500,
                current_exposure=2000,
                daily_pnl=-200,
                num_positions=3
            )
            if not allowed:
                logger.warning(f"Trade blocked: {reason}")
        """
        # Update daily tracking
        self._update_daily_tracking(daily_pnl)
        
        # Update peak for drawdown calculation
        if portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = portfolio_value
        
        # Check circuit breaker
        if self.circuit_breaker_active:
            return False, f"Circuit breaker active: {self.circuit_breaker_reason}"
        
        # Check position size limit
        if trade_size > self.limits.max_position_size:
            reason = (
                f"Position size ${trade_size:.2f} exceeds limit "
                f"${self.limits.max_position_size:.2f}"
            )
            self.logger.warning(f"Trade blocked: {reason}")
            return False, reason
        
        # Check total exposure limit
        new_exposure = current_exposure + trade_size
        if new_exposure > self.limits.max_total_exposure:
            reason = (
                f"Total exposure ${new_exposure:.2f} would exceed limit "
                f"${self.limits.max_total_exposure:.2f}"
            )
            self.logger.warning(f"Trade blocked: {reason}")
            return False, reason
        
        # Check daily loss limit
        if self.daily_pnl < -self.limits.max_daily_loss:
            reason = (
                f"Daily loss ${abs(self.daily_pnl):.2f} exceeds limit "
                f"${self.limits.max_daily_loss:.2f}"
            )
            self.logger.warning(f"Trade blocked: {reason}")
            
            # Trigger circuit breaker if daily loss limit hit
            self.trigger_circuit_breaker(reason)
            return False, reason
        
        # Check max positions limit
        if num_positions >= self.limits.max_positions:
            reason = (
                f"Position count {num_positions} at limit {self.limits.max_positions}"
            )
            self.logger.warning(f"Trade blocked: {reason}")
            return False, reason
        
        # Check drawdown limit
        if self.peak_portfolio_value > 0:
            current_drawdown = (
                (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value * 100
            )
            
            if current_drawdown > self.limits.max_drawdown_pct:
                reason = (
                    f"Drawdown {current_drawdown:.1f}% exceeds limit "
                    f"{self.limits.max_drawdown_pct}%"
                )
                self.logger.warning(f"Trade blocked: {reason}")
                
                # Trigger circuit breaker if drawdown limit hit
                self.trigger_circuit_breaker(reason)
                return False, reason
        
        # All checks passed
        return True, "Trade approved"
    
    def trigger_circuit_breaker(self, reason: str):
        """
        Trigger circuit breaker - emergency stop all trading
        
        Args:
            reason: Reason for triggering circuit breaker
        """
        if self.circuit_breaker_active:
            return  # Already active
        
        self.circuit_breaker_active = True
        self.circuit_breaker_reason = reason
        self.circuit_breaker_time = datetime.utcnow()
        
        self.logger.critical("=" * 60)
        self.logger.critical("🚨 CIRCUIT BREAKER TRIGGERED 🚨")
        self.logger.critical(f"Reason: {reason}")
        self.logger.critical(f"Time: {self.circuit_breaker_time.isoformat()}")
        self.logger.critical("All trading has been DISABLED")
        self.logger.critical("=" * 60)
        
        # Send emergency notification (would integrate with notification system)
        self._send_emergency_notification(reason)
    
    def reset_circuit_breaker(self, manual_override: bool = False):
        """
        Reset circuit breaker to resume trading
        
        Args:
            manual_override: If True, allows manual reset. Otherwise requires
                           conditions to be met (e.g., new trading day)
        """
        if not self.circuit_breaker_active:
            self.logger.info("Circuit breaker not active")
            return
        
        if not manual_override:
            # Auto-reset only on new trading day
            current_date = datetime.utcnow().date()
            if current_date <= self.daily_reset_time:
                self.logger.warning(
                    "Circuit breaker can only auto-reset on new trading day"
                )
                return
        
        self.circuit_breaker_active = False
        old_reason = self.circuit_breaker_reason
        self.circuit_breaker_reason = None
        self.circuit_breaker_time = None
        
        self.logger.warning("=" * 60)
        self.logger.warning("✓ Circuit Breaker RESET")
        self.logger.warning(f"Previous reason: {old_reason}")
        self.logger.warning("Trading ENABLED")
        self.logger.warning("=" * 60)
    
    def _update_daily_tracking(self, daily_pnl: float):
        """Update daily P&L tracking and reset if new day"""
        current_date = datetime.utcnow().date()
        
        if current_date > self.daily_reset_time:
            # New day - reset tracking
            self.logger.info(f"Daily P&L reset: ${self.daily_pnl:.2f} -> $0.00")
            self.daily_pnl = 0.0
            self.daily_reset_time = current_date
            
            # Auto-reset circuit breaker on new day (if not manually triggered)
            if self.circuit_breaker_active:
                self.reset_circuit_breaker(manual_override=False)
        
        self.daily_pnl = daily_pnl
    
    def _send_emergency_notification(self, reason: str):
        """
        Send emergency notification
        
        Args:
            reason: Circuit breaker reason
            
        Note: This would integrate with the notification service
        """
        # Placeholder - in production, this would send actual notifications
        # via email, SMS, Slack, etc.
        self.logger.critical(f"EMERGENCY ALERT: {reason}")
    
    def get_risk_status(self) -> Dict:
        """
        Get current risk status
        
        Returns:
            Dict with risk metrics and status
        """
        return {
            'circuit_breaker_active': self.circuit_breaker_active,
            'circuit_breaker_reason': self.circuit_breaker_reason,
            'circuit_breaker_time': (
                self.circuit_breaker_time.isoformat()
                if self.circuit_breaker_time else None
            ),
            'daily_pnl': self.daily_pnl,
            'daily_loss_limit': self.limits.max_daily_loss,
            'daily_loss_remaining': self.limits.max_daily_loss + self.daily_pnl,
            'peak_portfolio_value': self.peak_portfolio_value,
            'limits': {
                'max_position_size': self.limits.max_position_size,
                'max_daily_loss': self.limits.max_daily_loss,
                'max_total_exposure': self.limits.max_total_exposure,
                'max_drawdown_pct': self.limits.max_drawdown_pct,
                'max_positions': self.limits.max_positions
            }
        }
    
    def update_limits(self, new_limits: Dict):
        """
        Update risk limits
        
        Args:
            new_limits: Dict with new limit values
        """
        if 'max_position_size' in new_limits:
            self.limits.max_position_size = new_limits['max_position_size']
        
        if 'max_daily_loss' in new_limits:
            self.limits.max_daily_loss = new_limits['max_daily_loss']
        
        if 'max_total_exposure' in new_limits:
            self.limits.max_total_exposure = new_limits['max_total_exposure']
        
        if 'max_drawdown_pct' in new_limits:
            self.limits.max_drawdown_pct = new_limits['max_drawdown_pct']
        
        if 'max_positions' in new_limits:
            self.limits.max_positions = new_limits['max_positions']
        
        self.logger.info(f"Risk limits updated: {new_limits}")
