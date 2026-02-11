#!/usr/bin/env bash
# Reproducible install test: fresh venv, install project, import engine, import dashboard.
# Run from project root: ./scripts/install_test.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VENV_DIR="${VENV_DIR:-.venv-install-test}"
echo "[install_test] Creating venv at $VENV_DIR"
python3 -m venv "$VENV_DIR"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
echo "[install_test] Installing project with [dashboard,dev]"
pip install -q --upgrade pip
pip install -q -e ".[dashboard,dev]"
echo "[install_test] Import engine"
python3 -c "from engine import ExecutionEngine; print('  engine OK')"
echo "[install_test] Import dashboard (create_app)"
python3 -c "
from market_strategy_bot.dashboard_app import create_app
app = create_app()
print('  dashboard OK, routes:', len(list(app.url_map.iter_rules())))
"
echo "[install_test] All imports OK"
deactivate
echo "[install_test] Done. Remove venv with: rm -rf $VENV_DIR"
