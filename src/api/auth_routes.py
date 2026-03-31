from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.logger import logger
from src.core.security import (
    generate_api_key,
    get_password_hash,
    hash_api_key,
    verify_password,
)
from src.database.database import users_collection
from src.database.redis_client import redis_client

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterModel(BaseModel):
    email: EmailStr
    password: str


class LoginModel(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def register_user(data: RegisterModel, response: Response):
    try:
        existing = await users_collection.find_one({"email": data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

        new_api_key = generate_api_key()
        hashed_api_key = hash_api_key(new_api_key)

        new_user = {
            "email": data.email,
            "password_hash": get_password_hash(data.password),
            "api_key_hash": hashed_api_key,
            "role": "free",
            "subscription_status": "active",
            "daily_requests_limit": 75,
            "requests_today": 0,
            "last_request_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "watchlist": [],
            "created_at": datetime.now(timezone.utc),
        }

        await users_collection.insert_one(new_user)
        
        # Setel cookie otentikasi
        response.set_cookie(
            key="session_token",
            value=new_api_key,
            httponly=True,
            samesite="lax",
            secure=False, # Set ke True di production (HTTPS dialihkan)
            max_age=30 * 24 * 60 * 60, # 30 hari
        )

        return {
            "status": "success",
            "message": "Registrasi berhasil.",
            "api_key": new_api_key,
            "code": 201,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error registering user: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login_user(data: LoginModel, response: Response):
    fail_key = f"login_fail:{data.email}"

    failed_attempts_raw = await redis_client.get(fail_key)
    failed_attempts = int(failed_attempts_raw) if failed_attempts_raw else 0

    if failed_attempts >= 5:
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak percobaan gagal. Akun dikunci 15 menit.",
        )

    user = await users_collection.find_one({"email": data.email})

    if not user or not verify_password(data.password, user["password_hash"]):
        await redis_client.incr(fail_key)
        await redis_client.expire(fail_key, 900)
        raise HTTPException(status_code=400, detail="Email atau password salah.")

    await redis_client.delete(fail_key)
    
    # Session Rotation: Generate key baru setiap login
    old_hash = user.get("api_key_hash")
    new_api_key = generate_api_key()
    hashed_api_key = hash_api_key(new_api_key)

    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"api_key_hash": hashed_api_key}, "$unset": {"api_key": ""}},
    )

    # Invalidate old cache
    if old_hash:
        from src.database.cache_manager import SmartCache
        await SmartCache.delete(f"auth:user:{old_hash}")
    
    # Setel cookie otentikasi (HttpOnly & SameSite)
    response.set_cookie(
        key="session_token",
        value=new_api_key,
        httponly=True,
        samesite="lax",
        secure=False, # Gunakan True di production dengan HTTPS
        max_age=30 * 24 * 60 * 60, # 30 hari
    )

    return {
        "status": "success",
        "user": {
            "email": user["email"],
            "role": user["role"],
            "api_key": new_api_key, # Key baru untuk sesi ini
        },
    }


@router.post("/logout")
async def logout_user(response: Response):
    """
    Mengakhiri sesi dengan menghapus cookie otentikasi.
    """
    response.delete_cookie(key="session_token")
    return {"status": "success", "message": "Berhasil keluar."}
