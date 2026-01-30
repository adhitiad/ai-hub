import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import dotenv
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Route Admin Baru (Pastikan file src/api/admin_routes.py sudah dibuat)
from src.api.admin_routes import router as admin_router
from src.api.alert_routes import router as alert_router

# --- Imports Routes ---
from src.api.auth_routes import router as auth_router
from src.api.backtest_routes import router as backtest_router
from src.api.journal_routes import router as journal_router
from src.api.market_data_routes import router as market_router
from src.api.owner_ops import router as owner_router
from src.api.pipeline_routes import router as pipeline_router
from src.api.screener_routes import router as screener_router
from src.api.search_routes import router as search_router
from src.api.simulation_routes import router as sim_router
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

dotenv.load_dotenv()


# --- Lifespan Manager (Modern Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("✅ API Server Starting up...")

    # 1. Jalankan Indexing Database
    await init_db_indexes()

    # 2. Jalankan Background Tasks
    # Simpan task reference agar tidak terkena garbage collection
    tasks = [
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

    # 2. Tutup koneksi Database
    await close_db_connection()
    logger.info("🔒 Database Connection Closed")

    # 3. Tutup koneksi Redis
    await redis_client.close()  # Close Redis
    logger.info("🔒 Redis Connection Closed")


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


# Catatan: Route 'new_route' dihapus karena tidak relevan untuk production.


# --- 3. Global Endpoints ---
app = FastAPI(title="AI Trading Hub", lifespan=lifespan)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "status": "online",
        "system": "AI-Hub Production Ready",
        "version": "0.1-Alpha",
        "environment": f"{os.getenv('ENVIRONMENT', 'development')}",
        "server_time": datetime.now(),
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "ram_usage": f"{psutil.virtual_memory().percent}%",
        "cfg": {
            "signal_agent": {
                "enabled": f"{os.getenv('SIGNAL_AGENT_ENABLED', 'true').lower() == 'true'}",
                "threshold": 0.5,
            },
            "other_config": {
                "enabled": f"{os.getenv('OTHER_CONFIG_ENABLED', 'true').lower() == 'true'}",
                "value": 42,
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
    return {
        "status": "healthy",
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "ram_usage": f"{psutil.virtual_memory().percent}%",
        "server_time": datetime.now(timezone.utc),
    }
