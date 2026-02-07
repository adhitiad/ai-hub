#!/usr/bin/env python3
"""
File untuk melatih model single asset dengan konfigurasi yang mudah diatur.
Hasil training akan disimpan di folder models dengan nama file yang informatif.
"""

import argparse
import asyncio
import datetime
import logging
import os
import warnings

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


async def train_single_asset(
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
            logger.warning(f"⚠️ Model sudah ada: {model_path}")
            logger.info("⏭️ Skipping training...")
            return False

        # 4. Fetch data
        logger.info("🔄 Fetching data...")
        df = await fetch_data_async(symbol, period=period, interval=interval)

        if df.empty or len(df) < 200:  # Minimal data untuk indikator
            logger.warning(f"⚠️ Data tidak cukup: {len(df)} rows")
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


def get_available_assets(category: str | None = None):
    """
    Mendapatkan list asset yang tersedia di database.
    """
    loop = asyncio.get_event_loop()
    assets = loop.run_until_complete(assets_collection.find({}).to_list(length=1000))

    if category:
        assets = [
            a for a in assets if a.get("category", "").lower() == category.lower()
        ]

    return assets


def main():
    parser = argparse.ArgumentParser(
        description="Melatih model single asset dengan konfigurasi yang mudah diatur"
    )
    parser.add_argument(
        "symbol",
        help="Symbol asset yang akan dilatih (misal: BBCA.JK, BTCUSDT, EURUSD)",
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
        "--list",
        action="store_true",
        help="List semua asset yang tersedia di database",
    )
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        help="List asset berdasarkan kategori (misal: stocks_indo, crypto, forex)",
    )

    args = parser.parse_args()

    if args.list:
        assets = get_available_assets(args.category)
        print(
            f"📋 Available assets{' in category ' + args.category if args.category else ''}:"
        )
        for asset in assets:
            print(f"  - {asset['symbol']} ({asset.get('category', 'UNKNOWN')})")
        return

    # Jalankan training
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    success = asyncio.run(
        train_single_asset(args.symbol, args.timesteps, args.period, args.interval)
    )

    if success:
        logger.info("🎉 Training completed successfully!")
    else:
        logger.error("💥 Training failed!")
        return 1


if __name__ == "__main__":
    main()
