"""
Simple entry point for running the trading bot.

This module delegates to :mod:`trading_bot.app` to parse command line
arguments, set up the dependency injection container and run the bot.
It can be invoked directly with ``python -m project.main`` or
``python project/main.py``.
"""

from trading_bot.app import parse_args, setup_container, TradingBot


def run_bot() -> None:
    """Parse command line arguments and start the trading bot."""
    args = parse_args()
    container = setup_container(args)
    bot = TradingBot(container)
    bot.run()


if __name__ == "__main__":
    run_bot()