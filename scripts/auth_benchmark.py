import asyncio
import time
import hashlib

# Mocking parts of the system
def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

class MockMongo:
    def __init__(self, latency=0.02):
        self.latency = latency
        self.data = {
            "api_key_hash": hash_api_key("test_key"),
            "email": "test@example.com",
            "subscription_status": "active",
            "daily_requests_limit": 100,
            "requests_today": 10,
            "role": "user"
        }

    async def find_one(self, query):
        await asyncio.sleep(self.latency)
        if query.get("api_key_hash") == self.data["api_key_hash"]:
            return self.data
        return None

class MockRedis:
    def __init__(self, latency=0.001):
        self.latency = latency
        self.cache = {}

    async def get(self, key):
        await asyncio.sleep(self.latency)
        return self.cache.get(key)

    async def set(self, key, value, ex=None):
        await asyncio.sleep(self.latency)
        self.cache[key] = value
        return True

async def baseline_auth(api_key, mongo):
    hashed_key = hash_api_key(api_key)
    user = await mongo.find_one({"api_key_hash": hashed_key})
    if not user:
        return None
    return user

async def cached_auth(api_key, mongo, redis):
    hashed_key = hash_api_key(api_key)
    cache_key = f"auth:user:{hashed_key}"

    # Try cache
    cached_user = await redis.get(cache_key)
    if cached_user:
        return cached_user

    # DB fallback
    user = await mongo.find_one({"api_key_hash": hashed_key})
    if user:
        await redis.set(cache_key, user, ex=300)
    return user

async def run_benchmark():
    mongo = MockMongo(latency=0.02) # 20ms
    redis = MockRedis(latency=0.001) # 1ms
    api_key = "test_key"
    iterations = 100

    print(f"--- Benchmarking {iterations} iterations ---")

    # Baseline (Always DB)
    start_time = time.time()
    for _ in range(iterations):
        await baseline_auth(api_key, mongo)
    baseline_duration = time.time() - start_time
    print(f"Baseline (Always DB): {baseline_duration:.4f}s (avg: {baseline_duration/iterations*1000:.2f}ms)")

    # Cached
    # First call (Miss)
    await cached_auth(api_key, mongo, redis)

    start_time = time.time()
    for _ in range(iterations):
        await cached_auth(api_key, mongo, redis)
    cached_duration = time.time() - start_time
    print(f"Optimized (Cached): {cached_duration:.4f}s (avg: {cached_duration/iterations*1000:.2f}ms)")

    improvement = (baseline_duration - cached_duration) / baseline_duration * 100
    print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
