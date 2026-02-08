"""
Data Validator Service

Validates CSV structure, data quality, and integrity checks.
Ensures all trading data meets quality standards before display.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from decimal import Decimal


class DataValidator:
    """Validate trading data for quality and integrity"""

    def __init__(self):
        """Initialize data validator"""
        pass

    def validate_csv_data(self, csv_path: Path) -> Dict[str, Any]:
        """
        Validate CSV structure and data quality

        Args:
            csv_path: Path to CSV file

        Returns:
            Dictionary with validation results
        """
        required_columns = [
            "id",
            "symbol",
            "strategy",
            "entry_time",
            "exit_time",
            "pnl_usd",
            "status",
        ]

        issues = []
        row_count = 0

        # Check file exists
        if not csv_path.exists():
            return {
                "valid": False,
                "issues": [f"CSV file not found: {csv_path}"],
                "row_count": 0,
            }

        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                if not headers:
                    return {
                        "valid": False,
                        "issues": ["CSV file is empty or has no headers"],
                        "row_count": 0,
                    }

                # Validate headers
                missing_columns = set(required_columns) - set(headers)
                if missing_columns:
                    issues.append(f"Missing columns: {', '.join(missing_columns)}")

                # Validate each row
                for row_num, row in enumerate(reader, start=2):
                    row_count += 1

                    # Validate timestamp format
                    for time_field in ["entry_time", "exit_time"]:
                        if time_field in row and row.get(time_field):
                            try:
                                ts = datetime.fromisoformat(row[time_field])

                                # Check for future timestamps
                                if ts > datetime.now():
                                    issues.append(
                                        f"Row {row_num}: {time_field} is in the future"
                                    )
                            except (ValueError, TypeError):
                                issues.append(
                                    f"Row {row_num}: Invalid {time_field} format"
                                )

                    # Validate pnl_usd is numeric
                    if "pnl_usd" in row:
                        try:
                            pnl = float(row.get("pnl_usd", 0))

                            # Check for extreme values (likely data errors)
                            if abs(pnl) > 100000:
                                issues.append(
                                    f"Row {row_num}: Suspicious P&L value: ${pnl}"
                                )
                        except (ValueError, TypeError):
                            issues.append(f"Row {row_num}: Invalid pnl_usd value")

                    # Validate status
                    if "status" in row:
                        valid_statuses = ["open", "closed", "pending"]
                        status = row.get("status", "").lower()
                        if status and status not in valid_statuses:
                            issues.append(
                                f"Row {row_num}: Invalid status '{status}' "
                                f"(must be one of {valid_statuses})"
                            )

        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Error reading CSV: {str(e)}"],
                "row_count": 0,
            }

        return {"valid": len(issues) == 0, "issues": issues, "row_count": row_count}

    def validate_polymarket_prices(
        self, yes_price: float, no_price: float
    ) -> Dict[str, Any]:
        """
        Validate Polymarket price ranges

        Args:
            yes_price: Yes side price
            no_price: No side price

        Returns:
            Validation result
        """
        issues = []

        # Validate yes price
        if not (0 <= yes_price <= 1):
            issues.append(f"Yes price {yes_price} out of range (0-1)")

        # Validate no price
        if not (0 <= no_price <= 1):
            issues.append(f"No price {no_price} out of range (0-1)")

        # Validate sum
        sum_price = yes_price + no_price
        if not (0.85 <= sum_price <= 1.05):
            issues.append(
                f"Price sum {sum_price:.4f} is suspicious " f"(expected 0.85-1.05)"
            )

        return {"valid": len(issues) == 0, "issues": issues}

    def validate_crypto_price(self, symbol: str, price: float) -> Dict[str, Any]:
        """
        Validate cryptocurrency price ranges

        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            price: Price in USD

        Returns:
            Validation result
        """
        # Reasonable price ranges (as of 2026)
        price_ranges = {
            "BTC": (10000, 200000),
            "ETH": (500, 20000),
            "SOL": (10, 500),
            "XRP": (0.10, 10),
            "ADA": (0.10, 5),
            "MATIC": (0.10, 10),
            "AVAX": (5, 200),
        }

        issues = []
        symbol_upper = symbol.upper()

        if symbol_upper in price_ranges:
            min_price, max_price = price_ranges[symbol_upper]

            if not (min_price <= price <= max_price):
                issues.append(
                    f"{symbol} price ${price} outside reasonable range "
                    f"(${min_price}-${max_price})"
                )

        return {"valid": len(issues) == 0, "issues": issues}

    def check_data_integrity(
        self,
        trades: List[Dict[str, Any]],
        calculated_total_pnl: float,
        displayed_total_pnl: float,
        calculated_win_rate: float,
        displayed_win_rate: float,
        total_trades_count: int,
    ) -> Dict[str, Any]:
        """
        Run integrity checks on dashboard data

        Args:
            trades: List of all trades
            calculated_total_pnl: Freshly calculated total P&L
            displayed_total_pnl: P&L shown on dashboard
            calculated_win_rate: Freshly calculated win rate
            displayed_win_rate: Win rate shown on dashboard
            total_trades_count: Total trades shown on dashboard

        Returns:
            Integrity check results
        """
        issues = []

        # Check total P&L matches
        pnl_diff = abs(calculated_total_pnl - displayed_total_pnl)
        if pnl_diff > 0.01:
            issues.append(
                f"Total P&L mismatch: calculated ${calculated_total_pnl:.2f}, "
                f"displayed ${displayed_total_pnl:.2f} (diff: ${pnl_diff:.2f})"
            )

        # Check win rate matches
        wr_diff = abs(calculated_win_rate - displayed_win_rate)
        if wr_diff > 0.1:
            issues.append(
                f"Win rate mismatch: calculated {calculated_win_rate:.2f}%, "
                f"displayed {displayed_win_rate:.2f}% (diff: {wr_diff:.2f}%)"
            )

        # Check trade count matches
        if len(trades) != total_trades_count:
            issues.append(
                f"Trade count mismatch: found {len(trades)} trades, "
                f"displayed {total_trades_count}"
            )

        # Check for suspicious win rate (100% with many trades)
        if calculated_win_rate == 100.0 and len(trades) > 10:
            issues.append(
                f"Win rate is exactly 100% with {len(trades)} trades - "
                f"this is statistically suspicious"
            )

        # Check for outlier trades
        if trades:
            pnls = [t["pnl_usd"] for t in trades]
            mean = sum(pnls) / len(pnls)

            if len(pnls) > 1:
                variance = sum((x - mean) ** 2 for x in pnls) / len(pnls)
                std = variance**0.5

                outliers = [p for p in pnls if abs(p - mean) > 3 * std]
                if outliers:
                    issues.append(
                        f"Found {len(outliers)} outlier trades "
                        f"(>3 std deviations from mean)"
                    )

        # Check for future timestamps
        future_trades = [
            t
            for t in trades
            if datetime.fromisoformat(t["entry_time"]) > datetime.now()
        ]
        if future_trades:
            issues.append(f"{len(future_trades)} trades have future timestamps")

        return {"healthy": len(issues) == 0, "issues": issues, "checks_run": 5}
