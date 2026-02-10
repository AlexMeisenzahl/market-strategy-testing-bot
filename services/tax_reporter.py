"""
Tax Reporter - IRS Form 8949 Generator
Generates tax reports for cryptocurrency trading
Supports FIFO, LIFO, and Specific ID cost basis methods
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
import csv
import io
from decimal import Decimal

CostBasisMethod = Literal["FIFO", "LIFO", "SPECIFIC_ID"]


class TaxReporter:
    """
    Generates IRS Form 8949 reports for cryptocurrency trading.
    Calculates capital gains/losses and classifies as short-term or long-term.
    """

    def __init__(self):
        self.long_term_threshold_days = 365  # Holdings > 1 year are long-term

    def generate_form_8949(
        self, trades: List[Dict[str, Any]], year: int, method: CostBasisMethod = "FIFO"
    ) -> str:
        """
        Generate IRS Form 8949 report.

        Args:
            trades: List of trade dictionaries with buy/sell info
            year: Tax year to generate report for
            method: Cost basis calculation method (FIFO, LIFO, SPECIFIC_ID)

        Returns:
            CSV string in Form 8949 format
        """
        # Filter trades for the specified year
        year_trades = self._filter_trades_by_year(trades, year)

        if not year_trades:
            return self._generate_empty_report(year)

        # Calculate cost basis and gains/losses
        transactions = self._calculate_gains_losses(year_trades, method)

        # Separate into short-term and long-term
        short_term = [t for t in transactions if not t["is_long_term"]]
        long_term = [t for t in transactions if t["is_long_term"]]

        # Generate CSV
        return self._generate_csv_report(short_term, long_term, year, method)

    def _filter_trades_by_year(
        self, trades: List[Dict[str, Any]], year: int
    ) -> List[Dict[str, Any]]:
        """Filter trades that occurred in the specified year."""
        filtered = []

        for trade in trades:
            date = trade.get("date") or trade.get("timestamp")
            if not date:
                continue

            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

            if date.year == year:
                filtered.append(trade)

        return filtered

    def _calculate_gains_losses(
        self, trades: List[Dict[str, Any]], method: CostBasisMethod
    ) -> List[Dict[str, Any]]:
        """
        Calculate capital gains/losses for each transaction.

        This is a simplified implementation. In production, you would need:
        1. Proper tracking of individual lots (purchases)
        2. Matching sales to purchases based on method (FIFO/LIFO/Specific ID)
        3. Handling of partial lot sales
        4. Tracking of fees and commissions
        """
        transactions = []

        # Group by asset
        assets = {}
        for trade in trades:
            asset = trade.get("asset") or trade.get("symbol", "UNKNOWN")
            if asset not in assets:
                assets[asset] = {"buys": [], "sells": []}

            if trade.get("side") == "buy" or trade.get("type") == "buy":
                assets[asset]["buys"].append(trade)
            elif trade.get("side") == "sell" or trade.get("type") == "sell":
                assets[asset]["sells"].append(trade)

        # Calculate gains for each asset
        for asset, data in assets.items():
            buys = sorted(data["buys"], key=lambda x: self._get_trade_date(x))
            sells = sorted(data["sells"], key=lambda x: self._get_trade_date(x))

            if method == "FIFO":
                transactions.extend(self._calculate_fifo(asset, buys, sells))
            elif method == "LIFO":
                transactions.extend(self._calculate_lifo(asset, buys, sells))
            elif method == "SPECIFIC_ID":
                # Specific ID requires manual lot selection - simplified here
                transactions.extend(self._calculate_fifo(asset, buys, sells))

        return transactions

    def _calculate_fifo(
        self, asset: str, buys: List[Dict], sells: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Calculate gains using First-In-First-Out method."""
        transactions = []
        buy_queue = buys.copy()

        for sell in sells:
            sell_amount = sell.get("amount", 0)
            sell_price = sell.get("price", 0)
            sell_date = self._get_trade_date(sell)
            sell_proceeds = sell_amount * sell_price

            remaining_to_sell = sell_amount
            cost_basis = 0
            acquisition_date = None

            while remaining_to_sell > 0 and buy_queue:
                buy = buy_queue[0]
                buy_amount = buy.get("amount", 0)
                buy_price = buy.get("price", 0)
                buy_date = self._get_trade_date(buy)

                if not acquisition_date:
                    acquisition_date = buy_date

                if buy_amount <= remaining_to_sell:
                    # Use entire buy lot
                    cost_basis += buy_amount * buy_price
                    remaining_to_sell -= buy_amount
                    buy_queue.pop(0)
                else:
                    # Use partial buy lot
                    cost_basis += remaining_to_sell * buy_price
                    buy["amount"] = buy_amount - remaining_to_sell
                    remaining_to_sell = 0

            if acquisition_date and sell_date:
                days_held = (sell_date - acquisition_date).days
                is_long_term = days_held >= self.long_term_threshold_days
            else:
                is_long_term = False

            gain_loss = sell_proceeds - cost_basis

            transactions.append(
                {
                    "asset": asset,
                    "description": f"{sell_amount:.8f} {asset}",
                    "acquisition_date": (
                        acquisition_date.strftime("%m/%d/%Y")
                        if acquisition_date
                        else "VARIOUS"
                    ),
                    "sale_date": (
                        sell_date.strftime("%m/%d/%Y") if sell_date else "UNKNOWN"
                    ),
                    "proceeds": round(sell_proceeds, 2),
                    "cost_basis": round(cost_basis, 2),
                    "gain_loss": round(gain_loss, 2),
                    "is_long_term": is_long_term,
                    "days_held": days_held if acquisition_date and sell_date else 0,
                }
            )

        return transactions

    def _calculate_lifo(
        self, asset: str, buys: List[Dict], sells: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Calculate gains using Last-In-First-Out method."""
        # Reverse buy order for LIFO
        buys_reversed = list(reversed(buys))
        return self._calculate_fifo(asset, buys_reversed, sells)

    def _get_trade_date(self, trade: Dict[str, Any]) -> Optional[datetime]:
        """Extract and parse trade date."""
        date = trade.get("date") or trade.get("timestamp")
        if not date:
            return None

        if isinstance(date, str):
            try:
                return datetime.fromisoformat(date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        return date

    def _generate_csv_report(
        self,
        short_term: List[Dict],
        long_term: List[Dict],
        year: int,
        method: CostBasisMethod,
    ) -> str:
        """Generate CSV report in Form 8949 format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            ["IRS Form 8949 - Sales and Other Dispositions of Capital Assets"]
        )
        writer.writerow([f"Tax Year: {year}"])
        writer.writerow([f"Cost Basis Method: {method}"])
        writer.writerow([])

        # Part I - Short-Term Capital Gains and Losses
        writer.writerow(["PART I - SHORT-TERM CAPITAL GAINS AND LOSSES"])
        writer.writerow(["Assets held 1 year or less"])
        writer.writerow([])
        writer.writerow(
            [
                "(a) Description of property",
                "(b) Date acquired",
                "(c) Date sold",
                "(d) Proceeds",
                "(e) Cost basis",
                "(f) Gain or (loss)",
            ]
        )

        short_term_total = 0
        for transaction in short_term:
            writer.writerow(
                [
                    transaction["description"],
                    transaction["acquisition_date"],
                    transaction["sale_date"],
                    f"${transaction['proceeds']:.2f}",
                    f"${transaction['cost_basis']:.2f}",
                    f"${transaction['gain_loss']:.2f}",
                ]
            )
            short_term_total += transaction["gain_loss"]

        writer.writerow([])
        writer.writerow(
            ["Short-Term Total:", "", "", "", "", f"${short_term_total:.2f}"]
        )
        writer.writerow([])
        writer.writerow([])

        # Part II - Long-Term Capital Gains and Losses
        writer.writerow(["PART II - LONG-TERM CAPITAL GAINS AND LOSSES"])
        writer.writerow(["Assets held more than 1 year"])
        writer.writerow([])
        writer.writerow(
            [
                "(a) Description of property",
                "(b) Date acquired",
                "(c) Date sold",
                "(d) Proceeds",
                "(e) Cost basis",
                "(f) Gain or (loss)",
            ]
        )

        long_term_total = 0
        for transaction in long_term:
            writer.writerow(
                [
                    transaction["description"],
                    transaction["acquisition_date"],
                    transaction["sale_date"],
                    f"${transaction['proceeds']:.2f}",
                    f"${transaction['cost_basis']:.2f}",
                    f"${transaction['gain_loss']:.2f}",
                ]
            )
            long_term_total += transaction["gain_loss"]

        writer.writerow([])
        writer.writerow(["Long-Term Total:", "", "", "", "", f"${long_term_total:.2f}"])
        writer.writerow([])

        # Summary
        writer.writerow(["SUMMARY"])
        writer.writerow(["Short-Term Gain/Loss:", f"${short_term_total:.2f}"])
        writer.writerow(["Long-Term Gain/Loss:", f"${long_term_total:.2f}"])
        writer.writerow(
            ["Total Gain/Loss:", f"${(short_term_total + long_term_total):.2f}"]
        )
        writer.writerow([])
        writer.writerow(
            [
                "Note: This is a simplified report. Consult a tax professional for accurate filing."
            ]
        )

        return output.getvalue()

    def _generate_empty_report(self, year: int) -> str:
        """Generate an empty report when no trades exist for the year."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            ["IRS Form 8949 - Sales and Other Dispositions of Capital Assets"]
        )
        writer.writerow([f"Tax Year: {year}"])
        writer.writerow([])
        writer.writerow(["No taxable transactions found for this year."])

        return output.getvalue()

    def calculate_tax_summary(
        self, trades: List[Dict[str, Any]], year: int, method: CostBasisMethod = "FIFO"
    ) -> Dict[str, Any]:
        """
        Calculate tax summary without generating full report.

        Returns:
            Dictionary with summary statistics
        """
        year_trades = self._filter_trades_by_year(trades, year)

        if not year_trades:
            return {
                "year": year,
                "method": method,
                "short_term_gain": 0,
                "long_term_gain": 0,
                "total_gain": 0,
                "transaction_count": 0,
            }

        transactions = self._calculate_gains_losses(year_trades, method)

        short_term = [t for t in transactions if not t["is_long_term"]]
        long_term = [t for t in transactions if t["is_long_term"]]

        short_term_gain = sum(t["gain_loss"] for t in short_term)
        long_term_gain = sum(t["gain_loss"] for t in long_term)

        return {
            "year": year,
            "method": method,
            "short_term_gain": round(short_term_gain, 2),
            "long_term_gain": round(long_term_gain, 2),
            "total_gain": round(short_term_gain + long_term_gain, 2),
            "transaction_count": len(transactions),
            "short_term_count": len(short_term),
            "long_term_count": len(long_term),
        }

    def generate_report(self, year: int = None) -> List[Dict[str, Any]]:
        """
        Generate tax report data for download

        Args:
            year: Tax year (defaults to current year)

        Returns:
            List of trade dictionaries formatted for CSV export
        """
        if year is None:
            year = datetime.now().year

        # Get trades from data files
        from dashboard.services.data_parser import DataParser
        from pathlib import Path

        parser = DataParser(logs_dir=Path("data"))
        trades = parser.get_all_trades()

        # Filter by year
        year_trades = self._filter_trades_by_year(trades, year)

        # Calculate gains/losses
        transactions = self._calculate_gains_losses(year_trades, "FIFO")

        # Format for CSV
        report_data = []
        for txn in transactions:
            report_data.append(
                {
                    "date": txn.get("sale_date", ""),
                    "type": "SALE",
                    "amount": txn.get("amount", 0),
                    "symbol": txn.get("asset", ""),
                    "realized_pnl": round(txn.get("gain_loss", 0), 2),
                }
            )

        return report_data


# Example usage
if __name__ == "__main__":
    # Sample trades for testing
    sample_trades = [
        {
            "date": "2024-01-15",
            "side": "buy",
            "asset": "BTC",
            "amount": 0.5,
            "price": 40000,
        },
        {
            "date": "2024-06-15",
            "side": "sell",
            "asset": "BTC",
            "amount": 0.5,
            "price": 45000,
        },
    ]

    reporter = TaxReporter()
    report = reporter.generate_form_8949(sample_trades, 2024, "FIFO")
    print(report)

    summary = reporter.calculate_tax_summary(sample_trades, 2024, "FIFO")
    print("\nSummary:", summary)
