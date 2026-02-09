import os
import sys
from datetime import timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# --- 1. Validasi Environment Variable ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "ai_hub")

if not MONGO_URI:
    print("❌ FATAL ERROR: MONGO_URI is not set in .env file.")
    sys.exit(1)

# --- 2. Setup Client ---
client = AsyncIOMotorClient(MONGO_URI, tz_aware=True, tzinfo=timezone.utc)
db = client[DB_NAME]

# Definisi Collections
users_collection = db.users
signals_collection = db.signals
transactions_collection = db.transactions
requests_collection = db.upgrade_requests
assets_collection = db.assets
presets_collection = db.screener_presets
alerts_collection = db.alerts


# --- 3. Helper Functions ---
def fix_id(doc):
    """Mengubah ObjectId menjadi string 'id' untuk respons JSON."""
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


async def close_db_connection():
    """Menutup koneksi database saat server shutdown (Graceful Shutdown)."""
    client.close()
    print("🔒 MongoDB Connection Closed.")


async def init_db_indexes():
    """Membuat Index untuk performa query."""
    try:
        # Users
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("api_key")

        # Signals
        await signals_collection.create_index([("status", 1), ("symbol", 1)])
        # TTL Index: Hapus sinyal lama setelah 7 hari
        await signals_collection.create_index(
            "created_at", expireAfterSeconds=86400 * 7
        )

        # Transactions
        await transactions_collection.create_index("order_id", unique=True)

        # Upgrade Requests
        await requests_collection.create_index([("user_email", 1), ("status", 1)])

        print("⚡ Database Indexes Optimized")
    except Exception as e:
        print(f"⚠️ Warning during index creation: {e}")
