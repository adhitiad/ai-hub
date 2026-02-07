from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter  # <--- Import ini
from pydantic import BaseModel, EmailStr

from src.core.database import fix_id, users_collection  # <--- Pakai Mongo
from src.core.logger import logger
from src.core.redis_client import redis_client
from src.core.security import generate_api_key, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterModel(BaseModel):
    email: EmailStr
    password: str


class LoginModel(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def register_user(data: RegisterModel):
    # 1. Cek Email (Async)
    try:
        existing = await users_collection.find_one({"email": data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

        # 2. Siapkan Dokumen User
        new_user = {
            "email": data.email,
            "password_hash": get_password_hash(data.password),
            "api_key": generate_api_key(),
            "role": "free",
            "subscription_status": "active",
            "daily_requests_limit": 50,
            "requests_today": 0,
            "last_request_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "watchlist": [],  # <--- Embed Watchlist disini
            "created_at": datetime.now(timezone.utc),
        }

        # 3. Simpan ke MongoDB
        await users_collection.insert_one(new_user)
        return {
            "status": "success",
            "message": "Registrasi berhasil.",
            "code": 201,
        }
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login_user(data: LoginModel):
    # 1. Cari User
    fail_key = f"login_fail:{data.email}"
    failed_attempts = await redis_client.get(fail_key)

    if failed_attempts and int(failed_attempts) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak percobaan gagal. Akun dikunci 15 menit.",
        )

    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=400, detail="Email atau password salah.")

    # 2. Verifikasi Password
    if not user or not verify_password(data.password, user["password_hash"]):
        # JIKA GAGAL: Catat kegagalan di Redis
        await redis_client.incr(fail_key)
        await redis_client.expire(fail_key, 900)  # Reset setelah 15 menit (900 detik)
        raise HTTPException(status_code=400, detail="Email atau password salah.")

    # JIKA SUKSES: Hapus catatan kegagalan
    await redis_client.delete(fail_key)

    return {
        "status": "success",
        "user": {
            "email": user["email"],
            "role": user["role"],
            "api_key": user["api_key"],
        },
    }
