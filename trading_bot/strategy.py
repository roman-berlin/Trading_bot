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

from typing import Optional, Any

from .container import Container
from .config import BotConfig
from .interfaces import IOrderExecutor, IBroker
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
    _container : Container
        The dependency injection container.
    _executor : IOrderExecutor
        Responsible for placing trades.
    _pip_value : float
        Value of one pip (provided by data feed).
    ref_buy : ReferencePoint
        Last reference point for buy checks (time and price).
    ref_sell : ReferencePoint
        Last reference point for sell checks (time and price).
    """

    def __init__(
        self,
        container: Any,
        executor: Optional[IOrderExecutor] = None,
        pip_value: float = 0.0,
    ) -> None:
        """Initialize the distance/time breakout strategy.

        Parameters
        ----------
        container : Container | BotConfig
            The dependency injection container used to resolve other
            components or a plain :class:`BotConfig` instance when
            running without the DI system (e.g., in backtests).
        executor : Optional[IOrderExecutor], default None
            Explicit order executor.  If omitted and `container` has a
            ``resolve`` method, the executor will be resolved from the
            container.  If neither condition is met, an error will be
            raised.
        pip_value : float, default 0.0
            Size of one pip in price units.  If zero and an
            :class:`IBroker` can be resolved from the container, it will
            be obtained from the broker.
        """
        # Determine whether we have a real container or just a config
        if hasattr(container, "resolve"):
            self._container = container  # type: ignore[assignment]
        else:
            # Store a dummy container reference for type consistency; actual
            # resolution will be skipped and config stored separately
            self._container = None
        self._config_or_container = container

        # Resolve executor
        if executor is not None:
            self._executor = executor
        elif self._container and hasattr(self._container, "resolve"):
            # Attempt to resolve IOrderExecutor from container
            try:
                self._executor = self._container.resolve(IOrderExecutor)
            except Exception as e:
                raise ValueError(f"Unable to resolve order executor: {e}")
        else:
            raise ValueError("Order executor must be provided when no container is available")

        self._pip_value = pip_value

        # Initialize reference points
        now = datetime.datetime.now()
        self.ref_buy = ReferencePoint(now, 0.0)
        self.ref_sell = ReferencePoint(now, 0.0)

        # Obtain pip value from broker if not provided
        if self._pip_value == 0:
            try:
                broker: Optional[IBroker] = None
                if self._container and hasattr(self._container, "resolve"):
                    broker = self._container.resolve(IBroker)  # type: ignore[arg-type]
                # If broker provides pip_value, compute for current symbol
                if broker and hasattr(broker, "pip_value"):
                    cfg = self._get_config()
                    self._pip_value = broker.pip_value(cfg.symbol)
            except Exception as e:
                cfg = self._get_config()
                debug(f"Failed to get pip value from broker: {e}", cfg.symbol, cfg.enable_debug)
    
    def _get_config(self) -> BotConfig:
        """Return the current configuration.

        If a dependency injection container is available this method
        resolves the :class:`BotConfig` from it, otherwise it assumes
        that `_config_or_container` is a direct :class:`BotConfig` instance.
        """
        if self._container and hasattr(self._container, "resolve"):
            return self._container.resolve(BotConfig)
        # Fallback: assume stored object is a BotConfig
        return self._config_or_container  # type: ignore[return-value]

    def reset_buy(self, current_bid: float) -> None:
        """Reset the reference point for buy checks."""
        config = self._get_config()
        self.ref_buy.time = datetime.datetime.now()
        self.ref_buy.price = current_bid
        debug(f"Buy reference reset: price={current_bid}", config.symbol, config.enable_debug)

    def reset_sell(self, current_ask: float) -> None:
        """Reset the reference point for sell checks."""
        config = self._get_config()
        self.ref_sell.time = datetime.datetime.now()
        self.ref_sell.price = current_ask
        debug(f"Sell reference reset: price={current_ask}", config.symbol, config.enable_debug)

    def update(self, bid: float, ask: float) -> None:
        """Evaluate strategy conditions on each tick and place trades when triggered."""
        config = self._get_config()
        now = datetime.datetime.now()
        
        # compute differences in seconds since last check
        buy_time_diff = (now - self.ref_buy.time).total_seconds()
        sell_time_diff = (now - self.ref_sell.time).total_seconds()
        
        # compute price differences in pips
        buy_price_diff = (bid - self.ref_buy.price) / self._pip_value if self._pip_value > 0 else 0
        sell_price_diff = (self.ref_sell.price - ask) / self._pip_value if self._pip_value > 0 else 0
        
        # check buy condition
        if buy_price_diff >= config.distance_pips and buy_time_diff <= config.time_seconds:
            debug(f"Buy condition met: +{buy_price_diff:.1f} pips in {buy_time_diff:.0f} seconds",
                  config.symbol, config.enable_debug)
            if self._executor.open_buy(bid, ask, self._pip_value):
                self.reset_buy(bid)
        
        # check sell condition
        if sell_price_diff >= config.distance_pips and sell_time_diff <= config.time_seconds:
            debug(f"Sell condition met: -{sell_price_diff:.1f} pips in {sell_time_diff:.0f} seconds",
                  config.symbol, config.enable_debug)
            if self._executor.open_sell(bid, ask, self._pip_value):
                self.reset_sell(ask)
        
        # update reference points if time window expired
        if buy_time_diff > config.time_seconds:
            self.reset_buy(bid)
        if sell_time_diff > config.time_seconds:
            self.reset_sell(ask)
        
        # trailing stop management
        if hasattr(self._executor, 'modify_trailing_stops'):
            self._executor.modify_trailing_stops(self._pip_value)
