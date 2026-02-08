#!/usr/bin/env python3
"""
Demo script to show bot output without full-screen mode
"""

import yaml
import time
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from monitor import PolymarketMonitor
from detector import ArbitrageDetector
from paper_trader import PaperTrader
from logger import get_logger


def main():
    """Run a simple demo"""
    console = Console()

    console.print(
        "\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]"
    )
    console.print(
        "[bold cyan]     POLYMARKET ARBITRAGE BOT - PAPER TRADING DEMO           [/bold cyan]"
    )
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n"
    )

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Initialize components
    monitor = PolymarketMonitor(config)
    detector = ArbitrageDetector(config)
    trader = PaperTrader(config)

    console.print("[green]✓[/green] Bot initialized successfully")
    console.print("[yellow]⚠[/yellow]  Paper Trading Mode - NO REAL MONEY\n")

    # Status table
    status_table = Table(title="Bot Status", box=box.ROUNDED)
    status_table.add_column("Setting", style="cyan")
    status_table.add_column("Value", style="green")

    status_table.add_row("Paper Trading", "✓ Enabled")
    status_table.add_row("Kill Switch", "✗ Disabled")
    status_table.add_row("Max Trade Size", f"${config['max_trade_size']}")
    status_table.add_row("Min Profit Margin", f"{config['min_profit_margin']*100}%")
    status_table.add_row("Max Trades/Hour", str(config["max_trades_per_hour"]))

    console.print(status_table)
    console.print()

    # Simulate scanning markets
    console.print("[bold]Scanning markets...[/bold]\n")

    # Get demo markets
    markets = [
        {"id": "btc-above-100k", "question": "BTC-above-100k"},
        {"id": "eth-above-4k", "question": "ETH-above-4k"},
    ]

    # Fetch prices
    prices_dict = {}
    for market in markets:
        prices = monitor.get_market_prices(market["id"])
        if prices:
            prices_dict[market["id"]] = prices
            console.print(
                f"[green]✓[/green] Scanned: {market['question']} - YES: ${prices['yes']:.3f}, NO: ${prices['no']:.3f}"
            )

    console.print()

    # Find opportunities
    opportunities = detector.find_arbitrage_opportunities(markets, prices_dict)

    if opportunities:
        console.print(
            f"[yellow]⚠️  Found {len(opportunities)} arbitrage opportunities![/yellow]\n"
        )

        for opp in opportunities:
            # Create opportunity panel
            opp_text = (
                f"Market: {opp.market_name}\n"
                f"YES Price: ${opp.yes_price:.3f}\n"
                f"NO Price: ${opp.no_price:.3f}\n"
                f"Sum: ${opp.price_sum:.3f}\n"
                f"Profit Margin: {opp.profit_margin:.1f}%\n"
                f"Expected Profit: ${opp.expected_profit:.3f}"
            )

            console.print(
                Panel(opp_text, title="Arbitrage Opportunity", border_style="yellow")
            )

            # Execute paper trade
            if trader.can_trade():
                trade = trader.execute_paper_trade(opp)
                if trade:
                    console.print(f"[green]✓[/green] Paper trade executed!")
                    console.print(f"   Cost: ${trade.total_cost:.2f}")
                    console.print(f"   Expected return: ${trade.expected_return:.2f}")
                    console.print(f"   Expected profit: ${trade.expected_profit:.2f}\n")
    else:
        console.print("[dim]No arbitrage opportunities found in this scan.[/dim]\n")

    # Show statistics
    trade_stats = trader.get_statistics()
    rate_stats = monitor.get_rate_limit_status()

    stats_table = Table(title="Trading Statistics", box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Paper Trades Executed", str(trade_stats["trades_executed"]))
    stats_table.add_row("Total Paper Profit", f"${trade_stats['total_profit']:.2f}")
    stats_table.add_row("Return Percentage", f"{trade_stats['return_percentage']:.1f}%")
    stats_table.add_row(
        "API Usage",
        f"{rate_stats['current']}/{rate_stats['max']} ({rate_stats['percentage']:.0f}%)",
    )

    console.print(stats_table)
    console.print()

    # Show log locations
    console.print("[bold]Log Files:[/bold]")
    console.print("  📊 Trades: logs/trades.csv")
    console.print("  📋 Opportunities: logs/opportunities.csv")
    console.print("  ⚠️  Errors: logs/errors.log")
    console.print("  🔌 Connection: logs/connection.log")
    console.print()

    console.print(
        "[green]✓ Demo complete! Run 'python3 bot.py' for the full dashboard.[/green]\n"
    )


if __name__ == "__main__":
    main()
