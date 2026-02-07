from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.api.roles import UserRole, check_permission
from src.core.database import fix_id, requests_collection, users_collection
from src.core.logger import logger


# --- Models ---
class UpgradeRequestModel(BaseModel):
    target_role: str


class ApprovalModel(BaseModel):
    request_id: str
    action: str  # "APPROVE" or "REJECT"
    note: str = ""


# --- Endpoints ---

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


def verify_admin(user: dict = Depends(get_current_user)):
    """Verifikasi apakah user adalah admin."""
    if not check_permission(user.get("role", ""), UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access Denied.")
    return user


@router.get("/users")
async def get_all_users(status: str = "all", admin: dict = Depends(verify_admin)):
    """Melihat daftar user untuk manajemen"""
    query = {}
    if status == "pending_upgrade":
        query["subscription_status"] = "pending_review"

    cursor = users_collection.find(query).limit(100)
    users = await cursor.to_list(length=100)

    # Sanitasi data (hapus password hash)
    for u in users:
        u["_id"] = str(u["_id"])
        u.pop("password_hash", None)

    return users


@router.post("/user/request-upgrade")
async def request_role_upgrade(
    req: UpgradeRequestModel, user: dict = Depends(get_current_user)
):
    """User meminta upgrade role ke Premium/Enterprise."""
    if req.target_role not in ["premium", "enterprise"]:
        raise HTTPException(status_code=400, detail="Role target tidak valid.")

    # Cek apakah sudah ada request pending
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
        # Gunakan Timezone Aware Datetime
        "created_at": datetime.now(timezone.utc),
        "admin_note": "",
    }
    await requests_collection.insert_one(new_req)
    return {"message": "Permohonan terkirim. Tunggu persetujuan Admin."}


@router.get("/admin/upgrade-queue")
async def get_pending_requests(user: dict = Depends(get_current_user)):
    """Admin melihat daftar request pending."""
    if not check_permission(user.get("role", ""), UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access Denied.")

    cursor = requests_collection.find({"status": "PENDING"}).sort("created_at", 1)
    requests = await cursor.to_list(length=100)
    return [fix_id(r) for r in requests]


@router.post("/admin/execute-upgrade")
async def process_upgrade_request(
    approval: ApprovalModel, user: dict = Depends(get_current_user)
):
    """Admin menyetujui atau menolak request."""
    if not check_permission(user.get("role", ""), UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access Denied.")

    try:
        obj_id = ObjectId(approval.request_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Request ID")

    request_data = await requests_collection.find_one({"_id": obj_id})
    if not request_data:
        raise HTTPException(status_code=404, detail="Request tidak ditemukan.")

    timestamp = datetime.now(timezone.utc)

    if approval.action == "APPROVE":
        new_limit = 1000 if request_data["requested_role"] == "premium" else 999999

        # Gunakan transaction untuk mencegah race condition
        async with await users_collection.database.client.start_session() as session:
            async with session.start_transaction():
                # Cek ulang status request sebelum update
                fresh_request = await requests_collection.find_one(
                    {"_id": obj_id}, session=session
                )
                if not fresh_request or fresh_request["status"] != "PENDING":
                    raise HTTPException(400, "Request sudah diproses oleh admin lain.")

                await users_collection.update_one(
                    {"email": request_data["user_email"]},
                    {
                        "$set": {
                            "role": request_data["requested_role"],
                            "daily_requests_limit": new_limit,
                        }
                    },
                    session=session,
                )
                logger.info(
                    f"✅ User {request_data['user_email']} promoted by {user['email']}"
                )

    # Update status request
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


@router.post("/approve-upgrade/{email}")
async def approve_upgrade(email: str, plan: str, admin: dict = Depends(verify_admin)):
    """Approve user ke Premium/Enterprise"""
    valid_plans = ["premium", "enterprise"]
    if plan not in valid_plans:
        raise HTTPException(400, "Plan tidak valid")

    result = await users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "role": plan,
                "subscription_status": "active",
                "upgraded_at": datetime.now(timezone.utc),
                "daily_requests_limit": 500 if plan == "premium" else 10000,
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(404, "User tidak ditemukan")

    return {"status": "success", "message": f"User {email} upgraded to {plan}"}


@router.get("/revenue-stats")
async def get_revenue_stats(admin: dict = Depends(verify_admin)):
    """Dashboard Admin: Hanya Pemasukan"""
    # Hitung user berdasarkan role
    pipeline = [{"$group": {"_id": "$role", "count": {"$sum": 1}}}]
    cursor = users_collection.aggregate(pipeline)
    stats = await cursor.to_list(length=None)

    counts = {item["_id"]: item["count"] for item in stats}

    # Asumsi Harga: Premium $29, Enterprise $99
    revenue = (counts.get("premium", 0) * 29) + (counts.get("enterprise", 0) * 99)

    return {
        "total_users": sum(counts.values()),
        "breakdown": counts,
        "monthly_revenue_usd": revenue,
        "last_updated": datetime.now(timezone.utc),
    }
