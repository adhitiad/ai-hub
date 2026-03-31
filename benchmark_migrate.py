import asyncio
import time
import os
from migrate_timezone import migrate_timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "ai_hub")

async def setup_test_data():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # Create test collection
    collection = db["users"]

    # Clear existing data for a clean test
    await collection.delete_many({})

    from datetime import datetime

    docs = []
    for i in range(1000):
        docs.append({
            "created_at": datetime.now(),
            "subscription_end_date": datetime.now(),
            "bonus_end_date": datetime.now(),
            "upgraded_at": datetime.now(),
            "last_updated": datetime.now(),
            "other_field": "data"
        })

    await collection.insert_many(docs)
    client.close()

async def run_benchmark():
    await setup_test_data()

    print("Running baseline benchmark...")
    start_time = time.time()
    await migrate_timezone(apply=True)
    end_time = time.time()

    print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
