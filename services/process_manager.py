"""
Process Manager for Market Strategy Testing Bot

Manages bot and dashboard process lifecycle.
"""

import os
import signal
import subprocess
import time
import psutil
from pathlib import Path
from typing import Optional, Tuple
from logger import get_logger

logger = get_logger()


class ProcessManager:
    """Manages bot and dashboard processes"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.bot_pid_file = self.base_dir / ".bot.pid"
        self.dashboard_pid_file = self.base_dir / ".dashboard.pid"
    
    def _read_pid(self, pid_file: Path) -> Optional[int]:
        """Read PID from file"""
        try:
            if pid_file.exists():
                pid = int(pid_file.read_text().strip())
                return pid
            return None
        except Exception as e:
            logger.log_error(f"Error reading PID file {pid_file}: {e}")
            return None
    
    def _write_pid(self, pid_file: Path, pid: int) -> bool:
        """Write PID to file"""
        try:
            pid_file.write_text(str(pid))
            return True
        except Exception as e:
            logger.log_error(f"Error writing PID file {pid_file}: {e}")
            return False
    
    def _remove_pid(self, pid_file: Path) -> bool:
        """Remove PID file"""
        try:
            if pid_file.exists():
                pid_file.unlink()
            return True
        except Exception as e:
            logger.log_error(f"Error removing PID file {pid_file}: {e}")
            return False
    
    def _is_process_running(self, pid: int, process_name: str = None) -> bool:
        """Check if process with given PID is running"""
        try:
            process = psutil.Process(pid)
            
            # Check if process is still alive
            if not process.is_running():
                return False
            
            # Optionally verify process name
            if process_name:
                cmdline = ' '.join(process.cmdline())
                if process_name not in cmdline:
                    logger.log_warning(f"PID {pid} is running but not {process_name}")
                    return False
            
            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            logger.log_error(f"Error checking process {pid}: {e}")
            return False
    
    def get_bot_pid(self) -> Optional[int]:
        """Get bot process ID"""
        return self._read_pid(self.bot_pid_file)
    
    def get_dashboard_pid(self) -> Optional[int]:
        """Get dashboard process ID"""
        return self._read_pid(self.dashboard_pid_file)
    
    def is_bot_running(self) -> bool:
        """Check if bot process is running"""
        pid = self.get_bot_pid()
        if pid is None:
            return False
        return self._is_process_running(pid, "bot.py")
    
    def is_dashboard_running(self) -> bool:
        """Check if dashboard process is running"""
        pid = self.get_dashboard_pid()
        if pid is None:
            return False
        return self._is_process_running(pid, "dashboard")
    
    def stop_process_gracefully(self, pid: int, timeout: int = 10) -> bool:
        """
        Stop process gracefully with SIGTERM, then SIGKILL if needed
        
        Args:
            pid: Process ID to stop
            timeout: Seconds to wait before force kill
            
        Returns:
            True if process stopped successfully
        """
        try:
            if not self._is_process_running(pid):
                logger.log_info(f"Process {pid} is not running")
                return True
            
            process = psutil.Process(pid)
            
            # Try graceful shutdown first
            logger.log_info(f"Sending SIGTERM to process {pid}")
            process.terminate()
            
            # Wait for process to exit
            try:
                process.wait(timeout=timeout)
                logger.log_info(f"Process {pid} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                logger.log_warning(f"Process {pid} did not terminate, forcing kill")
                process.kill()
                process.wait(timeout=5)
                logger.log_info(f"Process {pid} force killed")
                return True
                
        except psutil.NoSuchProcess:
            logger.log_info(f"Process {pid} already stopped")
            return True
        except Exception as e:
            logger.log_error(f"Error stopping process {pid}: {e}")
            return False
    
    def stop_bot(self, timeout: int = 10) -> bool:
        """Stop bot process gracefully"""
        pid = self.get_bot_pid()
        if pid is None:
            logger.log_info("No bot PID file found")
            return True
        
        success = self.stop_process_gracefully(pid, timeout)
        if success:
            self._remove_pid(self.bot_pid_file)
        return success
    
    def stop_dashboard(self, timeout: int = 10) -> bool:
        """Stop dashboard process gracefully"""
        pid = self.get_dashboard_pid()
        if pid is None:
            logger.log_info("No dashboard PID file found")
            return True
        
        success = self.stop_process_gracefully(pid, timeout)
        if success:
            self._remove_pid(self.dashboard_pid_file)
        return success
    
    def start_bot(self) -> Tuple[bool, Optional[int]]:
        """
        Start bot process
        
        Returns:
            (success, pid) tuple
        """
        try:
            # Check if already running
            if self.is_bot_running():
                logger.log_warning("Bot is already running")
                return False, self.get_bot_pid()
            
            # Start bot process
            logger.log_info("Starting bot process...")
            process = subprocess.Popen(
                ["python3", "bot.py"],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            pid = process.pid
            
            # Wait a moment to ensure it started
            time.sleep(2)
            
            if self._is_process_running(pid, "bot.py"):
                self._write_pid(self.bot_pid_file, pid)
                logger.log_info(f"Bot started with PID {pid}")
                return True, pid
            else:
                logger.log_error("Bot process failed to start")
                return False, None
                
        except Exception as e:
            logger.log_error(f"Error starting bot: {e}")
            return False, None
    
    def start_dashboard(self) -> Tuple[bool, Optional[int]]:
        """
        Start dashboard process
        
        Returns:
            (success, pid) tuple
        """
        try:
            # Check if already running
            if self.is_dashboard_running():
                logger.log_warning("Dashboard is already running")
                return False, self.get_dashboard_pid()
            
            # Start dashboard process
            logger.log_info("Starting dashboard process...")
            process = subprocess.Popen(
                ["python3", "start_dashboard.py"],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            pid = process.pid
            
            # Wait a moment to ensure it started
            time.sleep(2)
            
            if self._is_process_running(pid):
                self._write_pid(self.dashboard_pid_file, pid)
                logger.log_info(f"Dashboard started with PID {pid}")
                return True, pid
            else:
                logger.log_error("Dashboard process failed to start")
                return False, None
                
        except Exception as e:
            logger.log_error(f"Error starting dashboard: {e}")
            return False, None
    
    def restart_bot(self) -> Tuple[bool, Optional[int]]:
        """Restart bot process"""
        logger.log_info("Restarting bot...")
        
        # Stop existing process
        self.stop_bot()
        
        # Wait a moment
        time.sleep(2)
        
        # Start new process
        return self.start_bot()
    
    def restart_dashboard(self) -> Tuple[bool, Optional[int]]:
        """Restart dashboard process"""
        logger.log_info("Restarting dashboard...")
        
        # Stop existing process
        self.stop_dashboard()
        
        # Wait a moment
        time.sleep(2)
        
        # Start new process
        return self.start_dashboard()
    
    def force_stop_all(self) -> bool:
        """Force stop all bot and dashboard processes"""
        logger.log_warning("Force stopping all processes...")
        
        success = True
        
        # Try to stop via PID files first
        success &= self.stop_bot(timeout=5)
        success &= self.stop_dashboard(timeout=5)
        
        # Also find and kill any remaining processes
        try:
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(process.cmdline())
                    if 'bot.py' in cmdline or 'start_dashboard.py' in cmdline:
                        logger.log_info(f"Force killing process {process.pid}: {cmdline}")
                        process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.log_error(f"Error during force stop: {e}")
            success = False
        
        return success
    
    def get_process_info(self, pid: int) -> Optional[dict]:
        """Get detailed process information"""
        try:
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'create_time': process.create_time(),
                'cmdline': ' '.join(process.cmdline())
            }
        except Exception as e:
            logger.log_error(f"Error getting process info for {pid}: {e}")
            return None
