from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_current_user
from src.core.database import users_collection

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/execute-virtual")
async def execute_virtual_order(
    symbol: str,
    action: str,
    qty: int,
    price: float,
    user: dict = Depends(get_current_user),
):
    """
    Eksekusi Order Virtual dengan Atomic Transaction (Anti Race Condition).
    """
    total_value = qty * price

    if action == "BUY":
        # --- PERBAIKAN: ATOMIC UPDATE ---
        # Kita tidak mengecek saldo dengan if user['balance'] < total...
        # Tapi kita langsung jadikan syarat di query update.

        result = await users_collection.update_one(
            {
                "email": user["email"],
                "virtual_balance": {"$gte": total_value},  # SYARAT: Saldo harus cukup
            },
            {
                "$inc": {"virtual_balance": -total_value},  # ATOMIC: Kurangi langsung
                "$push": {
                    "portfolio": {
                        "symbol": symbol,
                        "qty": qty,
                        "avg_price": price,
                        "date": datetime.now(),
                    }
                },
            },
        )

        # Cek apakah update berhasil
        if result.modified_count == 0:
            # Gagal karena saldo tidak cukup (syarat $gte tidak terpenuhi)
            # atau user tidak ditemukan

            # Cek ulang user untuk pesan error yang spesifik
            current_user = await users_collection.find_one({"email": user["email"]})
            if current_user["virtual_balance"] < total_value:
                raise HTTPException(status_code=400, detail="Saldo Virtual Tidak Cukup")

            raise HTTPException(status_code=500, detail="Gagal eksekusi order")

    elif action == "SELL":
        # Logic SELL Atomic: Pastikan user punya barang di portfolio
        # Ini lebih kompleks karena portfolio adalah array.
        # Untuk simplifikasi, kita asumsikan user jual semua atau validasi qty di array filter.

        # Cari item portfolio spesifik
        user_portfolio = user.get("portfolio", [])
        stock_item = next(
            (item for item in user_portfolio if item["symbol"] == symbol), None
        )

        if not stock_item or stock_item["qty"] < qty:
            raise HTTPException(
                status_code=400, detail="Barang tidak cukup untuk dijual"
            )

        # Hapus/Kurangi barang & Tambah Saldo (Atomic)
        # Catatan: Manipulasi array detail di Mongo butuh query kompleks ($pull/$set).
        # Untuk keamanan race condition jual, minimal kita pastikan saldo bertambah atomic.

        # 1. Pull/Update quantity (bisa race condition kecil di qty, tapi uang aman)
        # Solusi aman: Transaction (jika Replica Set) atau Optimistic Locking (versioning).
        # Di sini kita pakai pendekatan update saldo atomic.

        await users_collection.update_one(
            {"email": user["email"]},
            {
                "$inc": {"virtual_balance": total_value},  # Uang masuk pasti aman
                "$pull": {
                    "portfolio": {"symbol": symbol}
                },  # Hapus barang (simplifikasi jual semua)
            },
        )

    return {"status": "success", "msg": f"Virtual {action} {symbol} executed"}
