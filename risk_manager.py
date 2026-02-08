"""
Risk Manager Module - Multi-layer circuit breakers to protect capital

Implements multiple safety checks to stop trading when things go wrong:
- Consecutive losses (3 in a row)
- Hourly loss limits (dollar-based)
- Daily drawdown (percentage-based)
- Total drawdown from peak (percentage-based)
- Win rate degradation (below threshold)

Automatically pauses trading and provides specific reasons for each circuit breaker.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from logger import get_logger


class DrawdownProtection:
    """
    Multi-layer circuit breaker system to protect capital

    Monitors multiple risk metrics and automatically pauses trading when
    thresholds are exceeded. Each circuit breaker has specific reasoning
    and recovery conditions.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize drawdown protection

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()

        # Load circuit breaker thresholds from config
        risk_limits = config.get("risk_limits", {})

        self.max_consecutive_losses = risk_limits.get("max_consecutive_losses", 3)
        self.max_hourly_loss = risk_limits.get("max_hourly_loss_usd", 50.0)
        self.max_daily_drawdown_pct = risk_limits.get(
            "max_daily_drawdown_pct", 0.15
        )  # 15%
        self.max_total_drawdown_pct = risk_limits.get(
            "max_total_drawdown_pct", 0.25
        )  # 25%
        self.min_win_rate = risk_limits.get("min_win_rate", 0.50)  # 50%

        # Track current state
        self.consecutive_losses = 0
        self.hourly_losses = []  # List of (timestamp, loss_amount) tuples
        self.daily_start_capital = None
        self.peak_capital = None
        self.total_trades = 0
        self.winning_trades = 0

        # Pause state
        self.is_paused = False
        self.pause_reason = None
        self.paused_at = None
        self.triggered_breakers = []

        self.logger.log_warning(
            f"Drawdown Protection initialized - "
            f"Max consecutive losses: {self.max_consecutive_losses}, "
            f"Max hourly loss: ${self.max_hourly_loss:.2f}, "
            f"Max daily DD: {self.max_daily_drawdown_pct*100:.1f}%, "
            f"Max total DD: {self.max_total_drawdown_pct*100:.1f}%, "
            f"Min win rate: {self.min_win_rate*100:.1f}%"
        )

    def record_trade(self, profit: float, current_capital: float) -> None:
        """
        Record a trade result and update tracking metrics

        Args:
            profit: Profit/loss from trade (negative for loss)
            current_capital: Current total capital
        """
        self.total_trades += 1

        # Update peak capital
        if self.peak_capital is None or current_capital > self.peak_capital:
            self.peak_capital = current_capital

        # Set daily start capital if needed
        if self.daily_start_capital is None:
            self.daily_start_capital = current_capital

        # Track consecutive losses
        if profit < 0:
            self.consecutive_losses += 1
            # Add to hourly losses tracking
            self.hourly_losses.append((datetime.now(), abs(profit)))
        else:
            self.consecutive_losses = 0
            self.winning_trades += 1

        # Clean old hourly losses
        self._clean_old_hourly_losses()

    def check_all_breakers(self, current_capital: float) -> Dict[str, Any]:
        """
        Check all circuit breakers and pause if any are triggered

        Args:
            current_capital: Current total capital

        Returns:
            Dictionary with status and details about triggered breakers
        """
        # If already paused, return current state
        if self.is_paused:
            return {
                "trading_allowed": False,
                "is_paused": True,
                "pause_reason": self.pause_reason,
                "paused_at": self.paused_at,
                "triggered_breakers": self.triggered_breakers,
            }

        # Check each circuit breaker
        breakers = []

        # 1. Check consecutive losses
        loss_check = self.check_consecutive_losses()
        if loss_check["triggered"]:
            breakers.append(loss_check)

        # 2. Check hourly loss
        hourly_check = self.check_hourly_loss()
        if hourly_check["triggered"]:
            breakers.append(hourly_check)

        # 3. Check daily drawdown
        daily_check = self.check_daily_drawdown(current_capital)
        if daily_check["triggered"]:
            breakers.append(daily_check)

        # 4. Check total drawdown
        total_check = self.check_total_drawdown(current_capital)
        if total_check["triggered"]:
            breakers.append(total_check)

        # 5. Check win rate
        winrate_check = self.check_win_rate()
        if winrate_check["triggered"]:
            breakers.append(winrate_check)

        # If any breakers triggered, pause trading
        if breakers:
            self._pause_trading(breakers)
            return {
                "trading_allowed": False,
                "is_paused": True,
                "pause_reason": self.pause_reason,
                "paused_at": self.paused_at,
                "triggered_breakers": breakers,
            }

        # All clear
        return {
            "trading_allowed": True,
            "is_paused": False,
            "pause_reason": None,
            "triggered_breakers": [],
        }

    def check_consecutive_losses(self) -> Dict[str, Any]:
        """
        Check if consecutive loss limit exceeded

        Returns:
            Dictionary with trigger status and details
        """
        triggered = self.consecutive_losses >= self.max_consecutive_losses

        return {
            "name": "consecutive_losses",
            "triggered": triggered,
            "current_value": self.consecutive_losses,
            "threshold": self.max_consecutive_losses,
            "severity": "HIGH" if triggered else "OK",
            "message": (
                f"⛔ STOPPED: {self.consecutive_losses} consecutive losses "
                f"(limit: {self.max_consecutive_losses})"
                if triggered
                else f"Consecutive losses: {self.consecutive_losses}/{self.max_consecutive_losses}"
            ),
        }

    def check_hourly_loss(self) -> Dict[str, Any]:
        """
        Check if hourly loss limit exceeded

        Returns:
            Dictionary with trigger status and details
        """
        self._clean_old_hourly_losses()
        total_hourly_loss = sum(loss for _, loss in self.hourly_losses)
        triggered = total_hourly_loss >= self.max_hourly_loss

        return {
            "name": "hourly_loss",
            "triggered": triggered,
            "current_value": total_hourly_loss,
            "threshold": self.max_hourly_loss,
            "severity": "HIGH" if triggered else "OK",
            "message": (
                f"⛔ STOPPED: ${total_hourly_loss:.2f} lost in last hour "
                f"(limit: ${self.max_hourly_loss:.2f})"
                if triggered
                else f"Hourly loss: ${total_hourly_loss:.2f}/${self.max_hourly_loss:.2f}"
            ),
        }

    def check_daily_drawdown(self, current_capital: float) -> Dict[str, Any]:
        """
        Check if daily drawdown limit exceeded

        Args:
            current_capital: Current total capital

        Returns:
            Dictionary with trigger status and details
        """
        if self.daily_start_capital is None:
            return {
                "name": "daily_drawdown",
                "triggered": False,
                "current_value": 0,
                "threshold": self.max_daily_drawdown_pct,
                "severity": "OK",
                "message": "No daily baseline yet",
            }

        daily_pnl = current_capital - self.daily_start_capital
        daily_drawdown_pct = (
            abs(daily_pnl) / self.daily_start_capital if daily_pnl < 0 else 0
        )
        triggered = daily_drawdown_pct >= self.max_daily_drawdown_pct

        return {
            "name": "daily_drawdown",
            "triggered": triggered,
            "current_value": daily_drawdown_pct,
            "threshold": self.max_daily_drawdown_pct,
            "severity": "HIGH" if triggered else "OK",
            "message": (
                f"⛔ STOPPED: {daily_drawdown_pct*100:.1f}% daily drawdown "
                f"(limit: {self.max_daily_drawdown_pct*100:.1f}%)"
                if triggered
                else f"Daily drawdown: {daily_drawdown_pct*100:.1f}%/{self.max_daily_drawdown_pct*100:.1f}%"
            ),
        }

    def check_total_drawdown(self, current_capital: float) -> Dict[str, Any]:
        """
        Check if total drawdown from peak exceeded

        Args:
            current_capital: Current total capital

        Returns:
            Dictionary with trigger status and details
        """
        if self.peak_capital is None:
            return {
                "name": "total_drawdown",
                "triggered": False,
                "current_value": 0,
                "threshold": self.max_total_drawdown_pct,
                "severity": "OK",
                "message": "No peak capital yet",
            }

        total_drawdown = self.peak_capital - current_capital
        total_drawdown_pct = (
            total_drawdown / self.peak_capital if total_drawdown > 0 else 0
        )
        triggered = total_drawdown_pct >= self.max_total_drawdown_pct

        return {
            "name": "total_drawdown",
            "triggered": triggered,
            "current_value": total_drawdown_pct,
            "threshold": self.max_total_drawdown_pct,
            "severity": "HIGH" if triggered else "OK",
            "message": (
                f"⛔ STOPPED: {total_drawdown_pct*100:.1f}% down from peak "
                f"(limit: {self.max_total_drawdown_pct*100:.1f}%)"
                if triggered
                else f"Drawdown from peak: {total_drawdown_pct*100:.1f}%/{self.max_total_drawdown_pct*100:.1f}%"
            ),
        }

    def check_win_rate(self) -> Dict[str, Any]:
        """
        Check if win rate below minimum threshold

        Returns:
            Dictionary with trigger status and details
        """
        # Need minimum sample size (20 trades) for reliable win rate
        if self.total_trades < 20:
            return {
                "name": "win_rate",
                "triggered": False,
                "current_value": 0,
                "threshold": self.min_win_rate,
                "severity": "OK",
                "message": f"Insufficient trades for win rate check ({self.total_trades}/20)",
            }

        win_rate = self.winning_trades / self.total_trades
        triggered = win_rate < self.min_win_rate

        return {
            "name": "win_rate",
            "triggered": triggered,
            "current_value": win_rate,
            "threshold": self.min_win_rate,
            "severity": "HIGH" if triggered else "OK",
            "message": (
                f"⛔ STOPPED: {win_rate*100:.1f}% win rate "
                f"(minimum: {self.min_win_rate*100:.1f}%)"
                if triggered
                else f"Win rate: {win_rate*100:.1f}%/{self.min_win_rate*100:.1f}%"
            ),
        }

    def _pause_trading(self, triggered_breakers: List[Dict[str, Any]]) -> None:
        """
        Pause trading and log the reasons

        Args:
            triggered_breakers: List of triggered circuit breaker details
        """
        self.is_paused = True
        self.paused_at = datetime.now()
        self.triggered_breakers = triggered_breakers

        # Build comprehensive pause reason
        reasons = [breaker["message"] for breaker in triggered_breakers]
        self.pause_reason = " | ".join(reasons)

        # Log critical alert
        self.logger.log_critical(
            f"🚨 TRADING PAUSED - Circuit breakers triggered: {self.pause_reason}"
        )

        # Log each breaker individually
        for breaker in triggered_breakers:
            self.logger.log_critical(f"  - {breaker['name']}: {breaker['message']}")

        # Generate alert (if notification system available)
        self._generate_alert(triggered_breakers)

    def _generate_alert(self, triggered_breakers: List[Dict[str, Any]]) -> None:
        """
        Generate alerts for triggered circuit breakers

        Args:
            triggered_breakers: List of triggered circuit breaker details
        """
        # For now, just log the alert
        # In production, this could send email, SMS, push notification, etc.
        alert_msg = (
            f"⚠️ ALERT: {len(triggered_breakers)} circuit breaker(s) triggered!\n"
            f"Trading has been automatically paused.\n"
            f"Triggered breakers: {', '.join([b['name'] for b in triggered_breakers])}\n"
            f"Review logs and investigate before resuming."
        )
        self.logger.log_critical(alert_msg)

    def _clean_old_hourly_losses(self) -> None:
        """Remove losses older than 1 hour from tracking"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.hourly_losses = [
            (timestamp, loss)
            for timestamp, loss in self.hourly_losses
            if timestamp > cutoff_time
        ]

    def reset_daily_tracking(self, current_capital: float) -> None:
        """
        Reset daily tracking (call at start of each trading day)

        Args:
            current_capital: Current total capital
        """
        self.daily_start_capital = current_capital
        self.logger.log_warning(
            f"Daily tracking reset - Starting capital: ${current_capital:.2f}"
        )

    def resume_trading(self, force: bool = False) -> bool:
        """
        Resume trading after pause

        Args:
            force: Force resume even if conditions not cleared

        Returns:
            True if trading resumed successfully
        """
        if not self.is_paused:
            self.logger.log_warning("Trading not paused - nothing to resume")
            return False

        if force:
            self.is_paused = False
            self.pause_reason = None
            self.paused_at = None
            self.triggered_breakers = []
            self.logger.log_warning("⚠️ Trading FORCE RESUMED - Use with caution!")
            return True
        else:
            self.logger.log_warning(
                "Cannot resume without force=True. Investigate issues first!"
            )
            return False

    def get_risk_metrics(self, current_capital: float) -> Dict[str, Any]:
        """
        Get current risk metrics for monitoring/dashboard

        Args:
            current_capital: Current total capital

        Returns:
            Dictionary with all risk metrics
        """
        # Calculate win rate
        win_rate = 0
        if self.total_trades > 0:
            win_rate = self.winning_trades / self.total_trades

        # Calculate hourly loss
        self._clean_old_hourly_losses()
        hourly_loss = sum(loss for _, loss in self.hourly_losses)

        # Calculate drawdowns
        daily_dd_pct = 0
        if self.daily_start_capital:
            daily_pnl = current_capital - self.daily_start_capital
            if daily_pnl < 0:
                daily_dd_pct = abs(daily_pnl) / self.daily_start_capital

        total_dd_pct = 0
        if self.peak_capital:
            total_drawdown = self.peak_capital - current_capital
            if total_drawdown > 0:
                total_dd_pct = total_drawdown / self.peak_capital

        return {
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason,
            "consecutive_losses": self.consecutive_losses,
            "hourly_loss": hourly_loss,
            "daily_drawdown_pct": daily_dd_pct,
            "total_drawdown_pct": total_dd_pct,
            "win_rate": win_rate,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "peak_capital": self.peak_capital,
            "thresholds": {
                "max_consecutive_losses": self.max_consecutive_losses,
                "max_hourly_loss": self.max_hourly_loss,
                "max_daily_drawdown_pct": self.max_daily_drawdown_pct,
                "max_total_drawdown_pct": self.max_total_drawdown_pct,
                "min_win_rate": self.min_win_rate,
            },
        }
