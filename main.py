import asyncio
import time
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- API Imports ---
from src.api.auth import get_current_user
from src.api.auth_routes import router as auth_router
from src.api.owner_ops import router as owner_router
from src.api.roles import UserRole  # Pastikan file api/roles.py ada
from src.api.roles import check_permission
from src.api.search_routes import router as search_router
from src.api.user_routes import router as user_router

# Import koleksi MongoDB kita
from src.core.database import fix_id, requests_collection, users_collection

# --- Core Imports ---
from src.core.logger import logger
from src.core.producer import signal_producer_task
from src.core.signal_bus import signal_bus

app = FastAPI(title="AI Trading Hub (MongoDB)")

# --- 1. Setup CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 2. Middleware Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    user_key = request.headers.get("X-API-KEY", "Anonymous")

    logger.info(
        f"[{request.method}] {request.url.path} - {user_key} - {response.status_code} - {process_time:.4f}s"
    )
    return response


# --- 3. Daftarkan Router ---
app.include_router(auth_router)
app.include_router(owner_router)
app.include_router(search_router)
app.include_router(user_router)


# ==========================================
#  LOGIKA ADMIN & UPGRADE (MIGRATED TO MONGO)
# ==========================================


# --- Model Data Input ---
class UpgradeRequestModel(BaseModel):
    target_role: str  # 'premium' atau 'enterprise'


class ApprovalModel(BaseModel):
    request_id: str  # MongoDB ID adalah String (ObjectId), bukan Int
    action: str  # 'APPROVE' atau 'REJECT'
    note: str = ""


# --- Endpoint User Mengajukan Request ---
@app.post("/user/request-upgrade")
async def request_role_upgrade(
    req: UpgradeRequestModel, user: dict = Depends(get_current_user)
):
    """User Free mengajukan diri untuk jadi Premium/Enterprise."""

    if req.target_role not in ["premium", "enterprise"]:
        raise HTTPException(status_code=400, detail="Role tidak valid.")

    # Cek request pending (MongoDB)
    existing = await requests_collection.find_one(
        {"user_email": user["email"], "status": "PENDING"}
    )

    if existing:
        raise HTTPException(
            status_code=400, detail="Anda masih memiliki request yang sedang diproses."
        )

    # Simpan ke MongoDB
    try:
        new_req = {
            "user_email": user["email"],
            "requested_role": req.target_role,
            "status": "PENDING",
            "created_at": datetime.utcnow(),
            "admin_note": "",
        }
        await requests_collection.insert_one(new_req)
    except Exception as e:
        logger.error(f"Upgrade Request Error: {e}")
        raise HTTPException(status_code=500, detail="Gagal menyimpan request.")

    return {"message": "Permohonan terkirim. Tunggu persetujuan Admin."}


# --- Endpoint Admin Melihat Antrian ---
@app.get("/admin/upgrade-queue")
async def get_pending_requests(user: dict = Depends(get_current_user)):
    """Admin melihat siapa saja yang minta upgrade."""

    if not check_permission(user.get("role"), UserRole.ADMIN):
        raise HTTPException(
            status_code=403, detail="Hanya Admin yang boleh melihat ini."
        )

    # Ambil data PENDING dari Mongo
    cursor = requests_collection.find({"status": "PENDING"}).sort("created_at", 1)
    requests = await cursor.to_list(length=100)

    # Fix ID (ObjectId -> String)
    return [fix_id(r) for r in requests]


# --- Endpoint Admin Eksekusi (Approve/Reject) ---
@app.post("/admin/execute-upgrade")
async def process_upgrade_request(
    approval: ApprovalModel, user: dict = Depends(get_current_user)
):
    """Admin menyetujui atau menolak request."""

    if not check_permission(user.get("role"), UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access Denied.")

    from bson import ObjectId  # Butuh ini untuk convert string ID ke Mongo ID

    try:
        obj_id = ObjectId(approval.request_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Request ID")

    # Ambil Request
    request_data = await requests_collection.find_one({"_id": obj_id})

    if not request_data:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan.")

    if request_data["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Request ini sudah diproses.")

    # Logika Approve/Reject
    timestamp = datetime.utcnow()

    if approval.action == "APPROVE":
        new_limit = 1000 if request_data["requested_role"] == "premium" else 999999

        # Update User di Collection Users
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

    # Update Status Request
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
async def startup():
    logger.info("✅ API Server Starting up...")
    asyncio.create_task(signal_producer_task())


@app.get("/dashboard/all")
def get_dashboard():
    return signal_bus.get_all_signals()
