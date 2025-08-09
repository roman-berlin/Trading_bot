"""
Configurable parameters for the trading bot.

These variables define the behaviour of the strategy and risk
management.  You can adjust them without modifying the core logic.
"""

from dataclasses import dataclass


@dataclass
class BotConfig:
    """Holds configurable parameters for the trading bot."""

    # Symbol to trade (e.g. "EURUSD")
    symbol: str = "EURUSD"

    # Distance in pips the price must travel within the time window to
    # trigger a trade.  Equivalent to Distance_pips in the MQL5 EA.
    distance_pips: float = 10.0

    # Time window (seconds) in which the price movement must occur
    # before resetting.  Equivalent to Time_seconds in MQL5.
    time_seconds: int = 60

    # Fixed lot size when money management (MM) is disabled.
    lot_size: float = 0.01

    # Magic number used to tag orders from this EA/bot.
    magic_number: int = 987654

    # Money management coefficient.  When >0 the lot size will be
    # calculated as (equity / 10 000) * MM.  If 0, fixed lot size is
    # used.
    mm: float = 0.0

    # Maximum lot size allowed when MM is enabled.
    mm_max_lot: float = 10.0

    # Take profit and stop loss in pips.
    take_profit_pips: float = 20.0
    stop_loss_pips: float = 15.0

    # Trailing stop in pips (0 disables trailing stop).
    trailing_stop: float = 0.0

    # Enable debug messages to print out internal state.
    enable_debug: bool = True
