import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "ai_hub")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Definisi Collections (Mirip Tabel)
users_collection = db.users
signals_collection = db.signals
transactions_collection = db.transactions
requests_collection = db.upgrade_requests
assets_collection = db.assets
presets_collection = db.screener_presets  # Menyimpan settingan Screener user
alerts_collection = db.alerts  # Menyimpan Price Alert & Formula Alert


# Helper: Mengubah ObjectId (Data internal Mongo) menjadi String untuk JSON
def fix_id(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


# ... (kode lama) ...


async def init_db_indexes():
    """
    Membuat Index untuk mempercepat query hingga 100x lipat.
    """
    # 1. Users: Email harus unik, API Key harus cepat dicari
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("api_key")

    # 2. Signals: Sering dicari berdasarkan status (OPEN) dan Symbol
    await signals_collection.create_index([("status", 1), ("symbol", 1)])
    await signals_collection.create_index(
        "created_at", expireAfterSeconds=86400 * 7
    )  # Auto hapus sinyal > 7 hari (Opsional)

    # 3. Transactions: Order ID unik
    await transactions_collection.create_index("order_id", unique=True)

    print("⚡ Database Indexes Optimized")
