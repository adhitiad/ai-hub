import asyncio
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ai-trading-hub")

async def migrate():
    print(f"🚀 Memulai migrasi API Keys di database: {DB_NAME}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db["users"]

    cursor = users_collection.find({"api_key": {"$exists": True}})
    count = 0
    
    async for user in cursor:
        plain_key = user.get("api_key")
        if plain_key:
            hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
            
            await users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {"api_key_hash": hashed_key},
                    "$unset": {"api_key": ""}
                }
            )
            count += 1
            print(f"✅ Migrasi user: {user.get('email')} ({count})")

    print(f"\n✨ Migrasi SELESAI. {count} user telah diperbarui.")

if __name__ == "__main__":
    asyncio.run(migrate())
