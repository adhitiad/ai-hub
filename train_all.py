import asyncio
import datetime
import os

import dotenv
import gymnasium as gym
import shimmy
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# --- IMPORTS ---
from src.core.data_loader import fetch_data_async
from src.core.database import assets_collection
from src.core.env import AdvancedForexEnv

# [PENTING] Import Feature Engineering agar model pintar
from src.core.feature_engineering import enrich_data
from src.core.logger import logger

dotenv.load_dotenv()

try:
    from seed import seed_database
except ImportError:
    seed_database = None

# Batasi agar komputer tidak hang (misal max 3 training bersamaan)
MAX_CONCURRENT_TRAINING = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRAINING)


async def train_model(asset):
    """
    Melatih model untuk satu aset dengan Semaphore.
    """
    async with semaphore:
        symbol = asset["symbol"]
        category = asset.get("category", "UNKNOWN")
        safe_symbol = symbol.replace("=", "").replace("^", "").replace("/", "")

        path = os.path.join(
            "models",
            category.lower(),
            f"{safe_symbol}_{datetime.date.today().strftime('%Y-%m-%d')}.zip",
        )

        # Skip jika sudah ada hari ini
        if os.path.exists(path):
            logger.info(f"⏭️  SKIPPING {symbol}: Model already exists.")
            return

        logger.info(f"🔄 Fetching data for {symbol}...")

        try:
            # 1. Fetch Data
            df = await fetch_data_async(symbol, period="2y", interval="1h")

            if df.empty or len(df) < 200:  # Minimal data harus cukup untuk indikator
                logger.warning(
                    f"⚠️ Skipping {symbol}: Not enough data ({len(df)} rows)."
                )
                return

            # 2. [CRITICAL] Feature Engineering
            # Tambahkan indikator teknikal (RSI, MACD, dll) sebelum masuk Env
            df = enrich_data(df)

            # Hapus baris NaN akibat kalkulasi indikator
            df.dropna(inplace=True)

            logger.info(f"🧠 Training {symbol} with {len(df)} candles...")

            # 3. Setup Environment
            # Bungkus env agar kompatibel penuh dengan SB3
            def make_env():
                env = AdvancedForexEnv(df)
                return Monitor(env)  # Monitor untuk log reward

            # Gunakan DummyVecEnv untuk performa standar SB3
            vec_env = DummyVecEnv([make_env])

            # 4. Setup Model PPO
            model = PPO("MlpPolicy", vec_env, verbose=0, device="auto", ent_coef=0.01)

            # 5. Training di Thread terpisah (Non-Blocking)
            await asyncio.to_thread(model.learn, total_timesteps=15000)

            # 6. Simpan
            os.makedirs(os.path.dirname(path), exist_ok=True)
            model.save(path)
            logger.info(f"✅ Model saved: {path}")

            # Cleanup
            vec_env.close()

        except Exception as e:
            logger.error(f"❌ Error training {symbol}: {e}")
            # Traceback opsional jika ingin debug mendalam:
            logger.exception(e)


async def run_mass_training():
    print(
        f"🚀 Starting Mass Training (Async Mode - Max {MAX_CONCURRENT_TRAINING} concurrent)..."
    )

    # 1. Ambil Aset
    cursor = assets_collection.find({})
    assets = await cursor.to_list(length=5000)

    # 2. Auto-Seed
    if not assets:
        print("⚠️ Database Kosong! Menjalankan Auto-Seeding...")
        if seed_database:
            await seed_database()
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=5000)
        else:
            print("❌ Seed script tidak ditemukan.")
            return

    print(f"🔍 Found {len(assets)} assets. Queuing tasks...")

    # 3. Jalankan Training secara Concurrency (Parallel)
    # Kita buat list tasks, semaphore akan mengatur antriannya
    tasks = [train_model(asset) for asset in assets]

    # Jalankan semua tasks
    await asyncio.gather(*tasks)

    print("🎉 All training tasks finished!")


if __name__ == "__main__":
    # Windows fix untuk asyncio loop policy jika diperlukan
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(run_mass_training())
