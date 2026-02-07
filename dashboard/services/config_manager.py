"""
Config Manager Service

Manages reading and writing configuration files (config.yaml)
with proper validation and backup capabilities.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import shutil


class ConfigManager:
    """Manage configuration file reading and writing"""
    
    def __init__(self, config_path: Path):
        """
        Initialize config manager
        
        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)
        self.backup_dir = self.config_path.parent / 'config_backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings from config file
        
        Returns:
            Dictionary with all configuration
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config if config else {}
        except FileNotFoundError:
            return self._get_default_config()
        except Exception as e:
            raise Exception(f"Error reading config: {str(e)}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'paper_trading': True,
            'kill_switch': False,
            'notifications': {
                'email': {
                    'enabled': False,
                    'from_email': '',
                    'to_email': '',
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'password': ''
                },
                'desktop': {
                    'enabled': True
                },
                'telegram': {
                    'enabled': False,
                    'bot_token': '',
                    'chat_id': ''
                }
            },
            'strategies': {
                'rsi_scalp': {
                    'enabled': True,
                    'period': 14,
                    'oversold': 30,
                    'overbought': 70
                },
                'macd_trend': {
                    'enabled': True,
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9
                }
            }
        }
    
    def update_notification_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update notification settings
        
        Args:
            settings: New notification settings
        """
        # Create backup first
        self._create_backup()
        
        # Load current config
        config = self.get_all_settings()
        
        # Update notifications section
        if 'notifications' not in config:
            config['notifications'] = {}
        
        # Update each notification type
        for notif_type, notif_config in settings.items():
            if notif_type in ['email', 'desktop', 'telegram']:
                config['notifications'][notif_type] = notif_config
        
        # Save config
        self._save_config(config)
    
    def update_strategy_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update strategy settings
        
        Args:
            settings: New strategy settings
        """
        # Create backup first
        self._create_backup()
        
        # Load current config
        config = self.get_all_settings()
        
        # Update strategies section
        if 'strategies' not in config:
            config['strategies'] = {}
        
        config['strategies'].update(settings)
        
        # Save config
        self._save_config(config)
    
    def update_setting(self, key: str, value: Any) -> None:
        """
        Update a single setting
        
        Args:
            key: Setting key (can use dot notation like 'notifications.email.enabled')
            value: New value
        """
        # Create backup first
        self._create_backup()
        
        # Load current config
        config = self.get_all_settings()
        
        # Handle nested keys
        keys = key.split('.')
        current = config
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save config
        self._save_config(config)
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file
        
        Args:
            config: Configuration dictionary
        """
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise Exception(f"Error saving config: {str(e)}")
    
    def _create_backup(self) -> None:
        """Create backup of current config file"""
        if self.config_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'config_{timestamp}.yaml'
            shutil.copy2(self.config_path, backup_path)
            
            # Keep only last 10 backups
            backups = sorted(self.backup_dir.glob('config_*.yaml'))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
    
    def restore_backup(self, backup_name: str) -> None:
        """
        Restore from a backup file
        
        Args:
            backup_name: Name of backup file to restore
        """
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            shutil.copy2(backup_path, self.config_path)
        else:
            raise FileNotFoundError(f"Backup not found: {backup_name}")
    
    def list_backups(self) -> list:
        """
        List available backups
        
        Returns:
            List of backup filenames
        """
        backups = sorted(self.backup_dir.glob('config_*.yaml'), reverse=True)
        return [b.name for b in backups]
