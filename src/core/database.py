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
# di src/core/database.py


# Helper: Mengubah ObjectId (Data internal Mongo) menjadi String untuk JSON
def fix_id(doc):
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc
