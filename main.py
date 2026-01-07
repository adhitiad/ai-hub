import asyncio
from datetime import datetime

import subscription_scheduler
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.api.alert_routes import router as alert_router
from src.api.auth import get_current_user

# --- Import Routes ---
from src.api.auth_routes import router as auth_router
from src.api.backtest_routes import router as backtest_router
from src.api.journal_routes import router as journal_router

# (Import route baru Anda di sini jika ada, misal: market_router, alert_router)
from src.api.market_data_routes import router as market_router
from src.api.new_route import router as newroute
from src.api.owner_ops import router as owner_router
from src.api.pipeline_routes import router as pipeline_router
from src.api.roles import UserRole, check_permission
from src.api.screener_routes import router as screener_router
from src.api.search_routes import router as search_router
from src.api.user_routes import router as user_router
from src.core.database import (
    fix_id,
    init_db_indexes,
    requests_collection,
    users_collection,
)

# --- Import Core & Middleware ---
from src.core.logger import logger

# ⭐️ Import Middleware Baru
from src.core.middleware import register_middleware
from src.core.producer import signal_producer_task
from src.core.signal_bus import signal_bus
from src.core.socket_manager import broadcast_market_data, manager
from src.core.training_scheduler import training_scheduler_task

# --- Init App ---
app = FastAPI(
    title="AI Trading Hub (Production Ready)",
    description="Backend API with AI, Bandarmology, and Global Middleware",
    version="2.0.0",
)

# --- 1. Setup Middleware ---
# Panggil fungsi dari src/core/middleware.py
register_middleware(app)

# --- 2. Daftarkan Router ---
app.include_router(auth_router)
app.include_router(owner_router)
app.include_router(search_router)
app.include_router(user_router)
app.include_router(newroute)
# Route Fitur Baru
app.include_router(market_router)
app.include_router(alert_router)
app.include_router(screener_router)
app.include_router(journal_router)
app.include_router(pipeline_router)
app.include_router(backtest_router)

# ==========================================
#  LOGIKA ADMIN & UPGRADE (Legacy Routes)
# ==========================================
# ... (Kode endpoint admin/upgrade tetap sama seperti sebelumnya) ...
# (Saya singkat agar fokus pada perubahan middleware,
#  pastikan endpoint /user/request-upgrade dll tetap ada di sini
#  atau pindahkan ke file router terpisah untuk kerapihan)


class UpgradeRequestModel(BaseModel):
    target_role: str


class ApprovalModel(BaseModel):
    request_id: str
    action: str
    note: str = ""


@app.post("/user/request-upgrade")
async def request_role_upgrade(
    req: UpgradeRequestModel, user: dict = Depends(get_current_user)
):
    if req.target_role not in ["premium", "enterprise"]:
        raise HTTPException(status_code=400, detail="Role tidak valid.")

    existing = await requests_collection.find_one(
        {"user_email": user["email"], "status": "PENDING"}
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Anda masih memiliki request yang sedang diproses."
        )

    new_req = {
        "user_email": user["email"],
        "requested_role": req.target_role,
        "status": "PENDING",
        "created_at": datetime.utcnow(),
        "admin_note": "",
    }
    await requests_collection.insert_one(new_req)
    return {"message": "Permohonan terkirim. Tunggu persetujuan Admin."}


@app.get("/admin/upgrade-queue")
async def get_pending_requests(user: dict = Depends(get_current_user)):
    if not check_permission(user.get("role", ""), UserRole.ADMIN):
        raise HTTPException(
            status_code=403, detail="Hanya Admin yang boleh melihat ini."
        )

    cursor = requests_collection.find({"status": "PENDING"}).sort("created_at", 1)
    requests = await cursor.to_list(length=100)
    return [fix_id(r) for r in requests]


@app.post("/admin/execute-upgrade")
async def process_upgrade_request(
    approval: ApprovalModel, user: dict = Depends(get_current_user)
):
    if not check_permission(user.get("role", ""), UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access Denied.")

    from bson import ObjectId

    try:
        obj_id = ObjectId(approval.request_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Request ID")

    request_data = await requests_collection.find_one({"_id": obj_id})
    if not request_data:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan.")

    timestamp = datetime.utcnow()

    if approval.action == "APPROVE":
        new_limit = 1000 if request_data["requested_role"] == "premium" else 999999
        await users_collection.update_one(
            {"email": request_data["user_email"]},
            {
                "$set": {
                    "role": request_data["requested_role"],
                    "daily_requests_limit": new_limit,
                }
            },
        )
        logger.info(
            f"✅ User {request_data['user_email']} promoted to {request_data['requested_role']}"
        )

    await requests_collection.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "status": approval.action,
                "admin_note": f"Processed by {user['email']}. Note: {approval.note}",
                "updated_at": timestamp,
            }
        },
    )
    return {
        "status": "success",
        "action": approval.action,
        "user": request_data["user_email"],
    }


# --- System Startup ---


@app.on_event("startup")
async def startup_event():
    logger.info("✅ API Server Starting up...")

    # 1. Jalankan Indexing Database
    await init_db_indexes()

    # 2. Jalankan Producer Sinyal
    asyncio.create_task(signal_producer_task())

    # 3. Jalankan Stream Data Realtime (WebSocket)
    asyncio.create_task(broadcast_market_data())

    asyncio.create_task(subscription_scheduler.start_scheduler())

    asyncio.create_task(training_scheduler_task())


# --- ENDPOINT WEBSOCKET ---
@app.websocket("/ws/market/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, symbol)
    try:
        while True:
            # Keep connection alive, wait for client messages (optional)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, symbol)


@app.get("/dashboard/all")
def get_dashboard():
    return signal_bus.get_all_signals()
