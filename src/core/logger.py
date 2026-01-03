import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Buat folder logs jika belum ada
if not os.path.exists("logs"):
    os.makedirs("logs")


def setup_logger(name="AI_TRADING_BACKEND"):
    """
    Konfigurasi Logger Pusat dengan Fix Encoding Windows (UTF-8).
    """

    # --- 🛠️ WINDOWS FIX: FORCE UTF-8 STDOUT ---
    # Memaksa terminal Windows menerima emoji tanpa error
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
        except AttributeError:
            # Fallback untuk versi python lama
            import io

            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # 1. Inisialisasi Logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    # 2. Format Logging
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 3. Handler 1: File (Rotating)
    # PENTING: Tambahkan encoding='utf-8' agar file log bisa simpan emoji
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",  # <--- WAJIB ADA
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 4. Handler 2: Console (Terminal)
    # Kita arahkan eksplisit ke sys.stdout yang sudah di-reconfigure di atas
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Buat instance global agar mudah di-import
logger = setup_logger()
