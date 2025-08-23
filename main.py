"""
Command line entry point.
"""
from trading_bot.cli import build_parser
from trading_bot.config import Config
from trading_bot.exec.backtest_exec import BacktestExec
from trading_bot.data.csv_feed import CsvFeed
from trading_bot.strategy.distance_time import DistanceTime

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd == "backtest":
        cfg = Config.load(args.config)
        csv_path = args.csv or cfg.backtest.get("csv_path")
        feed_iter = CsvFeed(csv_path).iter()
        strat = DistanceTime(cfg)
        executor = BacktestExec(cfg)
        stats = executor.run(feed_iter, strat)
        print(stats)
    else:
        cfg = Config.load(args.config)
        dry = not args.send
        from trading_bot.exec.mt5_exec import MT5Exec  # lazy import
        mt5_exec = MT5Exec(cfg, dry_run=dry)
        mt5_exec.run_loop(DistanceTime(cfg))

if __name__ == "__main__":
    main()
