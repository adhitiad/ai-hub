import asyncio
import os

from stable_baselines3 import PPO

from src.core.data_loader import fetch_data
from src.core.database import assets_collection  # Import DB
from src.core.env import AdvancedForexEnv


async def train_model(asset):
    symbol = asset["symbol"]
    category = asset.get("category", "UNKNOWN")

    print(f"Training {symbol} ({category})...")

    # Fetch Data (Synchronous)
    # Kita bisa jalankan di thread terpisah jika mau, tapi untuk script training gapapa block
    try:
        df = fetch_data(symbol, period="2y")
        if df.empty:
            print(f"Skipping {symbol}: No Data")
            return

        env = AdvancedForexEnv(df)
        model = PPO("MlpPolicy", env, verbose=0)

        # Training
        model.learn(total_timesteps=10000)

        # Simpan Model
        # Format path: models/stocks_indo/BBCA.JK.zip
        safe_symbol = symbol.replace("=", "").replace("^", "")
        path = f"models/{category.lower()}/{safe_symbol}.zip"

        os.makedirs(os.path.dirname(path), exist_ok=True)
        model.save(path)
        print(f"✅ Model saved: {path}")

    except Exception as e:
        print(f"❌ Error training {symbol}: {e}")


async def run_mass_training():
    print("🚀 Starting Mass Training from MongoDB Assets...")

    # 1. Ambil aset dari DB
    cursor = assets_collection.find({})
    assets = await cursor.to_list(length=2000)

    if not assets:
        print("⚠️ Database kosong. Jalankan seed_assets.py dulu.")
        return

    # 2. Loop training
    # Kita tidak pakai gather (parallel) disini karena training itu berat di CPU.
    # Lebih baik serial (satu per satu) agar komputer tidak hang.
    for asset in assets:
        await train_model(asset)

    print("🎉 All training finished!")


if __name__ == "__main__":
    asyncio.run(run_mass_training())
