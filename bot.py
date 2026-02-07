"""
Main Bot Entry Point - Polymarket Arbitrage Bot

Real-time dashboard with live market monitoring
Paper trading only - NO REAL MONEY
"""

import yaml
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

from monitor import PolymarketMonitor
from detector import ArbitrageDetector
from paper_trader import PaperTrader
from logger import get_logger
from notifier import Notifier


class ArbitrageBot:
    """Main arbitrage bot with real-time dashboard"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize arbitrage bot
        
        Args:
            config_path: Path to configuration file
        """
        self.console = Console()
        self.config = self._load_config(config_path)
        self.logger = get_logger()
        
        # Initialize components
        self.monitor = PolymarketMonitor(self.config)
        self.detector = ArbitrageDetector(self.config)
        self.trader = PaperTrader(self.config)
        self.notifier = Notifier(self.config)
        
        # Bot state
        self.running = True
        self.paused = False
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.last_connection_check = datetime.now()
        
        # Activity log for dashboard
        self.activities = []
        self.alerts = []
        
        # Verify paper trading is enabled
        if not self.config.get('paper_trading', True):
            self.logger.log_critical("CRITICAL: Paper trading is disabled!")
            raise ValueError("Paper trading must be enabled!")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            self.console.print(f"[red]ERROR: Config file not found: {config_path}[/red]")
            sys.exit(1)
        except yaml.YAMLError as e:
            self.console.print(f"[red]ERROR: Invalid YAML in config file: {e}[/red]")
            sys.exit(1)
    
    def check_kill_switch(self) -> bool:
        """Check if kill switch is activated"""
        return self.config.get('kill_switch', False)
    
    def create_dashboard(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout()
        
        # Main sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="status", size=3),
            Layout(name="connection", size=5),
            Layout(name="data_sources", size=7),  # NEW: Data sources status
            Layout(name="rate_limit", size=5),
            Layout(name="trading", size=5),
            Layout(name="activity", size=10),
            Layout(name="alerts", size=5),
            Layout(name="footer", size=3)
        )
        
        return layout
    
    def update_dashboard(self, layout: Layout) -> None:
        """Update dashboard with current data"""
        # Header
        status_text = "✓ RUNNING" if self.running and not self.paused else "⏸ PAUSED"
        if self.check_kill_switch():
            status_text = "🚨 STOPPED (KILL SWITCH)"
        
        header_text = Text()
        header_text.append("POLYMARKET ARBITRAGE BOT - PAPER TRADING\n", style="bold cyan")
        header_text.append(f"Status: {status_text}", style="bold green" if status_text.startswith("✓") else "bold yellow")
        
        layout["header"].update(Panel(header_text, box=box.DOUBLE))
        
        # Status row
        runtime = datetime.now() - self.start_time
        runtime_str = f"{int(runtime.total_seconds() // 3600)}h {int((runtime.total_seconds() % 3600) // 60)}m"
        last_update_str = self.last_update.strftime("%H:%M:%S")
        
        status_text = f"Runtime: {runtime_str}                    Last Update: {last_update_str}"
        layout["status"].update(Panel(status_text, title="Status", box=box.ROUNDED))
        
        # Connection status
        conn_table = Table(show_header=False, box=None, padding=(0, 2))
        conn_table.add_column("Label", style="cyan")
        conn_table.add_column("Value")
        
        conn_healthy = self.monitor.connection_healthy
        conn_status = "✓ Healthy" if conn_healthy else "🚨 Unstable"
        conn_style = "green" if conn_healthy else "red"
        
        seconds_since_check = int((datetime.now() - self.last_connection_check).total_seconds())
        
        conn_table.add_row("Status:", Text(conn_status, style=conn_style))
        conn_table.add_row("Last Check:", f"{seconds_since_check} seconds ago")
        
        layout["connection"].update(Panel(conn_table, title="CONNECTION", box=box.ROUNDED))
        
        # Data sources status (NEW)
        try:
            ds_status = self.monitor.get_data_source_status()
            ds_table = Table(show_header=False, box=None, padding=(0, 2))
            ds_table.add_column("Label", style="cyan")
            ds_table.add_column("Value")
            
            # Binance status
            binance_connected = ds_status.get('binance', {}).get('connected', False)
            binance_text = "✓ Connected" if binance_connected else "✗ Disconnected"
            binance_style = "green" if binance_connected else "red"
            ds_table.add_row("Binance:", Text(binance_text, style=binance_style))
            
            # CoinGecko status
            cg_used = ds_status.get('coingecko', {}).get('rate_limit_used', 0)
            cg_max = ds_status.get('coingecko', {}).get('rate_limit_max', 50)
            ds_table.add_row("CoinGecko:", f"{cg_used}/{cg_max} req/min")
            
            # Aggregator success rate
            agg_success = ds_status.get('aggregator', {}).get('success_rate', 0)
            ds_table.add_row("Success Rate:", f"{agg_success:.1f}%")
            
            layout["data_sources"].update(Panel(ds_table, title="FREE DATA SOURCES", box=box.ROUNDED))
        except Exception as e:
            layout["data_sources"].update(Panel("Error loading data sources", title="DATA SOURCES", box=box.ROUNDED))
        
        # Rate limit status
        rate_status = self.monitor.get_rate_limit_status()
        rate_pct = rate_status['percentage']
        
        # Create progress bar
        bar_width = 20
        filled = int((rate_pct / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Color based on usage
        bar_color = "green"
        if rate_pct > 80:
            bar_color = "yellow"
        if rate_pct > 95:
            bar_color = "red"
        
        rate_table = Table(show_header=False, box=None, padding=(0, 2))
        rate_table.add_column("Label", style="cyan")
        rate_table.add_column("Value")
        
        usage_text = Text(f"{bar} {rate_status['current']}/{rate_status['max']} ({rate_pct:.0f}%)")
        usage_text.stylize(bar_color)
        
        rate_table.add_row("Usage:", usage_text)
        rate_table.add_row("Resets in:", f"{rate_status['reset_in']} seconds")
        
        layout["rate_limit"].update(Panel(rate_table, title="API RATE LIMIT", box=box.ROUNDED))
        
        # Trading activity
        trade_stats = self.trader.get_statistics()
        detect_stats = self.detector.get_statistics()
        
        trade_table = Table(show_header=False, box=None, padding=(0, 2))
        trade_table.add_column("Label", style="cyan")
        trade_table.add_column("Value")
        
        trade_table.add_row("Opportunities Found:", str(detect_stats['opportunities_found']))
        trade_table.add_row("Paper Trades Executed:", str(trade_stats['trades_executed']))
        
        profit_text = f"+${trade_stats['total_profit']:.2f} ({trade_stats['return_percentage']:.1f}% return)" if trade_stats['total_profit'] > 0 else "$0.00 (0% return)"
        profit_style = "green" if trade_stats['total_profit'] > 0 else "white"
        
        trade_table.add_row("Paper Profit:", Text(profit_text, style=profit_style))
        
        layout["trading"].update(Panel(trade_table, title="TRADING ACTIVITY", box=box.ROUNDED))
        
        # Latest activity
        activity_text = ""
        for activity in self.activities[-5:]:
            activity_text += activity + "\n"
        
        if not activity_text:
            activity_text = "(No activity yet)"
        
        layout["activity"].update(Panel(activity_text.rstrip(), title="LATEST ACTIVITY", box=box.ROUNDED))
        
        # Alerts
        alert_text = ""
        if self.alerts:
            for alert in self.alerts[-3:]:
                alert_text += alert + "\n"
        else:
            alert_text = "(No alerts)"
        
        alert_style = "yellow" if self.alerts else "green"
        layout["alerts"].update(Panel(alert_text.rstrip(), title="ALERTS", box=box.ROUNDED, style=alert_style))
        
        # Footer
        footer_text = "Press 'Q' to quit  |  Press 'P' to pause  |  'R' to resume"
        layout["footer"].update(Panel(footer_text, box=box.ROUNDED, style="dim"))
    
    def add_activity(self, message: str) -> None:
        """Add activity to dashboard log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activities.append(f"[{timestamp}] {message}")
        
        # Keep only last 20 activities
        if len(self.activities) > 20:
            self.activities = self.activities[-20:]
    
    def add_alert(self, message: str) -> None:
        """Add alert to dashboard"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.alerts.append(f"[{timestamp}] {message}")
        
        # Keep only last 10 alerts
        if len(self.alerts) > 10:
            self.alerts = self.alerts[-10:]
    
    def scan_markets(self) -> None:
        """Scan markets for arbitrage opportunities"""
        try:
            # Check connection health periodically
            if (datetime.now() - self.last_connection_check).total_seconds() > self.config.get('connection_check_interval', 10):
                is_healthy = self.monitor.check_connection_health()
                self.last_connection_check = datetime.now()
                
                if not is_healthy and self.config.get('auto_pause_on_connection_loss', True):
                    self.paused = True
                    self.add_alert("🚨 Connection lost - trading paused")
                    return
            
            # Get active markets (for demo, use predefined markets)
            markets_to_scan = self._get_demo_markets()
            
            # Fetch prices for each market
            prices_dict = {}
            for market in markets_to_scan:
                market_id = market['id']
                prices = self.monitor.get_market_prices(market_id)
                if prices:
                    prices_dict[market_id] = prices
            
            # Find arbitrage opportunities
            opportunities = self.detector.find_arbitrage_opportunities(markets_to_scan, prices_dict)
            
            # Log scanned markets
            for market in markets_to_scan:
                market_id = market['id']
                if market_id in prices_dict:
                    prices = prices_dict[market_id]
                    price_sum = prices['yes'] + prices['no']
                    
                    # Check if opportunity exists
                    opp = next((o for o in opportunities if o.market_id == market_id), None)
                    
                    if opp:
                        # Opportunity found
                        self.add_activity(
                            f"⚠️ OPPORTUNITY: {market['question']}\n"
                            f"           YES: ${prices['yes']:.2f}  NO: ${prices['no']:.2f}  "
                            f"SUM: ${price_sum:.2f} ({opp.profit_margin:.1f}% profit)"
                        )
                        
                        # Add alert for opportunity
                        if self.config.get("alert_on_opportunities", True):
                            self.add_alert(f"💰 {market['question'][:40]}... ({opp.profit_margin:.1f}% profit)")
                            self.notifier.alert_opportunity_found(market['question'], opp.profit_margin)
                            trade = self.trader.execute_paper_trade(opp)
                            if trade:
                                self.add_activity(
                                    f"           [PAPER] Bought ${self.config['max_trade_size']:.0f} YES + "
                                    f"${self.config['max_trade_size']:.0f} NO\n"
                                    f"           Expected profit: ${trade.expected_profit:.2f}"
                                )
                    else:
                        # No opportunity
                        self.add_activity(f"✓ Scanned: {market['question']} (no opportunity)")
            
            self.last_update = datetime.now()
            
        except Exception as e:
            self.logger.log_error(f"Error scanning markets: {str(e)}")
            self.add_alert(f"🚨 Error: {str(e)}")
    
    def _get_demo_markets(self) -> list:
        """Get demo markets for paper trading"""
        # For demo purposes, return some example markets
        # In production, this would fetch from Polymarket API
        demo_markets = [
            {'id': 'btc-above-100k', 'question': 'BTC-above-100k'},
            {'id': 'eth-above-4k', 'question': 'ETH-above-4k'},
        ]
        
        # Add any configured markets
        configured_markets = self.config.get('markets_to_watch', [])
        for market_name in configured_markets:
            market_id = market_name.lower().replace(' ', '-')
            if not any(m['id'] == market_id for m in demo_markets):
                demo_markets.append({
                    'id': market_id,
                    'question': market_name
                })
        
        return demo_markets
    
    def run(self) -> None:
        """Main bot loop with live dashboard"""
        self.console.clear()
        self.console.print("[bold cyan]Starting Polymarket Arbitrage Bot...[/bold cyan]")
        self.console.print("[yellow]Paper Trading Mode - NO REAL MONEY[/yellow]")
        time.sleep(2)
        
        layout = self.create_dashboard()
        
        try:
            with Live(layout, console=self.console, refresh_per_second=1, screen=True) as live:
                while self.running:
                    # Check kill switch
                    if self.check_kill_switch():
                        self.add_alert("🚨 KILL SWITCH ACTIVATED - Stopping bot")
                        self.running = False
                        break
                    
                    # Update dashboard
                    self.update_dashboard(layout)
                    live.update(layout)
                    
                    # Scan markets if not paused
                    if not self.paused:
                        self.scan_markets()
                    
                    # Sleep between scans
                    time.sleep(3)
                    
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Bot stopped by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]ERROR: {str(e)}[/red]")
            self.logger.log_critical(f"Bot crashed: {str(e)}")
        finally:
            self.console.print("\n[cyan]Shutting down...[/cyan]")
            
            # Shutdown data source connections
            try:
                self.monitor.shutdown()
                self.console.print("[green]✓ Data sources closed[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Error closing data sources: {e}[/yellow]")
            
            self.console.print(f"[green]Total paper profit: ${self.trader.get_statistics()['total_profit']:.2f}[/green]")


def main():
    """Entry point for the bot"""
    try:
        bot = ArbitrageBot()
        bot.run()
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
