import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logger import logger


# --- 1. Custom Logging Middleware ---
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Proses request
        try:
            response = await call_next(request)
        except Exception as e:
            # Jika error terjadi di tengah processing request (sebelum masuk route handler)
            logger.error(f"🔥 Middleware Error: {str(e)}")
            raise e

        process_time = time.time() - start_time

        # Ambil User Agent atau API Key (Masked) untuk log
        user_key = request.headers.get("X-API-KEY", "Anonymous")
        if len(user_key) > 10:
            user_key = user_key[:4] + "***" + user_key[-4:]

        # Log ke console/file
        log_msg = (
            f"[{request.method}] {request.url.path} "
            f"- User: {user_key} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.4f}s"
        )

        if response.status_code >= 400:
            logger.warning(f"⚠️ {log_msg}")
        else:
            logger.info(f"✅ {log_msg}")

        # Tambahkan Header Process-Time (Berguna untuk debug latency di frontend)
        response.headers["X-Process-Time"] = str(process_time)

        return response


# --- 2. Global Exception Handler ---
async def global_exception_handler(request: Request, exc: Exception):
    """
    Menangkap semua error yang tidak terhandle (Error 500)
    agar server tidak crash dan memberikan pesan jelas ke frontend.
    """
    error_msg = str(exc)
    trace = traceback.format_exc()

    logger.error(f"🔥 CRITICAL ERROR at {request.url.path}: {error_msg}\n{trace}")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "detail": error_msg,  # Bisa disembunyikan di production
            "path": request.url.path,
        },
    )


# --- 3. Main Setup Function ---
def register_middleware(app: FastAPI):
    """
    Fungsi utama untuk mendaftarkan semua middleware ke aplikasi FastAPI.
    """

    # A. CORS (Cross-Origin Resource Sharing)
    # Penting agar Frontend (localhost:3000) bisa hit API (localhost:8000)
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-production-domain.com",
        "*",  # Ganti spesifik domain saat production agar aman
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # B. Register Custom Logging Middleware
    app.add_middleware(LoggingMiddleware)

    # C. Register Exception Handlers
    app.add_exception_handler(Exception, global_exception_handler)
