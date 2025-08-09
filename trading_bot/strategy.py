"""
Trading strategy module.

Implements a distance/time breakout strategy similar to the provided
MQL5 expert advisor.  The strategy monitors the difference between the
current price and the last reference price and triggers a trade if
that difference exceeds a configured number of pips within a given
time window.
"""

import datetime
from dataclasses import dataclass

from .config import BotConfig
from .execution import OrderExecutor
from .utils import debug


@dataclass
class ReferencePoint:
    """Stores the time and price at which the reference was last updated."""
    time: datetime.datetime
    price: float


class DistanceTimeStrategy:
    """Distance/time breakout strategy.

    Attributes
    ----------
    config : BotConfig
        The configuration parameters for the strategy.
    executor : OrderExecutor
        Responsible for placing trades.
    ref_buy : ReferencePoint
        Last reference point for buy checks (time and price).
    ref_sell : ReferencePoint
        Last reference point for sell checks (time and price).
    pip_value : float
        Value of one pip (provided by data feed).
    """

    def __init__(self, config: BotConfig, executor: OrderExecutor, pip_value: float) -> None:
        now = datetime.datetime.now()
        # initialize reference points at current price/time; values will be overwritten on first update
        self.config = config
        self.executor = executor
        self.ref_buy = ReferencePoint(now, 0.0)
        self.ref_sell = ReferencePoint(now, 0.0)
        self.pip_value = pip_value

    def reset_buy(self, current_bid: float) -> None:
        """Reset the reference point for buy checks."""
        self.ref_buy.time = datetime.datetime.now()
        self.ref_buy.price = current_bid
        debug(f"Buy reference reset: price={current_bid}", self.config.symbol, self.config.enable_debug)

    def reset_sell(self, current_ask: float) -> None:
        """Reset the reference point for sell checks."""
        self.ref_sell.time = datetime.datetime.now()
        self.ref_sell.price = current_ask
        debug(f"Sell reference reset: price={current_ask}", self.config.symbol, self.config.enable_debug)

    def update(self, bid: float, ask: float) -> None:
        """Evaluate strategy conditions on each tick and place trades when triggered."""
        now = datetime.datetime.now()
        # compute differences in seconds since last check
        buy_time_diff = (now - self.ref_buy.time).total_seconds()
        sell_time_diff = (now - self.ref_sell.time).total_seconds()
        # compute price differences in pips
        buy_price_diff = (bid - self.ref_buy.price) / self.pip_value
        sell_price_diff = (self.ref_sell.price - ask) / self.pip_value
        # check buy condition
        if buy_price_diff >= self.config.distance_pips and buy_time_diff <= self.config.time_seconds:
            debug(f"Buy condition met: +{buy_price_diff:.1f} pips in {buy_time_diff:.0f} seconds",
                  self.config.symbol, self.config.enable_debug)
            if self.executor.open_buy(bid, ask, self.pip_value):
                self.reset_buy(bid)
        # check sell condition
        if sell_price_diff >= self.config.distance_pips and sell_time_diff <= self.config.time_seconds:
            debug(f"Sell condition met: -{sell_price_diff:.1f} pips in {sell_time_diff:.0f} seconds",
                  self.config.symbol, self.config.enable_debug)
            if self.executor.open_sell(bid, ask, self.pip_value):
                self.reset_sell(ask)
        # update reference points if time window expired
        if buy_time_diff > self.config.time_seconds:
            self.reset_buy(bid)
        if sell_time_diff > self.config.time_seconds:
            self.reset_sell(ask)
        # trailing stop management
        self.executor.modify_trailing_stops(self.pip_value)
