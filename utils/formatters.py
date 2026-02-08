"""
Formatters Utility

Consolidated formatting functions for consistent display across the application:
- Currency formatting
- Percentage formatting
- Date/time formatting
- Number formatting
- Duration formatting
"""

from typing import Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal


def format_currency(
    amount: Union[float, Decimal, int],
    currency: str = "USD",
    decimals: int = 2,
    show_sign: bool = False,
) -> str:
    """
    Format a number as currency

    Args:
        amount: Amount to format
        currency: Currency code (default: USD)
        decimals: Number of decimal places
        show_sign: Always show + sign for positive numbers

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(-50.25, show_sign=True)
        '-$50.25'
    """
    if amount is None:
        return f"${'-' * decimals}"

    symbol = "$" if currency == "USD" else currency

    # Handle sign
    sign = ""
    abs_amount = abs(float(amount))

    if amount < 0:
        sign = "-"
    elif show_sign and amount > 0:
        sign = "+"

    # Format with thousands separator
    formatted = f"{abs_amount:,.{decimals}f}"

    return f"{sign}{symbol}{formatted}"


def format_percentage(
    value: Union[float, Decimal],
    decimals: int = 2,
    show_sign: bool = True,
    multiply: bool = False,
) -> str:
    """
    Format a number as percentage

    Args:
        value: Value to format
        decimals: Number of decimal places
        show_sign: Show + sign for positive numbers
        multiply: Multiply by 100 (if value is 0.05 and multiply=True, shows 5%)

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(0.0523, multiply=True)
        '+5.23%'
        >>> format_percentage(5.23)
        '+5.23%'
    """
    if value is None:
        return "-%"

    actual_value = float(value) * 100 if multiply else float(value)

    sign = ""
    if actual_value > 0 and show_sign:
        sign = "+"
    elif actual_value < 0:
        sign = "-"

    return f"{sign}{abs(actual_value):.{decimals}f}%"


def format_number(
    number: Union[float, Decimal, int],
    decimals: int = 2,
    compact: bool = False,
    show_sign: bool = False,
) -> str:
    """
    Format a number with thousands separators

    Args:
        number: Number to format
        decimals: Number of decimal places
        compact: Use compact notation (K, M, B, T)
        show_sign: Show + sign for positive numbers

    Returns:
        Formatted number string

    Examples:
        >>> format_number(1234567.89)
        '1,234,567.89'
        >>> format_number(1234567.89, compact=True)
        '1.23M'
    """
    if number is None:
        return "-"

    num = float(number)

    if compact:
        return format_compact_number(num, decimals, show_sign)

    sign = ""
    if num > 0 and show_sign:
        sign = "+"
    elif num < 0:
        sign = "-"
        num = abs(num)

    return f"{sign}{num:,.{decimals}f}"


def format_compact_number(
    number: Union[float, int], decimals: int = 2, show_sign: bool = False
) -> str:
    """
    Format number in compact notation (K, M, B, T)

    Args:
        number: Number to format
        decimals: Number of decimal places
        show_sign: Show + sign for positive numbers

    Returns:
        Compact formatted number

    Examples:
        >>> format_compact_number(1234567)
        '1.23M'
        >>> format_compact_number(42500)
        '42.50K'
    """
    if number is None:
        return "-"

    num = float(number)
    sign = ""

    if num < 0:
        sign = "-"
        num = abs(num)
    elif show_sign and num > 0:
        sign = "+"

    if num >= 1_000_000_000_000:
        return f"{sign}{num / 1_000_000_000_000:.{decimals}f}T"
    elif num >= 1_000_000_000:
        return f"{sign}{num / 1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:
        return f"{sign}{num / 1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{sign}{num / 1_000:.{decimals}f}K"
    else:
        return f"{sign}{num:.{decimals}f}"


