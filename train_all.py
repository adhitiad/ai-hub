import asyncio
import datetime
import os

import dotenv
import gymnasium as gym  # Gunakan gymnasium modern
import shimmy  # Pastikan install: pip install shimmy>=0.2.1
from stable_baselines3 import PPO

# Import Loader Async Baru
from src.core.data_loader import fetch_data_async
from src.core.database import assets_collection
from src.core.env import AdvancedForexEnv
from src.core.logger import logger

dotenv.load_dotenv()

try:
    from seed import seed_database
except ImportError:
    seed_database = None


async def train_model(asset):
    """
    Melatih model untuk satu aset (Support Saham & Crypto).
    """
    symbol = asset["symbol"]
    category = asset.get("category", "UNKNOWN")

    # Bersihkan simbol untuk nama file (misal BTC/USDT -> BTCUSDT)
    safe_symbol = symbol.replace("=", "").replace("^", "").replace("/", "")

    path = os.path.join(
        "models",
        category.lower(),
        f"{safe_symbol}_{datetime.date.today().strftime('%Y-%m-%d')}.zip",
    )

    if os.path.exists(path):
        logger.info(f"⏭️  SKIPPING {symbol}: Model already exists.")
        return

    logger.info(f"🔄 Fetching data for {symbol} ({category})...")

    try:
        # [UPDATE] Gunakan fetch_data_async
        df = await fetch_data_async(symbol, period="2y", interval="1h")

        if df.empty or len(df) < 100:
            logger.warning(f"⚠️ Skipping {symbol}: Not enough data fetched.")
            return

        logger.info(f"🧠 Training {symbol} with {len(df)} candles...")

        # Setup Environment
        # Pastikan AdvancedForexEnv kompatibel dengan Gymnasium/Shimmy
        env = AdvancedForexEnv(df)

        # Setup Model PPO
        model = PPO("MlpPolicy", env, verbose=0, device="auto")

        # Mulai Training (Async friendly execution)
        await asyncio.to_thread(model.learn, total_timesteps=10000)

        # Simpan
        os.makedirs(os.path.dirname(path), exist_ok=True)
        model.save(path)
        logger.info(f"✅ Model saved: {path}")

    except Exception as e:
        logger.error(f"❌ Error training {symbol}: {e}")


async def run_mass_training():
    print("🚀 Starting Mass Training (Async Mode)...")

    # 1. Ambil Aset
    cursor = assets_collection.find({})
    assets = await cursor.to_list(length=5000)

    # 2. Auto-Seed jika kosong
    if not assets:
        print("⚠️ Database Kosong! Menjalankan Auto-Seeding...")
        if seed_database:
            await seed_database()
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=5000)
        else:
            print("❌ Seed script tidak ditemukan.")
            return

    print(f"🔍 Found {len(assets)} assets. Starting loop...")

    # 3. Loop Training (Sequential agar tidak membebani RAM/CPU)
    for i, asset in enumerate(assets):
        print(f"[{i+1}/{len(assets)}] Processing {asset['symbol']}...")
        await train_model(asset)

    print("🎉 All training tasks finished!")


if __name__ == "__main__":
    asyncio.run(run_mass_training())
