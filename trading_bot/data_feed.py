"""
MetaTrader 5 data feed adapter.

This module encapsulates connection to the MetaTrader 5 terminal and
provides methods for retrieving current bid/ask prices and
historical price data for backtesting.
"""

import datetime
from typing import Optional, Tuple

import pandas as pd
import MetaTrader5 as mt5

from .utils import debug, get_pip_value


class MT5DataFeed:
    """Wraps connection to the MetaTrader 5 terminal."""

    def __init__(self, symbol: str, enable_debug: bool = False) -> None:
        self.symbol = symbol
        self.enable_debug = enable_debug
        self.connected: bool = False
        self.point: float = 0.0
        self.digits: int = 0
        self.pip: float = 0.0

    def connect(self) -> bool:
        """Initialize connection to the MT5 terminal.

        Returns True if the connection succeeds, False otherwise.
        """
        if not mt5.initialize():
            debug("Failed to initialize MT5 connection", self.symbol, self.enable_debug)
            return False
        info = mt5.terminal_info()
        version = mt5.version()
        debug(f"Connected to MT5 terminal: {version}", self.symbol, self.enable_debug)
        # store basic symbol information
        self.point = mt5.symbol_info(self.symbol).point
        self.digits = mt5.symbol_info(self.symbol).digits
        self.pip = get_pip_value(self.point, self.digits)
        self.connected = True
        return True

    def disconnect(self) -> None:
        """Shutdown the MT5 connection."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            debug("MT5 connection closed", self.symbol, self.enable_debug)

    def current_prices(self) -> Tuple[float, float]:
        """Return the current bid and ask prices for the configured symbol."""
        tick = mt5.symbol_info_tick(self.symbol)
        return tick.bid, tick.ask

    def copy_ticks(self, start: datetime.datetime, count: int) -> pd.DataFrame:
        """Retrieve a specified number of ticks starting from a datetime.

        This is primarily useful for backtesting or analysis outside of
        live trading.
        """
        ticks = mt5.copy_ticks_from(self.symbol, start, count, mt5.COPY_TICKS_ALL)
        df = pd.DataFrame(ticks)
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def copy_rates(self, timeframe: int, start: datetime.datetime, count: int) -> pd.DataFrame:
        """Retrieve OHLC bars for a given timeframe starting at a datetime."""
        rates = mt5.copy_rates_from(self.symbol, timeframe, start, count)
        df = pd.DataFrame(rates)
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
