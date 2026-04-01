import asyncio
import time
import os
import json

METRICS_PATH = "models/metrics.json"

async def test_read():
    max_delay = 0
    is_running = True
    async def monitor():
        nonlocal max_delay
        while is_running:
            t = time.perf_counter()
            await asyncio.sleep(0.001)
            delay = time.perf_counter() - t - 0.001
            max_delay = max(max_delay, delay)

    mon_task = asyncio.create_task(monitor())
    await asyncio.sleep(0.01)

    start = time.perf_counter()
    def _read_metrics():
        with open(METRICS_PATH, "r") as f:
            content = f.read()
            return content

    content = await asyncio.to_thread(_read_metrics)
    print(f"Read metrics: {(time.perf_counter() - start) * 1000:.2f}ms")

    is_running = False
    await asyncio.sleep(0.01)
    print(f"Max event loop delay: {max_delay * 1000:.2f}ms")

if __name__ == "__main__":
    os.makedirs('models', exist_ok=True)
    with open('models/metrics.json', 'w') as f:
        json.dump({"dummy": "data"}, f)
    asyncio.run(test_read())
