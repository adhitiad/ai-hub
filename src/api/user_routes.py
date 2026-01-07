"""
adalAH
"""

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel

from src.api.auth import get_current_user

# Fix Imports: Tambahkan 'src.' dan import 'fix_id'
from src.core.agent import get_detailed_signal
from src.core.config_assets import get_asset_info
from src.core.database import fix_id, users_collection

router = APIRouter(prefix="/user", tags=["User Data"])


class TelegramConnectModel(BaseModel):
    telegram_chat_id: str  # String karena ID telegram bisa panjang


@router.post("/connect-telegram")
async def connect_telegram(
    data: TelegramConnectModel, user: dict = Depends(get_current_user)
):
    """
    User memasukkan Chat ID Telegram mereka (didapat dari bot).
    Sistem akan menyimpan ID ini untuk keperluan broadcast.
    """
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$set": {"telegram_chat_id": data.telegram_chat_id}}
    )
    return {
        "status": "success",
        "message": "Telegram berhasil terhubung! Anda akan menerima sinyal live.",
    }


@router.post("/watchlist/add")
async def add_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$addToSet": {"watchlist": symbol}}
    )
    return {"status": "added", "symbol": symbol}


@router.delete("/watchlist/remove")
async def remove_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$pull": {"watchlist": symbol}}
    )
    return {"status": "removed"}


@router.get("/watchlist")
async def get_my_watchlist(user: dict = Depends(get_current_user)):
    current_data = await users_collection.find_one({"_id": user["_id"]})
    return current_data.get("watchlist", []) if current_data else []


@router.get("/admin/search-user")
async def search_users(q: str):
    cursor = users_collection.find({"email": {"$regex": q, "$options": "i"}})
    users = await cursor.to_list(length=10)
    return [fix_id(u) for u in users]


# --- 1. Simpan Konfigurasi Saldo ---
@router.post("/settings/balance")
async def update_balance_settings(
    stock_idr: int = Body(..., embed=True),
    forex_usd: float = Body(..., embed=True),
    user: dict = Depends(get_current_user),
):
    """
    User menginput saldo real mereka.
    Example: stock_idr = 50000000 (50 Juta), forex_usd = 500 (500 Dollar)
    """
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"config_balance": {"stock": stock_idr, "forex": forex_usd}}},
    )
    return {"status": "success", "message": "Saldo trading berhasil diupdate."}


# --- 2. Get Signal dengan Saldo Pribadi ---
@router.get("/signal/check/{symbol}")
async def check_personal_signal(symbol: str, user: dict = Depends(get_current_user)):
    """
    Mengambil sinyal + Money Management yang disesuaikan dengan saldo user.
    """
    # Ambil saldo dari database user
    config = user.get("config_balance", {})

    # Jika user belum seting, pakai default aman
    custom_balance = {
        "stock": config.get("stock", 10000000),  # Default tampilan 10jt
        "forex": config.get("forex", 100),  # Default tampilan 100 usd
    }

    # Get asset info
    asset_info = get_asset_info(symbol)

    # Panggil Agent
    result = get_detailed_signal(symbol, asset_info, custom_balance=custom_balance)

    return result


@router.post("/settings/telegram")
async def update_telegram_id(
    chat_id: str = Body(..., embed=True), user: dict = Depends(get_current_user)
):
    """
    User menyimpan ID Telegram untuk notifikasi.
    Cara dapat ID: User chat ke bot telegram 'userinfobot' atau sejenisnya.
    """
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$set": {"telegram_chat_id": chat_id}}
    )
    return {
        "status": "success",
        "message": "Telegram ID saved. You will verify signals now.",
    }
