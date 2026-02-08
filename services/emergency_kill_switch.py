"""
Emergency Kill Switch

Immediately stop all trading and disable all strategies.
"""

import logging
from typing import Dict
from datetime import datetime

from database.competition_models import Strategy, Config
from logger import get_logger

logger = get_logger()


class EmergencyKillSwitch:
    """Emergency stop all trading"""

    def __init__(self):
        """Initialize kill switch"""
        self.activated_at = None
        self.activation_reason = None

    def activate_kill_switch(
        self, 
        reason: str, 
        close_positions: bool = False,
        activated_by: str = "system"
    ) -> Dict:
        """
        EMERGENCY STOP - Disable all strategies and stop trading
        
        Args:
            reason: Reason for activation
            close_positions: Whether to close all positions
            activated_by: Who activated the kill switch
            
        Returns:
            Activation result
        """
        try:
            logger.critical(f"🚨 KILL SWITCH ACTIVATED by {activated_by}: {reason}")
            
            # Set global kill switch flag
            Config.set_bool('kill_switch_active', True)
            Config.set('kill_switch_reason', reason)
            Config.set('kill_switch_activated_at', datetime.utcnow().isoformat())
            Config.set('kill_switch_activated_by', activated_by)
            
            self.activated_at = datetime.utcnow()
            self.activation_reason = reason
            
            # Disable all strategies
            strategies = Strategy.get_all()
            disabled_count = 0
            
            for strategy in strategies:
                if strategy['enabled']:
                    Strategy.update(
                        strategy['id'],
                        enabled=0,
                        emergency_disabled=1,
                        disable_reason=f"Kill switch: {reason}"
                    )
                    disabled_count += 1
                    logger.warning(f"Disabled strategy: {strategy['name']}")
            
            result = {
                'status': 'activated',
                'reason': reason,
                'activated_by': activated_by,
                'activated_at': self.activated_at.isoformat(),
                'strategies_disabled': disabled_count,
                'close_positions': close_positions
            }
            
            # TODO: If close_positions is True, integrate with position closing logic
            if close_positions:
                logger.warning("Position closing not yet implemented")
                result['positions_closed'] = 0
            
            return result
            
        except Exception as e:
            logger.error(f"Error activating kill switch: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def deactivate_kill_switch(self, admin_password: str = None) -> Dict:
        """
        Reactivate bot (requires admin confirmation)
        
        Args:
            admin_password: Admin password for confirmation
            
        Returns:
            Deactivation result
        """
        try:
            # TODO: Add password validation when admin system is implemented
            # For now, allow deactivation
            
            if not self.is_active():
                return {
                    'status': 'error',
                    'message': 'Kill switch is not active'
                }
            
            logger.info("🔓 Kill switch deactivated")
            
            # Clear kill switch flag
            Config.set_bool('kill_switch_active', False)
            Config.set('kill_switch_deactivated_at', datetime.utcnow().isoformat())
            
            # Note: We don't automatically re-enable strategies
            # Admin must manually review and re-enable them
            
            self.activated_at = None
            self.activation_reason = None
            
            return {
                'status': 'deactivated',
                'deactivated_at': datetime.utcnow().isoformat(),
                'note': 'Strategies remain disabled. Manually review and re-enable.'
            }
            
        except Exception as e:
            logger.error(f"Error deactivating kill switch: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def is_active(self) -> bool:
        """Check if kill switch is active"""
        try:
            return Config.get_bool('kill_switch_active', default=False)
        except Exception as e:
            logger.error(f"Error checking kill switch status: {e}")
            return False

    def get_status(self) -> Dict:
        """Get kill switch status"""
        try:
            is_active = self.is_active()
            
            status = {
                'active': is_active,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if is_active:
                status['reason'] = Config.get('kill_switch_reason')
                status['activated_at'] = Config.get('kill_switch_activated_at')
                status['activated_by'] = Config.get('kill_switch_activated_by')
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting kill switch status: {e}")
            return {
                'active': False,
                'error': str(e)
            }


# Global instance
kill_switch = EmergencyKillSwitch()
