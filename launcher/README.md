# Market Strategy Bot — Desktop Launcher

Lightweight Python GUI launcher for single-user use. Starts the engine and dashboard, checks for updates, opens the browser.

## Requirements

- Python 3.8+
- tkinter (usually included with Python)

## Run

From the **project root**:

```bash
python launcher/launcher.py
```

Or from anywhere:

```bash
python /path/to/market-strategy-testing-bot/launcher/launcher.py
```

The launcher uses the directory containing `launcher.py` to resolve the project root (parent directory).

## Features

- **Start** — Installs dependencies if needed (`pip install -e ".[dashboard]"` when `pyproject.toml` changes), starts engine and dashboard, waits for port 5000, opens browser.
- **Stop** — Gracefully stops engine and dashboard (SIGTERM, then SIGKILL if needed).
- **Restart** — Stop then Start.
- **Check for Updates** — `git fetch` and compare with remote; if behind, offers to pull, reinstall deps, and restart.
- **Open Logs** — Opens `launcher/launcher.log` in the default app.

On launch, the launcher checks for Git updates and can prompt to pull and reinstall before you start.

Only one instance can run at a time (lock file `.launcher.lock` in project root). Closing the window stops subprocesses and releases the lock.

## Logs

- Launcher events: `launcher/launcher.log`
- Engine/dashboard logs: project `logs/` and console of those processes (not written by the launcher).

## Platform

Tested on macOS and Windows. Uses `CREATE_NO_WINDOW` on Windows so engine and dashboard do not open extra console windows.
