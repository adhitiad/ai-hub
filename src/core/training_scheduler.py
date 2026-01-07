import asyncio
import datetime

from src.core.continuous_learner import train_weekly_models
from src.core.logger import logger


async def training_scheduler_task():
    """
    Mengecek waktu setiap jam. Jika Hari Minggu jam 02:00 pagi, jalankan training.
    """
    logger.info("📅 Training Scheduler Started (Target: Sunday @ 02:00 AM)")

    while True:
        now = datetime.datetime.now()

        # Weekday 6 = Minggu (Senin=0, ..., Minggu=6)
        if now.weekday() == 6:
            # Jalankan jam 2 pagi saat server sepi
            if now.hour == 2:
                logger.info("🚀 IT'S SUNDAY! Starting Auto-Training...")

                # Jalankan fungsi blocking di thread terpisah agar API tidak macet
                await asyncio.to_thread(train_weekly_models)

                # Tidur 20 jam agar tidak dijalankan berulang-ulang di hari yang sama
                await asyncio.sleep(20 * 3600)

        # Cek lagi jam depan
        await asyncio.sleep(3600)
