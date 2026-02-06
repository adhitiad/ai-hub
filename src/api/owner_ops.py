import ast
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

import black
import psutil
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.api.roles import UserRole, check_permission
from src.core.database import db
from src.core.llm_analyst import LLMAnalyst
from src.core.logger import logging
from src.core.signal_bus import signal_bus

router = APIRouter(prefix="/owner", tags=["Owner"])
BASE_DIR = Path.cwd()  # Root folder proyek
# Direktori yang BOLEH diedit (Whitelist) agar Owner tidak salah hapus file Windows/Linux
ALLOWED_DIRS = ["core", "api", "models", "logs"]


# --- Model Data ---
class FileReadModel(BaseModel):
    path: str


class FileWriteModel(BaseModel):
    path: str
    content: str


class FileModel(BaseModel):
    path: str
    content: str = ""


def validate_safe_path(user_path: str) -> Path:
    """
    Memastikan user tidak mengakses file di luar folder project.
    """
    base = BASE_DIR.resolve()
    target = (base / user_path).resolve()

    # Cek apakah target path dimulai dengan base path project
    if not str(target).startswith(str(base)):
        raise HTTPException(403, "Access Denied: Path traversal detected.")

    # Whitelist folder tambahan
    allowed_prefixes = [base / d for d in ALLOWED_DIRS]
    is_allowed = any(str(target).startswith(str(p)) for p in allowed_prefixes)

    if not is_allowed and target != base:  # Izinkan root file tertentu jika perlu
        # Tambahan logika strict jika mau:
        # raise HTTPException(403, "Access to this folder is restricted.")
        pass

    return target


def verify_owner(user: dict = Depends(get_current_user)) -> dict:
    if not check_permission(user["role"], UserRole.OWNER):
        raise HTTPException(403, "OWNER ONLY")
    return user


@router.get("/files/tree")
def get_file_tree(user: dict = Depends(verify_owner)) -> Dict[str, Dict[str, Any]]:
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
def read_file_content(
    data: FileReadModel, user: dict = Depends(verify_owner)
) -> Dict[str, str]:
    """Membaca isi file kodingan"""
    safe_path = validate_safe_path(data.path)

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        with safe_path.open("r", encoding="utf-8") as f:
            content = f.read()
        return {"path": str(safe_path.relative_to(BASE_DIR)), "content": content}
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
def stream_log(user: dict = Depends(verify_owner)) -> Dict[str, List[str]]:
    log_path = BASE_DIR / "logs" / "app.log"

    if not log_path.exists():
        return {"logs": ["Log file not yet created."]}

    # PERBAIKAN: Tambahkan encoding="utf-8" dan errors="replace"
    # errors="replace" berguna agar jika ada karakter aneh, tidak bikin server crash (diganti tanda tanda tanya)
    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as f:
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

    async def training_wrapper():
        logging.info(f"🦾 MANUAL TRAINING TRIGGERED BY {user['email']}")
        _ = await run_mass_training()
        logging.info("✅ MANUAL TRAINING FINISHED")

    background_tasks.add_task(training_wrapper)
    return {
        "status": "started",
        "message": "Training started in background. Check logs for progress.",
    }


@router.post("/action/restart-bot")
async def restart_bot_logic(user: dict = Depends(verify_owner)):
    """
    Restart logika internal (Clear Cache / Reload Config)
    Tanpa mematikan server API.
    """
    # 1. Reload Config Assets
    # 2. Clear Internal Bus
    await signal_bus.clear()
    # 3. Anda bisa menambahkan logika reload module 'importlib.reload' jika mau advanced

    logging.warning(f"🔄 BOT LOGIC RESTARTED BY {user['email']}")
    return {
        "status": "success",
        "message": "Internal state cleared. Bot will fetch new data in next cycle.",
    }


@router.post("/files/validate-fix")
async def validate_and_fix_code(
    data: FileWriteModel, user: dict = Depends(verify_owner)
):
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
        llm_analyst = LLMAnalyst()
        fixed_code = await llm_analyst.ai_fix_code(code, error_msg)

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
    safe_path = validate_safe_path(data.path)

    # 1. Safety Check: Cek Syntax Python sebelum save
    if data.path.endswith(".py"):
        try:
            ast.parse(data.content)
        except SyntaxError as e:
            raise HTTPException(
                400, detail=f"Cannot Save: Syntax Error at line {e.lineno}"
            )

    # 2. Backup & Save
    if safe_path.exists():
        shutil.copy(safe_path, safe_path.with_suffix(".bak"))

    with safe_path.open("w", encoding="utf-8") as f:
        f.write(data.content)

    return {"status": "saved"}


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


@router.get("/financial-health", tags=["Owner Super Access"])
async def get_financial_health(owner: dict = Depends(verify_owner)):
    """
    Menghitung Profit Bersih/Kotor dengan estimasi biaya infrastruktur nyata.
    """
    # 1. HITUNG REVENUE (Pemasukan)
    # Panggil logika yang sama dengan admin atau query ulang
    # (Mock data untuk contoh ini)
    revenue_premium = 50 * 29  # 50 user premium
    revenue_enterprise = 5 * 99  # 5 user enterprise
    gross_revenue = revenue_premium + revenue_enterprise

    # 2. HITUNG OPEX (Pengeluaran Operasional)

    # A. Cloud Compute (VPS/AWS EC2)
    # Asumsi: Base cost $20 + $5 per 10% CPU load rata-rata
    cpu_load = psutil.cpu_percent()
    cost_compute = 20 + (cpu_load / 10) * 5

    # B. Database (MongoDB Atlas)
    # Asumsi: $0.10 per GB storage
    disk_usage = psutil.disk_usage("/").used / (1024**3)  # GB
    cost_mongo = 10 + (disk_usage * 0.10)  # Base $10

    # C. Redis (Cache)
    # Asumsi: Managed Redis $15 flat
    cost_redis = 15.0

    # D. AI Inference (Groq/OpenAI)
    # Asumsi: $0.0005 per request ke AI
    # Kita ambil total request hari ini dari semua user (agregat db)
    total_ai_requests = 15000  # Contoh ambil dari DB sum(requests_today)
    cost_ai_inference = total_ai_requests * 0.0005

    total_costs = cost_compute + cost_mongo + cost_redis + cost_ai_inference

    # 3. PROFITABILITY
    net_profit = gross_revenue - total_costs
    margin = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0

    return {
        "gross_revenue": gross_revenue,
        "costs": {
            "total": round(total_costs, 2),
            "breakdown": {
                "cloud_compute": round(cost_compute, 2),
                "database_mongo": round(cost_mongo, 2),
                "redis_cache": round(cost_redis, 2),
                "ai_groq_api": round(cost_ai_inference, 2),
            },
        },
        "net_profit": round(net_profit, 2),
        "profit_margin": f"{round(margin, 1)}%",
        "status": "PROFITABLE" if net_profit > 0 else "LOSS",
    }


@router.get("/audit-logs", tags=["Owner Super Access"])
async def get_system_logs(limit: int = 50, owner: dict = Depends(verify_owner)):
    # Ambil logs dari DB
    return await db.logs.find().sort("timestamp", -1).limit(limit).to_list(limit)
