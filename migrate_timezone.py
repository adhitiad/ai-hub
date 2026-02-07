import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "ai_hub")


FIELDS_BY_COLLECTION = {
    "users": [
        "created_at",
        "subscription_end_date",
        "bonus_end_date",
        "upgraded_at",
        "last_updated",
    ],
    "signals": ["created_at", "closed_at"],
    "transactions": ["created_at", "updated_at"],
    "upgrade_requests": ["created_at", "updated_at"],
    "alerts": ["created_at"],
    "reports": ["uploaded_at"],
    "logs": ["timestamp"],
    "market_data": ["timestamp"],
    "assets": ["created_at", "updated_at"],
    "screener_presets": ["created_at", "updated_at"],
}


async def migrate_timezone(apply: bool) -> int:
    if not MONGO_URI:
        logging.info("ERROR: MONGO_URI is not set in environment/.env")
        return 1

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    total_docs = 0
    updated_docs = 0
    updated_fields = 0

    for collection_name, fields in FIELDS_BY_COLLECTION.items():
        collection = db[collection_name]
        query = {"$or": [{field: {"$exists": True}} for field in fields]}
        projection = {field: 1 for field in fields}
        projection["_id"] = 1

        cursor = collection.find(query, projection=projection).batch_size(500)

        coll_scanned = 0
        coll_updated = 0
        coll_fields = 0

        async for doc in cursor:
            total_docs += 1
            coll_scanned += 1
            updates = {}
            for field in fields:
                value = doc.get(field)
                if isinstance(value, datetime) and value.tzinfo is None:
                    updates[field] = value.replace(tzinfo=timezone.utc)

            if updates:
                updated_fields += len(updates)
                updated_docs += 1
                coll_fields += len(updates)
                coll_updated += 1
                if apply:
                    await collection.update_one({"_id": doc["_id"]}, {"$set": updates})

        logging.info(
            f"OK {collection_name}: scanned {coll_scanned} docs, updated {coll_updated} docs, fields set {coll_fields}"
        )

    client.close()

    mode = "APPLY" if apply else "DRY-RUN"
    logging.info("-" * 60)
    logging.info(f"Mode        : {mode}")
    logging.info(f"Collections : {len(FIELDS_BY_COLLECTION)}")
    logging.info(f"Docs scanned: {total_docs}")
    logging.info(f"Docs updated: {updated_docs}")
    logging.info(f"Fields set  : {updated_fields}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize naive datetime fields to UTC-aware datetimes."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply updates (default is dry-run).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(migrate_timezone(apply=args.apply))
    sys.exit(exit_code)
