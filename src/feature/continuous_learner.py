import asyncio
import datetime
import glob
import os

from stable_baselines3 import PPO

from src.core.config_assets import ASSETS, get_asset_info
from src.core.env import TradingEnv
from src.core.logger import logger
from src.database.data_loader import fetch_data, fetch_data_async
from src.database.memory import get_mistake_history  # <--- Import Memory

def get_latest_model_path(symbol, category):
    model_dir = os.path.join(os.getcwd(), "models")
    if not os.path.exists(model_dir):
        return None

    models = [f for f in os.listdir(model_dir) if f.startswith(f"{symbol}_{category}")]
    if not models:
        return None

    latest_model = max(models, key=lambda f: os.path.getctime(os.path.join(model_dir, f)))
    return os.path.join(model_dir, latest_model)

async def train_weekly_models_async():
    """
    Fungsi utama yang dipanggil Scheduler setiap Hari Minggu.
    """

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    logger.info("🔄 STARTING WEEKLY RETRAINING WITH MEMORY: %s", today_str)

    for category, items in ASSETS.items():
        for symbol in items:
            try:
                # 1. Fetch Data Market
                df = fetch_data(symbol, period="2y", interval="1h")
                if df.empty:
                    continue

                # 2. AMBIL INGATAN MASA LALU (MISTAKES)
                logger.info("🧠 Loading bad memories for %s...", symbol)
                mistakes = await get_mistake_history(symbol)
                logger.info("found %s historical errors to learn from.", len(mistakes))

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
                save_path = os.path.join(os.getcwd(), "models", f"{safe_symbol}_{today_str}.zip")

                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                model.save(save_path)

                logger.info("✅ Model Updated: %s", save_path)

            except Exception as e:
                logger.error("❌ Error training %s: %s", symbol, e)

    logger.info("🏁 WEEKLY RETRAINING FINISHED")


# Wrapper sync untuk dipanggil thread (jika perlu)
def train_weekly_models():
    asyncio.run(train_weekly_models_async())