def format_datetime(
    dt: Union[datetime, str],
    format_type: str = "standard",
    timezone: Optional[str] = None,
) -> str:
    """
    Format datetime in various formats

    Args:
        dt: Datetime object or ISO string
        format_type: Format type ('standard', 'short', 'time_only', 'date_only', 'iso')
        timezone: Timezone name (not implemented yet)

    Returns:
        Formatted datetime string

    Examples:
        >>> format_datetime(datetime.now(), 'standard')
        '2024-02-08 14:32:15'
        >>> format_datetime(datetime.now(), 'short')
        '02/08/24 2:32 PM'
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except:
            return dt

    if not isinstance(dt, datetime):
        return str(dt)

    formats = {
        "standard": "%Y-%m-%d %H:%M:%S",
        "short": "%m/%d/%y %I:%M %p",
        "time_only": "%H:%M:%S",
        "date_only": "%Y-%m-%d",
        "iso": "%Y-%m-%dT%H:%M:%S",
        "friendly": "%B %d, %Y at %I:%M %p",
    }

    format_str = formats.get(format_type, formats["standard"])
    return dt.strftime(format_str)


def format_duration(
    seconds: Union[int, float], compact: bool = False, show_seconds: bool = True
) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds
        compact: Use compact format (1d 2h vs 1 day 2 hours)
        show_seconds: Include seconds in output

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(3665)
        '1 hour 1 minute 5 seconds'
        >>> format_duration(3665, compact=True)
        '1h 1m 5s'
    """
    if seconds is None or seconds < 0:
        return "0s" if compact else "0 seconds"

    delta = timedelta(seconds=int(seconds))

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []

    if days > 0:
        parts.append(f"{days}d" if compact else f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(
            f"{hours}h" if compact else f"{hours} hour{'s' if hours != 1 else ''}"
        )
    if minutes > 0:
        parts.append(
            f"{minutes}m"
            if compact
            else f"{minutes} minute{'s' if minutes != 1 else ''}"
        )
    if show_seconds and (secs > 0 or not parts):
        parts.append(
            f"{secs}s" if compact else f"{secs} second{'s' if secs != 1 else ''}"
        )

    return " ".join(parts) if parts else ("0s" if compact else "0 seconds")


def format_ago(dt: Union[datetime, str]) -> str:
    """
    Format datetime as relative time (e.g., "5 minutes ago")

    Args:
        dt: Datetime object or ISO string

    Returns:
        Relative time string

    Examples:
        >>> format_ago(datetime.now() - timedelta(minutes=5))
        '5 minutes ago'
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except:
            return dt

    if not isinstance(dt, datetime):
        return str(dt)

    now = datetime.now() if dt.tzinfo is None else datetime.now(dt.tzinfo)
    delta = now - dt

    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return format_datetime(dt, "date_only")


def format_price_change(
    current: float,
    previous: float,
    show_sign: bool = True,
    show_percentage: bool = True,
) -> str:
    """
    Format price change with amount and percentage

    Args:
        current: Current price
        previous: Previous price
        show_sign: Show + sign for positive changes
        show_percentage: Include percentage in output

    Returns:
        Formatted price change

    Examples:
        >>> format_price_change(105, 100)
        '+$5.00 (+5.00%)'
    """
    if current is None or previous is None or previous == 0:
        return "-"

    change = current - previous
    change_pct = (change / previous) * 100

    currency_str = format_currency(change, show_sign=show_sign)

    if show_percentage:
        pct_str = format_percentage(change_pct, show_sign=show_sign)
        return f"{currency_str} ({pct_str})"
    else:
        return currency_str


def format_quantity(
    quantity: Union[float, Decimal], decimals: int = 8, trim_zeros: bool = True
) -> str:
    """
    Format quantity (typically for crypto amounts)

    Args:
        quantity: Quantity to format
        decimals: Maximum decimal places
        trim_zeros: Remove trailing zeros

    Returns:
        Formatted quantity

    Examples:
        >>> format_quantity(0.00012345)
        '0.00012345'
        >>> format_quantity(1.50000000)
        '1.5'
    """
    if quantity is None:
        return "-"

    formatted = f"{float(quantity):.{decimals}f}"

    if trim_zeros and "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")

    return formatted


def format_ratio(
    numerator: Union[float, int], denominator: Union[float, int], decimals: int = 2
) -> str:
    """
    Format a ratio

    Args:
        numerator: Numerator value
        denominator: Denominator value
        decimals: Decimal places

    Returns:
        Formatted ratio

    Examples:
        >>> format_ratio(75, 100)
        '0.75'
        >>> format_ratio(3, 4)
        '0.75'
    """
    if denominator is None or denominator == 0:
        return "-"

    ratio = float(numerator) / float(denominator)
    return f"{ratio:.{decimals}f}"


def format_status_badge(status: str, uppercase: bool = True) -> str:
    """
    Format status text consistently

    Args:
        status: Status text
        uppercase: Convert to uppercase

    Returns:
        Formatted status
    """
    if not status:
        return "UNKNOWN"

    status = status.replace("_", " ")

    if uppercase:
        return status.upper()
    else:
        return status.title()


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
