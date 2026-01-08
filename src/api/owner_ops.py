import ast
import os
import shutil

import black
import psutil
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.api.roles import UserRole, check_permission
from src.core.llm_analyst import ai_fix_code
from src.core.logger import logging
from src.core.signal_bus import signal_bus

router = APIRouter(prefix="/owner", tags=["Owner"])
BASE_DIR = os.getcwd()
# Direktori yang BOLEH diedit (Whitelist) agar Owner tidak salah hapus file Windows/Linux
ALLOWED_DIRS = ["core", "api", "models", "logs"]
BASE_DIR = os.getcwd()  # Root folder proyek


# --- Model Data ---
class FileWriteModel(BaseModel):
    path: str
    content: str


class FileModel(BaseModel):
    path: str
    content: str = ""


def verify_owner(user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], UserRole.OWNER):
        raise HTTPException(403, "OWNER ONLY")
    return user


@router.get("/files/tree")
def get_file_tree(user: dict = Depends(verify_owner)):
    """Mengambil struktur folder proyek untuk ditampilkan di Sidebar Frontend"""
    file_tree = {}

    for root, dirs, files in os.walk(BASE_DIR):
        # Filter: Hanya tampilkan folder yang diizinkan
        # Ambil relative path
        rel_path = os.path.relpath(root, BASE_DIR)

        if rel_path == "." or any(rel_path.startswith(d) for d in ALLOWED_DIRS):
            file_tree[rel_path] = {
                "folders": dirs,
                "files": [
                    f
                    for f in files
                    if f.endswith((".py", ".json", ".txt", ".md", ".log", ".env"))
                ],
            }

    return file_tree


@router.post("/files/read")
def read_file_content(path_data: dict, user: dict = Depends(verify_owner)):
    """Membaca isi file kodingan"""
    file_path = path_data.get("path")

    if not file_path:
        raise HTTPException(status_code=400, detail="Path is required.")

    # Security Check: Prevent Directory Traversal (../..)
    safe_path = os.path.abspath(os.path.join(BASE_DIR, file_path))
    if not safe_path.startswith(BASE_DIR):
        raise HTTPException(status_code=403, detail="Access denied: Path unsafe.")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": file_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/files/save")
# def save_file(data: FileModel, user=Depends(verify_owner)):
#     path = os.path.abspath(os.path.join(BASE_DIR, data.path))
#     shutil.copy(path, path + ".bak")
#     with open(path, "w") as f:
#         f.write(data.content)
#     return {"status": "saved"}


@router.get("/logs/stream")
def stream_log(user=Depends(verify_owner)):
    log_path = "logs/app.log"

    if not os.path.exists(log_path):
        return {"logs": ["Log file not yet created."]}

    # PERBAIKAN: Tambahkan encoding="utf-8" dan errors="replace"
    # errors="replace" berguna agar jika ada karakter aneh, tidak bikin server crash (diganti tanda tanya)
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            # Ambil 50 baris terakhir
            return {"logs": lines[-50:]}
    except Exception as e:
        return {"logs": [f"Error reading log file: {str(e)}"]}


# ==========================================
# 3. AI TRAINING CONTROL
# ==========================================


@router.post("/action/retrain")
def trigger_manual_training(
    background_tasks: BackgroundTasks, user: dict = Depends(verify_owner)
):
    """
    Owner menekan tombol 'Retrain AI' di dashboard.
    Bot akan belajar ulang di background.
    """
    from train_all import run_mass_training  # Import fungsi training

    def training_wrapper():
        logging.info(f"🦾 MANUAL TRAINING TRIGGERED BY {user['email']}")
        run_mass_training()
        logging.info("✅ MANUAL TRAINING FINISHED")

    background_tasks.add_task(training_wrapper)
    return {
        "status": "started",
        "message": "Training started in background. Check logs for progress.",
    }


@router.post("/action/restart-bot")
def restart_bot_logic(user: dict = Depends(verify_owner)):
    """
    Restart logika internal (Clear Cache / Reload Config)
    Tanpa mematikan server API.
    """
    # 1. Reload Config Assets
    # 2. Clear Internal Bus
    signal_bus._storage = {}
    # 3. Anda bisa menambahkan logika reload module 'importlib.reload' jika mau advanced

    logging.warning(f"🔄 BOT LOGIC RESTARTED BY {user['email']}")
    return {
        "status": "success",
        "message": "Internal state cleared. Bot will fetch new data in next cycle.",
    }


@router.post("/files/validate-fix")
def validate_and_fix_code(data: FileWriteModel, user: dict = Depends(verify_owner)):
    """
    Fitur Magic:
    1. Cek Syntax
    2. Jika Aman -> Format pakai Black (Prettier)
    3. Jika Error -> Minta AI perbaiki (Auto Fix)
    """
    code = data.content

    try:
        # 1. Cek Syntax & Format (Black)
        # Black akan throw error jika syntax python salah
        formatted_code = black.format_str(code, mode=black.Mode())
        return {
            "status": "valid",
            "message": "✅ Code Formatted (Black)",
            "content": formatted_code,
        }

    except Exception as e:
        # Syntax Error terdeteksi!
        error_msg = str(e)

        # 2. Oper ke AI untuk diperbaiki
        print(f"⚠️ Syntax Error Detected: {error_msg}. Asking AI to fix...")
        fixed_code = ai_fix_code(code, error_msg)

        if fixed_code:
            # Validasi ulang hasil kerjaan AI
            try:
                ast.parse(fixed_code)  # Cek syntax lagi
                return {
                    "status": "fixed",
                    "message": "✨ AI Fixed the Syntax Error!",
                    "content": fixed_code,
                }
            except:
                pass  # AI gagal fix

        return {
            "status": "error",
            "message": f"❌ Syntax Error: {error_msg}",
            "content": code,  # Kembalikan kode asli
        }


@router.post("/files/save")
def save_file(data: FileWriteModel, user: dict = Depends(verify_owner)):
    """
    Menyimpan file TAPI menolak jika Syntax Error.
    Mencegah Server Crash (Error 500).
    """
    path = os.path.abspath(os.path.join(BASE_DIR, data.path))

    # 1. Safety Check: Cek Syntax Python sebelum save
    if data.path.endswith(".py"):
        try:
            ast.parse(data.content)
        except SyntaxError as e:
            raise HTTPException(
                400, detail=f"Cannot Save: Syntax Error at line {e.lineno}"
            )

    # 2. Backup & Save
    if os.path.exists(path):
        shutil.copy(path, path + ".bak")

    with open(path, "w", encoding="utf-8") as f:
        f.write(data.content)

    return {"status": "saved"}


from src.core.database import db


@router.get("/db/view/{collection_name}")
async def view_database_content(
    collection_name: str, limit: int = 20, user: dict = Depends(verify_owner)
):
    """
    Owner Only: Mengintip isi database mentah.
    """
    if collection_name not in ["users", "signals", "transactions", "upgrade_requests"]:
        raise HTTPException(400, "Restricted Collection")

    try:
        cursor = db[collection_name].find({}).limit(limit).sort("_id", -1)
        data = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for item in data:
            if "_id" in item:
                item["id"] = str(item["_id"])
                del item["_id"]

        return data
    except Exception as e:
        raise HTTPException(500, str(e))
