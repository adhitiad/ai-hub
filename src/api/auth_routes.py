from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from src.core.database import fix_id, users_collection  # <--- Pakai Mongo
from src.core.security import generate_api_key, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterModel(BaseModel):
    email: EmailStr
    password: str


class LoginModel(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register_user(data: RegisterModel):
    # 1. Cek Email (Async)
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
        "last_request_date": datetime.now().strftime("%Y-%m-%d"),
        "watchlist": [],  # <--- Embed Watchlist disini
        "created_at": datetime.utcnow(),
    }

    # 3. Simpan ke MongoDB
    await users_collection.insert_one(new_user)
    return {"status": "success", "message": "Registrasi berhasil."}


@router.post("/login")
async def login_user(data: LoginModel):
    # 1. Cari User
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=400, detail="Email atau password salah.")

    # 2. Verifikasi Password
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Email atau password salah.")

    return {
        "status": "success",
        "user": {
            "email": user["email"],
            "role": user["role"],
            "api_key": user["api_key"],
        },
    }
