import asyncio
import json
import aiofiles
import os
import shutil

import torch
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.agent import ai_agent
from src.core.logger import logger
from src.core.trainer import train_model_pipeline  # Asumsi fungsi training utama
from src.database.data_loader import load_historical_data
from src.feature.feature_enginering import enrich_data

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
        state_dict = await asyncio.to_thread(torch.load, MODEL_PATH, map_location="cpu")
        ai_agent.model.policy.load_state_dict(state_dict)
        logger.info("✅ AI Models reloaded successfully")
    except Exception as e:
        logger.error("❌ Failed to reload models: %s", e)


async def weekly_retraining_job():
    logger.info("🚀 Starting Weekly AI Retraining...")

    symbol = []
    # 1. Simpan performa model lama (jika ada)
    old_accuracy = 0.0

    if await asyncio.to_thread(os.path.exists, METRICS_PATH):
        async with aiofiles.open(METRICS_PATH, "r") as f:
            content = await f.read()
            old_data = await asyncio.to_thread(json.loads, content)
        old_accuracy = old_data.get("win_rate", 0)

    # 2. Jalankan Training (Hasilnya disimpan di temp path dulu)
    temp_model_path = "models/temp_new_model.pth"
    try:
        # Fungsi ini harus return dict metrics: {'win_rate': 0.65, 'loss': ...}
        # dan menyimpan state_dict ke temp_model_path
        new_metrics = train_model_pipeline(symbol, save_path=temp_model_path)
        new_accuracy = new_metrics.get("win_rate", 0)

        logger.info(
            "📊 Model Comparison: Old=%.2f vs New=%.2f", old_accuracy, new_accuracy
        )

        # 3. Compare & Swap
        if new_accuracy > old_accuracy:
            logger.info("✅ New model is better! Upgrading production model.")

            # Backup model lama
            if await asyncio.to_thread(os.path.exists, MODEL_PATH):
                await asyncio.to_thread(shutil.move, MODEL_PATH, BACKUP_PATH)

            # Pasang model baru
            await asyncio.to_thread(shutil.move, temp_model_path, MODEL_PATH)

            # Simpan metrics baru

            async with aiofiles.open(METRICS_PATH, "w") as f:
                content = await asyncio.to_thread(json.dumps, new_metrics)
                await f.write(content)

            await reload_ai_models()

        else:
            logger.info("⚠️ New model did not improve. Discarding.")
            if await asyncio.to_thread(os.path.exists, temp_model_path):
                await asyncio.to_thread(os.remove, temp_model_path)

    except Exception as e:
        logger.error("❌ Training Failed: %s", e)


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

    df = enrich_data(df)

    # 3. AI Belajar sendiri
    ai_agent.train_self(df, timesteps=50000)
