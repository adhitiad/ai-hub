import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ai-trading-hub")

async def setup_indexes():
    print(f"🛠️  Menyetel DB Indexes di: {DB_NAME}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # 1. User Indexes
    # Email harus unik
    await db.users.create_index("email", unique=True)
    # API Key Hash harus unik dan cepat dicari
    await db.users.create_index("api_key_hash", unique=True)
    
    # 2. Log Indexes (Agar query audit logs cepat)
    # Sortir berdasarkan timestamp (descending)
    await db.logs.create_index([("timestamp", -1)])
    # Sortir berdasarkan user
    await db.logs.create_index("user")

    # 3. Market Signals (Query harian)
    await db.signals.create_index([("timestamp", -1)])
    await db.signals.create_index("symbol")

    print("✅ Indexes berhasil dibuat!")

if __name__ == "__main__":
    asyncio.run(setup_indexes())
