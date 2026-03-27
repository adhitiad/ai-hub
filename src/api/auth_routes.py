from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.logger import logger
from src.core.security import generate_api_key, get_password_hash, verify_password
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
async def register_user(data: RegisterModel):
    try:
        existing = await users_collection.find_one({"email": data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

        new_api_key = generate_api_key()

        new_user = {
            "email": data.email,
            "password_hash": get_password_hash(data.password),
            "api_key": new_api_key,  # Simpan plain untuk backward compatibility (idealnya di-hash)
            "role": "free",
            "subscription_status": "active",
            "daily_requests_limit": 50,
            "requests_today": 0,
            "last_request_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "watchlist": [],
            "created_at": datetime.now(timezone.utc),
        }

        await users_collection.insert_one(new_user)
        return {
            "status": "success",
            "message": "Registrasi berhasil.",
            "api_key": new_api_key,  # Tampilkan HANYA SEKALI di sini
            "code": 201,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error registering user: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login_user(data: LoginModel):
    fail_key = f"login_fail:{data.email}"

    # Ambil record gagal dari redis (Handle jika redis mengembalikan bytes)
    failed_attempts_raw = await redis_client.get(fail_key)
    failed_attempts = int(failed_attempts_raw) if failed_attempts_raw else 0

    if failed_attempts >= 5:
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak percobaan gagal. Akun dikunci 15 menit.",
        )

    user = await users_collection.find_one({"email": data.email})

    # PERBAIKAN KRITIS: Gabungkan cek user ada ATAU password salah dalam satu blok
    # Agar jika email tidak ada, sistem tetap mencatatnya sebagai percobaan gagal.
    if not user or not verify_password(data.password, user["password_hash"]):
        await redis_client.incr(fail_key)
        await redis_client.expire(fail_key, 900)  # 15 menit
        # Jangan beri tahu apakah email atau password yang salah (Mencegah enumerasi email)
        raise HTTPException(status_code=400, detail="Email atau password salah.")

    # Reset kegagalan jika sukses
    await redis_client.delete(fail_key)

    # Catatan: Di masa depan, ganti pengembalian 'api_key' ini dengan JWT Access Token
    return {
        "status": "success",
        "user": {
            "email": user["email"],
            "role": user["role"],
            "api_key": user.get("api_key", ""),
        },
    }
