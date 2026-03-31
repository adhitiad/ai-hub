import os
from datetime import datetime, timezone
from typing import Any, Dict

import dotenv
from bson import ObjectId
from fastapi import HTTPException, Security

from src.core.security import hash_api_key
from src.database.cache_manager import SmartCache
from src.database.database import users_collection

dotenv.load_dotenv()


from fastapi.security.api_key import APIKeyCookie, APIKeyHeader
from starlette.requests import Request

dotenv.load_dotenv()


api_key_header_name = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=api_key_header_name, auto_error=False)

api_key_cookie_name = "session_token"
api_key_cookie = APIKeyCookie(name=api_key_cookie_name, auto_error=False)


def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Konversi ObjectId dan datetime ke format yang bisa di-serialize msgpack."""
    serialized = user.copy()
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    # Hanya serialize field datetime yang kita tahu ada
    for key in ["created_at", "api_key_created_at", "api_key_last_rotated"]:
        if key in serialized and isinstance(serialized[key], datetime):
            serialized[key] = serialized[key].isoformat()
    return serialized


def deserialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Kembalikan string ObjectId dan ISO datetime ke format aslinya."""
    deserialized = user.copy()
    if "_id" in deserialized:
        deserialized["_id"] = ObjectId(deserialized["_id"])
    for key in ["created_at", "api_key_created_at", "api_key_last_rotated"]:
        if key in deserialized and isinstance(deserialized[key], str):
            try:
                deserialized[key] = datetime.fromisoformat(deserialized[key])
            except (ValueError, TypeError):
                pass
    return deserialized


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

    # 1. Cari User Info (Identity) di Cache atau Mongo
    hashed_key = hash_api_key(api_key)
    cache_key = f"auth:user:{hashed_key}"

    user = await SmartCache.get(cache_key)
    if user:
        user = deserialize_user(user)
    else:
        user = await users_collection.find_one({"api_key_hash": hashed_key})
        if user:
            # Jangan cache field yang cepat berubah (rate limiting fields)
            # agar cache tetap valid lebih lama untuk identitas.
            cached_data = serialize_user(user)
            await SmartCache.set(cache_key, cached_data, ttl=600)

    if not user:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    if user.get("subscription_status") != "active":
        raise HTTPException(status_code=403, detail="Account Suspended")

    # 2. Rate Limiting & Identity Verification (Always Fresh from DB)
    # Kita gunakan find_one_and_update untuk memastikan rate limit akurat & user masih valid.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Logic: Jika hari berganti, reset ke 1. Jika tidak, increment.
    # Kita butuh status user terbaru juga untuk keamanan (misal baru saja di-suspend).

    # Filter untuk bypass limit
    is_privileged = user.get("role") in ["owner", "admin"]
    limit = max(user.get("daily_requests_limit", 75), 200)

    # Atomic Update & Fetch
    # Jika hari berbeda, kita reset requests_today.
    # Jika hari sama, kita cek limit (kecuali admin/owner).

    update_query = {"_id": user["_id"]}

    # Jika data di objek user (mungkin dari cache) menunjukkan hari sudah berganti,
    # kita coba reset di DB.
    if user.get("last_request_date") != today:
        updated_user = await users_collection.find_one_and_update(
            update_query,
            {"$set": {"requests_today": 1, "last_request_date": today}},
            return_document=True
        )
    else:
        # Jika hari sama, kita increment TAPI hanya jika belum kena limit
        # (Untuk non-privileged users)
        if not is_privileged:
            update_query["requests_today"] = {"$lt": limit}

        updated_user = await users_collection.find_one_and_update(
            update_query,
            {"$inc": {"requests_today": 1}},
            return_document=True
        )

        if not updated_user:
            # Jika find_one_and_update gagal karena filter limit, berarti limit tercapai
            # (Atau user dihapus tiba-tiba, tapi biasanya karena limit)
            actual_user = await users_collection.find_one({"_id": user["_id"]})
            if actual_user and actual_user.get("requests_today", 0) >= limit:
                 raise HTTPException(status_code=429, detail="Daily Limit Reached")
            raise HTTPException(status_code=403, detail="User Not Found or Invalid")

    return updated_user
