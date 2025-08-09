"""
Utility functions for logging and pip conversion.

This module contains helpers for printing debug messages with
timestamps, converting price differences to pips and vice versa, and
calculating pip values based on the number of decimal places in
currency pairs.
"""

import datetime
from typing import Optional


def debug(message: str, symbol: Optional[str] = None, enabled: bool = True) -> None:
    """Print a timestamped debug message if debugging is enabled.

    Parameters
    ----------
    message: str
        The message to print.
    symbol: Optional[str]
        Optional symbol to include in the message prefix.
    enabled: bool
        Whether to actually print the message.
    """
    if not enabled:
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{symbol}] " if symbol else ""
    print(f"{timestamp} {prefix}{message}")


def get_pip_value(point: float, digits: int) -> float:
    """Calculate the pip value based on the broker's point size and digits.

    In five- or three-decimal pricing (e.g. EURUSD at 1.12345), one pip is
    ten points.  Otherwise one pip equals one point.

    Returns
    -------
    float
        The value of one pip.
    """
    return point * 10 if digits in (5, 3) else point
