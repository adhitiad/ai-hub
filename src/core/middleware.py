import hashlib
import time
import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.logger import logger
from src.database.database import db  # Asumsi ada koneksi DB
from src.database.redis_client import redis_client


# --- 1. Custom Logging Middleware ---
# --- 1. Custom Logging Middleware (Pure ASGI to support WebSockets) ---
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Jika bukan HTTP (misal WebSocket), lewatkan saja tanpa modifikasi
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Logika Logging untuk HTTP
        request = Request(scope, receive)
        start_time = time.time()

        # Kita perlu membungkus 'send' untuk mendapatkan status code response
        response_status = [200]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_status[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error("🔥 Middleware Error: %s", e)
            raise e

        # Skip logging untuk path docs/static atau GET biasa yang tidak sensitif
        if request.url.path in ["/docs", "/openapi.json", "/health", "/"]:
            return

        process_time = time.time() - start_time
        status_code = response_status[0]

        # Audit logging (POST/PUT/DELETE)
        if request.method in ["POST", "PUT", "DELETE"] or any(x in request.url.path for x in ["admin", "owner"]):
            user_email = request.headers.get("X-User-Email", "Anonymous")
            log_entry = {
                "timestamp": datetime.now(timezone.utc),
                "user": user_email,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "process_time": f"{process_time:.4f}s",
            }
            try:
                # Simpan ke DB secara non-blocking
                await db.logs.insert_one(log_entry)
            except Exception as e:
                logger.error("❌ Failed to save audit log: %s", e)

        # Console Log
        log_msg = f"[{request.method}] {request.url.path} - Status: {status_code} - Time: {process_time:.4f}s"
        if status_code >= 400:
            logger.warning("⚠️ %s", log_msg)
        else:
            logger.info("✅ %s", log_msg)


# --- 2. Global Exception Handler ---
async def global_exception_handler(request: Request, exc: Exception):
    """
    Menangkap semua error yang tidak terhandle (Error 500)
    agar server tidak crash dan memberikan pesan jelas ke frontend.
    """
    error_msg = str(exc)
    trace = traceback.format_exc()

    logger.error("🔥 CRITICAL ERROR at %s: %s\n%s", request.url.path, error_msg, trace)

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "detail": error_msg,
            "path": request.url.path,
        },
    )


# --- 3. Main Setup Function ---
def register_middleware(app: FastAPI):
    """
    Fungsi utama untuk mendaftarkan semua middleware ke aplikasi FastAPI.
    """

    # A. CORS (Cross-Origin Resource Sharing)
    # Gunakan list spesifik, hindari "*" jika allow_credentials=True
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://10.10.1.124:3000", # Network IP Anda
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # B. Register Custom Logging Middleware
    # Gunakan add_middleware dengan class ASGI murni
    app.add_middleware(LoggingMiddleware)

    # C. Register Exception Handlers
    app.add_exception_handler(Exception, global_exception_handler)


# Pseudo-code logic untuk middleware.py
async def check_trial_access(user_id):
    # Cek pemakaian bulan ini di Redis
    current_month = datetime.now().strftime("%Y-%m")
    usage_key = f"trial_usage:{user_id}:{current_month}"

    if redis_client.redis is None:
        raise HTTPException(500, "Redis connection not initialized")

    used_minutes = await redis_client.redis.get(usage_key) or 0

    if int(used_minutes) >= 120:  # 120 Menit = 2 Jam
        raise HTTPException(403, "Kuota Trial 2 Jam/Bulan Habis. Upgrade ke Premium.")

    # Jika lolos, catat waktu request ini (misal tambah 1 menit per request atau hitung durasi sesi)
    # Cara simpel: Asumsi 1 request = 1 poin, atau tracking WebSocket duration.


# Middleware untuk validasi API key
async def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    user = await db.users.find_one({"api_key_hash": key_hash})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Cek apakah key sudah expired (opsional)
    key_age = datetime.now(timezone.utc) - user.get("api_key_created_at", datetime.now(timezone.utc))
    if key_age.days > 90:  # Rotate setiap 90 hari
        raise HTTPException(
            status_code=401, detail="API key expired. Please regenerate."
        )

    return user
