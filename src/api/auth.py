import os
from datetime import datetime

import dotenv
from fastapi import HTTPException, Security
from src.core.security import hash_api_key
from src.database.database import fix_id, users_collection

dotenv.load_dotenv()


from fastapi.security.api_key import APIKeyHeader, APIKeyCookie
from starlette.requests import Request

dotenv.load_dotenv()


api_key_header_name = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=api_key_header_name, auto_error=False)

api_key_cookie_name = "session_token"
api_key_cookie = APIKeyCookie(name=api_key_cookie_name, auto_error=False)


async def get_current_user(
    request: Request,
    api_key_h: str = Security(api_key_header),
    api_key_c: str = Security(api_key_cookie),
):
    api_key = api_key_h or api_key_c

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Otentikasi diperlukan. Sesi mungkin kedaluwarsa.",
        )

    # 1. Cari di Mongo dengan Hash API Key
    hashed_key = hash_api_key(api_key)
    user = await users_collection.find_one({"api_key_hash": hashed_key})

    if not user:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    if user.get("subscription_status") != "active":
        raise HTTPException(status_code=403, detail="Account Suspended")

    # 2. Rate Limiting Logic (Update count di Mongo)
    today = datetime.now().strftime("%Y-%m-%d")

    update_fields = {}
    if user.get("last_request_date") != today:
        update_fields = {"requests_today": 1, "last_request_date": today}
    else:
        # Cek Limit
        limit = max(user.get("daily_requests_limit", 75), 200)
        # Owner & Admin bypass limit
        if (
            user.get("role") not in ["owner", "admin"]
            and user.get("requests_today", 0) >= limit
        ):
            raise HTTPException(status_code=429, detail="Daily Limit Reached")

        update_fields = {"requests_today": user.get("requests_today", 0) + 1}

    # Update counter secara background (fire and forget)
    await users_collection.update_one({"_id": user["_id"]}, {"$set": update_fields})

    # --- PERBAIKAN: Return User Utuh (Raw) ---
    # Jangan gunakan fix_id(user) di sini karena akan menghapus '_id'.
    # Route lain membutuhkan '_id' asli untuk operasi database.
    return user
