import asyncio
import datetime
import os

import dotenv
from stable_baselines3 import PPO

# Import dari project sendiri
from src.core.data_loader import fetch_data
from src.core.database import assets_collection
from src.core.env import AdvancedForexEnv

dotenv.load_dotenv()

# Import fungsi seeding dari file seed.py
# Pastikan file seed.py ada di folder yang sama (root)
try:
    from seed import seed_database
except ImportError:
    seed_database = None


async def train_model(asset):
    """
    Melatih model untuk satu aset.
    Skip jika file model sudah ada.
    """
    symbol = asset["symbol"]
    category = asset.get("category", "UNKNOWN")

    # Tentukan path penyimpanan
    safe_symbol = symbol.replace("=", "").replace("^", "")
    path = os.path.join(
        "models",
        category.lower(),
        f"{safe_symbol}_{datetime.date.today().strftime('%Y-%m-%d')}.zip",
    )

    # 1. Cek Apakah Model Sudah Ada? (SKIP jika ada)
    if os.path.exists(path):
        print(f"⏭️  SKIPPING {symbol}: Model already exists at {path}")
        return

    print(f"Training {symbol} ({category})...")

    try:
        # 2. Fetch Data (2 tahun)
        df = fetch_data(symbol, period="2y", interval="1h")
        if df.empty:
            print(f"⚠️ Skipping {symbol}: No Data found.")
            return

        # 3. Setup Environment & Model
        env = AdvancedForexEnv(df)
        model = PPO("MlpPolicy", env, verbose=0)

        # 4. Mulai Training
        model.learn(total_timesteps=10000)

        # 5. Simpan Model
        os.makedirs(os.path.dirname(path), exist_ok=True)
        model.save(path)
        print(f"✅ Model saved: {path}")

    except Exception as e:
        print(f"❌ Error training {symbol}: {e}")


async def run_mass_training():
    print("🚀 Starting Mass Training from MongoDB Assets...")

    # 1. AMBIL ASET DARI DATABASE
    cursor = assets_collection.find({})
    assets = await cursor.to_list(length=2000)

    # --- LOGIKA AUTO-SEED JIKA KOSONG ---
    if not assets:
        print("⚠️  Database Aset Kosong!")

        if seed_database and asyncio.iscoroutinefunction(seed_database):
            print("🌱 Menjalankan Auto-Seeding (seed.py)...")
            await seed_database()

            # Ambil ulang data setelah seeding
            print("🔄 Refreshing asset list form DB...")
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=2000)
        else:
            print("❌ Error: seed.py tidak ditemukan. Cannot auto-seed.")
            return

    if not assets:
        print("❌ Masih tidak ada aset setelah seeding. Aborting.")
        return
    # ------------------------------------

    print(f"🔍 Found {len(assets)} assets in MongoDB. Checking models...")

    # 2. Loop Training
    for asset in assets:
        await train_model(asset)

    print("🎉 All training tasks finished!")


if __name__ == "__main__":
    asyncio.run(run_mass_training())
