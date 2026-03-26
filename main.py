import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

import dotenv
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse  # Pindahkan import ke atas
from fastapi_limiter import FastAPILimiter
from pymongo.errors import ConnectionFailure
from redis.exceptions import ConnectionError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address  # Hapus alias redundan

# --- Imports Routes ---
from src.api.admin_routes import router as admin_router
from src.api.alert_routes import router as alert_router
from src.api.analysis_routes import router as analysis_router
from src.api.auth_routes import router as auth_router
from src.api.backtest_routes import router as backtest_router
from src.api.chat_routes import router as chat_router
from src.api.dashboard_routes import router as dashboard_router
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
from src.core.logger import logger
from src.core.middleware import register_middleware
from src.core.producer import signal_producer_task
from src.core.stream_manager import StreamManager
from src.core.subscription_scheduler import start_scheduler
from src.core.training_scheduler import training_scheduler_task
from src.database.database import close_db_connection, init_db_indexes
from src.database.redis_client import redis_client
from src.database.socket_manager import manager, redis_connector_task

# Load environment variables
dotenv.load_dotenv()


# --- Configuration Validation ---
def validate_config():
    required_envs = ["MONGO_URI", "MONGO_DB_NAME", "SECRET_KEY"]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


# --- Lifespan Manager (Modern Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("✅ API Server Starting up...")

    try:
        validate_config()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise

    try:
        await redis_client.connect()
        logger.info("✅ Redis connection established")
    except ConnectionError as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

    try:
        await FastAPILimiter.init(redis_client.redis)
        logger.info("✅ FastAPILimiter initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize FastAPILimiter: {e}")
        raise

    try:
        await init_db_indexes()
        logger.info("✅ Database indexes initialized")
    except ConnectionFailure as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Simpan task reference agar tidak terkena garbage collection
    tasks: List[asyncio.Task] = [
        asyncio.create_task(signal_producer_task()),
        asyncio.create_task(redis_connector_task()),
        asyncio.create_task(start_scheduler()),
        asyncio.create_task(training_scheduler_task()),
        asyncio.create_task(StreamManager().start_consumer()),
    ]

    try:
        # Aplikasi berjalan di sini
        yield
    finally:
        # --- SHUTDOWN --- (Akan selalu dieksekusi walau terjadi error/crash)
        logger.info("🛑 API Server Shutting down...")

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ Background tasks cancelled")

        try:
            await close_db_connection()
            logger.info("🔒 Database Connection Closed")
        except Exception as e:
            logger.error(f"❌ Error closing database: {e}")

        try:
            await redis_client.close()
            logger.info("🔒 Redis Connection Closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis: {e}")


# --- Init App ---
app = FastAPI(
    title="AI Trading Hub (Production Ready)",
    description="Backend API with AI, Bandarmology, and Global Middleware",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=os.getenv("DEBUG", "False").lower() == "true",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc: Exception):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )


# --- 1. Setup Middleware ---
register_middleware(app)


# --- 2. Register Routes ---
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(owner_router)
app.include_router(admin_router)
app.include_router(dashboard_router)
app.include_router(search_router)
app.include_router(market_router)
app.include_router(alert_router)
app.include_router(screener_router)
app.include_router(journal_router)
app.include_router(pipeline_router)
app.include_router(backtest_router)
app.include_router(sim_router)
app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(portfolio_router)
app.include_router(subscription_router)


# --- 3. Global Endpoints ---


@app.get("/")
async def root():
    """
    Root endpoint
    """
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
            },
            # PERBAIKAN: JANGAN PERNAH mengekspos host, port, apalagi URI database ke endpoint publik!
            "dependencies_configured": {
                "redis": bool(os.getenv("REDIS_HOST")),
                "mongo": bool(os.getenv("MONGO_URI")),
            },
        },
    }


@app.websocket("/ws/market/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, symbol)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"❌ WS Disconnected: {symbol}")
        manager.disconnect(websocket, symbol)


@app.get("/health")
def health_check():
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
        # Catatan: Ini hanya mengecek apakah env variable diset, bukan koneksi aktual.
        "dependencies": {
            "database": "configured" if os.getenv("MONGO_URI") else "missing_config",
            "redis": "configured" if os.getenv("REDIS_HOST") else "missing_config",
        },
    }
