"""
Command line interface for the trading bot.
"""
import argparse
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Modular trading bot")
    sub = parser.add_subparsers(dest="cmd", required=True)
    back = sub.add_parser("backtest", help="Run a backtest over a CSV file")
    back.add_argument("--config", required=True)
    back.add_argument("--csv")
    back.add_argument("--start")
    back.add_argument("--end")
    live = sub.add_parser("live", help="Run live trading")
    live.add_argument("--config", required=True)
    live.add_argument("--dry-run", action="store_true", default=True)
    live.add_argument("--send", action="store_true")
    return parser
