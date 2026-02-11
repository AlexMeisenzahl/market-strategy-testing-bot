"""
TUI Monitor (read-only). NOT the execution engine.

Displays live status from state/bot_state.json and logs/activity.json.
Does NOT fetch markets, execute strategies, or execute trades.
- To run the trading engine: python main.py  (canonical execution path)
- This TUI: python bot.py  (optional terminal dashboard; pause/resume via control.json)
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

# Paths (project root)
PROJECT_ROOT = Path(__file__).resolve().parent
STATE_PATH = PROJECT_ROOT / "state" / "bot_state.json"
ACTIVITY_PATH = PROJECT_ROOT / "logs" / "activity.json"
CONTROL_PATH = PROJECT_ROOT / "state" / "control.json"


def _read_json(path: Path, default: Any) -> Any:
    """Read JSON file with graceful handling of missing/partial/invalid data."""
    try:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _format_activity_item(item: Dict[str, Any]) -> str:
    """Format a single activity log item for display."""
    ts = item.get("timestamp", "")[:19].replace("T", " ")
    atype = item.get("type", "")
    if atype == "opportunity_found":
        strategy = item.get("strategy", "")
        market = item.get("market_name", "?")[:40]
        profit = item.get("profit_margin", 0)
        action = item.get("action", "found")
        return f"[{ts}] [{strategy}] {market}... ({profit:.1f}%) [{action}]"
    if atype == "trade_executed":
        strategy = item.get("strategy", "")
        count = item.get("count", 0)
        return f"[{ts}] Trade: {strategy} x{count}"
    if atype == "alert_triggered":
        msg = item.get("message", "")
        return f"[{ts}] Alert: {msg[:60]}"
    if atype == "error":
        msg = item.get("message", "Error")[:50]
        return f"[{ts}] Error: {msg}..."
    if atype == "bot_started":
        return f"[{ts}] Bot started"
    if atype == "bot_stopped":
        return f"[{ts}] Bot stopped"
    if atype == "risk_trigger":
        mid = item.get("market_id", "?")
        action = item.get("action", "")
        return f"[{ts}] Risk: {mid} -> {action}"
    if atype == "position_closed":
        return f"[{ts}] Position closed: {item.get('action', '')}"
    return f"[{ts}] {atype}"


def _get_key_nonblocking() -> Optional[str]:
    """Read a single key if available (Unix/Mac). Returns None if no key or unsupported."""
    try:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        if not sys.stdin.isatty():
            return None
        if select.select([sys.stdin], [], [], 0)[0]:
            old = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                return sys.stdin.read(1).lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except (ImportError, OSError):
        pass
    return None


def _write_control(signal: Dict[str, Any]) -> None:
    """Write control signal to state/control.json (best-effort)."""
    try:
        CONTROL_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTROL_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(signal, indent=2), encoding="utf-8")
        tmp.replace(CONTROL_PATH)
    except (OSError, json.JSONEncodeError):
        pass


class BotTUI:
    """Read-only TUI that displays engine state from state/bot_state.json and logs/activity.json."""

    def __init__(self):
        self.console = Console()
        self.running = True
        self.paused = False  # Local TUI notion; engine pause is in control.json

    def _load_state(self) -> Dict[str, Any]:
        return _read_json(STATE_PATH, {})

    def _load_activity(self) -> List[Dict[str, Any]]:
        data = _read_json(ACTIVITY_PATH, [])
        if not isinstance(data, list):
            return []
        return data

    def create_dashboard(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="status", size=3),
            Layout(name="connection", size=4),
            Layout(name="rate_limit", size=4),
            Layout(name="trading", size=5),
            Layout(name="positions", size=4),
            Layout(name="activity", size=12),
            Layout(name="footer", size=3),
        )
        return layout

    def update_dashboard(self, layout: Layout) -> None:
        state = self._load_state()
        activities = self._load_activity()

        # Header
        status = state.get("status", "unknown")
        if status == "running":
            status_text = "✓ RUNNING" if not self.paused else "⏸ PAUSED (local)"
        elif status == "stopped":
            status_text = "🛑 STOPPED"
        else:
            status_text = f"… {status}"

        header = Text()
        header.append("POLYMARKET ARBITRAGE BOT - TUI (Read-Only)\n", style="bold cyan")
        header.append(f"Engine: {status_text}", style="bold green")
        layout["header"].update(Panel(header, box=box.DOUBLE))

        # Status row
        runtime = state.get("runtime_seconds", 0)
        h, m = runtime // 3600, (runtime % 3600) // 60
        last = state.get("last_update", "")
        if last:
            try:
                dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                last = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                pass
        layout["status"].update(
            Panel(
                f"Runtime: {h}h {m}m   Last Update: {last}",
                title="Status",
                box=box.ROUNDED,
            )
        )

        # Connection
        conn = state.get("connection", {})
        healthy = conn.get("healthy", False)
        conn_status = "✓ Healthy" if healthy else "— Unknown"
        conn_style = "green" if healthy else "dim"
        rtt = conn.get("response_time_ms", 0)
        conn_table = Table(show_header=False, box=None, padding=(0, 2))
        conn_table.add_column("Label", style="cyan")
        conn_table.add_column("Value")
        conn_table.add_row("Status:", Text(conn_status, style=conn_style))
        conn_table.add_row("Response:", f"{rtt} ms")
        layout["connection"].update(Panel(conn_table, title="CONNECTION", box=box.ROUNDED))

        # Rate limit
        rl = state.get("rate_limit", {})
        pct = float(rl.get("usage_pct", 0) or 0)
        bar_w = 20
        filled = int(min(100, pct) / 100 * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        bar_style = "green" if pct < 80 else "yellow" if pct < 95 else "red"
        rl_table = Table(show_header=False, box=None, padding=(0, 2))
        rl_table.add_column("Label", style="cyan")
        rl_table.add_column("Value")
        rl_table.add_row("Usage:", Text(f"{bar} {pct:.0f}%", style=bar_style))
        rl_table.add_row("Reset:", f"{rl.get('reset_seconds', 0)}s")
        layout["rate_limit"].update(
            Panel(rl_table, title="API RATE LIMIT", box=box.ROUNDED)
        )

        # Trading
        tr = state.get("trading", {})
        opps = tr.get("opportunities_found", 0)
        trades = tr.get("trades_executed", 0)
        profit = float(tr.get("paper_profit", 0) or 0)
        balance = float(state.get("balance", 0) or 0)

        trade_table = Table(show_header=False, box=None, padding=(0, 2))
        trade_table.add_column("Label", style="cyan")
        trade_table.add_column("Value")
        trade_table.add_row("Opportunities:", str(opps))
        trade_table.add_row("Trades Executed:", str(trades))
        profit_style = "green" if profit > 0 else "white" if profit == 0 else "red"
        trade_table.add_row("Paper Profit:", Text(f"${profit:.2f}", style=profit_style))
        trade_table.add_row("Balance:", f"${balance:.2f}")
        layout["trading"].update(
            Panel(trade_table, title="TRADING ACTIVITY", box=box.ROUNDED)
        )

        # Positions
        positions = state.get("positions", [])
        if not isinstance(positions, list):
            positions = []
        pos_lines = []
        for p in positions[-5:]:
            sym = p.get("symbol", "?")
            qty = p.get("quantity", 0)
            avg = p.get("avg_price", 0)
            pos_lines.append(f"  {sym}: {qty:.2f} @ ${avg:.2f}")
        pos_text = "\n".join(pos_lines) if pos_lines else "(No open positions)"
        layout["positions"].update(
            Panel(pos_text, title="POSITIONS", box=box.ROUNDED)
        )

        # Activity
        act_lines = [_format_activity_item(a) for a in activities[-8:]]
        act_text = "\n".join(reversed(act_lines)) if act_lines else "(No activity yet)"
        layout["activity"].update(
            Panel(act_text.rstrip(), title="LATEST ACTIVITY", box=box.ROUNDED)
        )

        # Footer
        footer = "Q: quit | P: pause engine | R: resume engine | Ctrl+C: quit"
        layout["footer"].update(Panel(footer, box=box.ROUNDED, style="dim"))

    def run(self) -> None:
        self.console.clear()
        self.console.print("[bold cyan]Bot TUI - Read-only interface[/bold cyan]")
        self.console.print(
            "[yellow]Start the engine with: python main.py[/yellow]"
        )
        self.console.print(
            "[dim]Reading from state/bot_state.json and logs/activity.json[/dim]\n"
        )
        time.sleep(2)

        layout = self.create_dashboard()

        try:
            with Live(
                layout, console=self.console, refresh_per_second=2, screen=True
            ) as live:
                while self.running:
                    key = _get_key_nonblocking()
                    if key == "q":
                        self.running = False
                        break
                    if key == "p":
                        self.paused = True
                        _write_control({"pause": True})
                    if key == "r":
                        self.paused = False
                        _write_control({"pause": False})

                    self.update_dashboard(layout)
                    live.update(layout)
                    time.sleep(0.5)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]TUI stopped by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            raise
        finally:
            self.console.print("\n[cyan]TUI closed. Engine continues if running.[/cyan]")


def main() -> None:
    try:
        tui = BotTUI()
        tui.run()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
