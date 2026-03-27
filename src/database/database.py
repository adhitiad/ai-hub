import hashlib
import os
import secrets
import sys
from datetime import datetime, timezone

from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient



# PERBAIKAN: Gunakan logger bawaan sistem
from src.core.logger import logger

load_dotenv()

# --- 1. Validasi Environment Variable ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv(
    "MONGO_DB_NAME", "ai_trading_hub"
)  # Pastikan nama DB default sesuai

if not MONGO_URI:
    logger.error("❌ FATAL ERROR: MONGO_URI is not set in .env file.")
    sys.exit(1)

# --- 2. Setup Client ---
client = AsyncIOMotorClient(MONGO_URI, tz_aware=True, tzinfo=timezone.utc)
db = client[DB_NAME]

users_collection = db.users
signals_collection = db.signals
transactions_collection = db.transactions
requests_collection = db.upgrade_requests
assets_collection = db.assets
presets_collection = db.screener_presets
alerts_collection = db.alerts


# --- 3. Helper Functions ---
def fix_id(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


async def close_db_connection():
    client.close()
    logger.info("🔒 MongoDB Connection Closed.")


async def init_db_indexes():
    try:
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("api_key")

        await signals_collection.create_index([("status", 1), ("symbol", 1)])
        await signals_collection.create_index(
            "created_at", expireAfterSeconds=86400 * 7
        )

        await transactions_collection.create_index("order_id", unique=True)
        await requests_collection.create_index([("user_email", 1), ("status", 1)])

        logger.info("⚡ Database Indexes Optimized")
    except Exception as e:
        logger.warning("⚠️ Warning during index creation: %s", e)


async def regenerate_api_key(user_id: str) -> str:
    """Generate API key baru dan invalidate yang lama secara aman"""
    new_key = f"ak_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(new_key.encode()).hexdigest()

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "api_key_hash": key_hash,
                "api_key_created_at": datetime.now(timezone.utc),
                "api_key_last_rotated": datetime.now(timezone.utc),
            },
            "$push": {
                "api_key_history": {
                    "hash": key_hash,
                    "created_at": datetime.now(timezone.utc),
                }
            },
        },
    )
    return new_key
