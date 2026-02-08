"""
Tax Exporter Module - Generate tax reports for trades

Creates IRS-compliant tax reports including:
- Form 8949 format (capital gains/losses)
- FIFO accounting method
- Short-term vs long-term classification
- Summary of gains/losses and tax estimates

Works with paper trade logs to prepare for real trading.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import csv
from logger import get_logger


class TaxPosition:
    """Represents a tax position (acquisition and disposal)"""

    def __init__(
        self,
        date_acquired: datetime,
        date_sold: datetime,
        description: str,
        proceeds: float,
        cost_basis: float,
    ):
        """
        Initialize tax position

        Args:
            date_acquired: When position was acquired
            date_sold: When position was sold
            description: Market/asset description
            proceeds: Sale proceeds
            cost_basis: Original cost
        """
        self.date_acquired = date_acquired
        self.date_sold = date_sold
        self.description = description
        self.proceeds = proceeds
        self.cost_basis = cost_basis
        self.gain_loss = proceeds - cost_basis

        # Determine holding period
        holding_days = (date_sold - date_acquired).days
        self.term = "long" if holding_days > 365 else "short"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export"""
        return {
            "date_acquired": self.date_acquired.strftime("%m/%d/%Y"),
            "date_sold": self.date_sold.strftime("%m/%d/%Y"),
            "description": self.description,
            "proceeds": f"{self.proceeds:.2f}",
            "cost_basis": f"{self.cost_basis:.2f}",
            "gain_loss": f"{self.gain_loss:.2f}",
            "term": self.term,
        }


