#!/usr/bin/env python3
"""
File untuk melatih beberapa asset sekaligus (batch training).
Hasil training akan disimpan di folder models dengan nama file yang informatif.
"""

import argparse
import asyncio
import datetime
import logging
import os
import warnings
from concurrent.futures import ThreadPoolExecutor

import dotenv

os.environ.setdefault("GYM_DISABLE_WARNINGS", "1")
logging.getLogger("gym").setLevel(logging.ERROR)
# Suppress gym deprecation warning from gym package used by SB3
warnings.filterwarnings("ignore", message=".*Gym has been unmaintained.*")

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from src.core.config_assets import get_asset_info

# Impor core modules
from src.core.data_loader import fetch_data_async
from src.core.database import assets_collection
from src.core.env import TradingEnv
from src.core.feature_enginering import enrich_data
from src.core.logger import logger

# Load environment variables
dotenv.load_dotenv()

# Batasi jumlah training yang berjalan sekaligus
MAX_CONCURRENT = 3


async def train_asset(
    symbol: str, total_timesteps: int = 15000, period: str = "2y", interval: str = "1h"
):
    """
    Melatih model untuk single asset dengan konfigurasi yang ditentukan.
    """
    logger.info(f"🚀 Starting training for {symbol}")
    logger.info(
        f"🔧 Configuration: timesteps={total_timesteps}, period={period}, interval={interval}"
    )

    try:
        # 1. Ambil informasi asset
        info = get_asset_info(symbol)
        category = info.get("category", "UNKNOWN").lower() if info else "common"
        safe_symbol = symbol.replace("=", "").replace("^", "").replace("/", "")

        # 2. Generate path untuk menyimpan model
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        model_filename = f"{safe_symbol}_{current_date}_{total_timesteps}steps.zip"
        model_path = os.path.join("models", category, model_filename)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # 3. Periksa apakah model dengan konfigurasi yang sama sudah ada
        if os.path.exists(model_path):
            logger.warning(f"⚠️ Model already exists: {model_path}")
            logger.info("⏭️ Skipping training...")
            return False

        # 4. Fetch data
        logger.info("🔄 Fetching data...")
        df = await fetch_data_async(symbol, period=period, interval=interval)

        if df.empty or len(df) < 200:  # Minimal data untuk indikator
            logger.warning(f"⚠️ Not enough data: {len(df)} rows")
            return False

        # 5. Feature engineering
        logger.info("🧠 Applying feature engineering...")
        df = enrich_data(df)
        df.dropna(inplace=True)
        logger.info(f"📊 Data ready: {len(df)} rows")

        # 6. Setup environment
        def make_env():
            env = TradingEnv(df)
            return Monitor(env)

        vec_env = DummyVecEnv([make_env])

        # 7. Setup model PPO
        logger.info("🤖 Initializing PPO model...")
        model = PPO("MlpPolicy", vec_env, verbose=0, device="auto", ent_coef=0.01)

        # 8. Training
        logger.info("🏃‍♂️ Starting training...")
        await asyncio.to_thread(model.learn, total_timesteps=total_timesteps)

        # 9. Simpan model
        logger.info("💾 Saving model...")
        model.save(model_path)
        logger.info(f"✅ Model saved to: {model_path}")

        # 10. Cleanup
        vec_env.close()

        return True

    except Exception as e:
        logger.error(f"❌ Error training {symbol}: {e}")
        logger.exception(e)
        return False


async def run_batch_training(
    symbols: list,
    total_timesteps: int = 15000,
    period: str = "2y",
    interval: str = "1h",
):
    """
    Melatih beberapa asset sekaligus dengan batasan concurrency.
    """
    logger.info(f"🚀 Batch Training Started for {len(symbols)} assets")
    logger.info(
        f"🔧 Configuration: timesteps={total_timesteps}, period={period}, interval={interval}"
    )
    logger.info(f"🔄 Max concurrent training: {MAX_CONCURRENT}")

    # Semaphore untuk mengatur concurrency
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def bounded_train(symbol):
        async with semaphore:
            return await train_asset(symbol, total_timesteps, period, interval)

    # Buat tasks dan jalankan secara concurrent
    tasks = [bounded_train(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)

    # Hitung hasil
    success_count = sum(1 for result in results if result is True)
    failed_count = len(symbols) - success_count

    logger.info(f"🎉 Batch Training Completed!")
    logger.info(f"✅ Success: {success_count}")
    logger.info(f"❌ Failed: {failed_count}")

    return success_count, failed_count


async def _get_assets_by_category(category: str):
    assets = await assets_collection.find({}).to_list(length=1000)
    assets = [a for a in assets if a.get("category", "").lower() == category.lower()]
    return [a["symbol"] for a in assets]


def main():
    parser = argparse.ArgumentParser(
        description="Melatih beberapa asset sekaligus (batch training) dengan konfigurasi yang mudah diatur"
    )
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        help="Category asset yang akan dilatih (misal: stocks_indo, crypto, forex)",
    )
    parser.add_argument(
        "-s",
        "--symbols",
        type=str,
        help="Daftar symbol asset dipisahkan oleh koma (misal: BBCA.JK,BRENTCrude,ETHUSDT)",
    )
    parser.add_argument(
        "-t",
        "--timesteps",
        type=int,
        default=15000,
        help="Total timesteps untuk training (default: 15000)",
    )
    parser.add_argument(
        "-p",
        "--period",
        type=str,
        default="2y",
        help="Periode data yang akan diambil (default: 2y, contoh: 1y, 6mo, 30d)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=str,
        default="1h",
        help="Interval data (default: 1h, contoh: 5m, 15m, 1d)",
    )
    parser.add_argument(
        "-l",
        "--list-categories",
        action="store_true",
        help="List semua kategori asset yang tersedia",
    )

    args = parser.parse_args()

    if args.list_categories:
        assets = asyncio.run(assets_collection.find({}).to_list(length=1000))
        categories = set(a.get("category", "UNKNOWN").lower() for a in assets)
        print("Available categories:")
        for category in sorted(categories):
            count = sum(1 for a in assets if a.get("category", "").lower() == category)
            print(f"  - {category} ({count} assets)")
        return

    # Tentukan list symbol yang akan dilatih
    symbols = []
    if args.category:
        symbols = asyncio.run(_get_assets_by_category(args.category))
        if not symbols:
            logger.error(f"❌ No assets found in category: {args.category}")
            return 1
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        logger.error("❌ Please specify either --category or --symbols")
        return 1

    logger.info(f"🔍 Training {len(symbols)} assets...")

    # Jalankan training
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    success_count, failed_count = asyncio.run(
        run_batch_training(symbols, args.timesteps, args.period, args.interval)
    )

    if failed_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    main()
