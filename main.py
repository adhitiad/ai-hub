import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

import dotenv
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi_limiter import FastAPILimiter
from pymongo.errors import ConnectionFailure
from redis.exceptions import ConnectionError

# Route Admin Baru (Pastikan file src/api/admin_routes.py sudah dibuat)
from src.api.admin_routes import router as admin_router
from src.api.alert_routes import router as alert_router
from src.api.analysis_routes import router as analysis_router

# --- Imports Routes ---
from src.api.auth_routes import router as auth_router
from src.api.backtest_routes import router as backtest_router
from src.api.chat_routes import router as chat_router
from src.api.journal_routes import router as journal_router
from src.api.market_data_routes import router as market_router
from src.api.owner_ops import router as owner_router
from src.api.pipeline_routes import router as pipeline_router
from src.api.portfolio_routes import router as portfolio_router
from src.api.screener_routes import router as screener_router
from src.api.search_routes import router as search_router
from src.api.simulation_routes import router as sim_router
from src.api.subscription_routes import router as subscription_router
from src.api.user_routes import router as user_router

# --- Imports Core ---
from src.core.database import close_db_connection, init_db_indexes
from src.core.logger import logger
from src.core.middleware import register_middleware
from src.core.producer import signal_producer_task
from src.core.redis_client import redis_client
from src.core.signal_bus import signal_bus
from src.core.socket_manager import manager, redis_connector_task
from src.core.stream_manager import StreamManager
from src.core.subscription_scheduler import start_scheduler
from src.core.training_scheduler import training_scheduler_task


# --- Configuration Validation ---
def validate_config():
    required_envs = ["MONGO_URI", "MONGO_DB_NAME", "SECRET_KEY"]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


dotenv.load_dotenv()


# --- Lifespan Manager (Modern Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("✅ API Server Starting up...")

    # 1. Validasi konfigurasi
    try:
        validate_config()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise

    # 2. Initialize Redis connection FIRST
    try:
        await redis_client.connect()
        logger.info("✅ Redis connection established")
    except ConnectionError as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

    # 3. Initialize FastAPILimiter BEFORE anything that might use it
    try:
        await FastAPILimiter.init(redis_client.redis)
        logger.info("✅ FastAPILimiter initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize FastAPILimiter: {e}")
        raise

    # 4. Jalankan Indexing Database
    try:
        await init_db_indexes()
        logger.info("✅ Database indexes initialized")
    except ConnectionFailure as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # 5. Jalankan Background Tasks
    # Simpan task reference agar tidak terkena garbage collection
    tasks: List[asyncio.Task] = [
        asyncio.create_task(signal_producer_task()),
        # Ganti broadcast_market_data dengan redis_connector_task
        asyncio.create_task(redis_connector_task()),
        asyncio.create_task(start_scheduler()),
        asyncio.create_task(training_scheduler_task()),
        asyncio.create_task(StreamManager().start_consumer()),
    ]

    yield  # Aplikasi berjalan di sini

    # --- SHUTDOWN ---
    logger.info("🛑 API Server Shutting down...")

    # 1. Cancel background tasks
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("✅ Background tasks cancelled")

    # 2. Tutup koneksi Database
    try:
        await close_db_connection()
        logger.info("🔒 Database Connection Closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")

    # 3. Tutup koneksi Redis
    try:
        await redis_client.close()  # Close Redis
        logger.info("🔒 Redis Connection Closed")
    except Exception as e:
        logger.error(f"❌ Error closing Redis: {e}")


# --- Init App ---
app = FastAPI(
    title="AI Trading Hub (Production Ready)",
    description="Backend API with AI, Bandarmology, and Global Middleware",
    version="2.1.0",
    lifespan=lifespan,  # Menggunakan lifespan handler
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=os.getenv("DEBUG", "False").lower() == "true",
)

# --- 1. Setup Middleware ---
register_middleware(app)

# --- 2. Register Routes ---
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(owner_router)
app.include_router(admin_router)  # Route Admin yang sudah dipisah
app.include_router(search_router)
app.include_router(market_router)
app.include_router(alert_router)
app.include_router(screener_router)
app.include_router(journal_router)
app.include_router(pipeline_router)
app.include_router(backtest_router)
app.include_router(sim_router)
app.include_router(analysis_router)  # Route Analisis
app.include_router(chat_router)  # Route Chat
app.include_router(portfolio_router)  # Route Portfolio
app.include_router(subscription_router)  # Route Subscription


# Catatan: Route 'new_route' dihapus karena tidak relevan untuk production.


# --- 3. Global Endpoints ---


@app.get("/")
async def root():
    """
    Root endpoint
    """
    # Get system info with error handling
    try:
        cpu_usage = f"{psutil.cpu_percent()}%"
        ram_usage = f"{psutil.virtual_memory().percent}%"
    except Exception as e:
        cpu_usage = "N/A"
        ram_usage = "N/A"
        logger.error(f"❌ Error getting system info: {e}")

    return {
        "status": "online",
        "system": "AI-Hub Production Ready",
        "version": "2.1.0",
        "environment": f"{os.getenv('ENVIRONMENT', 'development')}",
        "server_time": datetime.now(timezone.utc),
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "cfg": {
            "signal_agent": {
                "enabled": f"{os.getenv('SIGNAL_AGENT_ENABLED', 'true').lower() == 'true'}",
                "threshold": 0.5,
            },
            "other_config": {
                "enabled": f"{os.getenv('OTHER_CONFIG_ENABLED', 'true').lower() == 'true'}",
                "value": 42,
            },
            # Tambahkan config dari environment
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": os.getenv("REDIS_PORT", "6379"),
            },
            "mongo": {
                "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
                "db_name": os.getenv("MONGO_DB_NAME", "ai_trading_hub"),
            },
        },
    }


@app.websocket("/ws/market/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, symbol)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Handle disconnection
        logger.info(f"❌ WS Disconnected: {symbol}")
        manager.disconnect(websocket, symbol)


@app.get("/health")
def health_check():
    # Get system info with error handling
    try:
        cpu_usage = f"{psutil.cpu_percent()}%"
        ram_usage = f"{psutil.virtual_memory().percent}%"
    except Exception as e:
        cpu_usage = "N/A"
        ram_usage = "N/A"
        logger.error(f"❌ Error getting system info: {e}")

    return {
        "status": "healthy",
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "server_time": datetime.now(timezone.utc),
        # Tambahkan health check untuk dependencies
        "dependencies": {
            "database": "healthy" if os.getenv("MONGO_URI") else "unhealthy",
            "redis": "healthy" if os.getenv("REDIS_HOST") else "unhealthy",
        },
    }
