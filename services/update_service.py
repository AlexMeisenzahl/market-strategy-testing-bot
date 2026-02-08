"""
Update Service for Market Strategy Testing Bot

Handles the complete update lifecycle with automatic rollback and safety checks.
"""

import os
import sys
import shutil
import subprocess
import uuid
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum

from logger import get_logger
from version_manager import VersionManager
from services.process_manager import ProcessManager

logger = get_logger()


class UpdateStatus(Enum):
    """Update status enumeration"""
    IDLE = "idle"
    CHECKING = "checking"
    BACKING_UP = "backing_up"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    RESTARTING = "restarting"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    CANCELLED = "cancelled"


class UpdateService:
    """Manages the update process with comprehensive safety checks"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.version_manager = VersionManager(self.base_dir)
        self.process_manager = ProcessManager(self.base_dir)
        
        self.lock_file = self.base_dir / ".update_lock"
        self.backups_dir = self.base_dir / "backups"
        self.progress_file = self.base_dir / "logs" / "update_progress.json"
        
        # Ensure directories exist
        self.backups_dir.mkdir(exist_ok=True)
        self.progress_file.parent.mkdir(exist_ok=True)
        
        self.current_update_id = None
        self.current_backup = None
    
    def _create_lock(self, update_id: str) -> bool:
        """Create update lock file"""
        try:
            lock_data = {
                'update_id': update_id,
                'start_time': datetime.now(timezone.utc).isoformat() + 'Z',
                'pid': os.getpid(),
                'step': UpdateStatus.CHECKING.value
            }
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            
            logger.log_info(f"Created update lock: {update_id}")
            return True
            
        except Exception as e:
            logger.log_error(f"Error creating lock file: {e}")
            return False
    
    def _remove_lock(self) -> bool:
        """Remove update lock file"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.log_info("Removed update lock")
            return True
        except Exception as e:
            logger.log_error(f"Error removing lock file: {e}")
            return False
    
    def _is_locked(self) -> Tuple[bool, Optional[Dict]]:
        """
        Check if update is locked
        
        Returns:
            (is_locked, lock_data) tuple
        """
        try:
            if not self.lock_file.exists():
                return False, None
            
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            
            # Check if lock is stale (older than 30 minutes)
            # Handle both 'Z' and '+00:00' timezone formats for proper parsing
            start_time_str = lock_data['start_time'].replace('Z', '+00:00')
            start_time = datetime.fromisoformat(start_time_str)
            age = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            if age > 1800:  # 30 minutes
                logger.log_warning(f"Found stale lock (age: {age}s), considering it invalid")
                return False, lock_data
            
            return True, lock_data
            
        except Exception as e:
            logger.log_error(f"Error checking lock file: {e}")
            return False, None
    
    def unlock_update(self, force: bool = False) -> bool:
        """
        Unlock update system
        
        Args:
            force: Force unlock even if recent
            
        Returns:
            True if unlocked successfully
        """
        is_locked, lock_data = self._is_locked()
        
        if not is_locked and not self.lock_file.exists():
            logger.log_info("No lock file found")
            return True
        
        if force or not is_locked:
            return self._remove_lock()
        
        logger.log_warning("Lock is recent and update may be in progress")
        return False
    
    def _update_progress(self, status: UpdateStatus, progress: int, message: str, logs: List[str] = None):
        """Update progress file"""
        try:
            progress_data = {
                'update_id': self.current_update_id,
                'status': status.value,
                'progress': progress,
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
                'logs': logs or []
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
            
            logger.log_info(f"Progress: {progress}% - {message}")
            
        except Exception as e:
            logger.log_error(f"Error updating progress: {e}")
    
    def get_progress(self) -> Optional[Dict]:
        """Get current update progress"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.log_error(f"Error reading progress: {e}")
            return None
    
    def pre_flight_checks(self) -> Tuple[bool, List[Dict]]:
        """
        Run pre-flight checks before update
        
        Returns:
            (all_passed, checks_list) tuple
        """
        checks = []
        all_passed = True
        
        # Check 1: Git installed
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True, timeout=5)
            checks.append({'name': 'Git installed', 'passed': True, 'message': 'Git is available'})
        except Exception as e:
            checks.append({'name': 'Git installed', 'passed': False, 'message': f'Git not found: {e}'})
            all_passed = False
        
        # Check 2: Internet connection
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            checks.append({'name': 'Internet connection', 'passed': True, 'message': 'Internet is accessible'})
        except Exception:
            checks.append({'name': 'Internet connection', 'passed': False, 'message': 'No internet connection'})
            all_passed = False
        
        # Check 3: GitHub accessible
        try:
            import requests
            response = requests.get('https://api.github.com', timeout=5)
            if response.status_code == 200:
                checks.append({'name': 'GitHub accessible', 'passed': True, 'message': 'GitHub API is reachable'})
            else:
                checks.append({'name': 'GitHub accessible', 'passed': False, 'message': f'GitHub returned {response.status_code}'})
                all_passed = False
        except Exception as e:
            checks.append({'name': 'GitHub accessible', 'passed': False, 'message': f'Cannot reach GitHub: {e}'})
            all_passed = False
        
        # Check 4: Write permissions
        try:
            test_file = self.base_dir / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            checks.append({'name': 'Write permissions', 'passed': True, 'message': 'Have write access'})
        except Exception as e:
            checks.append({'name': 'Write permissions', 'passed': False, 'message': f'No write access: {e}'})
            all_passed = False
        
        # Check 5: Disk space (need at least 1GB)
        try:
            import shutil
            stat = shutil.disk_usage(self.base_dir)
            free_gb = stat.free / (1024**3)
            if free_gb >= 1.0:
                checks.append({'name': 'Disk space', 'passed': True, 'message': f'{free_gb:.1f}GB free'})
            else:
                checks.append({'name': 'Disk space', 'passed': False, 'message': f'Only {free_gb:.1f}GB free (need 1GB)'})
                all_passed = False
        except Exception as e:
            checks.append({'name': 'Disk space', 'passed': False, 'message': f'Cannot check disk space: {e}'})
        
        # Check 6: No other updates running
        is_locked, lock_data = self._is_locked()
        if is_locked:
            checks.append({'name': 'No concurrent updates', 'passed': False, 'message': 'Another update is in progress'})
            all_passed = False
        else:
            checks.append({'name': 'No concurrent updates', 'passed': True, 'message': 'No other updates running'})
        
        # Check 7: Git repository status
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                if result.stdout.strip():
                    checks.append({'name': 'Git status', 'passed': True, 'message': 'Local changes will be stashed'})
                else:
                    checks.append({'name': 'Git status', 'passed': True, 'message': 'Working directory clean'})
            else:
                checks.append({'name': 'Git status', 'passed': False, 'message': 'Not a git repository'})
                all_passed = False
        except Exception as e:
            checks.append({'name': 'Git status', 'passed': False, 'message': f'Git error: {e}'})
            all_passed = False
        
        return all_passed, checks
    
    def create_backup(self) -> Tuple[bool, Optional[str]]:
        """
        Create full backup of current system
        
        Returns:
            (success, backup_name) tuple
        """
        try:
            # Generate backup name
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backups_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            logger.log_info(f"Creating backup: {backup_name}")
            
            # Backup Python files
            for py_file in self.base_dir.glob("*.py"):
                shutil.copy2(py_file, backup_path)
            
            # Backup VERSION file
            if (self.base_dir / "VERSION").exists():
                shutil.copy2(self.base_dir / "VERSION", backup_path)
            
            # Backup config
            if (self.base_dir / "config.yaml").exists():
                shutil.copy2(self.base_dir / "config.yaml", backup_path)
            
            # Backup services directory
            if (self.base_dir / "services").exists():
                shutil.copytree(
                    self.base_dir / "services",
                    backup_path / "services",
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc')
                )
            
            # Backup dashboard directory
            if (self.base_dir / "dashboard").exists():
                shutil.copytree(
                    self.base_dir / "dashboard",
                    backup_path / "dashboard",
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc')
                )
            
            # Backup database files
            if (self.base_dir / "database").exists():
                shutil.copytree(
                    self.base_dir / "database",
                    backup_path / "database",
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc')
                )
            
            # Backup state directory
            if (self.base_dir / "state").exists():
                shutil.copytree(self.base_dir / "state", backup_path / "state")
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            logger.log_info(f"Backup created: {backup_name} ({size_mb:.1f}MB)")
            
            # Cleanup old backups (keep 5 most recent)
            self._cleanup_old_backups(keep=5)
            
            return True, backup_name
            
        except Exception as e:
            logger.log_error(f"Error creating backup: {e}")
            return False, None
    
    def _cleanup_old_backups(self, keep: int = 5):
        """Remove old backups, keeping only the most recent ones"""
        try:
            backups = sorted(
                [d for d in self.backups_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for old_backup in backups[keep:]:
                logger.log_info(f"Removing old backup: {old_backup.name}")
                shutil.rmtree(old_backup)
                
        except Exception as e:
            logger.log_error(f"Error cleaning up backups: {e}")
    
    def download_update(self) -> Tuple[bool, List[str]]:
        """
        Download update from GitHub
        
        Returns:
            (success, changed_files) tuple
        """
        try:
            logger.log_info("Downloading update from GitHub...")
            changed_files = []
            
            # Stash local changes if any
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                logger.log_info("Stashing local changes...")
                subprocess.run(
                    ['git', 'stash', 'save', 'auto-update-stash'],
                    cwd=self.base_dir,
                    check=True,
                    timeout=30
                )
            
            # Fetch from origin
            subprocess.run(
                ['git', 'fetch', 'origin', 'main'],
                cwd=self.base_dir,
                check=True,
                capture_output=True,
                timeout=60
            )
            
            # Get list of files that will change
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD', 'origin/main'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            changed_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            
            # Pull changes
            subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=self.base_dir,
                check=True,
                capture_output=True,
                timeout=60
            )
            
            logger.log_info(f"Downloaded update: {len(changed_files)} files changed")
            return True, changed_files
            
        except Exception as e:
            logger.log_error(f"Error downloading update: {e}")
            return False, []
    
    def install_dependencies(self) -> Tuple[bool, str]:
        """
        Install/update dependencies
        
        Returns:
            (success, message) tuple
        """
        try:
            logger.log_info("Installing dependencies...")
            
            # Check if requirements.txt exists
            requirements_file = self.base_dir / "requirements.txt"
            if not requirements_file.exists():
                return True, "No requirements.txt found"
            
            # Install requirements
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.log_info("Dependencies installed successfully")
                return True, "Dependencies installed"
            else:
                logger.log_error(f"Dependency installation failed: {result.stderr}")
                return False, f"Installation error: {result.stderr[:200]}"
                
        except Exception as e:
            logger.log_error(f"Error installing dependencies: {e}")
            return False, str(e)
    
    def health_check(self) -> Tuple[bool, List[Dict]]:
        """
        Run post-update health checks
        
        Returns:
            (all_passed, checks_list) tuple
        """
        checks = []
        all_passed = True
        
        # Give processes time to start
        time.sleep(5)
        
        # Check 1: Bot process running
        if self.process_manager.is_bot_running():
            checks.append({'name': 'Bot process', 'passed': True, 'message': 'Bot is running'})
        else:
            checks.append({'name': 'Bot process', 'passed': False, 'message': 'Bot not running'})
            all_passed = False
        
        # Check 2: Dashboard process running
        if self.process_manager.is_dashboard_running():
            checks.append({'name': 'Dashboard process', 'passed': True, 'message': 'Dashboard is running'})
        else:
            checks.append({'name': 'Dashboard process', 'passed': False, 'message': 'Dashboard not running'})
            all_passed = False
        
        # Check 3: Test imports
        try:
            import bot
            import dashboard.app
            checks.append({'name': 'Module imports', 'passed': True, 'message': 'All modules importable'})
        except Exception as e:
            checks.append({'name': 'Module imports', 'passed': False, 'message': f'Import error: {e}'})
            all_passed = False
        
        # Check 4: Config loads
        try:
            import yaml
            config_file = self.base_dir / "config.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    yaml.safe_load(f)
                checks.append({'name': 'Config file', 'passed': True, 'message': 'Config loads correctly'})
            else:
                checks.append({'name': 'Config file', 'passed': True, 'message': 'No config file (OK)'})
        except Exception as e:
            checks.append({'name': 'Config file', 'passed': False, 'message': f'Config error: {e}'})
            all_passed = False
        
        return all_passed, checks
    
    def rollback(self, backup_name: str = None) -> bool:
        """
        Rollback to previous version
        
        Args:
            backup_name: Specific backup to restore, or use latest
            
        Returns:
            True if rollback successful
        """
        try:
            logger.log_warning(f"Starting rollback...")
            
            # Determine backup to use
            if backup_name is None:
                backup_name = self.version_manager.get_latest_backup()
            
            if backup_name is None:
                logger.log_error("No backup available for rollback")
                return False
            
            backup_path = self.backups_dir / backup_name
            if not backup_path.exists():
                logger.log_error(f"Backup not found: {backup_name}")
                return False
            
            logger.log_info(f"Rolling back to backup: {backup_name}")
            
            # Stop processes
            self.process_manager.stop_bot()
            self.process_manager.stop_dashboard()
            time.sleep(2)
            
            # Restore files
            logger.log_info("Restoring files from backup...")
            for item in backup_path.iterdir():
                dest = self.base_dir / item.name
                
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            
            # Restart processes
            logger.log_info("Restarting processes...")
            self.process_manager.start_bot()
            self.process_manager.start_dashboard()
            
            # Verify
            time.sleep(5)
            if self.process_manager.is_bot_running() and self.process_manager.is_dashboard_running():
                logger.log_info("Rollback completed successfully")
                return True
            else:
                logger.log_error("Processes failed to start after rollback")
                return False
                
        except Exception as e:
            logger.log_error(f"Error during rollback: {e}")
            return False
    
    def perform_update(self) -> Dict:
        """
        Perform complete update process with automatic rollback on failure
        
        Returns:
            Result dict with status and details
        """
        start_time = time.time()
        logs = []
        update_id = str(uuid.uuid4())
        self.current_update_id = update_id
        
        try:
            # Create lock
            if not self._create_lock(update_id):
                return {'success': False, 'error': 'Failed to create update lock'}
            
            logs.append("Update started")
            self._update_progress(UpdateStatus.CHECKING, 5, "Running pre-flight checks...", logs)
            
            # Pre-flight checks
            checks_passed, checks = self.pre_flight_checks()
            if not checks_passed:
                failed_checks = [c['name'] for c in checks if not c['passed']]
                error_msg = f"Pre-flight checks failed: {', '.join(failed_checks)}"
                logs.append(f"❌ {error_msg}")
                self._update_progress(UpdateStatus.FAILED, 0, error_msg, logs)
                self._remove_lock()
                return {'success': False, 'error': error_msg, 'checks': checks}
            
            logs.append("✅ Pre-flight checks passed")
            self._update_progress(UpdateStatus.BACKING_UP, 15, "Creating backup...", logs)
            
            # Create backup
            backup_success, backup_name = self.create_backup()
            if not backup_success:
                error_msg = "Failed to create backup"
                logs.append(f"❌ {error_msg}")
                self._update_progress(UpdateStatus.FAILED, 0, error_msg, logs)
                self._remove_lock()
                return {'success': False, 'error': error_msg}
            
            self.current_backup = backup_name
            logs.append(f"✅ Backup created: {backup_name}")
            self._update_progress(UpdateStatus.DOWNLOADING, 30, "Downloading from GitHub...", logs)
            
            # Download update
            download_success, changed_files = self.download_update()
            if not download_success:
                error_msg = "Failed to download update"
                logs.append(f"❌ {error_msg}")
                logs.append("🔄 Rolling back...")
                self._update_progress(UpdateStatus.ROLLING_BACK, 0, "Rolling back...", logs)
                self.rollback(backup_name)
                self._remove_lock()
                return {'success': False, 'error': error_msg, 'rolled_back': True}
            
            logs.append(f"✅ Downloaded {len(changed_files)} changed files")
            self._update_progress(UpdateStatus.INSTALLING, 50, "Installing dependencies...", logs)
            
            # Install dependencies
            install_success, install_msg = self.install_dependencies()
            if not install_success:
                error_msg = f"Failed to install dependencies: {install_msg}"
                logs.append(f"❌ {error_msg}")
                logs.append("🔄 Rolling back...")
                self._update_progress(UpdateStatus.ROLLING_BACK, 0, "Rolling back...", logs)
                self.rollback(backup_name)
                self._remove_lock()
                return {'success': False, 'error': error_msg, 'rolled_back': True}
            
            logs.append(f"✅ {install_msg}")
            self._update_progress(UpdateStatus.RESTARTING, 70, "Restarting processes...", logs)
            
            # Restart bot
            bot_success, bot_pid = self.process_manager.restart_bot()
            if not bot_success:
                error_msg = "Failed to restart bot"
                logs.append(f"❌ {error_msg}")
                logs.append("🔄 Rolling back...")
                self._update_progress(UpdateStatus.ROLLING_BACK, 0, "Rolling back...", logs)
                self.rollback(backup_name)
                self._remove_lock()
                return {'success': False, 'error': error_msg, 'rolled_back': True}
            
            logs.append(f"✅ Bot restarted (PID: {bot_pid})")
            
            # Restart dashboard
            dashboard_success, dashboard_pid = self.process_manager.restart_dashboard()
            if not dashboard_success:
                error_msg = "Failed to restart dashboard"
                logs.append(f"❌ {error_msg}")
                logs.append("🔄 Rolling back...")
                self._update_progress(UpdateStatus.ROLLING_BACK, 0, "Rolling back...", logs)
                self.rollback(backup_name)
                self._remove_lock()
                return {'success': False, 'error': error_msg, 'rolled_back': True}
            
            logs.append(f"✅ Dashboard restarted (PID: {dashboard_pid})")
            self._update_progress(UpdateStatus.VERIFYING, 85, "Running health checks...", logs)
            
            # Health check
            health_passed, health_checks = self.health_check()
            if not health_passed:
                failed_checks = [c['name'] for c in health_checks if not c['passed']]
                error_msg = f"Health checks failed: {', '.join(failed_checks)}"
                logs.append(f"❌ {error_msg}")
                logs.append("🔄 Rolling back...")
                self._update_progress(UpdateStatus.ROLLING_BACK, 0, "Rolling back...", logs)
                self.rollback(backup_name)
                self._remove_lock()
                return {'success': False, 'error': error_msg, 'rolled_back': True, 'health_checks': health_checks}
            
            logs.append("✅ Health checks passed")
            
            # Update VERSION file
            update_info = self.version_manager.check_for_updates()
            if update_info['available']:
                self.version_manager.set_current_version(update_info['latest'])
            
            # Record update in history
            duration = int(time.time() - start_time)
            record = {
                'update_id': update_id,
                'date': datetime.now(timezone.utc).isoformat() + 'Z',
                'from_version': update_info.get('current', 'unknown'),
                'to_version': update_info.get('latest', 'unknown'),
                'status': 'success',
                'duration_seconds': duration,
                'backup': backup_name,
                'changes': update_info.get('changes', []),
                'rollback_available': True
            }
            self.version_manager.add_update_record(record)
            
            logs.append("✅ Update completed successfully")
            self._update_progress(UpdateStatus.COMPLETE, 100, "Update completed!", logs)
            self._remove_lock()
            
            return {
                'success': True,
                'update_id': update_id,
                'duration_seconds': duration,
                'backup': backup_name,
                'changed_files': len(changed_files),
                'logs': logs
            }
            
        except Exception as e:
            logger.log_error(f"Unexpected error during update: {e}")
            logs.append(f"❌ Unexpected error: {e}")
            
            # Attempt rollback
            if self.current_backup:
                logs.append("🔄 Rolling back...")
                self._update_progress(UpdateStatus.ROLLING_BACK, 0, "Rolling back...", logs)
                rollback_success = self.rollback(self.current_backup)
                self._remove_lock()
                return {
                    'success': False,
                    'error': str(e),
                    'rolled_back': rollback_success,
                    'logs': logs
                }
            else:
                self._remove_lock()
                return {'success': False, 'error': str(e), 'logs': logs}
