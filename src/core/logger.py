import logging
import os
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
            if os.path.exists(source):
                super().rotate(source, dest)
        except (PermissionError, OSError):
            # OSError menangkap WinError 32: File being used by another process
            self._windows_safe_rotate(source, dest)

    def _windows_safe_rotate(self, source, dest):
        """
        Metode fallback yang lebih aman untuk rotasi file di Windows.
        """
        try:
            # Tutup handler sementara untuk melepaskan lock
            if self.stream:
                self.stream.close()
                self.stream = None

            # Jika file tujuan ada, coba hapus dulu
            if os.path.exists(dest):
                try:
                    os.remove(dest)
                except Exception:
                    pass

            # Coba rename file lagi
            if os.path.exists(source):
                try:
                    os.rename(source, dest)
                except Exception:
                    # Jika rename gagal (masih lock), coba copy + truncate
                    # Ini adalah metode 'last resort'
                    try:
                        import shutil
                        shutil.copy2(source, dest)
                        with open(source, 'w', encoding=self.encoding) as f:
                            f.truncate()
                    except Exception:
                        pass

            # Buka kembali file log baru
            self.stream = self._open()
        except Exception:
            # Jika semua gagal, coba buka kembali stream agar logging tetap jalan
            try:
                if not self.stream:
                    self.stream = self._open()
            except Exception:
                pass


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
