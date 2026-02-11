#!/usr/bin/env python3
"""
Personal desktop launcher for Market Strategy Bot.
Runs engine + dashboard as subprocesses, checks for updates, opens browser.
Single-user; no modifications to engine or dashboard code.
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from tkinter import Button, Frame, Label, messagebox, Tk

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
LAUNCHER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = LAUNCHER_DIR.parent
LOCK_FILE = PROJECT_ROOT / ".launcher.lock"
DEPS_HASH_FILE = LAUNCHER_DIR / ".deps_hash"
LOG_FILE = LAUNCHER_DIR / "launcher.log"
DASHBOARD_PORT = 5000
DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"
PORT_READY_TIMEOUT = 60
TERM_TIMEOUT = 10
KILL_TIMEOUT = 3
IS_WINDOWS = platform.system() == "Windows"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Reduce noise from third-party libs
    logging.getLogger("urllib3").setLevel(logging.WARNING)


log = logging.getLogger("launcher")

# ---------------------------------------------------------------------------
# Single instance (lock file)
# ---------------------------------------------------------------------------
def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if IS_WINDOWS:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.OpenProcess(0x100000, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError, AttributeError):
        return False


_lock_handle = None


def acquire_lock() -> bool:
    """Return True if we own the lock; False if another instance is running."""
    global _lock_handle
    # Stale lock: if lock file exists, check whether that PID is still running
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if _pid_exists(pid):
                return False
        except (ValueError, OSError):
            pass
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass
    try:
        try:
            import portalocker
            f = open(LOCK_FILE, "w")
            try:
                portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
            except portalocker.LockException:
                f.close()
                try:
                    LOCK_FILE.unlink(missing_ok=True)
                except OSError:
                    pass
                return False
            f.write(str(os.getpid()))
            f.flush()
            _lock_handle = f
            return True
        except ImportError:
            LOCK_FILE.write_text(str(os.getpid()))
            return True
    except OSError:
        return False


def release_lock() -> None:
    global _lock_handle
    try:
        if _lock_handle is not None:
            try:
                _lock_handle.close()
            except OSError:
                pass
            _lock_handle = None
        if LOCK_FILE.exists():
            try:
                if LOCK_FILE.read_text().strip() == str(os.getpid()):
                    LOCK_FILE.unlink()
            except OSError:
                pass
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Git update check (fetch + compare HEAD)
# ---------------------------------------------------------------------------
def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def check_for_updates() -> tuple[bool, str]:
    """
    Run git fetch and compare HEAD with remote. Return (behind, message).
    If git is not installed or not a repo, return (False, message).
    """
    if not shutil.which("git"):
        return False, "Git not installed; skipping update check."
    if not (PROJECT_ROOT / ".git").exists():
        return False, "Not a git repository."
    try:
        r = _run_git(PROJECT_ROOT, "fetch", "origin")
        if r.returncode != 0:
            return False, f"git fetch failed: {r.stderr or r.stdout or 'unknown'}"
        r = _run_git(PROJECT_ROOT, "rev-parse", "HEAD", "@{u}")
        if r.returncode != 0:
            return False, "Could not resolve HEAD or upstream."
        local, remote = r.stdout.strip().splitlines()[:2]
        if local == remote:
            return False, "Already up to date."
        return True, "Updates available. Use 'Check for Updates' then confirm to pull."
    except subprocess.TimeoutExpired:
        return False, "Update check timed out."
    except Exception as e:
        return False, str(e)


def do_pull() -> tuple[bool, str]:
    """Run git pull. Return (success, message)."""
    if not shutil.which("git"):
        return False, "Git not installed."
    try:
        r = _run_git(PROJECT_ROOT, "pull", "origin")
        if r.returncode != 0:
            return False, r.stderr or r.stdout or "git pull failed"
        return True, r.stdout or "Pull completed."
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Dependencies: hash of pyproject.toml, reinstall if changed
# ---------------------------------------------------------------------------
def _deps_changed() -> bool:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return False
    h = hashlib.sha256(pyproject.read_bytes()).hexdigest()
    if DEPS_HASH_FILE.exists() and DEPS_HASH_FILE.read_text().strip() == h:
        return False
    return True


def ensure_deps() -> tuple[bool, str]:
    """Run pip install -e \".[dashboard]\" if pyproject.toml hash changed. Return (success, message)."""
    if not _deps_changed():
        return True, "Dependencies unchanged."
    pyproject = PROJECT_ROOT / "pyproject.toml"
    h = hashlib.sha256(pyproject.read_bytes()).hexdigest()
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".[dashboard]"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r.returncode != 0:
            return False, r.stderr or r.stdout or "pip install failed"
        DEPS_HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEPS_HASH_FILE.write_text(h)
        return True, "Dependencies installed."
    except subprocess.TimeoutExpired:
        return False, "pip install timed out."
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Port ready check
# ---------------------------------------------------------------------------
def _can_connect_to_port(port: int) -> bool:
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False


