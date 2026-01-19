import asyncio
import datetime
import glob
import os

from stable_baselines3 import PPO

from src.core.config_assets import ASSETS, get_asset_info
from src.core.data_loader import fetch_data
from src.core.env import TradingEnv
from src.core.logger import logger
from src.core.memory import get_mistake_history  # <--- Import Memory

MODEL_DIR = "models"


def get_latest_model_path(symbol, category):
    """
    Mencari file model dengan tanggal paling baru.
    Format: models/category/SYMBOL_YYYY-MM-DD.zip
    """
    safe_symbol = symbol.replace("=", "").replace("^", "")
    base_dir = f"{MODEL_DIR}/{category.lower()}"

    # Cari semua file yang diawali nama simbol
    pattern = f"{base_dir}/{safe_symbol}_*.zip"
    files = glob.glob(pattern)

    # Juga cek file default (tanpa tanggal) sebagai fallback awal
    default_file = f"{base_dir}/{safe_symbol}.zip"
    if os.path.exists(default_file):
        files.append(default_file)

    if not files:
        return None

    # Sortir berdasarkan nama (String YYYY-MM-DD bisa disort secara alfabet)
    # File terbaru akan ada di urutan pertama (reverse=True)
    files.sort(reverse=True)
    return files[0]


async def train_weekly_models_async():
    """
    Fungsi utama yang dipanggil Scheduler setiap Hari Minggu.
    """

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    logger.info(f"🔄 STARTING WEEKLY RETRAINING WITH MEMORY: {today_str}")

    for category, items in ASSETS.items():
        for symbol in items:
            try:
                # 1. Fetch Data Market
                df = fetch_data(symbol, period="2y", interval="1h")
                if df.empty:
                    continue

                # 2. AMBIL INGATAN MASA LALU (MISTAKES)
                logger.info(f"🧠 Loading bad memories for {symbol}...")
                mistakes = await get_mistake_history(symbol)
                logger.info(f"found {len(mistakes)} historical errors to learn from.")

                # 3. Masukkan Memori ke Environment
                env = TradingEnv(df, mistakes_data=mistakes)

                # 4. Load Model Lama & Train
                latest_path = get_latest_model_path(symbol, category)
                if latest_path:
                    model = PPO.load(latest_path, env=env)
                else:
                    model = PPO(policy="MlpPolicy", env=env, verbose=0)

                # Train
                model.learn(total_timesteps=20000)

                # 5. Save dengan Tanggal (Versioning)
                safe_symbol = symbol.replace("=", "").replace("^", "")
                cat_dir = category.lower()

                # Nama file: SYMBOL_YYYY-MM-DD.zip
                filename = f"{safe_symbol}_{today_str}.zip"
                save_path = f"{MODEL_DIR}/{cat_dir}/{filename}"

                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                model.save(save_path)

                logger.info(f"✅ Model Updated: {save_path}")

            except Exception as e:
                logger.error(f"❌ Error training {symbol}: {e}")

    logger.info("🏁 WEEKLY RETRAINING FINISHED")


# Wrapper sync untuk dipanggil thread (jika perlu)
def train_weekly_models():
    asyncio.run(train_weekly_models_async())
