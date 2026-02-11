# Contributing to Market Strategy Bot

Thank you for your interest in contributing.

## Development Setup

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```
3. Install in editable mode:
   ```bash
   pip install -e ".[dev,dashboard]"
   ```
4. Copy `.env.example` to `.env` and configure as needed.

## Running the Bot

- **Engine:** `msb run-engine` or `python main.py`
- **Dashboard:** `msb run-dashboard` or `python start_dashboard.py`
- **TUI:** `msb run-tui` or `python bot.py`
- **System check:** `msb system-check`

## Project Structure

- `market_strategy_bot/` – Canonical package (CLI, system check, paths)
- `run_bot.py` – Main engine loop
- `engine.py` – Execution engine
- `strategy_manager.py` – Strategy orchestration
- `dashboard/` – Flask web dashboard
- `services/` – Core services
- `strategies/` – Trading strategies

## Code Quality

- Run tests: `pytest`
- Format: `black .`
- Lint: `flake8`

## Pull Requests

1. Fork and create a feature branch.
2. Make changes with clear commit messages.
3. Ensure tests pass.
4. Submit a pull request with a description of changes.
