"""
Entry point for the modular trading bot.

This script sets up the configuration, connects to the MetaTrader 5
terminal, and runs the distance/time strategy.  It is intended to be
run as a long‑running process or supervised service.  Use Ctrl+C to
stop.
"""

import time

from trading_bot.config import BotConfig
from trading_bot.data_feed import MT5DataFeed
from trading_bot.risk_manager import RiskManager
from trading_bot.execution import OrderExecutor
from trading_bot.strategy import DistanceTimeStrategy
from trading_bot.utils import debug


def run_bot():
    # Load configuration; you can modify the default values here or
    # instantiate BotConfig with different arguments.
    config = BotConfig()

    # Initialize data feed
    feed = MT5DataFeed(config.symbol, enable_debug=config.enable_debug)
    if not feed.connect():
        return

    # Initialize risk manager and executor
    risk_manager = RiskManager(config, enable_debug=config.enable_debug)
    executor = OrderExecutor(config, risk_manager)

    # Set up strategy with the pip value from the data feed
    strategy = DistanceTimeStrategy(config, executor, feed.pip)

    debug(f"Bot started on symbol {config.symbol}", config.symbol, config.enable_debug)

    try:
        while True:
            bid, ask = feed.current_prices()
            # On first iteration, initialize reference prices
            if strategy.ref_buy.price == 0.0:
                strategy.reset_buy(bid)
            if strategy.ref_sell.price == 0.0:
                strategy.reset_sell(ask)
            strategy.update(bid, ask)
            # Sleep briefly to avoid spamming the API; adjust to your needs
            time.sleep(1)
    except KeyboardInterrupt:
        debug("Bot interrupted by user", config.symbol, config.enable_debug)
    finally:
        feed.disconnect()


if __name__ == "__main__":
    run_bot()
