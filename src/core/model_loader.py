# src/core/model_loader.py
import asyncio
import glob

from stable_baselines3 import PPO

from src.core.logger import logger


class ModelCache:
    _models = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_model(cls, symbol: str, category: str):
        safe_symbol = symbol.replace("=", "").replace("^", "").replace("/", "")

        # 1. Cek Memory Cache
        if safe_symbol in cls._models:
            return cls._models[safe_symbol]

        # 2. Jika tidak ada, Load dari Disk (Thread Safe)
        async with cls._lock:
            # Double check pattern
            if safe_symbol in cls._models:
                return cls._models[safe_symbol]

            base_dir = f"models/{category}"
            pattern = f"{base_dir}/{safe_symbol}*.zip"
            files = glob.glob(pattern)

            # Fallback ke Generic
            if not files:
                files = glob.glob(f"{base_dir}/GENERIC*.zip")

            if files:
                files.sort(reverse=True)
                latest_file = files[0]
                try:
                    # Load model ke RAM
                    logger.info(f"📥 Loading Model to RAM: {safe_symbol}")
                    # Jalankan load di thread terpisah agar tidak block async loop
                    model = await asyncio.to_thread(PPO.load, latest_file)
                    cls._models[safe_symbol] = model
                    return model
                except Exception as e:
                    logger.error(f"Failed load model {symbol}: {e}")
                    return None
            return None

    @classmethod
    def clear_cache(cls):
        cls._models = {}
        logger.info("🧹 Model Cache Cleared")
