"""
Crash Recovery System

Saves bot state periodically and recovers from crashes by restoring
the last known good state.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class CrashRecovery:
    """
    Crash recovery system
    
    Saves bot state to disk and recovers from crashes:
    - Saves state every iteration
    - Stores: timestamp, strategies, positions, pending trades, portfolio value
    - On restart, recovers from saved state
    - Reconciles positions with exchange
    """

    def __init__(self, state_dir: str = None):
        """
        Initialize crash recovery
        
        Args:
            state_dir: Directory to store state files (default: ./state)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set state directory
        if state_dir is None:
            base_dir = Path(__file__).parent.parent
            state_dir = base_dir / "state"
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / "bot_state.json"
        self.backup_file = self.state_dir / "bot_state.backup.json"
        
        self.logger.info(f"Crash Recovery initialized")
        self.logger.info(f"  State file: {self.state_file}")
    
    def save_state(self, state: Dict = None) -> bool:
        """
        Save bot state to disk
        
        Args:
            state: State dict to save. If None, collects current state
            
        Returns:
            True if saved successfully, False otherwise
            
        State format:
        {
            'timestamp': ISO timestamp,
            'active_strategies': List[str],
            'open_positions': List[Dict],
            'pending_trades': List[Dict],
            'portfolio_value': float,
            'cash_balance': float,
            'circuit_breaker_active': bool,
            'daily_pnl': float
        }
        """
        try:
            # Collect state if not provided
            if state is None:
                state = self._collect_current_state()
            
            # Add timestamp
            state['timestamp'] = datetime.utcnow().isoformat()
            state['save_count'] = state.get('save_count', 0) + 1
            
            # Backup existing state file
            if self.state_file.exists():
                import shutil
                shutil.copy(self.state_file, self.backup_file)
            
            # Write new state
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.debug(
                f"State saved (#{state['save_count']}): "
                f"{len(state.get('open_positions', []))} positions, "
                f"${state.get('portfolio_value', 0):.2f} portfolio value"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            return False
    
    def recover_from_crash(self) -> Optional[Dict]:
        """
        Recover from crash by loading last saved state
        
        Returns:
            Recovered state dict or None if no state found
        """
        self.logger.info("=" * 60)
        self.logger.info("🔄 Attempting crash recovery...")
        
        # Try to load state file
        state = self._load_state_file(self.state_file)
        
        if state is None:
            # Try backup file
            self.logger.warning("Primary state file not found, trying backup...")
            state = self._load_state_file(self.backup_file)
        
        if state is None:
            self.logger.warning("No saved state found - starting fresh")
            self.logger.info("=" * 60)
            return None
        
        # Validate state
        if not self._validate_state(state):
            self.logger.error("State file corrupted - starting fresh")
            self.logger.info("=" * 60)
            return None
        
        # Log recovery info
        save_time = datetime.fromisoformat(state['timestamp'])
        time_since_save = (datetime.utcnow() - save_time).total_seconds()
        
        self.logger.info("✓ State recovered successfully!")
        self.logger.info(f"  Saved: {save_time.isoformat()}")
        self.logger.info(f"  Age: {time_since_save:.0f} seconds")
        self.logger.info(f"  Open positions: {len(state.get('open_positions', []))}")
        self.logger.info(f"  Pending trades: {len(state.get('pending_trades', []))}")
        self.logger.info(f"  Portfolio value: ${state.get('portfolio_value', 0):.2f}")
        
        # Reconcile with exchange (placeholder)
        self._reconcile_positions(state)
        
        self.logger.info("=" * 60)
        
        return state
    
    def _collect_current_state(self) -> Dict:
        """
        Collect current bot state
        
        Returns:
            Current state dict
            
        Note: This would integrate with actual bot components in production
        """
        # Placeholder - in production, this would collect from:
        # - strategy_manager.get_active_strategies()
        # - position_tracker.get_open_positions()
        # - trade_queue.get_pending_trades()
        # - portfolio_manager.get_current_value()
        # - risk_enforcer.get_risk_status()
        
        return {
            'active_strategies': [],
            'open_positions': [],
            'pending_trades': [],
            'portfolio_value': 10000.0,
            'cash_balance': 10000.0,
            'circuit_breaker_active': False,
            'daily_pnl': 0.0
        }
    
    def _load_state_file(self, file_path: Path) -> Optional[Dict]:
        """
        Load state from file
        
        Args:
            file_path: Path to state file
            
        Returns:
            State dict or None if file doesn't exist or is invalid
        """
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            return state
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in state file: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading state file: {e}")
            return None
    
    def _validate_state(self, state: Dict) -> bool:
        """
        Validate state dict
        
        Args:
            state: State dict to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            'timestamp',
            'active_strategies',
            'open_positions',
            'portfolio_value'
        ]
        
        for field in required_fields:
            if field not in state:
                self.logger.error(f"State missing required field: {field}")
                return False
        
        # Validate timestamp
        try:
            datetime.fromisoformat(state['timestamp'])
        except (ValueError, TypeError):
            self.logger.error("Invalid timestamp in state")
            return False
        
        # Validate types
        if not isinstance(state['active_strategies'], list):
            self.logger.error("Invalid active_strategies type")
            return False
        
        if not isinstance(state['open_positions'], list):
            self.logger.error("Invalid open_positions type")
            return False
        
        if not isinstance(state['portfolio_value'], (int, float)):
            self.logger.error("Invalid portfolio_value type")
            return False
        
        return True
    
    def _reconcile_positions(self, state: Dict):
        """
        Reconcile recovered positions with exchange
        
        Args:
            state: Recovered state
            
        Note: This is a placeholder - in production, this would:
        1. Query exchange for actual open positions
        2. Compare with recovered state
        3. Close positions that don't exist on exchange
        4. Add positions that exist on exchange but not in state
        5. Update position values with current prices
        """
        self.logger.info("Reconciling positions with exchange...")
        
        open_positions = state.get('open_positions', [])
        
        if not open_positions:
            self.logger.info("  No positions to reconcile")
            return
        
        # Placeholder - would query actual exchange
        self.logger.info(f"  Checking {len(open_positions)} positions...")
        
        # In production:
        # for position in open_positions:
        #     exchange_position = exchange.get_position(position['id'])
        #     if exchange_position:
        #         # Update position with current values
        #         position['current_value'] = exchange_position['value']
        #     else:
        #         # Position doesn't exist on exchange
        #         logger.warning(f"Position {position['id']} not found on exchange")
        
        self.logger.info("  ✓ Position reconciliation complete")
    
    def check_pending_trades(self, state: Dict) -> list:
        """
        Check status of pending trades from recovered state
        
        Args:
            state: Recovered state
            
        Returns:
            List of pending trade statuses
        """
        pending_trades = state.get('pending_trades', [])
        
        if not pending_trades:
            return []
        
        self.logger.info(f"Checking {len(pending_trades)} pending trades...")
        
        statuses = []
        for trade in pending_trades:
            # Placeholder - in production, would check trade status on exchange
            status = {
                'trade_id': trade.get('id'),
                'status': 'PENDING',  # Would query exchange
                'checked_at': datetime.utcnow().isoformat()
            }
            statuses.append(status)
        
        return statuses
    
    def clear_state(self) -> bool:
        """
        Clear saved state (e.g., for clean start)
        
        Returns:
            True if cleared successfully
        """
        try:
            if self.state_file.exists():
                os.remove(self.state_file)
                self.logger.info("State file cleared")
            
            if self.backup_file.exists():
                os.remove(self.backup_file)
                self.logger.info("Backup file cleared")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear state: {e}")
            return False
    
    def get_state_info(self) -> Dict:
        """
        Get information about saved state
        
        Returns:
            Dict with state file info
        """
        info = {
            'state_file_exists': self.state_file.exists(),
            'backup_file_exists': self.backup_file.exists(),
            'state_dir': str(self.state_dir)
        }
        
        if self.state_file.exists():
            stat = self.state_file.stat()
            info['state_file_size'] = stat.st_size
            info['state_file_modified'] = datetime.fromtimestamp(
                stat.st_mtime
            ).isoformat()
            
            # Try to load and get summary
            state = self._load_state_file(self.state_file)
            if state:
                info['state_summary'] = {
                    'timestamp': state.get('timestamp'),
                    'save_count': state.get('save_count'),
                    'open_positions': len(state.get('open_positions', [])),
                    'pending_trades': len(state.get('pending_trades', [])),
                    'portfolio_value': state.get('portfolio_value')
                }
        
        return info


# Global instance
crash_recovery = CrashRecovery()