def is_port_in_use(port: int) -> bool:
    """True if something is listening on the port (e.g. another dashboard)."""
    return _can_connect_to_port(port)


def wait_for_port(port: int, timeout: float = PORT_READY_TIMEOUT) -> bool:
    """Wait until something is accepting connections on port (e.g. dashboard ready)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _can_connect_to_port(port):
            return True
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------
def _popen_kw() -> dict:
    """Popen kwargs so child does not open a console window on Windows."""
    kw: dict = {"cwd": str(PROJECT_ROOT), "env": os.environ.copy()}
    if IS_WINDOWS:
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return kw


def start_engine() -> subprocess.Popen | None:
    try:
        p = subprocess.Popen(
            [sys.executable, "main.py"],
            **(_popen_kw() | {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}),
        )
        log.info("Engine started PID=%s", p.pid)
        return p
    except Exception as e:
        log.exception("Failed to start engine: %s", e)
        return None


def start_dashboard() -> subprocess.Popen | None:
    try:
        p = subprocess.Popen(
            [sys.executable, "dashboard/app.py"],
            **(_popen_kw() | {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}),
        )
        log.info("Dashboard started PID=%s", p.pid)
        return p
    except Exception as e:
        log.exception("Failed to start dashboard: %s", e)
        return None


def _terminate_process(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=TERM_TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait(timeout=KILL_TIMEOUT)
        except Exception:
            pass
    except Exception:
        pass


def stop_processes(engine: subprocess.Popen | None, dashboard: subprocess.Popen | None) -> None:
    # Dashboard first so port frees for future starts
    _terminate_process(dashboard)
    _terminate_process(engine)
    log.info("Processes stopped.")


# ---------------------------------------------------------------------------
# Open log / open URL
# ---------------------------------------------------------------------------
def open_log_file() -> None:
    path = LOG_FILE.resolve()
    if not path.exists():
        return
    try:
        if IS_WINDOWS:
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.run(["open" if platform.system() == "Darwin" else "xdg-open", str(path)], check=False)
    except Exception as e:
        log.warning("Could not open log file: %s", e)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class LauncherApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Market Strategy Bot — Launcher")
        self.root.minsize(320, 180)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.engine_proc: subprocess.Popen | None = None
        self.dashboard_proc: subprocess.Popen | None = None
        self._status = "Stopped"
        self._building_ui()

    def _status_set(self, value: str) -> None:
        self._status = value
        if hasattr(self, "status_label"):
            self.status_label.config(text=f"Status: {value}")

    def _building_ui(self) -> None:
        main = Frame(self.root, padx=12, pady=12)
        main.pack(fill="both", expand=True)
        self.status_label = Label(main, text="Status: Stopped", font=("", 10))
        self.status_label.pack(anchor="w", pady=(0, 8))
        btn_frame = Frame(main)
        btn_frame.pack(fill="x", pady=4)
        Button(btn_frame, text="Start", command=self._start, width=12).pack(side="left", padx=2)
        Button(btn_frame, text="Stop", command=self._stop, width=12).pack(side="left", padx=2)
        Button(btn_frame, text="Restart", command=self._restart, width=12).pack(side="left", padx=2)
        btn_frame2 = Frame(main)
        btn_frame2.pack(fill="x", pady=4)
        Button(btn_frame2, text="Check for Updates", command=self._check_updates_ui, width=18).pack(side="left", padx=2)
        Button(btn_frame2, text="Open Logs", command=open_log_file, width=12).pack(side="left", padx=2)

    def _on_close(self) -> None:
        self._stop()
        release_lock()
        self.root.destroy()

    def _start(self) -> None:
        if self.engine_proc is not None or self.dashboard_proc is not None:
            messagebox.showinfo("Launcher", "Services already running. Use Stop first.")
            return
        self._status_set("Starting...")
        self.root.update_idletasks()
        threading.Thread(target=self._start_worker, daemon=True).start()

    def _start_worker(self) -> None:
        def _cleanup_and_error(dialog_msg: str) -> None:
            stop_processes(self.engine_proc, self.dashboard_proc)
            self.engine_proc = None
            self.dashboard_proc = None
            self.root.after(0, lambda: self._status_set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Launcher", dialog_msg))

        try:
            if is_port_in_use(DASHBOARD_PORT):
                self.root.after(0, lambda: self._status_set("Error"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Launcher",
                    f"Port {DASHBOARD_PORT} is already in use. Stop the other process (e.g. another dashboard) and try again.",
                ))
                return
            ok, msg = ensure_deps()
            if not ok:
                self.root.after(0, lambda: self._status_set("Error"))
                self.root.after(0, lambda: messagebox.showerror("Dependencies", msg))
                return
            eng = start_engine()
            if eng is None:
                self.root.after(0, lambda: self._status_set("Error"))
                self.root.after(0, lambda: messagebox.showerror("Launcher", "Failed to start engine."))
                return
            self.engine_proc = eng
            dash = start_dashboard()
            if dash is None:
                stop_processes(self.engine_proc, None)
                self.engine_proc = None
                self.root.after(0, lambda: self._status_set("Error"))
                self.root.after(0, lambda: messagebox.showerror("Launcher", "Failed to start dashboard."))
                return
            self.dashboard_proc = dash
            if not wait_for_port(DASHBOARD_PORT):
                _cleanup_and_error("Dashboard port did not become ready in time.")
                return
            self.root.after(0, lambda: self._status_set("Running"))
            self.root.after(0, lambda: webbrowser.open(DASHBOARD_URL))
        except Exception as e:
            log.exception("Start worker error: %s", e)
            _cleanup_and_error(str(e))

    def _stop(self) -> None:
        self._status_set("Stopped")
        stop_processes(self.engine_proc, self.dashboard_proc)
        self.engine_proc = None
        self.dashboard_proc = None

    def _restart(self) -> None:
        self._stop()
        self.root.after(500, self._start)

    def _check_updates_ui(self) -> None:
        behind, msg = check_for_updates()
        if behind:
            if messagebox.askyesno("Updates", msg + "\n\nPull now and restart?"):
                self._do_update_flow()
        else:
            messagebox.showinfo("Updates", msg)

    def _do_update_flow(self) -> None:
        """Kill processes, pull, reinstall deps, restart."""
        self._status_set("Updating")
        self.root.update_idletasks()
        stop_processes(self.engine_proc, self.dashboard_proc)
        self.engine_proc = None
        self.dashboard_proc = None
        ok, msg = do_pull()
        if not ok:
            self.root.after(0, lambda: self._status_set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Update", msg))
            return
        # Force reinstall after pull so deps are always up to date
        if DEPS_HASH_FILE.exists():
            try:
                DEPS_HASH_FILE.unlink()
            except OSError:
                pass
        ok2, msg2 = ensure_deps()
        if not ok2:
            self.root.after(0, lambda: self._status_set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Dependencies", msg2))
            return
        self.root.after(0, lambda: self._status_set("Stopped"))
        messagebox.showinfo("Update", "Update complete. Click Start to run again.")

    def run(self) -> None:
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entry: update check on launch, then run GUI
# ---------------------------------------------------------------------------
def main() -> None:
    _setup_logging()
    if not acquire_lock():
        log.warning("Another launcher instance is already running.")
        messagebox.showerror("Launcher", "Another instance is already running.")
        sys.exit(1)
    behind, _ = check_for_updates()
    app = LauncherApp()
    if behind:
        if messagebox.askyesno("Updates", "Updates available. Pull now and reinstall before starting?"):
            app._do_update_flow()
    app.run()


if __name__ == "__main__":
    main()
