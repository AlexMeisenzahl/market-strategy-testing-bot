"""
Settings Manager

Manages bot settings persistence using YAML configuration files.
Provides load, save, apply, and reset functionality.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import shutil


logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Settings manager for bot configuration persistence
    
    Manages loading, saving, and applying settings to the running bot.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize settings manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.example_path = Path("config.example.yaml")
        self.backup_dir = Path("data/config_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure config file exists
        if not self.config_path.exists() and self.example_path.exists():
            shutil.copy(self.example_path, self.config_path)
            logger.info("Created config.yaml from config.example.yaml")

    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from configuration file
        
        Returns:
            Settings dictionary
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return {}
            
            with open(self.config_path, "r") as f:
                settings = yaml.safe_load(f)
            
            logger.info("Settings loaded successfully")
            return settings or {}
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return {}

    def save_settings(self, settings: Dict[str, Any], create_backup: bool = True) -> bool:
        """
        Save settings to configuration file
        
        Args:
            settings: Settings dictionary to save
            create_backup: Whether to create a backup before saving
            
        Returns:
            True if saved successfully
        """
        try:
            # Create backup if requested
            if create_backup and self.config_path.exists():
                self._create_backup()
            
            # Save settings
            with open(self.config_path, "w") as f:
                yaml.dump(settings, f, default_flow_style=False, sort_keys=False)
            
            logger.info("Settings saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def update_settings(self, updates: Dict[str, Any]) -> bool:
        """
        Update specific settings without overwriting entire config
        
        Args:
            updates: Dictionary of settings to update
            
        Returns:
            True if updated successfully
        """
        try:
            # Load current settings
            current_settings = self.load_settings()
            
            # Apply updates recursively
            updated_settings = self._deep_update(current_settings, updates)
            
            # Save updated settings
            return self.save_settings(updated_settings)
            
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reset settings to defaults from example config
        
        Returns:
            True if reset successfully
        """
        try:
            if not self.example_path.exists():
                logger.error("Example config file not found")
                return False
            
            # Create backup
            if self.config_path.exists():
                self._create_backup()
            
            # Copy example to config
            shutil.copy(self.example_path, self.config_path)
            
            logger.info("Settings reset to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific setting by dot-separated key path
        
        Args:
            key_path: Dot-separated path to setting (e.g., "telegram.enabled")
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        try:
            settings = self.load_settings()
            
            # Navigate through nested keys
            keys = key_path.split(".")
            value = settings
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get setting {key_path}: {e}")
            return default

    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        Set a specific setting by dot-separated key path
        
        Args:
            key_path: Dot-separated path to setting (e.g., "telegram.enabled")
            value: Value to set
            
        Returns:
            True if set successfully
        """
        try:
            settings = self.load_settings()
            
            # Navigate through nested keys and create if needed
            keys = key_path.split(".")
            current = settings
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set final value
            current[keys[-1]] = value
            
            return self.save_settings(settings)
            
        except Exception as e:
            logger.error(f"Failed to set setting {key_path}: {e}")
            return False

    def export_settings(self, export_path: Optional[str] = None) -> Optional[str]:
        """
        Export settings to a file
        
        Args:
            export_path: Path to export to (default: timestamped backup)
            
        Returns:
            Path to exported file or None if failed
        """
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = self.backup_dir / f"config_export_{timestamp}.yaml"
            else:
                export_path = Path(export_path)
            
            # Load current settings
            settings = self.load_settings()
            
            # Save to export path
            with open(export_path, "w") as f:
                yaml.dump(settings, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Settings exported to {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return None

    def import_settings(self, import_path: str) -> bool:
        """
        Import settings from a file
        
        Args:
            import_path: Path to import from
            
        Returns:
            True if imported successfully
        """
        try:
            import_path = Path(import_path)
            
            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return False
            
            # Load settings from import file
            with open(import_path, "r") as f:
                imported_settings = yaml.safe_load(f)
            
            if not imported_settings:
                logger.error("Import file is empty or invalid")
                return False
            
            # Save imported settings
            return self.save_settings(imported_settings)
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available configuration backups
        
        Returns:
            List of backup info dictionaries
        """
        try:
            backups = []
            
            for backup_file in sorted(self.backup_dir.glob("config_backup_*.yaml"), reverse=True):
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                })
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def restore_backup(self, backup_filename: str) -> bool:
        """
        Restore settings from a backup
        
        Args:
            backup_filename: Backup filename to restore
            
        Returns:
            True if restored successfully
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_filename}")
                return False
            
            # Create a backup before restoring
            if self.config_path.exists():
                self._create_backup()
            
            # Copy backup to config
            shutil.copy(backup_path, self.config_path)
            
            logger.info(f"Settings restored from {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def _create_backup(self):
        """Create a backup of current configuration"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"config_backup_{timestamp}.yaml"
            
            shutil.copy(self.config_path, backup_path)
            logger.debug(f"Created config backup: {backup_path.name}")
            
            # Keep only last 10 backups
            self._cleanup_old_backups(keep=10)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self, keep: int = 10):
        """
        Clean up old backups, keeping only the most recent ones
        
        Args:
            keep: Number of backups to keep
        """
        try:
            backups = sorted(
                self.backup_dir.glob("config_backup_*.yaml"),
                key=lambda p: p.stat().st_ctime,
                reverse=True,
            )
            
            # Delete old backups
            for backup in backups[keep:]:
                backup.unlink()
                logger.debug(f"Deleted old backup: {backup.name}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def _deep_update(self, base: Dict, updates: Dict) -> Dict:
        """
        Deep update a dictionary with another dictionary
        
        Args:
            base: Base dictionary
            updates: Updates to apply
            
        Returns:
            Updated dictionary
        """
        result = base.copy()
        
        for key, value in updates.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._deep_update(result[key], value)
            else:
                result[key] = value
        
        return result

    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate settings structure and values
        
        Args:
            settings: Settings to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check required top-level keys
        required_keys = ["paper_trading", "strategies"]
        for key in required_keys:
            if key not in settings:
                errors.append(f"Missing required key: {key}")
        
        # Validate paper_trading mode
        if "paper_trading" in settings and not isinstance(settings["paper_trading"], bool):
            errors.append("paper_trading must be a boolean")
        
        # Validate strategies configuration
        if "strategies" in settings:
            strategies = settings["strategies"]
            if not isinstance(strategies, dict):
                errors.append("strategies must be a dictionary")
            elif "enabled" not in strategies:
                warnings.append("strategies.enabled not specified")
        
        # Check telegram configuration if enabled
        if settings.get("telegram", {}).get("enabled"):
            telegram = settings["telegram"]
            if not telegram.get("bot_token"):
                warnings.append("Telegram enabled but bot_token not set")
            if not telegram.get("chat_id"):
                warnings.append("Telegram enabled but chat_id not set")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# Global instance
settings_manager: Optional[SettingsManager] = None


def get_settings_manager(config_path: str = "config.yaml") -> SettingsManager:
    """
    Get or create global settings manager instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        SettingsManager instance
    """
    global settings_manager
    
    if settings_manager is None:
        settings_manager = SettingsManager(config_path)
    
    return settings_manager
