# src/database/indexes.py
from motor.motor_asyncio import AsyncIOMotorClient

from src.core.logger import logger


async def create_indexes(db: AsyncIOMotorClient):
    """Create all necessary indexes"""

    # Users collection
    await db.users.create_index("email", unique=True)
    await db.users.create_index("api_key_hash", unique=True, sparse=True)
    await db.users.create_index("role")
    await db.users.create_index("subscription.status")
    await db.users.create_index("created_at")
    await db.users.create_index([("last_login", -1)])

    # Signals collection
    await db.signals.create_index("symbol")
    await db.signals.create_index([("timestamp", -1)])
    await db.signals.create_index([("symbol", "timestamp")])
    await db.signals.create_index("action")
    await db.signals.create_index("confidence")

    # Trades collection
    await db.trades.create_index("user_id")
    await db.trades.create_index("symbol")
    await db.trades.create_index([("user_id", "symbol")])
    await db.trades.create_index([("entry_time", -1)])
    await db.trades.create_index("status")
    await db.trades.create_index([("user_id", "status")])

    # Orders collection
    await db.orders.create_index("user_id")
    await db.orders.create_index("symbol")
    await db.orders.create_index("status")
    await db.orders.create_index("broker_order_id")
    await db.orders.create_index([("created_at", -1)])

    # Audit logs
    await db.audit_logs.create_index([("timestamp", -1)])
    await db.audit_logs.create_index("user_id")
    await db.audit_logs.create_index("action")
    await db.audit_logs.create_index([("user_id", "timestamp")])

    # TTL indexes untuk data temporary
    await db.sessions.create_index(
        "expires_at", expireAfterSeconds=0  # Auto-delete expired sessions
    )

    await db.password_resets.create_index("expires_at", expireAfterSeconds=0)

    logger.info("✅ All indexes created successfully")


# Index monitoring
async def analyze_query_performance(db: AsyncIOMotorClient):
    """Analyze slow queries"""
    # Get profiling data
    slow_queries = (
        await db.system.profile.find({"millis": {"$gt": 100}})  # Queries taking >100ms
        .sort("ts", -1)
        .limit(10)
        .to_list(length=10)
    )

    for query in slow_queries:
        logger.warning("Slow query: %s - %sms", query['ns'], query['millis'])
        logger.warning("Query: %s", query.get('query', 'N/A'))
        logger.warning("Plan: %s", query.get('planSummary', 'N/A'))
        logger.warning("---")

    return slow_queries
