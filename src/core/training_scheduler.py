import asyncio
import json
import os
import shutil
from datetime import datetime

import torch
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.agent import ai_agent
from src.core.data_loader import load_historical_data
from src.core.logger import logger
from src.core.trainer import train_model_pipeline  # Asumsi fungsi training utama

# Reload Model di Memory (Penting!)


# Path Model
MODEL_PATH = "models/production_model.pth"
BACKUP_PATH = "models/backup_model.pth"
METRICS_PATH = "models/metrics.json"

scheduler = AsyncIOScheduler()


async def reload_ai_models():
    """Reload the AI models into memory after updating the model file."""
    try:
        if ai_agent.model is None:
            logger.error("❌ AI Model not initialized")
            return
        state_dict = torch.load(MODEL_PATH, map_location="cpu")
        ai_agent.model.policy.load_state_dict(state_dict)
        logger.info("✅ AI Models reloaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to reload models: {e}")


async def weekly_retraining_job():
    logger.info("🚀 Starting Weekly AI Retraining...")

    symbol = []
    # 1. Simpan performa model lama (jika ada)
    old_accuracy = 0.0

    if os.path.exists(METRICS_PATH):
        import json

        with open(METRICS_PATH, "r") as f:
            old_data = json.load(f)
            old_accuracy = old_data.get("win_rate", 0)

    # 2. Jalankan Training (Hasilnya disimpan di temp path dulu)
    temp_model_path = "models/temp_new_model.pth"
    try:
        # Fungsi ini harus return dict metrics: {'win_rate': 0.65, 'loss': ...}
        # dan menyimpan state_dict ke temp_model_path
        new_metrics = train_model_pipeline(symbol, save_path=temp_model_path)
        new_accuracy = new_metrics.get("win_rate", 0)

        logger.info(
            f"📊 Model Comparison: Old={old_accuracy:.2f} vs New={new_accuracy:.2f}"
        )

        # 3. Compare & Swap
        if new_accuracy > old_accuracy:
            logger.info("✅ New model is better! Upgrading production model.")

            # Backup model lama
            if os.path.exists(MODEL_PATH):
                shutil.move(MODEL_PATH, BACKUP_PATH)

            # Pasang model baru
            shutil.move(temp_model_path, MODEL_PATH)

            # Simpan metrics baru

            with open(METRICS_PATH, "w") as f:
                json.dump(new_metrics, f)

            await reload_ai_models()

        else:
            logger.info("⚠️ New model did not improve. Discarding.")
            if os.path.exists(temp_model_path):
                os.remove(temp_model_path)

    except Exception as e:
        logger.error(f"❌ Training Failed: {e}")


async def training_scheduler_task():
    # Jadwalkan setiap Minggu jam 23:00 WIB
    scheduler.add_job(
        weekly_retraining_job, "cron", day_of_week="sun", hour=23, minute=0
    )
    scheduler.start()
    logger.info("📅 AI Training Scheduler Started (Weekly: Sun 23:00)")

    # Keep alive logic if needed, or let main.py handle loop
    while True:
        await asyncio.sleep(3600)


async def nightly_training(symbol, limit=1000):
    # 1. Load data 1000 candle terakhir
    df = load_historical_data(symbol)

    # 2. Lakukan feature engineering (hitung RSI, MACD, Scaled Close)
    from src.core.feature_enginering import enrich_data

    df = enrich_data(df)

    # 3. AI Belajar sendiri
    ai_agent.train_self(df, timesteps=50000)
