import argparse
import json
import logging
import sys
from datetime import datetime

import config
import fetch_data
from backtest import Backtester


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stdout,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Binary Market Strategy Engine: Buy No Early",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initial capital in USD",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live market data (default: synthetic)",
    )
    parser.add_argument(
        "--kalshi-key",
        type=str,
        default=None,
        metavar="API_KEY",
        help="Kalshi API key for live data",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results.json",
        metavar="FILE",
        help="Path to JSON output file",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for price simulation",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--max-age",
        type=float,
        default=20.0,
        help="Maximum market age in minutes for entry",
    )
    parser.add_argument(
        "--min-yes-price",
        type=float,
        default=0.70,
        help="Minimum Yes price for entry signal",
    )
    parser.add_argument(
        "--min-ev",
        type=float,
        default=0.10,
        help="Minimum expected value for entry signal",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> config.AppConfig:
    cfg = config.default_config()
    cfg.strategy.max_age_minutes = args.max_age
    cfg.strategy.min_yes_price = args.min_yes_price
    cfg.strategy.min_expected_return = args.min_ev
    cfg.backtest.initial_capital = args.capital
    return cfg


def print_header() -> None:
    print("=" * 72)
    print("  Binary Market Strategy Engine")
    print("  Strategy: Buy No Early")
    print("=" * 72)
    print()


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)
    logger = logging.getLogger(__name__)

    print_header()

    cfg = build_config(args)

    markets = fetch_data.get_all_markets(
        use_mock=not args.live,
        kalshi_api_key=args.kalshi_key,
        cfg=cfg.fetch,
    )

    if not markets:
        logger.error("No markets available. Exiting.")
        return 1

    backtester = Backtester(cfg=cfg, seed=args.seed)
    result = backtester.run(markets, verbose=True)

    output = {
        "run_timestamp": datetime.now().isoformat(),
        "config": {
            "initial_capital": cfg.backtest.initial_capital,
            "max_age_minutes": cfg.strategy.max_age_minutes,
            "min_yes_price": cfg.strategy.min_yes_price,
            "min_expected_return": cfg.strategy.min_expected_return,
            "stop_loss_pct": cfg.risk.stop_loss_pct,
            "take_profit_pct": cfg.risk.take_profit_pct,
            "max_hold_minutes": cfg.risk.max_hold_minutes,
        },
        "metrics": result.metrics,
        "signals": result.signals,
        "trades": result.trades,
        "snapshots": result.snapshots,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    logger.info("Results saved to %s", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
