import logging
import os
import shutil
import sys
from logging.handlers import RotatingFileHandler

# Buat folder logs jika belum ada
os.makedirs("logs", exist_ok=True)


class WindowsRotatingFileHandler(RotatingFileHandler):
    """
    Custom RotatingFileHandler untuk menangani masalah locking file di Windows.
    Menggunakan pendekatan yang lebih aman untuk rotasi file.
    """

    def rotate(self, source, dest):
        """
        Override metode rotate untuk menangani masalah PermissionError di Windows.
        """
        try:
            # Coba metode default terlebih dahulu
            super().rotate(source, dest)
        except PermissionError:
            # Metode fallback jika terjadi locking file di Windows
            self._windows_safe_rotate(source, dest)

    def _windows_safe_rotate(self, source, dest):
        """
        Metode fallback yang lebih aman untuk rotasi file di Windows.
        """
        try:
            # Tutup handler sementara untuk melepaskan lock
            if self.stream:
                self.stream.close()

            # Coba rename file lagi
            if os.path.exists(dest):
                os.remove(dest)
            os.rename(source, dest)

            # Buka kembali file log baru
            self.stream = self._open()
        except Exception as e:
            print(f"Failed to rotate log file: {e}", file=sys.stderr)
            # Jika gagal, coba buka file log kembali tanpa rotasi
            try:
                self.stream = self._open()
            except Exception as open_error:
                print(f"Failed to reopen log file: {open_error}", file=sys.stderr)


def setup_logger(name="AI_TRADING_BACKEND"):
    """
    Konfigurasi Logger Pusat dengan Fix Encoding Windows (UTF-8)
    dan Rotasi File yang Aman di Windows.
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
    logger.propagate = False

    if logger.handlers:
        return logger

    # 2. Format Logging
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 3. Handler 1: File (Rotating) dengan Fix Windows Locking
    # PENTING: Tambahkan encoding='utf-8' agar file log bisa simpan emoji
    file_handler = WindowsRotatingFileHandler(
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