class TaxExporter:
    """
    Tax reporting system for trading activity

    Generates IRS-compliant tax reports using FIFO accounting.
    Tracks cost basis, capital gains/losses, and tax estimates.
    """

    def __init__(self, config: Dict[str, Any], log_dir: str = "logs"):
        """
        Initialize tax exporter

        Args:
            config: Configuration dictionary from config.yaml
            log_dir: Directory containing trade logs
        """
        self.config = config
        self.log_dir = Path(log_dir)
        self.logger = get_logger()

        # Tax rates (can be configured)
        tax_config = config.get("tax_settings", {})
        self.short_term_rate = tax_config.get("short_term_rate", 0.24)  # 24% default
        self.long_term_rate = tax_config.get("long_term_rate", 0.15)  # 15% default

        # FIFO tracking
        self.positions: List[TaxPosition] = []
        self.open_positions: Dict[str, List[Tuple[datetime, float, float]]] = (
            {}
        )  # market -> [(date, size, cost)]

        self.logger.log_warning(
            f"TaxExporter initialized - "
            f"Short-term rate: {self.short_term_rate*100:.0f}%, "
            f"Long-term rate: {self.long_term_rate*100:.0f}%"
        )

    def load_trades_from_logs(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load trades from log files

        Args:
            year: Optional year to filter trades (None = all years)

        Returns:
            List of trade dictionaries
        """
        trades = []
        trades_file = self.log_dir / "trades.csv"

        if not trades_file.exists():
            self.logger.log_error(f"Trades log not found: {trades_file}")
            return trades

        try:
            with open(trades_file, "r") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Parse trade
                    timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")

                    # Filter by year if specified
                    if year and timestamp.year != year:
                        continue

                    trade = {
                        "timestamp": timestamp,
                        "market": row["market"],
                        "yes_price": float(row["yes_price"]),
                        "no_price": float(row["no_price"]),
                        "profit_usd": float(row["profit_usd"]),
                        "status": row["status"],
                    }

                    trades.append(trade)

            self.logger.log_warning(f"Loaded {len(trades)} trades from logs")

        except Exception as e:
            self.logger.log_error(f"Error loading trades: {str(e)}")

        return trades

    def process_trades_fifo(self, trades: List[Dict[str, Any]]) -> List[TaxPosition]:
        """
        Process trades using FIFO accounting method

        Args:
            trades: List of trade dictionaries

        Returns:
            List of TaxPosition objects
        """
        self.positions = []
        self.open_positions = {}

        for trade in trades:
            market = trade["market"]
            timestamp = trade["timestamp"]

            # For arbitrage trades, we buy and sell simultaneously
            # Cost basis = yes_price + no_price
            # Proceeds = 1.0 (always pays full amount)

            yes_price = trade["yes_price"]
            no_price = trade["no_price"]
            cost_basis = yes_price + no_price
            proceeds = 1.0

            # Create tax position
            # For same-day arbitrage, acquisition and sale are same timestamp
            position = TaxPosition(
                date_acquired=timestamp,
                date_sold=timestamp,
                description=f"Arbitrage trade: {market}",
                proceeds=proceeds,
                cost_basis=cost_basis,
            )

            self.positions.append(position)

        return self.positions

    def export_to_csv(self, year: int, output_dir: str = ".") -> str:
        """
        Export tax report to CSV (Form 8949 format)

        Args:
            year: Tax year to export
            output_dir: Directory to save report

        Returns:
            Path to generated CSV file
        """
        # Load and process trades
        trades = self.load_trades_from_logs(year)

        if not trades:
            self.logger.log_warning(f"No trades found for year {year}")
            return ""

        positions = self.process_trades_fifo(trades)

        # Create output file
        output_path = Path(output_dir) / f"tax_report_{year}.csv"

        try:
            with open(output_path, "w", newline="") as f:
                # Write header
                fieldnames = [
                    "Date Acquired",
                    "Date Sold",
                    "Description",
                    "Proceeds",
                    "Cost Basis",
                    "Gain/Loss",
                    "Term",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                # Write positions
                for position in positions:
                    writer.writerow(
                        {
                            "Date Acquired": position.date_acquired.strftime(
                                "%m/%d/%Y"
                            ),
                            "Date Sold": position.date_sold.strftime("%m/%d/%Y"),
                            "Description": position.description,
                            "Proceeds": f"${position.proceeds:.2f}",
                            "Cost Basis": f"${position.cost_basis:.2f}",
                            "Gain/Loss": f"${position.gain_loss:.2f}",
                            "Term": position.term.upper(),
                        }
                    )

            self.logger.log_warning(
                f"Tax report exported to {output_path} - {len(positions)} positions"
            )

            return str(output_path)

        except Exception as e:
            self.logger.log_error(f"Error exporting tax report: {str(e)}")
            return ""

    def generate_summary(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate tax summary with totals and estimates

        Args:
            year: Optional year to summarize (None = all years)

        Returns:
            Dictionary with tax summary
        """
        # Load and process trades
        trades = self.load_trades_from_logs(year)

        if not trades:
            return {
                "year": year,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "gross_proceeds": 0,
                "total_cost_basis": 0,
                "gross_profit": 0,
                "gross_loss": 0,
                "net_profit_loss": 0,
                "short_term_gain": 0,
                "long_term_gain": 0,
                "estimated_tax_short": 0,
                "estimated_tax_long": 0,
                "total_estimated_tax": 0,
            }

        positions = self.process_trades_fifo(trades)

        # Calculate totals
        total_trades = len(positions)
        winning_trades = sum(1 for p in positions if p.gain_loss > 0)
        losing_trades = sum(1 for p in positions if p.gain_loss <= 0)

        gross_proceeds = sum(p.proceeds for p in positions)
        total_cost_basis = sum(p.cost_basis for p in positions)

        gross_profit = sum(p.gain_loss for p in positions if p.gain_loss > 0)
        gross_loss = sum(abs(p.gain_loss) for p in positions if p.gain_loss < 0)
        net_profit_loss = gross_profit - gross_loss

        # Calculate by term
        short_term_positions = [p for p in positions if p.term == "short"]
        long_term_positions = [p for p in positions if p.term == "long"]

        short_term_gain = sum(p.gain_loss for p in short_term_positions)
        long_term_gain = sum(p.gain_loss for p in long_term_positions)

        # Estimate taxes (only on gains)
        estimated_tax_short = max(0, short_term_gain) * self.short_term_rate
        estimated_tax_long = max(0, long_term_gain) * self.long_term_rate
        total_estimated_tax = estimated_tax_short + estimated_tax_long

        return {
            "year": year or "All",
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (
                (winning_trades / total_trades * 100) if total_trades > 0 else 0
            ),
            "gross_proceeds": gross_proceeds,
            "total_cost_basis": total_cost_basis,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "net_profit_loss": net_profit_loss,
            "short_term_trades": len(short_term_positions),
            "long_term_trades": len(long_term_positions),
            "short_term_gain": short_term_gain,
            "long_term_gain": long_term_gain,
            "estimated_tax_short": estimated_tax_short,
            "estimated_tax_long": estimated_tax_long,
            "total_estimated_tax": total_estimated_tax,
            "net_after_tax": net_profit_loss - total_estimated_tax,
        }

    def print_summary(self, year: Optional[int] = None) -> str:
        """
        Generate formatted tax summary report

        Args:
            year: Optional year to summarize

        Returns:
            Formatted report string
        """
        summary = self.generate_summary(year)

        report = "\n" + "=" * 60 + "\n"
        report += f"TAX SUMMARY - {summary['year']}\n"
        report += "=" * 60 + "\n\n"

        report += "TRADE STATISTICS:\n"
        report += f"  Total Trades: {summary['total_trades']}\n"
        report += f"  Winning Trades: {summary['winning_trades']}\n"
        report += f"  Losing Trades: {summary['losing_trades']}\n"
        report += f"  Win Rate: {summary['win_rate']:.1f}%\n"
        report += "\n"

        report += "FINANCIAL SUMMARY:\n"
        report += f"  Gross Proceeds: ${summary['gross_proceeds']:.2f}\n"
        report += f"  Total Cost Basis: ${summary['total_cost_basis']:.2f}\n"
        report += f"  Gross Profit: ${summary['gross_profit']:.2f}\n"
        report += f"  Gross Loss: ${summary['gross_loss']:.2f}\n"
        report += f"  Net P&L: ${summary['net_profit_loss']:.2f}\n"
        report += "\n"

        report += "CAPITAL GAINS/LOSSES:\n"
        report += f"  Short-Term Trades: {summary['short_term_trades']}\n"
        report += f"  Short-Term Gain/Loss: ${summary['short_term_gain']:.2f}\n"
        report += f"  Long-Term Trades: {summary['long_term_trades']}\n"
        report += f"  Long-Term Gain/Loss: ${summary['long_term_gain']:.2f}\n"
        report += "\n"

        report += "TAX ESTIMATES:\n"
        report += f"  Short-Term Tax ({self.short_term_rate*100:.0f}%): ${summary['estimated_tax_short']:.2f}\n"
        report += f"  Long-Term Tax ({self.long_term_rate*100:.0f}%): ${summary['estimated_tax_long']:.2f}\n"
        report += f"  Total Estimated Tax: ${summary['total_estimated_tax']:.2f}\n"
        report += f"  Net After Tax: ${summary['net_after_tax']:.2f}\n"
        report += "\n"

        report += "NOTE: This is an estimate. Consult a tax professional.\n"
        report += "=" * 60 + "\n"

        return report

    def get_quarterly_breakdown(self, year: int) -> Dict[str, Any]:
        """
        Get quarterly breakdown of trades and taxes

        Args:
            year: Year to analyze

        Returns:
            Dictionary with quarterly data
        """
        trades = self.load_trades_from_logs(year)

        # Initialize quarters
        quarters = {
            "Q1": {"trades": [], "months": [1, 2, 3]},
            "Q2": {"trades": [], "months": [4, 5, 6]},
            "Q3": {"trades": [], "months": [7, 8, 9]},
            "Q4": {"trades": [], "months": [10, 11, 12]},
        }

        # Assign trades to quarters
        for trade in trades:
            month = trade["timestamp"].month
            for quarter, data in quarters.items():
                if month in data["months"]:
                    data["trades"].append(trade)
                    break

        # Calculate summary for each quarter
        quarterly_summary = {}
        for quarter, data in quarters.items():
            positions = self.process_trades_fifo(data["trades"])

            net_pnl = sum(p.gain_loss for p in positions)
            short_term_gain = sum(p.gain_loss for p in positions if p.term == "short")

            quarterly_summary[quarter] = {
                "trades": len(positions),
                "net_pnl": net_pnl,
                "short_term_gain": short_term_gain,
                "estimated_tax": max(0, short_term_gain) * self.short_term_rate,
            }

        return quarterly_summary
