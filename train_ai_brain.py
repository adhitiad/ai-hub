#!/usr/bin/env python3
"""
Manual training script for AI Brain (PPO).
Saves to: models/ai_trader_ppo_YYYY-MM-DD_{timesteps}steps.zip
"""

import argparse
import asyncio
import logging
import os
import sys
import warnings

# Suppress gym deprecation warning from gym package used by SB3
os.environ.setdefault("GYM_DISABLE_WARNINGS", "1")
logging.getLogger("gym").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*Gym has been unmaintained.*")

from src.core.agent import ai_agent
from src.core.data_loader import load_historical_data
from src.core.database import assets_collection
from src.core.logger import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train AI Brain (PPO) and save dated model artifact."
    )
    parser.add_argument(
        "-s",
        "--symbols",
        type=str,
        default="AAPL",
        help="Comma-separated symbols to train sequentially (default: AAPL).",
    )
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        help="Train all symbols in a category (e.g. forex, crypto, stocks_indo).",
    )
    parser.add_argument(
        "-l",
        "--list-categories",
        action="store_true",
        help="List available categories from database and exit.",
    )
    parser.add_argument(
        "-t",
        "--timesteps",
        type=int,
        default=15000,
        help="Total timesteps for training (default: 15000).",
    )
    parser.add_argument(
        "-p",
        "--period",
        type=str,
        default="2y",
        help="Data period to fetch (default: 2y).",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=str,
        default="1h",
        help="Data interval (default: 1h).",
    )
    return parser.parse_args()


async def _get_assets_by_category(category: str) -> list[str]:
    assets = await assets_collection.find({}).to_list(length=1000)
    assets = [a for a in assets if a.get("category", "").lower() == category.lower()]
    return [a["symbol"] for a in assets]


async def _list_categories() -> list[str]:
    assets = await assets_collection.find({}).to_list(length=1000)
    return sorted(set(a.get("category", "UNKNOWN").lower() for a in assets))


def main() -> int:
    args = parse_args()
    if args.list_categories:
        categories = asyncio.run(_list_categories())
        logger.info("Available categories:")
        for category in categories:
            logger.info(f"  - {category}")
        return 0

    if args.category:
        symbols = asyncio.run(_get_assets_by_category(args.category))
        if not symbols:
            logger.info(f"ERROR: No assets found in category: {args.category}")
            return 1
    else:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    if not symbols:
        logger.info("ERROR: No symbols provided.")
        return 1

    for symbol in symbols:
        df = load_historical_data(symbol, period=args.period, interval=args.interval)
        if df.empty:
            logger.info(f"ERROR: No data fetched for {symbol}")
            return 1

        ai_agent.train_self(df, timesteps=args.timesteps)

    model_dir = "models"
    files = [
        f
        for f in os.listdir(model_dir)
        if f.startswith("ai_trader_ppo_") and f.endswith("steps.zip")
    ]
    if not files:
        logger.info("ERROR: No dated AI brain model found after training.")
        return 1

    latest = max((os.path.join(model_dir, f) for f in files), key=os.path.getmtime)
    logger.info(f"Saved: {latest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
