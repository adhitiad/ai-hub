import asyncio

from src.core.agent import get_detailed_signal
from src.core.config_assets import ASSETS
from src.core.logger import logger
from src.core.signal_bus import signal_bus


async def process_single(symbol):
    try:
        data = await asyncio.to_thread(get_detailed_signal, symbol)
        signal_bus.update_signal(symbol, data)
        return True
    except Exception as e:
        logger.error(f"Worker Error {symbol}: {e}")
        return False


async def signal_producer_task():
    logger.info("🚀 PRODUCER STARTED")
    while True:
        tasks = []
        for cat, symbols in ASSETS.items():
            for sym in symbols:
                tasks.append(process_single(sym))

        await asyncio.gather(*tasks)
        signal_bus.save_snapshot()
        await asyncio.sleep(60)
