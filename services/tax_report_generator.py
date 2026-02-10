"""
Tax Report Generator

Generates tax reports for trading activity:
- IRS Form 8949 CSV format
- TurboTax import CSV format
- Tax summary with short/long-term gains
"""

import csv
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class TaxReportGenerator:
    """
    Generates tax reports from trade history

    Supports IRS Form 8949 and TurboTax import formats.
    """

    def __init__(self):
        """Initialize tax report generator"""
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def generate_irs_8949_csv(self, trades: List[Dict[str, Any]]) -> str:
        """
        Generate IRS Form 8949 CSV format

        Form 8949 columns:
        - Description of property
        - Date acquired
        - Date sold
        - Proceeds (sales price)
        - Cost or other basis
        - Gain or loss

        Args:
            trades: List of closed trades

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Description of Property",
                "Date Acquired",
                "Date Sold or Disposed",
                "Proceeds (Sales Price)",
                "Cost or Other Basis",
                "Gain or Loss",
                "Type (Short/Long)",
            ]
        )

        # Write trades
        for trade in trades:
            description = self._get_trade_description(trade)
            date_acquired = self._get_trade_date(
                trade.get("entry_time", trade.get("timestamp"))
            )
            date_sold = self._get_trade_date(
                trade.get("exit_time", trade.get("closed_at"))
            )

            # Calculate proceeds and cost
            size = trade.get("size", 0)
            entry_price = trade.get("entry_price", 0)
            exit_price = trade.get("exit_price", entry_price)

            cost_basis = size * entry_price
            proceeds = size * exit_price
            gain_loss = trade.get(
                "realized_pnl", trade.get("pnl", proceeds - cost_basis)
            )

            # Determine if short-term or long-term
            holding_type = self._get_holding_type(date_acquired, date_sold)

            writer.writerow(
                [
                    description,
                    date_acquired,
                    date_sold,
                    f"${proceeds:.2f}",
                    f"${cost_basis:.2f}",
                    f"${gain_loss:.2f}",
                    holding_type,
                ]
            )

        return output.getvalue()

    def generate_turbotax_csv(self, trades: List[Dict[str, Any]]) -> str:
        """
        Generate TurboTax import CSV format

        TurboTax columns:
        - Security Name
        - Symbol
        - Quantity
        - Date Acquired
        - Date Sold
        - Proceeds
        - Cost Basis
        - Adjustment Code
        - Adjustment Amount

        Args:
            trades: List of closed trades

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Security Name",
                "Symbol",
                "Quantity",
                "Date Acquired",
                "Date Sold",
                "Proceeds",
                "Cost Basis",
                "Adjustment Code",
                "Adjustment Amount",
            ]
        )

        # Write trades
        for trade in trades:
            security_name = self._get_trade_description(trade)
            # TurboTax CSV format requires symbol to be max 10 characters
            symbol = trade.get("market_id", "UNKNOWN")[:10]
            quantity = trade.get("size", 0)
            date_acquired = self._get_trade_date(
                trade.get("entry_time", trade.get("timestamp"))
            )
            date_sold = self._get_trade_date(
                trade.get("exit_time", trade.get("closed_at"))
            )

            entry_price = trade.get("entry_price", 0)
            exit_price = trade.get("exit_price", entry_price)

            cost_basis = quantity * entry_price
            proceeds = quantity * exit_price

            writer.writerow(
                [
                    security_name,
                    symbol,
                    f"{quantity:.4f}",
                    date_acquired,
                    date_sold,
                    f"{proceeds:.2f}",
                    f"{cost_basis:.2f}",
                    "",  # No adjustment code
                    "0.00",  # No adjustment amount
                ]
            )

        return output.getvalue()

    def generate_tax_summary(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate tax summary with short/long-term capital gains

        Args:
            trades: List of closed trades

        Returns:
            Dictionary with tax summary
        """
        short_term_trades = []
        long_term_trades = []

        short_term_gain = 0.0
        long_term_gain = 0.0

        for trade in trades:
            date_acquired = self._parse_date(
                trade.get("entry_time", trade.get("timestamp"))
            )
            date_sold = self._parse_date(trade.get("exit_time", trade.get("closed_at")))

            gain_loss = trade.get("realized_pnl", trade.get("pnl", 0))

            # Determine if short-term or long-term
            if date_acquired and date_sold:
                holding_days = (date_sold - date_acquired).days

                if holding_days <= 365:
                    short_term_trades.append(trade)
                    short_term_gain += gain_loss
                else:
                    long_term_trades.append(trade)
                    long_term_gain += gain_loss
            else:
                # Default to short-term if dates not available
                short_term_trades.append(trade)
                short_term_gain += gain_loss

        total_gain = short_term_gain + long_term_gain

        # Calculate tax implications (estimated)
        # Short-term gains taxed as ordinary income (assume 24% bracket)
        # Long-term gains taxed at preferential rates (assume 15%)
        estimated_st_tax = max(0, short_term_gain * 0.24)
        estimated_lt_tax = max(0, long_term_gain * 0.15)
        estimated_total_tax = estimated_st_tax + estimated_lt_tax

        return {
            "tax_year": datetime.now().year,
            "total_trades": len(trades),
            "short_term": {
                "trades": len(short_term_trades),
                "total_gain_loss": short_term_gain,
                "gains": sum(
                    t.get("realized_pnl", t.get("pnl", 0))
                    for t in short_term_trades
                    if t.get("realized_pnl", t.get("pnl", 0)) > 0
                ),
                "losses": sum(
                    t.get("realized_pnl", t.get("pnl", 0))
                    for t in short_term_trades
                    if t.get("realized_pnl", t.get("pnl", 0)) < 0
                ),
                "estimated_tax": estimated_st_tax,
            },
            "long_term": {
                "trades": len(long_term_trades),
                "total_gain_loss": long_term_gain,
                "gains": sum(
                    t.get("realized_pnl", t.get("pnl", 0))
                    for t in long_term_trades
                    if t.get("realized_pnl", t.get("pnl", 0)) > 0
                ),
                "losses": sum(
                    t.get("realized_pnl", t.get("pnl", 0))
                    for t in long_term_trades
                    if t.get("realized_pnl", t.get("pnl", 0)) < 0
                ),
                "estimated_tax": estimated_lt_tax,
            },
            "totals": {
                "total_gain_loss": total_gain,
                "estimated_total_tax": estimated_total_tax,
                "net_after_tax": total_gain - estimated_total_tax,
            },
            "notes": [
                "Tax estimates are approximate and for informational purposes only.",
                "Short-term gains (held <= 1 year) estimated at 24% ordinary income tax rate.",
                "Long-term gains (held > 1 year) estimated at 15% capital gains tax rate.",
                "Consult a tax professional for accurate tax calculations.",
            ],
        }

    def _get_trade_description(self, trade: Dict[str, Any]) -> str:
        """
        Get trade description for tax forms

        Args:
            trade: Trade dictionary

        Returns:
            Description string
        """
        market_name = trade.get("market_name", trade.get("market_id", "Unknown Market"))
        direction = trade.get("direction", "")

        if len(market_name) > 50:
            market_name = market_name[:47] + "..."

        return f"{direction.upper()} - {market_name}" if direction else market_name

    def _get_trade_date(self, timestamp: Any) -> str:
        """
        Format trade date for tax forms (MM/DD/YYYY)

        Args:
            timestamp: Timestamp string or datetime

        Returns:
            Formatted date string
        """
        date = self._parse_date(timestamp)

        if date:
            return date.strftime("%m/%d/%Y")

        return "N/A"

    def _parse_date(self, timestamp: Any) -> Optional[datetime]:
        """
        Parse date from various timestamp formats

        Args:
            timestamp: Timestamp string or datetime

        Returns:
            Datetime object or None
        """
        if not timestamp:
            return None

        if isinstance(timestamp, datetime):
            return timestamp

        if isinstance(timestamp, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                try:
                    # Try other common formats
                    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except:
                    return None

        return None

    def _get_holding_type(self, date_acquired: str, date_sold: str) -> str:
        """
        Determine if holding is short-term or long-term

        Args:
            date_acquired: Acquisition date (MM/DD/YYYY)
            date_sold: Sale date (MM/DD/YYYY)

        Returns:
            "Short-term" or "Long-term"
        """
        try:
            acquired = datetime.strptime(date_acquired, "%m/%d/%Y")
            sold = datetime.strptime(date_sold, "%m/%d/%Y")

            holding_days = (sold - acquired).days

            return "Long-term" if holding_days > 365 else "Short-term"

        except:
            return "Short-term"  # Default to short-term if dates invalid

    def save_report(self, report_data: str, filename: str) -> str:
        """
        Save report to file

        Args:
            report_data: Report content
            filename: Filename to save as

        Returns:
            Path to saved file
        """
        filepath = self.data_dir / filename

        with open(filepath, "w") as f:
            f.write(report_data)

        logger.info(f"Saved tax report: {filepath}")

        return str(filepath)


# Global instance
tax_report_generator: Optional[TaxReportGenerator] = None


def get_tax_report_generator() -> TaxReportGenerator:
    """
    Get or create global tax report generator instance

    Returns:
        TaxReportGenerator instance
    """
    global tax_report_generator

    if tax_report_generator is None:
        tax_report_generator = TaxReportGenerator()

    return tax_report_generator
