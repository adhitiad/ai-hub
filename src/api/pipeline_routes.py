from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends

from src.api.auth import get_current_user
from src.api.roles import UserRole, check_permission
from src.core.pipeline import run_auto_optimization

router = APIRouter(prefix="/pipeline", tags=["AI Auto-Optimizer"])


@router.post("/optimize")
async def trigger_optimization(
    background_tasks: BackgroundTasks,
    symbol: Optional[str] = "BBCA.JK",
    user: dict = Depends(get_current_user),
):
    """
    Menjalankan proses: Train -> Validasi -> Deploy.
    Hanya Owner/Admin yang boleh (karena memakan resource CPU).
    """
    if not check_permission(user["role"], UserRole.ADMIN):
        return {"status": "error", "message": "Permission Denied"}

    # Jalankan di background agar tidak timeout
    background_tasks.add_task(run_auto_optimization, symbol)

    return {
        "status": "started",
        "message": f"Optimasi AI untuk {symbol} berjalan di background. Cek log nanti.",
    }


@router.get("/status")
def get_optimization_status(symbol: Optional[str] = None):
    # Di real app, Anda perlu menyimpan status 'task' ke database/memori
    # untuk dicek progressnya.
    return {
        "symbol": symbol or "all",
        "status": "idle",
        "progress": 0,
        "message": "Pipeline idle. No active optimization task.",
        "last_run": None,
        "eta": None,
    }
