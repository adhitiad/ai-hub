
## 2024-05-19 - FastApi Main Thread Blocking with ML Models
**Learning:** Loading large ML models (`PPO.load()`) inside synchronous functions block the entire FastAPI event loop leading to extremely poor latency when processing multiple users or large background tasks. Even seemingly "one-off" loads during initialization (`__init__`) can significantly delay startup times.
**Action:** Always wrap heavy synchronous operations (like Model Loading and Training) with `await asyncio.to_thread(...)`. Move model instantiation from `__init__` methods to an explicit `async def initialize(...)` method executed on startup events. Use an LRU Cache to store frequently used models in memory to avoid redundant Disk I/O.
